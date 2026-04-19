"""Generate user_facing definitions for strategy parameters.

When a strategy's parameters lack user_facing metadata (question + options),
this module generates them via a single LLM call and caches the result.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .integrations import decrypt_secret_payload, get_user_integration


_GENERATE_USER_FACING_PROMPT = """\
You create beginner-friendly parameter labels for trading strategies.
For each technical parameter, generate:
- question: a simple question a non-expert can answer
- options: 2-4 choices with label, value, and short desc

Rules:
- Options must use actual numeric values from the parameter's range
- Labels in Chinese, simple and intuitive
- desc in Chinese, explaining tradeoff in plain language

Respond with strict JSON array:
[{"key":"param_key","user_facing":{"question":"...","options":[{"label":"...","value":1.0,"desc":"..."}]}}]
"""


class UserFacingGenerationError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def generate_user_facing(
    *,
    user_id,
    integration_id,
    parameters: list[dict],
) -> list[dict]:
    """Generate user_facing definitions for parameters that lack them.

    Parameters that already have user_facing are passed through unchanged.
    Only parameters missing user_facing are sent to the LLM.

    Returns the full parameter list with user_facing populated.
    """
    needs_generation = []
    result = list(parameters)

    for i, param in enumerate(parameters):
        if not isinstance(param.get("user_facing"), dict):
            needs_generation.append((i, param))

    if not needs_generation:
        return result

    integration = get_user_integration(integration_id, user_id)
    if integration is None:
        return _fallback_user_facing(result, needs_generation)
    if integration.provider_key != "openai_compatible":
        return _fallback_user_facing(result, needs_generation)

    config_public = dict(integration.config_public or {})
    secret_payload = decrypt_secret_payload(integration)

    try:
        generated = _request_generation(
            base_url=str(config_public.get("base_url") or "").strip(),
            model=str(config_public.get("model") or "").strip(),
            api_key=str(secret_payload.get("api_key") or "").strip(),
            parameters=[p for _, p in needs_generation],
        )
    except Exception:
        return _fallback_user_facing(result, needs_generation)

    # Merge generated user_facing back into result
    generated_map = {g.get("key"): g.get("user_facing") for g in generated if isinstance(g, dict)}

    for idx, param in needs_generation:
        key = param.get("key") or param.get("name")
        if key and key in generated_map:
            result[idx] = {**result[idx], "user_facing": generated_map[key]}

    return result


def _request_generation(*, base_url, model, api_key, parameters):
    if not base_url or not model or not api_key:
        return []

    param_descriptions = json.dumps(
        [
            {
                "key": p.get("key") or p.get("name"),
                "type": p.get("type"),
                "min": p.get("min"),
                "max": p.get("max"),
                "default": p.get("default"),
                "description": p.get("description"),
            }
            for p in parameters
        ],
        ensure_ascii=False,
    )

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": _GENERATE_USER_FACING_PROMPT},
            {"role": "user", "content": f"Generate user_facing for these parameters:\n{param_descriptions}"},
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
        return []

    content = choices[0].get("message", {}).get("content", "")
    return _parse_generation_response(content)


def _parse_generation_response(content):
    text = content.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    # Validate each item
    validated = []
    for item in data:
        if not isinstance(item, dict):
            continue
        uf = item.get("user_facing")
        if not isinstance(uf, dict):
            continue
        if not isinstance(uf.get("question"), str):
            continue
        options = uf.get("options")
        if not isinstance(options, list) or len(options) == 0:
            continue
        validated.append(item)

    return validated


def _fallback_user_facing(result, needs_generation):
    """Generate basic user_facing without LLM."""
    for idx, param in needs_generation:
        key = param.get("key") or param.get("name", "")
        ptype = param.get("type", "")
        min_val = param.get("min")
        max_val = param.get("max")
        default = param.get("default")

        if ptype in ("integer", "int", "number", "float") and min_val is not None and max_val is not None:
            low = min_val + (max_val - min_val) * 0.25
            mid = min_val + (max_val - min_val) * 0.5
            high = min_val + (max_val - min_val) * 0.75
            if ptype in ("integer", "int"):
                low, mid, high = int(round(low)), int(round(mid)), int(round(high))

            result[idx] = {
                **result[idx],
                "user_facing": {
                    "question": f"Choose {key} sensitivity:",
                    "options": [
                        {"label": "Low", "value": low, "desc": "Conservative setting"},
                        {"label": "Medium", "value": mid, "desc": "Balanced setting"},
                        {"label": "High", "value": high, "desc": "Aggressive setting"},
                    ],
                },
            }
        elif ptype == "enum":
            options = param.get("enum") or param.get("options") or []
            result[idx] = {
                **result[idx],
                "user_facing": {
                    "question": f"Select {key}:",
                    "options": [{"label": str(o), "value": o, "desc": ""} for o in options],
                },
            }
        else:
            result[idx] = {
                **result[idx],
                "user_facing": {
                    "question": f"Enter {key}:",
                    "options": [
                        {"label": "Default", "value": default, "desc": "Recommended value"},
                    ],
                },
            }

    return result
