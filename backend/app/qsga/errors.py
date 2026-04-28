from __future__ import annotations

from .result import VerificationError


def verification_error(
    code: str,
    path: str,
    message: str,
    *,
    category: str,
    severity: str = "error",
    repairable: bool = False,
) -> VerificationError:
    return VerificationError(
        code=code,
        path=path,
        message=message,
        severity=severity,
        category=category,
        repairable=repairable,
    )
