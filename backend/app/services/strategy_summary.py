"""Strategy summary formatter.

Takes a generated strategy (code + parameters) and produces a human-readable
explanation of the strategy logic and parameter list for user review.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .integrations import decrypt_secret_payload, get_user_integration


_SUMMARY_PROMPT = """\
You explain trading strategies in simple terms for non-expert users.
Given a strategy's code and parameters, produce:
1. A one-sentence strategy summary (what it does)
2. A plain-language explanation of the logic (2-4 sentences)
3. A parameter list with each parameter's purpose explained simply

Respond with strict JSON:
{"summary":"...","explanation":"...","parameters":[{"key":"...","label":"...","purpose":"..."}]}
"""


class StrategySummaryError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def format_strategy_summary(
    *,
    user_id,
    integration_id,
    code: str,
    parameters: list[dict],
) -> dict:
    """Generate a human-readable summary of a strategy.

    Falls back to a basic extraction if the LLM call fails.
    """
    integration = get_user_integration(integration_id, user_id)
    if integration is None:
        return _fallback_summary(code, parameters)
    if integration.provider_key != "openai_compatible":
        return _fallback_summary(code, parameters)

    config_public = dict(integration.config_public or {})
    secret_payload = decrypt_secret_payload(integration)

    try:
        result = _request_summary(
            base_url=str(config_public.get("base_url") or "").strip(),
            model=str(config_public.get("model") or "").strip(),
            api_key=str(secret_payload.get("api_key") or "").strip(),
            code=code,
            parameters=parameters,
        )
    except Exception:
        return _fallback_summary(code, parameters)

    return result


def _request_summary(*, base_url, model, api_key, code, parameters):
    if not base_url or not model or not api_key:
        return _fallback_summary(code, parameters)

    param_descriptions = "\n".join(
        f"- {p.get('key', '?')}: type={p.get('type', '?')}, "
        f"range=[{p.get('min', '?')}, {p.get('max', '?')}], "
        f"default={p.get('default', '?')}"
        for p in parameters
    )

    user_content = f"Strategy code:\n```\n{code[:4000]}\n```\n\nParameters:\n{param_descriptions}"

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": _SUMMARY_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")

    parsed = json.loads(body)
    choices = parsed.get("choices") or []
    if not choices:
        return _fallback_summary(code, parameters)

    content = choices[0].get("message", {}).get("content", "")
    return _parse_summary_response(content, code, parameters)


def _parse_summary_response(content, code, parameters):
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _fallback_summary(code, parameters)

    if not isinstance(data, dict):
        return _fallback_summary(code, parameters)

    return {
        "summary": str(data.get("summary") or "").strip() or _extract_summary_from_code(code),
        "explanation": str(data.get("explanation") or "").strip() or "AI-generated trading strategy.",
        "parameters": [
            {
                "key": p.get("key", param.get("key", "")),
                "label": str(p.get("label") or param.get("key", "")),
                "purpose": str(p.get("purpose") or ""),
            }
            for p, param in zip(
                data.get("parameters") or [{}] * len(parameters),
                parameters,
            )
        ],
    }


def _fallback_summary(code, parameters):
    """Generate a basic summary without LLM."""
    summary = _extract_summary_from_code(code)
    param_list = [
        {
            "key": p.get("key", ""),
            "label": p.get("key", ""),
            "purpose": p.get("description") or f"{p.get('type', 'unknown')} parameter",
        }
        for p in parameters
    ]
    return {
        "summary": summary,
        "explanation": "Custom trading strategy with configurable parameters.",
        "parameters": param_list,
    }


def _extract_summary_from_code(code):
    """Extract first docstring or comment as a basic summary."""
    docstring_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
    if docstring_match:
        return docstring_match.group(1).strip().split("\n")[0]

    comment_lines = [line.lstrip("# ").strip() for line in code.split("\n") if line.strip().startswith("#")]
    if comment_lines:
        return comment_lines[0]

    return "Custom trading strategy"
