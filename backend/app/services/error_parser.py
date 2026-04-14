import json
import re
from typing import Any


DEFAULT_EXAMPLE_CODE = """# 检查策略参数是否已定义
window = ctx.parameters.get('window', 20)"""

ERROR_EXAMPLES = {
    "NameError": """# 在 on_init() 中获取参数
sma_period = ctx.parameters.get('sma_period', 20)""",
    "TypeError": """# 确保参数类型正确
window = int(ctx.parameters.get('window', 20))""",
    "KeyError": """# 读取参数前先提供默认值
threshold = ctx.parameters.get('threshold', 0.05)""",
    "ImportError": """# 使用平台支持的依赖库
import pandas as pd
import numpy as np""",
    "SyntaxError": """if price > 0:
    return price""",
    "AttributeError": """# 调用属性前先确认对象结构
close_price = bar.get('close')""",
}


def _sanitize_error_text(raw_error: Any) -> str:
    text = str(raw_error or "").replace("\r\n", "\n").strip()
    if not text:
        return "RuntimeError: 未知错误"

    sanitized = re.sub(r'File "[^"]*[\\/](strategy\.py)"', r'File "\1"', text)
    sanitized = re.sub(r'File "[^"]*[\\/](sandbox_template\.py)"', r'File "\1"', sanitized)
    sanitized = re.sub(r'(/[A-Za-z0-9._-]+)+/(strategy\.py)', r'\2', sanitized)
    sanitized = re.sub(r'[A-Za-z]:[\\/][^"\n]+[\\/](strategy\.py)', r'\1', sanitized)
    return sanitized


def _extract_line(text: str) -> int | None:
    matches = re.findall(r'line (\d+)', text)
    return int(matches[-1]) if matches else None


def _extract_exception(text: str) -> tuple[str, str]:
    for line in reversed([item.strip() for item in text.splitlines() if item.strip()]):
        match = re.match(r'([A-Za-z_][\w.]*?(?:Error|Exception)):\s*(.+)', line)
        if match:
            error_type = match.group(1).split(".")[-1]
            if error_type == "ModuleNotFoundError":
                error_type = "ImportError"
            return error_type, match.group(2).strip()
    return "RuntimeError", text.splitlines()[-1].strip() if text.splitlines() else "未知错误"


def _build_name_error(detail: str) -> tuple[str, str]:
    variable = re.search(r"name '([^']+)' is not defined", detail)
    name = variable.group(1) if variable else "变量"
    return (
        f"未定义的变量 '{name}'",
        "请检查变量名是否正确，或确认是否已在策略参数中定义该参数。",
    )


def _build_type_error(detail: str) -> tuple[str, str]:
    missing_argument = re.search(r"missing .* argument[s]?: '([^']+)'", detail)
    if missing_argument:
        arg_name = missing_argument.group(1)
        return (
            f"缺少参数 '{arg_name}'",
            "请检查策略调用时是否传入了必需参数，并确认参数类型符合预期。",
        )
    return (
        f"类型错误：{detail}",
        "请检查参与计算的变量类型，以及策略参数是否需要显式转换。",
    )


def _build_key_error(detail: str) -> tuple[str, str]:
    missing_key = re.search(r"'([^']+)'", detail)
    key_name = missing_key.group(1) if missing_key else "参数"
    return (
        f"缺少参数 '{key_name}'",
        "请在策略参数配置中补充该参数，或为读取逻辑提供默认值。",
    )


def _build_import_error(detail: str) -> tuple[str, str]:
    module_match = re.search(r"No module named '([^']+)'", detail)
    module_name = module_match.group(1) if module_match else detail
    return (
        f"不支持的依赖库 '{module_name}'",
        "请检查导入名称是否正确，并查看支持的依赖库清单后再调整代码。",
    )


def _build_syntax_error(detail: str, line: int | None) -> tuple[str, str]:
    prefix = f"语法错误（第 {line} 行）" if line is not None else "语法错误"
    return (
        f"{prefix}：{detail}",
        "请检查这一行附近是否缺少冒号、括号、缩进或引号闭合。",
    )


def _build_attribute_error(detail: str) -> tuple[str, str]:
    attr_match = re.search(r"'([^']+)' object has no attribute '([^']+)'", detail)
    if attr_match:
        object_name, attr_name = attr_match.groups()
        return (
            f"对象 '{object_name}' 没有属性 '{attr_name}'",
            "请确认对象类型是否正确，并检查属性名拼写是否与平台对象结构一致。",
        )
    return (
        f"属性错误：{detail}",
        "请确认对象类型是否正确，并检查属性名拼写是否正确。",
    )


def _build_generic_error(error_type: str, detail: str) -> tuple[str, str]:
    return (
        f"{error_type}：{detail}",
        "请根据报错上下文检查策略逻辑、参数配置和依赖库导入。",
    )


def parse_execution_error(raw_error: Any) -> dict[str, Any]:
    sanitized = _sanitize_error_text(raw_error)
    error_type, detail = _extract_exception(sanitized)
    line = _extract_line(sanitized)

    builders = {
        "NameError": _build_name_error,
        "TypeError": _build_type_error,
        "KeyError": _build_key_error,
        "ImportError": _build_import_error,
        "SyntaxError": lambda item: _build_syntax_error(item, line),
        "AttributeError": _build_attribute_error,
    }
    message, suggestion = builders.get(error_type, lambda item: _build_generic_error(error_type, item))(detail)

    return {
        "type": error_type,
        "line": line,
        "message": message,
        "suggestion": suggestion,
        "example_code": ERROR_EXAMPLES.get(error_type, DEFAULT_EXAMPLE_CODE),
        "raw_error": sanitized,
    }


def dump_execution_error(raw_error: Any) -> str:
    return json.dumps(parse_execution_error(raw_error), ensure_ascii=False)


def load_execution_error(raw_error: Any) -> dict[str, Any] | None:
    if raw_error is None:
        return None
    if isinstance(raw_error, dict):
        return raw_error
    if isinstance(raw_error, str):
        try:
            payload = json.loads(raw_error)
        except json.JSONDecodeError:
            return parse_execution_error(raw_error)
        if isinstance(payload, dict) and "type" in payload:
            return payload
        return parse_execution_error(raw_error)
    return parse_execution_error(raw_error)
