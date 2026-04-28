from __future__ import annotations

import re

from ..errors import verification_error
from ..guardrails.policies import AMBIGUOUS_TERMS, UNSAFE_TERMS, UNSUPPORTED_TERMS
from ..result import (
    VerificationQuestion,
    VerificationResult,
    blocked_result,
    clarification_result,
    pass_result,
    rejected_result,
)


_PCT_RE = re.compile(r"\d+(?:\.\d+)?\s*%")


def verify_intent_guardrails(qyir: dict) -> VerificationResult:
    intent = qyir.get("intent") if isinstance(qyir, dict) else None
    intent = intent if isinstance(intent, dict) else {}
    raw_text = str(intent.get("raw_text") or "")
    classification = intent.get("classification")

    if classification == "unsafe" or _contains_any(raw_text, UNSAFE_TERMS):
        return rejected_result(
            [
                verification_error(
                    "UNSAFE_INTENT",
                    "$.intent.raw_text",
                    "请求包含保证收益、违法违规或明显不适当风险意图，不能生成策略草案",
                    category="safety",
                )
            ]
        )

    if classification == "unsupported" or _contains_any(raw_text, UNSUPPORTED_TERMS):
        return blocked_result(
            [
                verification_error(
                    "UNSUPPORTED_INTENT",
                    "$.intent.raw_text",
                    "请求超出 QYIR v1 支持范围，当前不能生成 QSGA 策略草案",
                    category="safety",
                )
            ]
        )

    if classification == "ambiguous" or _is_ambiguous(raw_text, qyir):
        return clarification_result(
            [
                VerificationQuestion(
                    id="risk.max_drawdown_pct",
                    path="$.risk.max_drawdown_pct",
                    message="你希望历史回测最大回撤阈值设置为多少？",
                    options=[10, 15, 20],
                )
            ],
            [
                verification_error(
                    "AMBIGUOUS_INTENT",
                    "$.intent.raw_text",
                    "请求包含模糊风险或时间表达，需要先澄清关键槽位",
                    category="safety",
                    repairable=True,
                )
            ],
        )

    return pass_result()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _is_ambiguous(text: str, qyir: dict) -> bool:
    if not _contains_any(text, AMBIGUOUS_TERMS):
        return False
    if _PCT_RE.search(text):
        return False
    risk = qyir.get("risk") if isinstance(qyir, dict) else None
    if isinstance(risk, dict) and (risk.get("max_drawdown_pct") is not None or risk.get("max_position_pct") is not None):
        return False
    return True
