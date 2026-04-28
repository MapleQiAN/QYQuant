from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .compiler.qyir_to_qysp import compile_qyir_to_qysp_project
from .guardrails import verify_intent_guardrails
from .result import VerificationResult, not_run_result
from .verifiers.domain_verifier import verify_qyir_domain
from .verifiers.qysp_verifier import build_and_analyze_qysp_project, verify_qysp_project
from .verifiers.runtime_verifier import verify_runtime_contract
from .verifiers.schema_verifier import verify_qyir_schema
from .verifiers.semantic_verifier import verify_semantic_slots


class QSGAPipelineError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def build_qsga_draft(qyir: dict, *, owner_id: str) -> dict:
    verification: dict[str, VerificationResult] = {
        "guardrails": not_run_result(),
        "schema": not_run_result(),
        "domain": not_run_result(),
        "semantic": not_run_result(),
        "qysp": not_run_result(),
        "runtime": not_run_result(),
    }

    guardrails_result = verify_intent_guardrails(qyir)
    verification["guardrails"] = guardrails_result
    if not guardrails_result.passed:
        return _pipeline_response(guardrails_result.status, verification)

    schema_result = verify_qyir_schema(qyir)
    verification["schema"] = schema_result
    if not schema_result.passed:
        return _pipeline_response("blocked", verification)

    domain_result = verify_qyir_domain(qyir)
    verification["domain"] = domain_result
    if not domain_result.passed:
        return _pipeline_response("blocked", verification)

    semantic_result = verify_semantic_slots(qyir)
    verification["semantic"] = semantic_result
    if not semantic_result.passed:
        return _pipeline_response("blocked", verification)

    with TemporaryDirectory(prefix="qsga-") as temp_dir:
        temp_root = Path(temp_dir)
        project_dir = compile_qyir_to_qysp_project(qyir, temp_root / "project")
        qysp_validation = verify_qysp_project(project_dir)
        verification["qysp"] = qysp_validation
        if not qysp_validation.passed:
            return _pipeline_response("blocked", verification)

        draft, _source_file, analysis, qysp_import_result = build_and_analyze_qysp_project(
            project_dir,
            temp_root / "strategy.qys",
            owner_id=owner_id,
        )
        verification["qysp"] = qysp_import_result
        if not qysp_import_result.passed:
            return _pipeline_response("blocked", verification)

        runtime_result = verify_runtime_contract(qyir, analysis)
        verification["runtime"] = runtime_result
        if not runtime_result.passed:
            return _pipeline_response("blocked", verification)

    return {
        "status": "draft_ready",
        "verification": _verification_payload(verification),
        "analysis": {
            **analysis,
            "draftImportId": draft.id,
        },
    }


def _pipeline_response(status: str, verification: dict[str, VerificationResult]) -> dict:
    return {
        "status": status,
        "verification": _verification_payload(verification),
        "analysis": {},
    }


def _verification_payload(verification: dict[str, VerificationResult]) -> dict:
    return {name: result.to_dict() for name, result in verification.items()}
