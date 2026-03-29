import hashlib
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path

from qysp.builder import build_package

from ..extensions import db
from ..models import File, StrategyImportDraft, StrategyVersion
from .strategy_import import (
    _strategy_storage_root,
    _upsert_strategy,
    _validate_manifest,
    _validate_package_integrity,
)


class StrategyImportConfirmError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def confirm_strategy_import(draft_import_id, *, owner_id, payload):
    draft = db.session.get(StrategyImportDraft, draft_import_id)
    if draft is None or draft.owner_id != owner_id:
        raise StrategyImportConfirmError("DRAFT_IMPORT_NOT_FOUND", "Import draft not found", 404)

    source_file = db.session.get(File, draft.source_file_id)
    if source_file is None or not source_file.path:
        raise StrategyImportConfirmError("DRAFT_SOURCE_NOT_FOUND", "Import source file not found", 404)

    if draft.source_type == "qys_package":
        try:
            _validate_package_integrity(source_file.path)
        except Exception as exc:
            raise StrategyImportConfirmError("INTEGRITY_CHECK_FAILED", "File integrity check failed", 422) from exc

    selected_entrypoint = payload.get("selectedEntrypoint") or {}
    selected_path = selected_entrypoint.get("path")
    selected_callable = selected_entrypoint.get("callable")
    selected_interface = selected_entrypoint.get("interface") or "event_v1"
    if not selected_path or not selected_callable:
        raise StrategyImportConfirmError("ENTRYPOINT_REQUIRED", "Selected entrypoint is required", 400)

    metadata = payload.get("metadata") or {}
    parameter_definitions = payload.get("parameterDefinitions")

    temp_root = _strategy_storage_root() / "_tmp" / f"confirm-{uuid.uuid4().hex}"
    project_dir = temp_root / "project"
    project_src_dir = project_dir / "src"
    project_src_dir.mkdir(parents=True, exist_ok=True)

    try:
        raw_payload = Path(source_file.path).read_bytes()
        source_text, base_manifest = _resolve_source_and_manifest(
            raw_payload,
            draft.source_type,
            selected_path,
        )

        manifest = _build_manifest(
            base_manifest=base_manifest,
            metadata=metadata,
            parameter_definitions=parameter_definitions,
            selected_callable=selected_callable,
            selected_interface=selected_interface,
        )
        _validate_manifest(manifest)

        (project_dir / "strategy.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (project_src_dir / "strategy.py").write_text(source_text, encoding="utf-8")

        built_package_path = temp_root / "built.qys"
        build_package(project_dir, output=built_package_path)
        _validate_package_integrity(built_package_path)
        package_bytes = built_package_path.read_bytes()

        storage_key = f"strategies/{uuid.uuid4().hex}.qys"
        stored_path = _strategy_storage_root() / storage_key
        stored_path.parent.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(package_bytes)

        strategy = _upsert_strategy(
            manifest=manifest,
            entrypoint_source=source_text,
            owner_id=owner_id,
            storage_key=storage_key,
        )

        built_file = File(
            owner_id=owner_id,
            filename=f"{manifest['id']}-{manifest['version']}.qys",
            content_type="application/zip",
            size=len(package_bytes),
            path=stored_path.as_posix(),
        )
        db.session.add(built_file)
        db.session.flush()

        strategy.original_source_file_id = source_file.id
        strategy.built_package_file_id = built_file.id

        version = StrategyVersion(
            strategy_id=strategy.id,
            version=manifest.get("version") or "1.0.0",
            file_id=built_file.id,
            checksum=hashlib.sha256(package_bytes).hexdigest(),
        )
        db.session.add(version)

        draft.status = "confirmed"
        db.session.commit()
        return strategy, version, built_file
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)


def _resolve_source_and_manifest(raw_payload, source_type, selected_path):
    if source_type == "python_file":
        try:
            return raw_payload.decode("utf-8"), {}
        except UnicodeDecodeError as exc:
            raise StrategyImportConfirmError("INVALID_SOURCE", "Python source must be UTF-8", 422) from exc

    if source_type not in {"source_zip", "qys_package"}:
        raise StrategyImportConfirmError("UNSUPPORTED_SOURCE_TYPE", "Unsupported import draft source type", 422)

    try:
        archive = zipfile.ZipFile(io.BytesIO(raw_payload), "r")
    except zipfile.BadZipFile as exc:
        raise StrategyImportConfirmError("INVALID_ARCHIVE", "Import source archive is invalid", 422) from exc

    with archive:
        names = {name.replace("\\", "/"): name for name in archive.namelist() if not name.endswith("/")}
        manifest = {}
        if "strategy.json" in names:
            try:
                manifest = json.loads(archive.read(names["strategy.json"]).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise StrategyImportConfirmError("INVALID_STRATEGY_PACKAGE", "strategy.json is invalid", 422) from exc

        archive_entry = names.get(selected_path.replace("\\", "/"))
        if archive_entry is None:
            raise StrategyImportConfirmError("ENTRYPOINT_SOURCE_MISSING", "Selected entrypoint source is missing", 422)

        try:
            source_text = archive.read(archive_entry).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StrategyImportConfirmError("INVALID_SOURCE", "Selected entrypoint source must be UTF-8", 422) from exc
        return source_text, manifest


def _build_manifest(*, base_manifest, metadata, parameter_definitions, selected_callable, selected_interface):
    manifest = dict(base_manifest or {})
    manifest["schemaVersion"] = "1.0"
    manifest["kind"] = "QYStrategy"
    manifest["id"] = manifest.get("id") or str(uuid.uuid4())
    manifest["name"] = metadata.get("name") or manifest.get("name") or "Imported Strategy"
    manifest["version"] = metadata.get("version") or manifest.get("version") or "1.0.0"
    description = metadata.get("description") or manifest.get("description")
    if description:
        manifest["description"] = description
    else:
        manifest.pop("description", None)
    manifest["language"] = "python"
    manifest["runtime"] = manifest.get("runtime") or {"name": "python", "version": "3.11"}
    manifest["entrypoint"] = {
        "path": "src/strategy.py",
        "callable": selected_callable,
        "interface": selected_interface or "event_v1",
    }
    manifest["parameters"] = parameter_definitions if parameter_definitions is not None else (manifest.get("parameters") or [])
    manifest["tags"] = metadata.get("tags") or manifest.get("tags") or []
    manifest["ui"] = {
        **(manifest.get("ui") or {}),
        "category": metadata.get("category") or ((manifest.get("ui") or {}).get("category")) or "other",
    }

    symbol = metadata.get("symbol")
    if symbol:
        manifest["universe"] = {
            **(manifest.get("universe") or {}),
            "symbols": [symbol],
        }
    return manifest
