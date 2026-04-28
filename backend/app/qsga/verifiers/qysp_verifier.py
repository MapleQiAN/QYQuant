from __future__ import annotations

from pathlib import Path

from qysp.builder import build_package
from qysp.validator import validate

from ..errors import verification_error
from ..result import VerificationError, VerificationResult, fail_result, pass_result
from ...services.strategy_import_analysis import analyze_strategy_import


class BufferedUpload:
    def __init__(self, *, filename: str, mimetype: str, payload: bytes):
        self.filename = filename
        self.mimetype = mimetype
        self._payload = payload

    def read(self) -> bytes:
        return self._payload


def verify_qysp_project(project_dir: str | Path) -> VerificationResult:
    validation = validate(project_dir)
    if validation["valid"]:
        return pass_result()
    return fail_result(
        [
            verification_error(
                "QYSP_VALIDATION_FAILED",
                "$.qysp",
                "Compiled QYSP project is invalid",
                category="qysp",
            )
        ]
    )


def build_and_analyze_qysp_project(project_dir: str | Path, package_path: str | Path, *, owner_id: str):
    errors: list[VerificationError] = []
    package = build_package(project_dir, package_path)
    upload = BufferedUpload(
        filename="qsga-strategy.qys",
        mimetype="application/octet-stream",
        payload=package.read_bytes(),
    )
    draft, source_file, analysis = analyze_strategy_import(upload, owner_id=owner_id)
    candidates = analysis.get("entrypointCandidates") or []
    if analysis.get("errors"):
        errors.append(
            verification_error(
                "QYSP_IMPORT_ANALYSIS_FAILED",
                "$.analysis.errors",
                "QYSP import analysis reported blocking errors",
                category="qysp",
            )
        )
    if not any(candidate.get("callable") == "on_bar" for candidate in candidates):
        errors.append(
            verification_error(
                "QYSP_ENTRYPOINT_NOT_FOUND",
                "$.analysis.entrypointCandidates",
                "Compiled package must expose on_bar entrypoint",
                category="qysp",
            )
        )
    return draft, source_file, analysis, fail_result(errors) if errors else pass_result()
