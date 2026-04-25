import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from ..extensions import db
from ..services.integrations import decrypt_secret_payload, get_user_integration
from .qysp_docs import get_api_reference
from .strategy_import_analysis import analyze_strategy_import


SUPPORTED_CATEGORY_VALUES = {
    "trend-following",
    "mean-reversion",
    "momentum",
    "multi-indicator",
    "other",
}

SUPPORTED_RISK_LEVELS = {"low", "medium", "high"}


class AIStrategyGenerationError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def generate_strategy_draft(*, user_id, integration_id, messages, locale="en"):
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
        locale=locale,
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
    metadata_candidates = {
        **dict(analysis.get("metadataCandidates") or {}),
        "name": normalized_strategy["name"],
        "description": normalized_strategy["description"],
        "category": normalized_strategy["category"],
        "symbol": normalized_strategy["symbol"],
        "tags": normalized_strategy["tags"],
        "version": normalized_strategy["version"],
    }
    if normalized_strategy.get("timeframe"):
        metadata_candidates["timeframe"] = normalized_strategy["timeframe"]
    if normalized_strategy.get("riskLevel"):
        metadata_candidates["riskLevel"] = normalized_strategy["riskLevel"]
    if normalized_strategy.get("logicExplanation"):
        metadata_candidates["logicExplanation"] = normalized_strategy["logicExplanation"]
    if normalized_strategy.get("riskRules"):
        metadata_candidates["riskRules"] = normalized_strategy["riskRules"]
    if normalized_strategy.get("suitableMarket"):
        metadata_candidates["suitableMarket"] = normalized_strategy["suitableMarket"]
    merged_analysis["metadataCandidates"] = metadata_candidates
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


