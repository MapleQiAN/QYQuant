from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from qysp.builder import build_package
from qysp.validator import validate

from .compiler.qyir_to_qysp import compile_qyir_to_qysp_project
from .verifiers.schema_verifier import verify_qyir_schema
from ..services.strategy_import_analysis import analyze_strategy_import


class QSGAPipelineError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def build_qsga_draft(qyir: dict, *, owner_id: str) -> dict:
    schema_result = verify_qyir_schema(qyir)
    if not schema_result.passed:
        raise QSGAPipelineError("QYIR_SCHEMA_INVALID", "QYIR schema verification failed", schema_result.to_dict())

    with TemporaryDirectory(prefix="qsga-") as temp_dir:
        temp_root = Path(temp_dir)
        project_dir = compile_qyir_to_qysp_project(qyir, temp_root / "project")
        validation = validate(project_dir)
        if not validation["valid"]:
            raise QSGAPipelineError("QYSP_VALIDATION_FAILED", "Compiled QYSP project is invalid", validation)

        package_path = build_package(project_dir, temp_root / "strategy.qys")
        upload = _BufferedUpload(
            filename="qsga-strategy.qys",
            mimetype="application/octet-stream",
            payload=package_path.read_bytes(),
        )
        draft, _source_file, analysis = analyze_strategy_import(upload, owner_id=owner_id)

    return {
        "status": "draft_ready",
        "verification": {
            "schema": schema_result.to_dict(),
            "qysp": {"status": "pass", "errors": []},
        },
        "analysis": {
            **analysis,
            "draftImportId": draft.id,
        },
    }


class _BufferedUpload:
    def __init__(self, *, filename: str, mimetype: str, payload: bytes):
        self.filename = filename
        self.mimetype = mimetype
        self._payload = payload

    def read(self) -> bytes:
        return self._payload
