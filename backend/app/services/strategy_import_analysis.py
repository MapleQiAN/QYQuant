import ast
import io
import json
import os
import uuid
import zipfile
from datetime import timedelta
from pathlib import Path

from ..extensions import db
from ..models import File, StrategyImportDraft
from ..utils.time import now_utc


MAX_IMPORT_SIZE = 10 * 1024 * 1024
ALLOWED_ANALYZE_EXT = {".py", ".zip", ".qys"}
IGNORED_DEPENDENCY_MANIFESTS = {"requirements.txt", "pyproject.toml", "setup.py", "Pipfile"}


class StrategyImportAnalysisError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def analyze_strategy_import(file_storage, owner_id):
    original_name = file_storage.filename or "strategy.py"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_ANALYZE_EXT:
        raise StrategyImportAnalysisError(
            "INVALID_FILE_TYPE",
            "Only .py, .zip, and .qys uploads are supported",
            400,
        )

    payload = file_storage.read()
    if not payload:
        raise StrategyImportAnalysisError("FILE_REQUIRED", "Strategy source file is required", 400)
    if len(payload) > MAX_IMPORT_SIZE:
        raise StrategyImportAnalysisError("FILE_TOO_LARGE", "Strategy source exceeds 10 MB", 400)

    stored_path = _strategy_storage_root() / "imports" / "raw" / f"{uuid.uuid4().hex}{ext}"
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(payload)

    file_record = File(
        owner_id=owner_id,
        filename=original_name,
        content_type=file_storage.mimetype or "application/octet-stream",
        size=len(payload),
        path=stored_path.as_posix(),
    )
    db.session.add(file_record)
    db.session.flush()

    analysis = _analyze_payload(original_name, payload)
    draft = StrategyImportDraft(
        owner_id=owner_id,
        source_file_id=file_record.id,
        source_type=analysis["sourceType"],
        status="analyzed",
        analysis_payload=analysis,
        expires_at=now_utc() + timedelta(hours=24),
    )
    db.session.add(draft)
    db.session.commit()
    return draft, file_record, analysis


def _analyze_payload(filename, payload):
    ext = Path(filename).suffix.lower()
    if ext == ".py":
        return _analyze_python_file(filename, payload)
    if ext in {".zip", ".qys"}:
        return _analyze_archive(filename, payload, source_type="qys_package" if ext == ".qys" else "source_zip")
    raise StrategyImportAnalysisError("INVALID_FILE_TYPE", "Unsupported strategy source type", 400)


def _analyze_python_file(filename, payload):
    try:
        source = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StrategyImportAnalysisError("INVALID_SOURCE", "Python source must be UTF-8", 422) from exc

    path = Path(filename).name
    inspection = _inspect_source(source, path)
    candidates = inspection["candidates"]
    errors = []
    if not inspection["syntaxValid"]:
      errors.append("Python syntax could not be parsed")
    elif not candidates:
      errors.append("No supported strategy entrypoint candidates found")

    metadata_candidates = {
        "name": _derived_name_from_filename(filename),
    }
    return {
        "sourceType": "python_file",
        "fileSummary": {
            "filename": filename,
            "size": len(payload),
            "entries": [path],
        },
        "entrypointCandidates": candidates,
        "metadataCandidates": metadata_candidates,
        "parameterCandidates": [],
        "warnings": [],
        "errors": errors,
        "validation": _build_validation(
            entrypoint_found=bool(candidates),
            syntax_valid=inspection["syntaxValid"],
            order_list_return_likely=inspection["orderListReturnLikely"],
            metadata_candidates=metadata_candidates,
        ),
    }


