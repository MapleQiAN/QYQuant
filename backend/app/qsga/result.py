from __future__ import annotations

from dataclasses import dataclass, field


PASS_STATUS = "pass"
FAIL_STATUS = "fail"
BLOCKED_STATUS = "blocked"
CLARIFICATION_STATUS = "clarification_required"
REJECTED_STATUS = "rejected"
NOT_RUN_STATUS = "not_run"
RUNNING_STATUS = "running"


@dataclass(frozen=True)
class VerificationError:
    code: str
    path: str
    message: str
    severity: str = "error"
    category: str = "general"
    repairable: bool = False

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
            "category": self.category,
            "repairable": self.repairable,
        }


@dataclass(frozen=True)
class VerificationQuestion:
    id: str
    path: str
    message: str
    options: list | None = None

    def to_dict(self) -> dict:
        payload = {
            "id": self.id,
            "path": self.path,
            "message": self.message,
        }
        if self.options is not None:
            payload["options"] = self.options
        return payload


@dataclass(frozen=True)
class VerificationResult:
    status: str
    errors: list[VerificationError] = field(default_factory=list)
    questions: list[VerificationQuestion] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == PASS_STATUS and not self.errors

    def to_dict(self) -> dict:
        payload = {
            "status": self.status,
            "errors": [error.to_dict() for error in self.errors],
        }
        if self.questions:
            payload["questions"] = [question.to_dict() for question in self.questions]
        return payload


def pass_result() -> VerificationResult:
    return VerificationResult(status=PASS_STATUS)


def fail_result(errors: list[VerificationError]) -> VerificationResult:
    return VerificationResult(status=FAIL_STATUS, errors=errors)


def blocked_result(errors: list[VerificationError]) -> VerificationResult:
    return VerificationResult(status=BLOCKED_STATUS, errors=errors)


def clarification_result(questions: list[VerificationQuestion], errors: list[VerificationError] | None = None) -> VerificationResult:
    return VerificationResult(status=CLARIFICATION_STATUS, errors=errors or [], questions=questions)


def rejected_result(errors: list[VerificationError]) -> VerificationResult:
    return VerificationResult(status=REJECTED_STATUS, errors=errors)


def not_run_result() -> VerificationResult:
    return VerificationResult(status=NOT_RUN_STATUS)


def running_result() -> VerificationResult:
    return VerificationResult(status=RUNNING_STATUS)

