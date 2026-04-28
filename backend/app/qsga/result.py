from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerificationError:
    code: str
    path: str
    message: str
    severity: str = "error"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class VerificationResult:
    status: str
    errors: list[VerificationError] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "pass" and not self.errors

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "errors": [error.to_dict() for error in self.errors],
        }


def pass_result() -> VerificationResult:
    return VerificationResult(status="pass")


def fail_result(errors: list[VerificationError]) -> VerificationResult:
    return VerificationResult(status="fail", errors=errors)

