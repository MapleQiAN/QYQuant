"""QYSP 策略包验证器 — JSON Schema 验证与 .qys 完整性校验。"""

from __future__ import annotations

import functools
import hashlib
import importlib.resources as pkg_resources
import json
import zipfile
from pathlib import Path

from jsonschema import Draft7Validator

from qysp.parameters import ValidationError


@functools.lru_cache(maxsize=1)
def _load_schema() -> dict:
    """从打包的 schema 文件加载 JSON Schema（结果缓存）。"""
    schema_text = (
        pkg_resources.files("qysp.schema")
        .joinpath("qysp.schema.json")
        .read_text(encoding="utf-8-sig")
    )
    return json.loads(schema_text)


def validate_schema(strategy_json: dict) -> list[str]:
    """验证 strategy.json 内容是否符合 QYSP JSON Schema。

    Args:
        strategy_json: 解析后的 strategy.json 字典。

    Returns:
        错误信息列表，空列表表示验证通过。
    """
    if not isinstance(strategy_json, dict):
        raise ValidationError("strategy_json must be a dict")

    schema = _load_schema()
    errors: list[str] = []

    v = Draft7Validator(schema)
    for error in sorted(v.iter_errors(strategy_json), key=lambda e: list(e.path)):
        field_path = ".".join(str(p) for p in error.absolute_path)
        if field_path:
            errors.append(f"Invalid field '{field_path}': {error.message}")
        else:
            errors.append(error.message)

    return errors


def validate_integrity(qys_path: str | Path) -> bool:
    """验证 .qys 包的 SHA256 完整性。

    Args:
        qys_path: .qys 文件路径。

    Returns:
        True 表示校验通过。

    Raises:
        ValidationError: 校验和不匹配或包结构异常。
        FileNotFoundError: 文件不存在。
    """
    qys_path = Path(qys_path)
    if not qys_path.exists():
        raise FileNotFoundError(f"File not found: {qys_path}")

    try:
        zf = zipfile.ZipFile(qys_path, "r")
    except zipfile.BadZipFile as e:
        raise ValidationError(f"Invalid .qys package (not a valid ZIP): {e}") from e

    with zf:
        names = zf.namelist()

        if "strategy.json" not in names:
            raise ValidationError("Missing strategy.json in .qys package")

        try:
            strategy_data = json.loads(zf.read("strategy.json"))
        except json.JSONDecodeError as e:
            raise ValidationError(f"Malformed strategy.json: {e}") from e

        integrity = strategy_data.get("integrity")
        if integrity is None:
            return True  # No integrity section — skip validation

        files = integrity.get("files")
        if files is None:
            return True  # No files key — skip

        if not isinstance(files, list):
            raise ValidationError("integrity.files must be an array")

        if len(files) == 0:
            return True  # Empty files list — skip

        for entry in files:
            if not isinstance(entry, dict):
                raise ValidationError("Each entry in integrity.files must be an object")
            if "path" not in entry or "sha256" not in entry:
                raise ValidationError(
                    f"integrity.files entry missing required keys (path, sha256): {entry}"
                )

            file_path = entry["path"]
            expected_sha256 = entry["sha256"]

            if file_path not in names:
                raise ValidationError(
                    f"File listed in manifest not found in package: {file_path}"
                )

            file_data = zf.read(file_path)
            actual_sha256 = hashlib.sha256(file_data).hexdigest()

            if actual_sha256 != expected_sha256:
                raise ValidationError(f"checksum mismatch: {file_path}")

    return True


def _read_strategy_from_zip(zf: zipfile.ZipFile) -> dict | None:
    """从已打开的 ZIP 中读取 strategy.json，失败返回 None 和错误信息。"""
    if "strategy.json" not in zf.namelist():
        return None
    try:
        return json.loads(zf.read("strategy.json"))
    except json.JSONDecodeError:
        return None


def validate(path: str | Path) -> dict:
    """统一验证入口 — 自动检测输入类型并执行相应验证。

    Args:
        path: .qys 文件路径或策略目录路径。

    Returns:
        验证结果字典: {"valid": bool, "errors": list[str], "metadata": dict}

    Raises:
        FileNotFoundError: 路径不存在。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    errors: list[str] = []
    metadata: dict = {}

    if path.is_file() and path.suffix == ".qys":
        # .qys 文件：完整性 + schema 验证（只打开 ZIP 一次）
        try:
            zf = zipfile.ZipFile(path, "r")
        except zipfile.BadZipFile as e:
            return {"valid": False, "errors": [f"Invalid .qys package: {e}"], "metadata": {}}

        with zf:
            # 完整性验证
            try:
                validate_integrity(path)
            except ValidationError as e:
                errors.append(str(e))

            # Schema 验证
            strategy_data = _read_strategy_from_zip(zf)
            if strategy_data is not None:
                metadata = {
                    "name": strategy_data.get("name", ""),
                    "version": strategy_data.get("version", ""),
                }
                schema_errors = validate_schema(strategy_data)
                errors.extend(schema_errors)
    elif path.is_dir():
        # 目录：仅 schema 验证
        strategy_file = path / "strategy.json"
        if not strategy_file.exists():
            errors.append("strategy.json not found in directory")
        else:
            try:
                strategy_data = json.loads(strategy_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                return {"valid": False, "errors": [f"Malformed strategy.json: {e}"], "metadata": {}}
            metadata = {
                "name": strategy_data.get("name", ""),
                "version": strategy_data.get("version", ""),
            }
            schema_errors = validate_schema(strategy_data)
            errors.extend(schema_errors)
    else:
        errors.append(f"Unsupported path type: {path}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "metadata": metadata,
    }
