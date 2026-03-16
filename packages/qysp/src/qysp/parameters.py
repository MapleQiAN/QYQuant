"""参数注入机制：ParameterProvider 与 ValidationError。

从 strategy.json 的 parameters 数组解析参数定义，
支持类型转换、必填校验、范围校验和 enum 约束。
"""

from __future__ import annotations

from typing import Any

from qysp.context import ParameterAccessor


class ValidationError(ValueError):
    """参数验证错误。"""


class ParameterProvider(ParameterAccessor):
    """增强版参数访问器，支持类型转换和验证。"""

    @classmethod
    def from_strategy_json(
        cls,
        definitions: list[dict[str, Any]],
        overrides: dict[str, Any] | None = None,
    ) -> ParameterProvider:
        """从 strategy.json 的 parameters 数组创建实例。

        Args:
            definitions: 参数定义列表，每项含 key、type 等字段。
            overrides: 可选的覆盖值字典，优先于 default。

        Returns:
            已验证并完成类型转换的 ParameterProvider 实例。
        """
        overrides = overrides or {}
        data: dict[str, Any] = {}

        for defn in definitions:
            key = defn["key"]
            param_type = defn.get("type", "string")

            # 确定原始值：overrides > default > 无值
            if key in overrides:
                raw_value = overrides[key]
            elif "default" in defn:
                raw_value = defn["default"]
            else:
                # 无值：检查是否必填
                if defn.get("required", False):
                    raise ValidationError(
                        f"必填参数 '{key}' 缺失：未提供值且无默认值"
                    )
                continue

            # 类型转换
            value = _coerce_value(key, raw_value, param_type)

            # 范围验证（仅数值类型）
            if "min" in defn and isinstance(value, (int, float)):
                if value < defn["min"]:
                    raise ValidationError(
                        f"参数 '{key}' 的值 {value} 小于最小值 {defn['min']}"
                    )
            if "max" in defn and isinstance(value, (int, float)):
                if value > defn["max"]:
                    raise ValidationError(
                        f"参数 '{key}' 的值 {value} 大于最大值 {defn['max']}"
                    )

            # enum 验证
            if "enum" in defn and value not in defn["enum"]:
                raise ValidationError(
                    f"参数 '{key}' 的值 '{value}' 不在允许列表 {defn['enum']} 中"
                )

            data[key] = value

        return cls(data)


_BOOL_TRUE = frozenset({"true", "1", "yes"})
_BOOL_FALSE = frozenset({"false", "0", "no"})


def _coerce_value(key: str, value: Any, target_type: str) -> Any:
    """将值转换为目标类型。

    Args:
        key: 参数名称（用于错误消息）。
        value: 原始值。
        target_type: 目标类型字符串。

    Returns:
        转换后的值。

    Raises:
        ValidationError: 转换失败时。
    """
    if target_type == "integer":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"参数 '{key}' 的值 '{value}' 无法转换为 integer"
            ) from e

    if target_type == "number":
        if isinstance(value, float):
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"参数 '{key}' 的值 '{value}' 无法转换为 number"
            ) from e

    if target_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower = value.lower()
            if lower in _BOOL_TRUE:
                return True
            if lower in _BOOL_FALSE:
                return False
        raise ValidationError(
            f"参数 '{key}' 的值 '{value}' 无法转换为 boolean"
        )

    if target_type == "string":
        return str(value)

    # 其他类型（array、object、enum 等）直接返回
    return value
