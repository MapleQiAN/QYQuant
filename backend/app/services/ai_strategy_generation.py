import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from ..extensions import db
from ..services.integrations import decrypt_secret_payload, get_user_integration
from .strategy_import_analysis import analyze_strategy_import


SUPPORTED_CATEGORY_VALUES = {
    "trend-following",
    "mean-reversion",
    "momentum",
    "multi-indicator",
    "other",
}


class AIStrategyGenerationError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def generate_strategy_draft(*, user_id, integration_id, messages):
    integration = get_user_integration(integration_id, user_id)
    if integration is None:
        raise AIStrategyGenerationError("INTEGRATION_NOT_FOUND", "Integration not found", 404)
    if integration.provider_key != "openai_compatible":
        raise AIStrategyGenerationError(
            "UNSUPPORTED_AI_PROVIDER",
            "Selected integration does not support AI strategy generation",
            422,
        )

    normalized_messages = _normalize_messages(messages)
    if not normalized_messages:
        raise AIStrategyGenerationError("MESSAGES_REQUIRED", "At least one user message is required", 400)

    config_public = dict(integration.config_public or {})
    secret_payload = decrypt_secret_payload(integration)
    completion = _request_chat_completion(
        base_url=str(config_public.get("base_url") or "").strip(),
        model=str(config_public.get("model") or "").strip(),
        api_key=str(secret_payload.get("api_key") or "").strip(),
        messages=normalized_messages,
    )
    parsed = _parse_model_response(completion)
    reply = str(parsed.get("reply") or "").strip() or "Strategy draft updated."
    strategy_payload = parsed.get("strategy")

    if not strategy_payload:
        return {"reply": reply, "analysis": None}

    normalized_strategy = _normalize_strategy_payload(strategy_payload)
    upload = _BufferedGeneratedUpload(
        filename=_generated_filename(normalized_strategy["name"]),
        mimetype="text/x-python",
        payload=normalized_strategy["code"].encode("utf-8"),
    )
    draft, _source_file, analysis = analyze_strategy_import(upload, owner_id=user_id)

    merged_analysis = dict(analysis)
    merged_analysis["metadataCandidates"] = {
        **dict(analysis.get("metadataCandidates") or {}),
        "name": normalized_strategy["name"],
        "description": normalized_strategy["description"],
        "category": normalized_strategy["category"],
        "symbol": normalized_strategy["symbol"],
        "tags": normalized_strategy["tags"],
        "version": normalized_strategy["version"],
    }
    merged_analysis["parameterCandidates"] = normalized_strategy["parameters"]
    draft.analysis_payload = merged_analysis
    db.session.commit()

    response_analysis = dict(merged_analysis)
    response_analysis["draftImportId"] = draft.id
    return {
        "reply": reply,
        "analysis": response_analysis,
    }


def _normalize_messages(messages):
    if not isinstance(messages, list):
        return []

    normalized = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def _request_chat_completion(*, base_url, model, api_key, messages):
    if not base_url:
        raise AIStrategyGenerationError("AI_BASE_URL_REQUIRED", "AI integration base_url is required", 422)
    if not model:
        raise AIStrategyGenerationError("AI_MODEL_REQUIRED", "AI integration model is required", 422)
    if not api_key:
        raise AIStrategyGenerationError("AI_API_KEY_REQUIRED", "AI integration api_key is required", 422)

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [{"role": "system", "content": _system_prompt()}, *messages],
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
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise AIStrategyGenerationError(
            "AI_REQUEST_FAILED",
            "AI provider request failed",
            502,
            details={"status": exc.code, "body": error_body[:1000]},
        ) from exc
    except urllib.error.URLError as exc:
        raise AIStrategyGenerationError(
            "AI_REQUEST_FAILED",
            "Could not reach AI provider",
            502,
            details={"reason": str(exc.reason)},
        ) from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise AIStrategyGenerationError("AI_RESPONSE_INVALID", "AI provider returned invalid JSON", 502) from exc

    choices = parsed.get("choices") or []
    if not choices:
        raise AIStrategyGenerationError("AI_RESPONSE_INVALID", "AI provider returned no choices", 502)
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        parts = [str(item.get("text") or "") for item in content if isinstance(item, dict)]
        content = "\n".join(part for part in parts if part)
    if not isinstance(content, str) or not content.strip():
        raise AIStrategyGenerationError("AI_RESPONSE_INVALID", "AI provider returned empty content", 502)
    return content