def _analyze_archive(filename, payload, *, source_type):
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload), "r")
    except zipfile.BadZipFile as exc:
        raise StrategyImportAnalysisError("INVALID_ARCHIVE", "Uploaded archive is invalid", 422) from exc

    with archive:
        entries = sorted(name for name in archive.namelist() if not name.endswith("/"))
        warnings = []
        errors = []
        candidates = []
        manifest = None

        if "strategy.json" in entries:
            try:
                manifest = json.loads(archive.read("strategy.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise StrategyImportAnalysisError("INVALID_STRATEGY_PACKAGE", "strategy.json is invalid", 422) from exc

        for entry in entries:
            if Path(entry).name in IGNORED_DEPENDENCY_MANIFESTS:
                warnings.append(f"Ignored unsupported dependency manifest: {Path(entry).name}")

        syntax_valid = True
        order_list_return_likely = None

        if manifest is not None:
            entrypoint = manifest.get("entrypoint") or {}
            entrypoint_path = (entrypoint.get("path") or "src/strategy.py").replace("\\", "/")
            entrypoint_callable = entrypoint.get("callable") or "Strategy"
            try:
                entrypoint_source = archive.read(entrypoint_path).decode("utf-8")
            except KeyError as exc:
                raise StrategyImportAnalysisError("INVALID_STRATEGY_PACKAGE", "Strategy entrypoint is missing", 422) from exc
            except UnicodeDecodeError as exc:
                raise StrategyImportAnalysisError("INVALID_SOURCE", f"{entrypoint_path} must be UTF-8", 422) from exc

            inspection = _inspect_source(entrypoint_source, entrypoint_path)
            syntax_valid = inspection["syntaxValid"]
            order_list_return_likely = inspection["orderListReturnLikely"]
            candidates.append(
                {
                    "path": entrypoint_path,
                    "callable": entrypoint_callable,
                    "interface": entrypoint.get("interface") or "event_v1",
                    "confidence": 1.0,
                }
            )
            if not syntax_valid:
                errors.append("Python syntax could not be parsed")
        else:
            any_syntax_error = False
            for entry in entries:
                if not entry.endswith(".py"):
                    continue
                try:
                    source = archive.read(entry).decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise StrategyImportAnalysisError("INVALID_SOURCE", f"{entry} must be UTF-8", 422) from exc
                inspection = _inspect_source(source, entry)
                candidates.extend(inspection["candidates"])
                if inspection["syntaxValid"] and inspection["orderListReturnLikely"] is not None and order_list_return_likely is None:
                    order_list_return_likely = inspection["orderListReturnLikely"]
                if not inspection["syntaxValid"]:
                    any_syntax_error = True

        candidates = _dedupe_candidates(candidates)
        if not candidates and manifest is None and any_syntax_error:
            syntax_valid = False
            errors.append("Python syntax could not be parsed")
        elif not candidates:
            errors.append("No supported strategy entrypoint candidates found")

        metadata_candidates = _metadata_from_manifest(manifest) if manifest else {"name": _derived_name_from_filename(filename)}
        parameter_candidates = (manifest or {}).get("parameters") or []
        return {
            "sourceType": source_type,
            "fileSummary": {
                "filename": filename,
                "size": len(payload),
                "entries": entries,
            },
            "entrypointCandidates": candidates,
            "metadataCandidates": metadata_candidates,
            "parameterCandidates": parameter_candidates,
            "warnings": warnings,
            "errors": errors,
            "validation": _build_validation(
                entrypoint_found=bool(candidates),
                syntax_valid=syntax_valid,
                order_list_return_likely=order_list_return_likely,
                metadata_candidates=metadata_candidates,
            ),
        }


def _inspect_source(source, path):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {
            "candidates": [],
            "syntaxValid": False,
            "orderListReturnLikely": None,
        }

    candidates = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Strategy":
            candidates.append(
                {
                    "path": path,
                    "callable": "Strategy",
                    "interface": "event_v1",
                    "confidence": 0.9,
                }
            )
        if isinstance(node, ast.FunctionDef) and node.name == "on_bar":
            candidates.append(
                {
                    "path": path,
                    "callable": "on_bar",
                    "interface": "event_v1",
                    "confidence": 0.8,
                }
            )
    return {
        "candidates": _dedupe_candidates(candidates),
        "syntaxValid": True,
        "orderListReturnLikely": _infer_order_list_return(tree),
    }


def _dedupe_candidates(candidates):
    deduped = []
    seen = set()
    for candidate in candidates:
        key = (candidate["path"], candidate["callable"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _metadata_from_manifest(manifest):
    if manifest is None:
        return {}
    return {
        "name": manifest.get("name"),
        "description": manifest.get("description"),
        "category": ((manifest.get("ui") or {}).get("category") or "other"),
        "tags": manifest.get("tags") or [],
        "symbol": _safe_symbol(manifest),
    }


def _derived_name_from_filename(filename):
    stem = Path(filename).stem.replace("-", " ").replace("_", " ").strip()
    return " ".join(part.capitalize() for part in stem.split()) or "Imported Strategy"


def _safe_symbol(manifest):
    universe = manifest.get("universe") or {}
    symbols = universe.get("symbols") or []
    if symbols:
        return symbols[0]

    dataset = (manifest.get("performance") or {}).get("backtest") or {}
    symbol = (dataset.get("dataset") or {}).get("symbol")
    return symbol or "N/A"


def _build_validation(*, entrypoint_found, syntax_valid, order_list_return_likely, metadata_candidates):
    return {
        "entrypointFound": entrypoint_found,
        "pythonSyntaxValid": syntax_valid,
        "orderListReturnLikely": order_list_return_likely,
        "metadataDetected": bool((metadata_candidates or {}).get("name") or (metadata_candidates or {}).get("symbol")),
    }


def _infer_order_list_return(tree):
    targets = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "on_bar":
            targets.append(node)
        if isinstance(node, ast.ClassDef) and node.name == "Strategy":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "on_bar":
                    targets.append(child)

    if not targets:
        return None

    saw_return = False
    for target in targets:
        for child in ast.walk(target):
            if not isinstance(child, ast.Return):
                continue
            saw_return = True
            if isinstance(child.value, ast.List):
                return True
    return False if saw_return else None


def _strategy_storage_root():
    configured = os.getenv("STRATEGY_STORAGE_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "storage"
