"""ParameterProvider 参数注入单元测试。"""

from __future__ import annotations

import pytest

from qysp.context import ParameterAccessor, StrategyContext, Account
from qysp.parameters import ParameterProvider, ValidationError


# ─── Task 1: ParameterProvider 核心类 ───


class TestFromStrategyJsonBasic:
    """测试从 definitions 创建 ParameterProvider，get 返回 default 值。"""

    def test_from_strategy_json_basic(self) -> None:
        definitions = [
            {"key": "lookback", "type": "integer", "default": 20},
            {"key": "threshold", "type": "number", "default": 0.05},
        ]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("lookback") == 20
        assert pp.get("threshold") == 0.05

    def test_from_strategy_json_with_overrides(self) -> None:
        definitions = [
            {"key": "lookback", "type": "integer", "default": 20},
        ]
        pp = ParameterProvider.from_strategy_json(definitions, overrides={"lookback": 50})
        assert pp.get("lookback") == 50

    def test_get_nonexistent_key_returns_default(self) -> None:
        pp = ParameterProvider.from_strategy_json([])
        assert pp.get("missing") is None
        assert pp.get("missing", 42) == 42

    def test_empty_constructor_backward_compat(self) -> None:
        pp = ParameterProvider()
        assert pp.get("anything") is None
        assert pp.get("anything", "fallback") == "fallback"


# ─── Task 2: 类型转换引擎 ───


class TestTypeCoercion:
    """测试 int/float/bool/str 四种类型转换。"""

    def test_coerce_integer_from_string(self) -> None:
        definitions = [{"key": "n", "type": "integer", "default": "42"}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("n") == 42
        assert isinstance(pp.get("n"), int)

    def test_coerce_integer_already_int(self) -> None:
        definitions = [{"key": "n", "type": "integer", "default": 42}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("n") == 42

    def test_coerce_number_from_string(self) -> None:
        definitions = [{"key": "x", "type": "number", "default": "3.14"}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("x") == pytest.approx(3.14)

    def test_coerce_number_already_float(self) -> None:
        definitions = [{"key": "x", "type": "number", "default": 3.14}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("x") == pytest.approx(3.14)

    @pytest.mark.parametrize("val", ["true", "True", "TRUE", "1", "yes", "Yes"])
    def test_coerce_boolean_true(self, val: str) -> None:
        definitions = [{"key": "flag", "type": "boolean", "default": val}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("flag") is True

    @pytest.mark.parametrize("val", ["false", "False", "FALSE", "0", "no", "No"])
    def test_coerce_boolean_false(self, val: str) -> None:
        definitions = [{"key": "flag", "type": "boolean", "default": val}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("flag") is False

    def test_coerce_boolean_already_bool(self) -> None:
        definitions = [{"key": "flag", "type": "boolean", "default": True}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("flag") is True

    def test_coerce_string(self) -> None:
        definitions = [{"key": "name", "type": "string", "default": 123}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("name") == "123"

    def test_coerce_invalid_type_raises(self) -> None:
        definitions = [{"key": "n", "type": "integer", "default": "abc"}]
        with pytest.raises(ValidationError, match="n"):
            ParameterProvider.from_strategy_json(definitions)

    def test_coerce_invalid_boolean_raises(self) -> None:
        definitions = [{"key": "flag", "type": "boolean", "default": "maybe"}]
        with pytest.raises(ValidationError, match="flag"):
            ParameterProvider.from_strategy_json(definitions)


# ─── Task 3: 参数验证 ───


class TestValidation:
    """测试必填参数、范围验证、enum 验证。"""

    def test_required_param_missing(self) -> None:
        definitions = [{"key": "api_key", "type": "string", "required": True}]
        with pytest.raises(ValidationError, match="api_key"):
            ParameterProvider.from_strategy_json(definitions)

    def test_required_param_with_default(self) -> None:
        definitions = [{"key": "api_key", "type": "string", "required": True, "default": "xxx"}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("api_key") == "xxx"

    def test_required_param_with_override(self) -> None:
        definitions = [{"key": "api_key", "type": "string", "required": True}]
        pp = ParameterProvider.from_strategy_json(definitions, overrides={"api_key": "yyy"})
        assert pp.get("api_key") == "yyy"

    def test_min_max_within_range(self) -> None:
        definitions = [{"key": "n", "type": "integer", "default": 10, "min": 5, "max": 20}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("n") == 10

    def test_min_violation(self) -> None:
        definitions = [{"key": "n", "type": "integer", "default": 3, "min": 5, "max": 20}]
        with pytest.raises(ValidationError, match="n") as exc_info:
            ParameterProvider.from_strategy_json(definitions)
        assert "3" in str(exc_info.value)
        assert "5" in str(exc_info.value)

    def test_max_violation(self) -> None:
        definitions = [{"key": "n", "type": "integer", "default": 25, "min": 5, "max": 20}]
        with pytest.raises(ValidationError, match="n") as exc_info:
            ParameterProvider.from_strategy_json(definitions)
        assert "25" in str(exc_info.value)
        assert "20" in str(exc_info.value)

    def test_enum_valid_value(self) -> None:
        definitions = [{"key": "mode", "type": "string", "default": "fast", "enum": ["fast", "slow"]}]
        pp = ParameterProvider.from_strategy_json(definitions)
        assert pp.get("mode") == "fast"

    def test_enum_invalid_value(self) -> None:
        definitions = [{"key": "mode", "type": "string", "default": "turbo", "enum": ["fast", "slow"]}]
        with pytest.raises(ValidationError, match="mode"):
            ParameterProvider.from_strategy_json(definitions)


# ─── Task 4 & 5: StrategyContext 集成与公共导出 ───


class TestIntegration:
    """测试与 StrategyContext 集成及公共导出。"""

    def test_strategy_context_with_provider(self) -> None:
        definitions = [{"key": "lookback", "type": "integer", "default": 20}]
        pp = ParameterProvider.from_strategy_json(definitions)
        ctx = StrategyContext(account=Account(cash=100000.0), parameters=pp)
        assert ctx.parameters.get("lookback") == 20
        assert ctx.parameters.get("lookback", 99) == 20
        assert ctx.parameters.get("missing", 99) == 99

    def test_parameter_accessor_unchanged(self) -> None:
        pa = ParameterAccessor({"x": 1})
        assert pa.get("x") == 1
        assert pa.get("y") is None
        assert pa.get("y", 2) == 2

    def test_backward_compat_empty_params(self) -> None:
        pp = ParameterProvider.from_strategy_json([], None)
        assert pp.get("anything") is None
        assert pp.get("anything", "default") == "default"

    def test_backward_compat_no_params(self) -> None:
        pp = ParameterProvider.from_strategy_json([], None)
        ctx = StrategyContext(account=Account(cash=100000.0), parameters=pp)
        assert ctx.parameters.get("x") is None

    def test_public_imports(self) -> None:
        from qysp import ParameterProvider, ValidationError
        assert ParameterProvider is not None
        assert ValidationError is not None
