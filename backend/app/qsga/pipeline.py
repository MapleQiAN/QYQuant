from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .compiler.qyir_to_qysp import compile_qyir_to_qysp_project
from .guardrails import verify_intent_guardrails
from .repair.loop import run_repair_loop
from .result import VerificationResult, not_run_result, running_result
from .verifiers.backtest_verifier import verify_backtest_result
from .verifiers.domain_verifier import verify_qyir_domain
from .verifiers.qysp_verifier import build_and_analyze_qysp_project, verify_qysp_project
from .verifiers.risk_auditor import audit_risk_constraints, verify_risk_audit
from .verifiers.runtime_verifier import verify_runtime_contract
from .verifiers.schema_verifier import verify_qyir_schema
from .verifiers.semantic_verifier import verify_semantic_slots
from ..extensions import db
from ..models import BacktestJob, BacktestJobStatus


class QSGAPipelineError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


TRUSTED_QSGA_REQUIRED_CHECKS = (
    "guardrails",
    "schema",
    "domain",
    "semantic",
    "qysp",
    "runtime",
    "backtest",
    "risk",
)


def build_qsga_draft(
    qyir: dict, *, owner_id: str, options: dict | None = None, backtest_runner=None
) -> dict:
    options = options or {}
    draft_payload = _build_verified_draft(qyir, owner_id=owner_id)
    if draft_payload["status"] != "draft_ready" or not _run_backtest_enabled(options):
        return _attach_trust_payload(draft_payload)

    return _attach_trust_payload(
        _handle_backtest_phase(
            qyir,
            draft_payload,
            owner_id=owner_id,
            options=options,
            backtest_runner=backtest_runner,
        )
    )


