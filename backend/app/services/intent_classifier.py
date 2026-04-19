"""Intent classification for user strategy descriptions.

Single LLM call that classifies a natural language description into one of
five strategy categories and extracts direction, timeframe, and confidence.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .integrations import decrypt_secret_payload, get_user_integration


CATEGORY_VALUES = frozenset({
    "trend_following",
    "mean_reversion",
    "momentum",
    "multi_indicator",
    "custom",
})

DIRECTION_VALUES = frozenset({"long", "short", "both"})
TIMEFRAME_VALUES = frozenset({"short", "medium", "long"})

_CLASSIFICATION_PROMPT = """\
You are a trading strategy intent classifier. Classify the user's description into exactly one strategy category, direction, and timeframe.

Categories:
- trend_following: chasing trends, going with momentum, moving averages crossover, breakout
- mean_reversion: buying dips, oversold bounce, reversion to mean, RSI extremes
- momentum: strength-based entry, volume surge, strong momentum continuation
- multi_indicator: combining multiple indicators, composite signals, confluence
- custom: anything that doesn't fit above categories

Respond with strict JSON only:
{"strategy_type":"...","direction":"long|short|both","timeframe":"short|medium|long","confidence":0.0-1.0}

Classification hints:
- "顺势", "追涨", "上涨趋势" → trend_following
- "反弹", "抄底", "超卖", "低位" → mean_reversion
- "动量", "放量", "强势突破" → momentum
- "综合判断", "多个指标", "结合" → multi_indicator
"""


class IntentClassificationError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def classify_intent(*, user_id, integration_id, description):
    """Classify a user's strategy description into structured intent.

    Returns dict with strategy_type, direction, timeframe, confidence.
    """
    if not description or not description.strip():
        raise IntentClassificationError(
            "DESCRIPTION_REQUIRED", "Strategy description is required", 400,
        )

    integration = get_user_integration(integration_id, user_id)
    if integration is None:
        raise IntentClassificationError("INTEGRATION_NOT_FOUND", "Integration not found", 404)
    if integration.provider_key != "openai_compatible":
        raise IntentClassificationError(
            "UNSUPPORTED_AI_PROVIDER",
            "Selected integration does not support intent classification",
            422,
        )

    config_public = dict(integration.config_public or {})
    secret_payload = decrypt_secret_payload(integration)

    result = _request_classification(
        base_url=str(config_public.get("base_url") or "").strip(),
        model=str(config_public.get("model") or "").strip(),
        api_key=str(secret_payload.get("api_key") or "").strip(),
        description=description.strip(),
    )
    return result


def _request_classification(*, base_url, model, api_key, description):
    if not base_url or not model or not api_key:
        raise IntentClassificationError(
            "AI_CONFIG_INCOMPLETE", "AI integration config is incomplete", 422,
        )

    payload = {
        "model": model,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": _CLASSIFICATION_PROMPT},
            {"role": "user", "content": description},
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

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise IntentClassificationError(
            "AI_REQUEST_FAILED", "AI provider request failed", 502,
            details={"status": exc.code, "body": error_body[:500]},
        ) from exc
    except urllib.error.URLError as exc:
        raise IntentClassificationError(
            "AI_REQUEST_FAILED", "Could not reach AI provider", 502,
            details={"reason": str(exc.reason)},
        ) from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise IntentClassificationError(
            "AI_RESPONSE_INVALID", "AI provider returned invalid JSON", 502,
        ) from exc

    choices = parsed.get("choices") or []
    if not choices:
        raise IntentClassificationError("AI_RESPONSE_INVALID", "No choices in response", 502)

    content = choices[0].get("message", {}).get("content", "")
    return _parse_classification(content)


def _parse_classification(content):
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IntentClassificationError(
            "AI_RESPONSE_INVALID", "Classification response is not valid JSON", 502,
            details={"content": content[:500]},
        ) from exc

    if not isinstance(data, dict):
        raise IntentClassificationError("AI_RESPONSE_INVALID", "Classification must be a JSON object", 502)

    strategy_type = str(data.get("strategy_type") or "custom").strip().lower()
    if strategy_type not in CATEGORY_VALUES:
        strategy_type = "custom"

    direction = str(data.get("direction") or "both").strip().lower()
    if direction not in DIRECTION_VALUES:
        direction = "both"

    timeframe = str(data.get("timeframe") or "medium").strip().lower()
    if timeframe not in TIMEFRAME_VALUES:
        timeframe = "medium"

    confidence = data.get("confidence")
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        confidence = 0.5
    confidence = round(float(confidence), 2)

    return {
        "strategy_type": strategy_type,
        "direction": direction,
        "timeframe": timeframe,
        "confidence": confidence,
    }
