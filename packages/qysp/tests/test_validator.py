"""QYSP 验证器单元测试 — 覆盖 JSON Schema 验证与 .qys 完整性校验。"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from qysp.parameters import ValidationError
from qysp.validator import validate, validate_integrity, validate_schema


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _minimal_strategy() -> dict:
    """返回仅包含 required 字段的最小合法 strategy.json。"""
    return {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": "a2e4a6cf-3f2f-4c5d-8a4a-1f5f9b2b2e10",
        "name": "Test Strategy",
        "version": "1.0.0",
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "main"},
    }


def _make_qys(tmp_path: Path, strategy_data: dict, files: dict[str, bytes] | None = None) -> Path:
    """创建一个 .qys（ZIP）测试包。

    Args:
        tmp_path: pytest 临时目录。
        strategy_data: strategy.json 的内容。
        files: 额外文件 {路径: 内容}。

    Returns:
        .qys 文件路径。
    """
    qys_path = tmp_path / "test.qys"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("strategy.json", json.dumps(strategy_data))
        if files:
            for name, content in files.items():
                zf.writestr(name, content)
    qys_path.write_bytes(buf.getvalue())
    return qys_path


# ---------------------------------------------------------------------------
# Schema 验证测试
# ---------------------------------------------------------------------------

class TestValidateSchema:
    def test_valid_minimal(self):
        """仅含 required 字段的 strategy.json 通过验证。"""
        errors = validate_schema(_minimal_strategy())
        assert errors == []

    def test_valid_with_ui(self):
        """包含 ui 字段的 strategy.json 通过验证。"""
        data = _minimal_strategy()
        data["ui"] = {
            "icon": "gold-icon",
            "category": "trend-following",
            "difficulty": "beginner",
        }
        errors = validate_schema(data)
        assert errors == []

    def test_valid_with_backtest(self):
        """包含 backtest 字段的 strategy.json 通过验证。"""
        data = _minimal_strategy()
        data["backtest"] = {
            "defaultPeriod": {"start": "2020-01-01", "end": "2024-12-31"},
            "initialCapital": 100000,
        }
        errors = validate_schema(data)
        assert errors == []

    def test_valid_full(self):
        """包含所有可选字段的 strategy.json 通过验证。"""
        data = _minimal_strategy()
        data["ui"] = {
            "icon": "trend-icon",
            "category": "momentum",
            "difficulty": "advanced",
        }
        data["backtest"] = {
            "defaultPeriod": {"start": "2020-01-01", "end": "2024-12-31"},
            "initialCapital": 50000,
        }
        data["tags"] = ["test"]
        errors = validate_schema(data)
        assert errors == []

    def test_valid_with_user_facing_parameter(self):
        """参数可包含 user_facing 引导元数据。"""
        data = _minimal_strategy()
        data["parameters"] = [
            {
                "key": "atr_multiplier",
                "type": "number",
                "default": 2.0,
                "min": 0.5,
                "max": 5.0,
                "user_facing": {
                    "question": "How much volatility can you accept?",
                    "options": [
                        {"label": "Tight", "value": 1.0, "desc": "Exit quickly"},
                        {"label": "Balanced", "value": 2.0},
                    ],
                },
            }
        ]
        errors = validate_schema(data)
        assert errors == []

    def test_missing_required(self):
        """缺少 required 字段时报错并指明字段名。"""
        data = _minimal_strategy()
        del data["name"]
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_invalid_type(self):
        """字段类型错误时报错并指明字段名。"""
        data = _minimal_strategy()
        data["name"] = 12345  # should be string
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_invalid_enum_category(self):
        """category 枚举值无效时报错。"""
        data = _minimal_strategy()
        data["ui"] = {"category": "invalid-category"}
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("category" in e for e in errors)

    def test_invalid_enum_difficulty(self):
        """difficulty 枚举值无效时报错。"""
        data = _minimal_strategy()
        data["ui"] = {"difficulty": "expert"}
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("difficulty" in e for e in errors)

    def test_backward_compat_gold_trend(self):
        """现有 GoldTrend 示例 strategy.json 通过验证。"""
        gold_trend_path = Path(__file__).parents[3] / "docs" / "strategy-format" / "examples" / "GoldTrend" / "strategy.json"
        if not gold_trend_path.exists():
            pytest.skip("GoldTrend example not found")
        data = json.loads(gold_trend_path.read_text(encoding="utf-8-sig"))
        errors = validate_schema(data)
        assert errors == []

    def test_backward_compat_gold_step_by_step(self):
        """现有 GoldStepByStep 示例 strategy.json 通过验证。"""
        gold_sbs_path = Path(__file__).parents[3] / "docs" / "strategy-format" / "examples" / "GoldStepByStep" / "strategy.json"
        if not gold_sbs_path.exists():
            pytest.skip("GoldStepByStep example not found")
        data = json.loads(gold_sbs_path.read_text(encoding="utf-8-sig"))
        errors = validate_schema(data)
        assert errors == []

    def test_backtest_date_format_invalid(self):
        """backtest.defaultPeriod 日期格式无效时报错。"""
        data = _minimal_strategy()
        data["backtest"] = {
            "defaultPeriod": {"start": "not-a-date", "end": "2024-12-31"},
        }
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("start" in e for e in errors)

    def test_non_dict_input(self):
        """非 dict 输入抛出 ValidationError。"""
        with pytest.raises(ValidationError, match="must be a dict"):
            validate_schema("not a dict")


# ---------------------------------------------------------------------------
# .qys 完整性验证测试
# ---------------------------------------------------------------------------

class TestValidateIntegrity:
    def test_valid(self, tmp_path: Path):
        """SHA256 匹配的 .qys 包验证通过。"""
        code = b"print('hello')"
        code_sha = hashlib.sha256(code).hexdigest()
        strategy = _minimal_strategy()
        strategy["integrity"] = {
            "files": [
                {"path": "src/strategy.py", "sha256": code_sha, "size": len(code)},
            ]
        }
        qys = _make_qys(tmp_path, strategy, {"src/strategy.py": code})
        assert validate_integrity(qys) is True

    def test_checksum_mismatch(self, tmp_path: Path):
        """SHA256 不匹配时抛出 ValidationError。"""
        strategy = _minimal_strategy()
        strategy["integrity"] = {
            "files": [
                {"path": "src/strategy.py", "sha256": "0" * 64, "size": 5},
            ]
        }
        qys = _make_qys(tmp_path, strategy, {"src/strategy.py": b"hello"})
        with pytest.raises(ValidationError, match="checksum mismatch"):
            validate_integrity(qys)

    def test_missing_file(self, tmp_path: Path):
        """manifest 中列出但包内不存在的文件报错。"""
        strategy = _minimal_strategy()
        strategy["integrity"] = {
            "files": [
                {"path": "missing.py", "sha256": "abc", "size": 0},
            ]
        }
        qys = _make_qys(tmp_path, strategy)
        with pytest.raises(ValidationError, match="not found in package"):
            validate_integrity(qys)

    def test_no_strategy_json(self, tmp_path: Path):
        """.qys 包缺少 strategy.json 时报错。"""
        qys_path = tmp_path / "bad.qys"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("other.txt", "data")
        qys_path.write_bytes(buf.getvalue())
        with pytest.raises(ValidationError, match="Missing strategy.json"):
            validate_integrity(qys_path)

    def test_no_integrity_field(self, tmp_path: Path):
        """strategy.json 无 integrity 字段时跳过验证，返回 True。"""
        strategy = _minimal_strategy()
        # No integrity key
        qys = _make_qys(tmp_path, strategy)
        assert validate_integrity(qys) is True

    def test_file_not_found(self, tmp_path: Path):
        """不存在的路径抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            validate_integrity(tmp_path / "nonexistent.qys")

    def test_bad_zip_file(self, tmp_path: Path):
        """非法 ZIP 文件抛出 ValidationError。"""
        bad_qys = tmp_path / "bad.qys"
        bad_qys.write_bytes(b"this is not a zip file")
        with pytest.raises(ValidationError, match="not a valid ZIP"):
            validate_integrity(bad_qys)

    def test_malformed_strategy_json(self, tmp_path: Path):
        """损坏的 strategy.json 抛出 ValidationError。"""
        qys_path = tmp_path / "bad_json.qys"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("strategy.json", "{invalid json")
        qys_path.write_bytes(buf.getvalue())
        with pytest.raises(ValidationError, match="Malformed strategy.json"):
            validate_integrity(qys_path)

    def test_integrity_files_not_list(self, tmp_path: Path):
        """integrity.files 非数组时抛出 ValidationError。"""
        strategy = _minimal_strategy()
        strategy["integrity"] = {"files": "not-a-list"}
        qys = _make_qys(tmp_path, strategy)
        with pytest.raises(ValidationError, match="must be an array"):
            validate_integrity(qys)

    def test_integrity_entry_missing_keys(self, tmp_path: Path):
        """integrity.files 条目缺少 path/sha256 时抛出 ValidationError。"""
        strategy = _minimal_strategy()
        strategy["integrity"] = {"files": [{"path": "only-path"}]}
        qys = _make_qys(tmp_path, strategy)
        with pytest.raises(ValidationError, match="missing required keys"):
            validate_integrity(qys)

    def test_repo_gold_step_by_step_package_is_valid(self):
        """仓库内置 GoldStepByStep.qys 应通过完整性校验。"""
        package_path = Path(__file__).parents[3] / "backend" / "strategy_store" / "GoldStepByStep.qys"
        if not package_path.exists():
            pytest.skip("GoldStepByStep package not found")
        assert validate_integrity(package_path) is True


