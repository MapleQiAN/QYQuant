import json
import os
import uuid
import zipfile
from pathlib import Path

from qysp.parameters import ValidationError as QYSPValidationError
from qysp.validator import validate_integrity, validate_schema

from ..extensions import db
from ..models import Strategy
from ..utils.crypto import encrypt_strategy, hash_strategy_source
from ..utils.time import now_ms


MAX_IMPORT_SIZE = 10 * 1024 * 1024
ALLOWED_IMPORT_EXT = {".qys", ".zip"}


class StrategyImportError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def import_strategy_package(file_storage, owner_id):
    original_name = file_storage.filename or "strategy.qys"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_IMPORT_EXT:
        raise StrategyImportError("INVALID_FILE_TYPE", "Only .qys packages are supported", 400)

    payload = file_storage.read()
    if not payload:
        raise StrategyImportError("FILE_REQUIRED", "Strategy package is required", 400)
    if len(payload) > MAX_IMPORT_SIZE:
        raise StrategyImportError("FILE_TOO_LARGE", "Strategy package exceeds 10 MB", 400)

    temp_path = _strategy_storage_root() / "_tmp" / f"{uuid.uuid4().hex}{ext}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(payload)
    try:
        from .strategy_import_analysis import StrategyImportAnalysisError, analyze_strategy_import
        from .strategy_import_confirm import StrategyImportConfirmError, confirm_strategy_import

        manifest, _ = _parse_package(temp_path)
        _validate_manifest(manifest)
        _validate_package_integrity(temp_path)

        buffered_upload = _BufferedImportUpload(
            filename=original_name,
            mimetype=file_storage.mimetype or "application/octet-stream",
            payload=payload,
        )
        draft, source_file, analysis = analyze_strategy_import(buffered_upload, owner_id)
        errors = analysis.get("errors") or []
        if errors:
            raise StrategyImportError("INVALID_STRATEGY_PACKAGE", errors[0], 422, details=errors)

        candidates = analysis.get("entrypointCandidates") or []
        if not candidates:
            raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "Strategy entrypoint is missing", 422)
        if len(candidates) > 1:
            raise StrategyImportError(
                "AMBIGUOUS_STRATEGY_ENTRYPOINT",
                "Legacy import only supports a single detected strategy entrypoint",
                422,
                details=candidates,
            )

        strategy, version, _built_file = confirm_strategy_import(
            draft.id,
            owner_id=owner_id,
            payload=_build_legacy_confirm_payload(draft.id, analysis, candidates[0]),
        )
        return strategy, version, source_file
    except StrategyImportAnalysisError as exc:
        raise StrategyImportError(exc.code, exc.message, exc.status, details=exc.details) from exc
    except StrategyImportConfirmError as exc:
        raise StrategyImportError(exc.code, exc.message, exc.status, details=exc.details) from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _build_legacy_confirm_payload(draft_import_id, analysis, entrypoint_candidate):
    metadata = dict(analysis.get("metadataCandidates") or {})
    if metadata.get("symbol") == "N/A":
        metadata.pop("symbol")
    return {
        "draftImportId": draft_import_id,
        "selectedEntrypoint": entrypoint_candidate,
        "metadata": metadata,
        "parameterDefinitions": analysis.get("parameterCandidates"),
    }


class _BufferedImportUpload:
    def __init__(self, *, filename, mimetype, payload):
        self.filename = filename
        self.mimetype = mimetype
        self._payload = payload

    def read(self):
        return self._payload


def _parse_package(package_path):
    try:
        with zipfile.ZipFile(package_path, "r") as archive:
            try:
                manifest = json.loads(archive.read("strategy.json").decode("utf-8"))
            except KeyError as exc:
                raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "strategy.json is required", 422) from exc
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "strategy.json is invalid", 422) from exc

            entrypoint = ((manifest.get("entrypoint") or {}).get("path") or "src/strategy.py").replace("\\", "/")
            try:
                entrypoint_source = archive.read(entrypoint).decode("utf-8")
            except KeyError as exc:
                raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "Strategy entrypoint is missing", 422) from exc
            except UnicodeDecodeError as exc:
                raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "Strategy entrypoint must be UTF-8", 422) from exc
            return manifest, entrypoint_source
    except zipfile.BadZipFile as exc:
        raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "Invalid .qys archive", 422) from exc


def _validate_manifest(manifest):
    errors = validate_schema(manifest)
    if errors:
        raise StrategyImportError("INVALID_STRATEGY_PACKAGE", "strategy.json schema validation failed", 422, details=errors)


def _validate_package_integrity(package_path):
    try:
        validate_integrity(package_path)
    except QYSPValidationError as exc:
        raise StrategyImportError("INTEGRITY_CHECK_FAILED", "File integrity check failed", 422) from exc


def _upsert_strategy(*, manifest, entrypoint_source, owner_id, storage_key):
    strategy_id = manifest.get("id") or str(uuid.uuid4())
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is not None and strategy.owner_id not in {None, owner_id}:
        raise StrategyImportError("STRATEGY_NOT_FOUND", "Strategy not found", 404)

    tags = manifest.get("tags")
    if not isinstance(tags, list):
        tags = []

    category = ((manifest.get("ui") or {}).get("category") or "other").strip() or "other"
    payload = entrypoint_source.encode("utf-8")
    fields = {
        "name": manifest.get("name") or "Imported Strategy",
        "symbol": _safe_symbol(manifest),
        "status": "draft",
        "description": manifest.get("description"),
        "category": category,
        "source": "upload",
        "tags": tags,
        "owner_id": owner_id,
        "storage_key": storage_key,
        "code_encrypted": _encrypt_strategy_payload(payload),
        "code_hash": hash_strategy_source(payload),
        "last_update": now_ms(),
        "updated_at": now_ms(),
    }

    if strategy is None:
        strategy = Strategy(
            id=strategy_id,
            returns=0,
            win_rate=0,
            max_drawdown=0,
            trades=0,
            created_at=now_ms(),
            **fields,
        )
        db.session.add(strategy)
        db.session.flush()
        return strategy

    for key, value in fields.items():
        setattr(strategy, key, value)
    db.session.flush()
    return strategy


def _encrypt_strategy_payload(payload):
    try:
        return encrypt_strategy(payload)
    except RuntimeError as exc:
        raise StrategyImportError(
            "STRATEGY_ENCRYPTION_UNAVAILABLE",
            "Strategy encryption is not configured",
            503,
        ) from exc
    except ValueError as exc:
        raise StrategyImportError(
            "STRATEGY_ENCRYPTION_UNAVAILABLE",
            "Strategy encryption key is invalid",
            503,
            details={"reason": str(exc)},
        ) from exc


def _safe_symbol(manifest):
    universe = manifest.get("universe") or {}
    symbols = universe.get("symbols") or []
    if symbols:
        return symbols[0]

    dataset = (manifest.get("performance") or {}).get("backtest") or {}
    symbol = (dataset.get("dataset") or {}).get("symbol")
    return symbol or "N/A"


def _strategy_storage_root():
    configured = os.getenv("STRATEGY_STORAGE_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "storage"