def _request_chat_completion(*, base_url, model, api_key, messages, locale="en"):
    if not base_url:
        raise AIStrategyGenerationError("AI_BASE_URL_REQUIRED", "AI integration base_url is required", 422)
    if not model:
        raise AIStrategyGenerationError("AI_MODEL_REQUIRED", "AI integration model is required", 422)
    if not api_key:
        raise AIStrategyGenerationError("AI_API_KEY_REQUIRED", "AI integration api_key is required", 422)

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [{"role": "system", "content": _system_prompt(locale)}, *messages],
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

    timeframe = str(payload.get("timeframe") or "").strip() or None
    risk_level = str(payload.get("riskLevel") or "").strip().lower() or None
    if risk_level and risk_level not in SUPPORTED_RISK_LEVELS:
        risk_level = None
    logic_explanation = str(payload.get("logicExplanation") or "").strip() or None
    risk_rules = str(payload.get("riskRules") or "").strip() or None
    suitable_market = str(payload.get("suitableMarket") or "").strip() or None

    return {
        "name": name,
        "description": description,
        "category": category,
        "symbol": symbol,
        "version": version,
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "timeframe": timeframe,
        "riskLevel": risk_level,
        "logicExplanation": logic_explanation,
        "riskRules": risk_rules,
        "suitableMarket": suitable_market,
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
    user_facing = item.get("user_facing")
    if not isinstance(user_facing, dict):
        user_facing = item.get("userFacing")
    if isinstance(user_facing, dict):
        payload["user_facing"] = user_facing
    return payload


def _generated_filename(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug or 'ai-generated-strategy'}.py"


def _strip_code_fence(code):
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", code, flags=re.DOTALL)
    return match.group(1).strip() if match else code


def _system_prompt(locale="en"):
    reference = _load_reference_material()
    if locale == "zh":
        return (
            "你是一位专业的量化策略架构师，服务于 QYQuant 平台。"
            "你负责生成可在 QYQuant 平台直接运行的生产级策略。"
            "始终严格遵循 QYSP event_v1 合约。"
            "仅返回严格的 JSON 格式，不要在 JSON 外包含任何 markdown 内容。\n\n"
            "Schema:\n"
            '{"reply":"给用户的回复文本（使用中文）","strategy":null|{'
            '"name":"策略名称",'
            '"description":"详细的专业描述（使用中文）",'
            '"category":"trend-following|mean-reversion|momentum|multi-indicator|other",'
            '"symbol":"BTCUSDT",'
            '"timeframe":"1h",'
            '"version":"1.0.0",'
            '"tags":["..."],'
            '"riskLevel":"low|medium|high",'
            '"logicExplanation":"用通俗易懂的语言解释策略逻辑，面向初学者（使用中文）",'
            '"riskRules":"用通俗易懂的语言解释风控规则（使用中文）",'
            '"suitableMarket":"描述适合的市场条件（使用中文）",'
            '"parameters":[{"key":"...","type":"integer|number|string|boolean|enum",'
            '"default":1,"min":1,"max":100,"step":1,"description":"...",'
            '"user_facing":{"label":"参数中文名称","group":"参数组名称（中文）","hint":"面向初学者的解释（中文）"},'
            '"enum":["..."]}],'
            '"code":"python 源码，带中文段注释"'
            '}}\n\n'
            "如果需求仍不清晰，将 strategy 设为 null，并在 reply 中提出一个简洁的追问。\n\n"
            "代码要求:\n"
            "- 必须定义 on_bar(ctx: StrategyContext, data: BarData) -> list[Order]，优先使用函数形式。\n"
            "- 使用 ctx.buy()/ctx.sell()，所有可调参数通过 ctx.parameters.get() 读取。\n"
            "- 禁止硬编码可调参数。每个阈值、周期、比例都必须是参数。\n"
            "- 代码结构需包含清晰的段注释：\n"
            "  # === 参数读取 ===\n"
            "  # === 信号检测 ===\n"
            "  # === 风险管理（止损/止盈） ===\n"
            "  # === 仓位管理 ===\n"
            "  # === 下单执行 ===\n"
            "- 必须包含止损和止盈逻辑，不允许无风控的策略。\n"
            "- 基于总资金比例进行仓位管理。\n"
            "- 使用 ctx state（setattr/getattr）跟踪持仓。\n"
            "- 禁止使用 input()、print()、外部文件、网络、pandas、numpy 或不支持的依赖。\n\n"
            "参数要求:\n"
            "- 每个参数必须有 user_facing，包含 label、group 和 hint。\n"
            "- 按逻辑分组：「指标参数」「风控参数」「仓位参数」「信号过滤」。\n"
            "- hint 应以初学者能理解的语言解释参数作用。\n"
            "- 提供合理的默认值和 min/max 范围。\n\n"
            "策略报告要求:\n"
            "- logicExplanation: 用通俗语言解释策略逻辑，可使用类比。\n"
            "- riskRules: 用通俗语言解释止损、止盈、仓位限制。\n"
            "- suitableMarket: 描述理想的市场条件（如上升趋势、震荡、高波动）。\n"
            "- riskLevel: 'low' 为严格止损+小仓位，'medium' 为均衡，'high' 为激进。\n\n"
            "参考约束:\n"
            f"{reference}"
        )
    return (
        "You are a professional quantitative strategy architect for the QYQuant platform. "
        "You generate runnable QYQuant strategies that are production-quality. "
        "Always follow QYSP event_v1 contract exactly. "
        "Reply with strict JSON only, no markdown outside the JSON.\n\n"
        "Schema:\n"
        '{"reply":"assistant text for user","strategy":null|{'
        '"name":"strategy name",'
        '"description":"detailed professional description",'
        '"category":"trend-following|mean-reversion|momentum|multi-indicator|other",'
        '"symbol":"BTCUSDT",'
        '"timeframe":"1h",'
        '"version":"1.0.0",'
        '"tags":["..."],'
        '"riskLevel":"low|medium|high",'
        '"logicExplanation":"plain language explanation of strategy logic, written for beginners",'
        '"riskRules":"plain language explanation of risk management rules",'
        '"suitableMarket":"description of ideal market conditions",'
        '"parameters":[{"key":"...","type":"integer|number|string|boolean|enum",'
        '"default":1,"min":1,"max":100,"step":1,"description":"...",'
        '"user_facing":{"label":"human-readable name","group":"parameter group name","hint":"explanation for beginners"},'
        '"enum":["..."]}],'
        '"code":"python source with section comments"'
        '}}\n\n'
        "If requirements still unclear, set strategy to null and ask one concise follow-up question in reply.\n\n"
        "CODE REQUIREMENTS:\n"
        "- Must define on_bar(ctx: StrategyContext, data: BarData) -> list[Order]. Prefer function form.\n"
        "- Use ctx.buy()/ctx.sell(). Read ALL tunable parameters from ctx.parameters.get().\n"
        "- NEVER hardcode tunable values. Every threshold, period, ratio must be a parameter.\n"
        "- Structure code with clear section comments:\n"
        "  # === Parameter Reading ===\n"
        "  # === Signal Detection ===\n"
        "  # === Risk Management (Stop Loss / Take Profit) ===\n"
        "  # === Position Sizing ===\n"
        "  # === Order Execution ===\n"
        "- ALWAYS include stop-loss and take-profit logic. No strategy without risk management.\n"
        "- Include position sizing based on total capital ratio.\n"
        "- Track open positions using ctx state (setattr/getattr).\n"
        "- Do not use input(), print(), external files, network, pandas, numpy, or unsupported dependencies.\n\n"
        "PARAMETER REQUIREMENTS:\n"
        "- Every parameter MUST have user_facing with label, group, and hint.\n"
        "- Group parameters logically: 'Indicator', 'Risk Management', 'Position Sizing', 'Signal Filter'.\n"
        "- hint should explain what the parameter does in beginner-friendly language.\n"
        "- Include sensible defaults and reasonable min/max ranges.\n\n"
        "STRATEGY REPORT REQUIREMENTS:\n"
        "- logicExplanation: Explain in plain language what the strategy does. Use analogies if helpful.\n"
        "- riskRules: Explain stop-loss, take-profit, position limits in plain language.\n"
        "- suitableMarket: Describe ideal market conditions (e.g., trending up, ranging, high volatility).\n"
        "- riskLevel: 'low' for tight stops + small positions, 'medium' for balanced, 'high' for aggressive.\n\n"
        "Reference constraints:\n"
        f"{reference}"
    )


def _load_reference_material():
    return get_api_reference()


class _BufferedGeneratedUpload:
    def __init__(self, *, filename, mimetype, payload):
        self.filename = filename
        self.mimetype = mimetype
        self._payload = payload

    def read(self):
        return self._payload