# ---------------------------------------------------------------------------
# 统一入口测试
# ---------------------------------------------------------------------------

class TestValidate:
    def test_qys_file(self, tmp_path: Path):
        """.qys 文件路径输入，执行完整验证。"""
        code = b"print('hello')"
        code_sha = hashlib.sha256(code).hexdigest()
        strategy = _minimal_strategy()
        strategy["integrity"] = {
            "files": [
                {"path": "src/strategy.py", "sha256": code_sha, "size": len(code)},
            ]
        }
        qys = _make_qys(tmp_path, strategy, {"src/strategy.py": code})
        result = validate(qys)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["metadata"]["name"] == "Test Strategy"

    def test_directory(self, tmp_path: Path):
        """目录路径输入，仅执行 schema 验证。"""
        strategy = _minimal_strategy()
        (tmp_path / "strategy.json").write_text(json.dumps(strategy), encoding="utf-8")
        result = validate(tmp_path)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_directory_no_strategy_json(self, tmp_path: Path):
        """目录中无 strategy.json 时报错。"""
        result = validate(tmp_path)
        assert result["valid"] is False
        assert any("strategy.json not found" in e for e in result["errors"])

    def test_nonexistent_path(self, tmp_path: Path):
        """不存在的路径抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            validate(tmp_path / "nonexistent")

    def test_qys_with_schema_errors(self, tmp_path: Path):
        """.qys 文件 schema 不合法时返回 errors。"""
        strategy = _minimal_strategy()
        del strategy["name"]  # Remove required field
        qys = _make_qys(tmp_path, strategy)
        result = validate(qys)
        assert result["valid"] is False
        assert any("name" in e for e in result["errors"])

    def test_qys_with_integrity_error(self, tmp_path: Path):
        """.qys 文件完整性校验失败时返回 errors。"""
        strategy = _minimal_strategy()
        strategy["integrity"] = {
            "files": [
                {"path": "src/strategy.py", "sha256": "0" * 64, "size": 5},
            ]
        }
        qys = _make_qys(tmp_path, strategy, {"src/strategy.py": b"hello"})
        result = validate(qys)
        assert result["valid"] is False
        assert any("checksum mismatch" in e for e in result["errors"])

    def test_qys_bad_zip(self, tmp_path: Path):
        """非法 ZIP .qys 文件返回错误而非崩溃。"""
        bad_qys = tmp_path / "bad.qys"
        bad_qys.write_bytes(b"not a zip")
        result = validate(bad_qys)
        assert result["valid"] is False
        assert any("Invalid .qys package" in e for e in result["errors"])

    def test_directory_malformed_json(self, tmp_path: Path):
        """目录中 strategy.json 损坏时返回错误。"""
        (tmp_path / "strategy.json").write_text("{bad json", encoding="utf-8")
        result = validate(tmp_path)
        assert result["valid"] is False
        assert any("Malformed" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# ValidationError 测试
# ---------------------------------------------------------------------------

class TestValidationError:
    def test_message_contains_field(self):
        """验证错误消息包含具体字段名。"""
        data = _minimal_strategy()
        data["ui"] = {"category": "bad-value"}
        errors = validate_schema(data)
        assert len(errors) > 0
        assert any("category" in e for e in errors)

    def test_is_exception(self):
        """ValidationError 是 Exception 子类。"""
        assert issubclass(ValidationError, Exception)

    def test_is_value_error(self):
        """ValidationError 是 ValueError 子类。"""
        assert issubclass(ValidationError, ValueError)


# ---------------------------------------------------------------------------
# 公共导入测试
# ---------------------------------------------------------------------------

class TestPublicImports:
    def test_imports_from_validator(self):
        """from qysp.validator import validate, ValidationError 无报错。"""
        from qysp.validator import validate, validate_schema, validate_integrity, ValidationError  # noqa: F811, F401
        assert callable(validate)
        assert callable(validate_schema)
        assert callable(validate_integrity)
        assert issubclass(ValidationError, Exception)

    def test_imports_from_qysp(self):
        """from qysp import validate, ValidationError 无报错。"""
        from qysp import validate, validate_schema, validate_integrity, ValidationError  # noqa: F811, F401
        assert callable(validate)
        assert callable(validate_schema)
        assert callable(validate_integrity)