def _build_verified_draft(qyir: dict, *, owner_id: str) -> dict:
    verification: dict[str, VerificationResult] = {
        "guardrails": not_run_result(),
        "schema": not_run_result(),
        "domain": not_run_result(),
        "semantic": not_run_result(),
        "qysp": not_run_result(),
        "runtime": not_run_result(),
        "backtest": not_run_result(),
        "risk": not_run_result(),
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

        draft, _source_file, analysis, qysp_import_result = (
            build_and_analyze_qysp_project(
                project_dir,
                temp_root / "strategy.qys",
                owner_id=owner_id,
            )
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


def _handle_backtest_phase(
    qyir: dict, draft_payload: dict, *, owner_id: str, options: dict, backtest_runner
) -> dict:
    backtest_result = options.get("backtestResult") or options.get("backtest_result")
    if backtest_result is None and backtest_runner is not None:
        backtest_result = backtest_runner(qyir, draft_payload)

    if backtest_result is None:
        return _mark_backtest_running(
            qyir, draft_payload, owner_id=owner_id, options=options
        )

    backtest_verification = verify_backtest_result(backtest_result)
    draft_payload["verification"]["backtest"] = backtest_verification.to_dict()
    if not backtest_verification.passed:
        draft_payload["status"] = "blocked"
        return draft_payload

    risk_audit = audit_risk_constraints(qyir, backtest_result)
    risk_verification = verify_risk_audit(risk_audit)
    draft_payload["verification"]["risk"] = risk_verification.to_dict()
    draft_payload["analysis"]["riskAudit"] = risk_audit
    draft_payload["analysis"]["historicalRiskNotice"] = (
        "风险结论仅描述指定历史回测窗口，不构成未来收益或风险保证。"
    )
    if risk_verification.passed:
        return draft_payload

    if _repair_enabled(options) and backtest_runner is not None:
        repair_result = run_repair_loop(
            qyir,
            risk_audit,
            draft_builder=lambda candidate: _build_verified_draft(
                candidate, owner_id=owner_id
            ),
            backtest_runner=backtest_runner,
            max_attempts=_max_repair_attempts(options),
        )
        if repair_result["status"] == "repaired":
            repaired_payload = repair_result["draft"]
            repaired_payload["verification"]["backtest"] = verify_backtest_result(
                repair_result["backtest_result"]
            ).to_dict()
            repaired_payload["verification"]["risk"] = verify_risk_audit(
                repair_result["risk_audit"]
            ).to_dict()
            repaired_payload["analysis"]["riskAudit"] = repair_result["risk_audit"]
            repaired_payload["analysis"]["repairHistory"] = repair_result["history"]
            repaired_payload["analysis"]["repairedQyir"] = repair_result["qyir"]
            repaired_payload["analysis"]["historicalRiskNotice"] = draft_payload[
                "analysis"
            ]["historicalRiskNotice"]
            return repaired_payload
        draft_payload["analysis"]["repairHistory"] = repair_result["history"]

    draft_payload["status"] = "blocked"
    return draft_payload


def _mark_backtest_running(
    qyir: dict, draft_payload: dict, *, owner_id: str, options: dict
) -> dict:
    job = _create_qsga_backtest_job(
        qyir, draft_payload, owner_id=owner_id, options=options
    )
    draft_payload["status"] = "running"
    draft_payload["verification"]["backtest"] = running_result().to_dict()
    draft_payload["analysis"]["backtestJobId"] = job.id
    return draft_payload


def _create_qsga_backtest_job(
    qyir: dict, draft_payload: dict, *, owner_id: str, options: dict
) -> BacktestJob:
    strategy = qyir.get("strategy") or {}
    universe = qyir.get("universe") or {}
    symbols = universe.get("symbols") or []
    params = {
        "qsga": True,
        "draft_import_id": draft_payload.get("analysis", {}).get("draftImportId"),
        "symbol": symbols[0] if symbols else None,
        "symbols": symbols,
        "interval": strategy.get("timeframe"),
        "start_time": options.get("startTime")
        or options.get("start_time")
        or options.get("startDate"),
        "end_time": options.get("endTime")
        or options.get("end_time")
        or options.get("endDate"),
        "data_source": options.get("dataSource") or options.get("data_source"),
        "enable_ai": False,
    }
    job = BacktestJob(
        user_id=owner_id,
        status=BacktestJobStatus.PENDING.value,
        params=params,
    )
    db.session.add(job)
    db.session.commit()
    return job


def _run_backtest_enabled(options: dict) -> bool:
    return bool(options.get("runBacktest") or options.get("run_backtest"))


def _repair_enabled(options: dict) -> bool:
    return bool(
        options.get("enableRepair")
        or options.get("enable_repair")
        or options.get("repairEnabled")
    )


def _max_repair_attempts(options: dict) -> int:
    try:
        return int(
            options.get("maxRepairAttempts", options.get("max_repair_attempts", 2))
        )
    except (TypeError, ValueError):
        return 2


def _pipeline_response(
    status: str, verification: dict[str, VerificationResult]
) -> dict:
    return {
        "status": status,
        "verification": _verification_payload(verification),
        "analysis": {},
    }


def _verification_payload(verification: dict[str, VerificationResult]) -> dict:
    return {name: result.to_dict() for name, result in verification.items()}


def _attach_trust_payload(payload: dict) -> dict:
    trust = evaluate_qsga_trust(payload.get("verification") or {})
    payload["trust"] = trust
    analysis = payload.setdefault("analysis", {})
    analysis["qsgaTrust"] = trust
    analysis["isTrusted"] = trust["trusted"]
    analysis["isVerified"] = trust["verified"]
    return payload


def evaluate_qsga_trust(verification: dict) -> dict:
    statuses = {
        name: str((result or {}).get("status") or "not_run")
        for name, result in verification.items()
        if isinstance(result, dict)
    }
    blocking = [
        name
        for name in TRUSTED_QSGA_REQUIRED_CHECKS
        if statuses.get(name, "not_run") != "pass"
    ]
    running = [name for name in blocking if statuses.get(name) == "running"]
    missing = [name for name in blocking if statuses.get(name, "not_run") == "not_run"]
    failed = [name for name in blocking if name not in running and name not in missing]
    trusted = not blocking
    if trusted:
        status = "trusted"
    elif running:
        status = "running"
    else:
        status = "unverified"
    return {
        "trusted": trusted,
        "verified": trusted,
        "status": status,
        "requiredChecks": list(TRUSTED_QSGA_REQUIRED_CHECKS),
        "blockingChecks": blocking,
        "runningChecks": running,
        "missingChecks": missing,
        "failedChecks": failed,
    }