def _parse_model_response(content):
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIStrategyGenerationError(
            "AI_RESPONSE_INVALID",
            "AI response is not valid JSON",
            502,
            details={"content": content[:1000]},
        ) from exc

    if not isinstance(payload, dict):
        raise AIStrategyGenerationError("AI_RESPONSE_INVALID", "AI response must be a JSON object", 502)
    return payload


def _normalize_strategy_payload(payload):
    if not isinstance(payload, dict):
        raise AIStrategyGenerationError("AI_STRATEGY_INVALID", "AI strategy payload must be an object", 422)

    raw_code = str(payload.get("code") or "").strip()
    if not raw_code:
        raise AIStrategyGenerationError("AI_STRATEGY_INVALID", "AI strategy code is required", 422)

    code = _strip_code_fence(raw_code)
    name = str(payload.get("name") or "").strip() or "AI Generated Strategy"
    description = str(payload.get("description") or "").strip() or "Generated from AI conversation"
    category = str(payload.get("category") or "other").strip().lower()
    if category not in SUPPORTED_CATEGORY_VALUES:
        category = "other"
    symbol = str(payload.get("symbol") or "").strip() or "BTCUSDT"
    version = str(payload.get("version") or "").strip() or "1.0.0"
    tags = payload.get("tags") if isinstance(payload.get("tags"), list) else []

    parameters = payload.get("parameters")
    if not isinstance(parameters, list):
        parameters = []

    return {
        "name": name,
        "description": description,
        "category": category,
        "symbol": symbol,
        "version": version,
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "parameters": [_normalize_parameter_definition(item) for item in parameters if isinstance(item, dict)],
        "code": code,
    }


def _normalize_parameter_definition(item):
    key = str(item.get("key") or item.get("name") or "").strip()
    if not key:
        raise AIStrategyGenerationError("AI_STRATEGY_INVALID", "Parameter key is required", 422)

    raw_type = str(item.get("type") or "string").strip().lower()
    normalized_type = {
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "number": "number",
        "str": "string",
        "string": "string",
        "bool": "boolean",
        "boolean": "boolean",
        "enum": "enum",
    }.get(raw_type, "string")

    payload = {
        "key": key,
        "type": normalized_type,
    }
    for field in ("default", "required", "min", "max", "step", "description"):
        if field in item:
            payload[field] = item.get(field)

    enum_values = item.get("enum")
    if enum_values is None:
        enum_values = item.get("options")
    if isinstance(enum_values, list):
        payload["enum"] = enum_values
    return payload


def _generated_filename(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug or 'ai-generated-strategy'}.py"


def _strip_code_fence(code):
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", code, flags=re.DOTALL)
    return match.group(1).strip() if match else code


def _system_prompt():
    return (
        "You generate runnable QYQuant strategies. "
        "Always follow QYSP event_v1 contract exactly. "
        "Reply with strict JSON only, no markdown. "
        "Schema: "
        '{"reply":"assistant text for user","strategy":null|{"name":"...","description":"...","category":"trend-following|mean-reversion|momentum|multi-indicator|other","symbol":"...","version":"1.0.0","tags":["..."],"parameters":[{"key":"...","type":"integer|number|string|boolean|enum","default":1,"min":1,"max":100,"step":1,"description":"...","enum":["..."]}],"code":"python source"}} '
        "If requirements still unclear, set strategy to null and ask one concise follow-up question in reply. "
        "If strategy is present, code must define on_bar(ctx: StrategyContext, data: BarData) -> list[Order] or a Strategy class with on_bar method, and prefer function form. "
        "Use ctx.buy()/ctx.sell(). Read parameters from ctx.parameters.get(). "
        "Do not use input(), print(), external files, network, pandas, numpy, or unsupported dependencies. "
        "Keep state on ctx via setattr/getattr if needed. "
        "Reference constraints:\n"
        f"{_load_reference_material()}"
    )


def _load_reference_material():
    repo_root = Path(__file__).resolve().parents[3]
    files = [
        repo_root / "docs" / "strategy-format" / "README.md",
        repo_root / "docs" / "strategy-format" / "examples" / "GoldStepByStep" / "README.md",
        repo_root / "packages" / "qysp" / "src" / "qysp" / "context.py",
    ]
    parts = []
    for path in files:
        try:
            parts.append(f"[{path.name}]\n{path.read_text(encoding='utf-8')}\n")
        except FileNotFoundError:
            continue
    return "\n".join(parts)[:16000]


class _BufferedGeneratedUpload:
    def __init__(self, *, filename, mimetype, payload):
        self.filename = filename
        self.mimetype = mimetype
        self._payload = payload

    def read(self):
        return self._payload
