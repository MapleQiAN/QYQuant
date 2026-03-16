"""QYS CLI — QYQuant Strategy Protocol 命令行工具。"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import textwrap
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

import click

from qysp import __version__


@click.group()
@click.version_option(version=__version__, prog_name="qys")
def cli() -> None:
    """QYS — QYQuant Strategy Protocol CLI."""


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

_STRATEGY_PY_TEMPLATE = textwrap.dedent("""\
    \"\"\"策略入口 — event_v1 接口。\"\"\"

    from __future__ import annotations


    def on_bar(ctx, data):
        \"\"\"每根 K 线触发的回调函数。

        Args:
            ctx: StrategyContext 策略上下文。
            data: BarData 当前 K 线数据。
        \"\"\"
        pass
""")


def _make_strategy_json(name: str, template: str) -> dict:
    """生成 strategy.json 内容。"""
    return {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": str(uuid.uuid4()),
        "name": name,
        "version": "0.1.0",
        "description": "",
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {
            "path": "src/strategy.py",
            "callable": "on_bar",
            "interface": "event_v1",
        },
        "parameters": [
            {
                "key": "period",
                "type": "integer",
                "default": 20,
                "min": 1,
                "max": 500,
                "description": "计算周期",
            }
        ],
        "ui": {"category": template},
    }


_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


@cli.command()
@click.argument("name")
@click.option(
    "--template",
    default="trend-following",
    type=click.Choice(
        ["trend-following", "mean-reversion", "momentum", "multi-indicator"]
    ),
    help="策略模板类型",
)
def init(name: str, template: str) -> None:
    """从模板创建新策略项目"""
    if not _VALID_NAME_RE.match(name):
        click.echo(
            f"无效的策略名称 '{name}'：只允许字母、数字、连字符、下划线和点号，"
            "且必须以字母或数字开头",
            err=True,
        )
        sys.exit(1)

    target = Path(name)
    if target.exists():
        click.echo(f"Directory '{name}' already exists")
        sys.exit(1)

    target.mkdir(parents=True)
    (target / "src").mkdir()

    # strategy.json
    strategy_data = _make_strategy_json(name, template)
    (target / "strategy.json").write_text(
        json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # src/strategy.py
    (target / "src" / "strategy.py").write_text(
        _STRATEGY_PY_TEMPLATE, encoding="utf-8"
    )

    # README.md
    readme = f"# {name}\n\n策略项目，基于 QYQuant Strategy Protocol。\n"
    (target / "README.md").write_text(readme, encoding="utf-8")

    click.echo(f"✅ 策略项目 '{name}' 创建成功（模板: {template}）")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("path", type=click.Path())
def validate(path: str) -> None:
    """验证策略包或策略目录"""
    from qysp.validator import validate as do_validate

    p = Path(path)
    if not p.exists():
        click.echo(f"路径不存在: {path}", err=True)
        sys.exit(2)

    result = do_validate(p)
    if result["valid"]:
        click.echo("✅ 验证通过")
    else:
        for err in result["errors"]:
            click.echo(f"❌ {err}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default=None, help="输出文件路径")
def build(source_dir: str, output: str | None) -> None:
    """将策略目录打包为 .qys 文件"""
    from qysp.validator import validate as do_validate

    src = Path(source_dir)
    strategy_json_path = src / "strategy.json"
    strategy_py_path = src / "src" / "strategy.py"

    if not strategy_json_path.exists():
        click.echo("❌ 缺少 strategy.json", err=True)
        sys.exit(1)
    if not strategy_py_path.exists():
        click.echo("❌ 缺少 src/strategy.py", err=True)
        sys.exit(1)

    # Read strategy.json
    strategy_data = json.loads(strategy_json_path.read_text(encoding="utf-8"))
    strategy_name = strategy_data.get("name", src.name)

    # Collect all files (relative to source_dir), filtering out junk
    _EXCLUDE_DIRS = {"__pycache__", ".git", ".svn", ".hg", ".venv", "node_modules"}
    _EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
    _EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", ".gitignore"}

    all_files: list[Path] = []
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        parts = set(f.relative_to(src).parts)
        if parts & _EXCLUDE_DIRS:
            continue
        if f.suffix in _EXCLUDE_SUFFIXES:
            continue
        if f.name in _EXCLUDE_NAMES:
            continue
        all_files.append(f)

    # Compute SHA256 for all files except strategy.json itself
    integrity_files: list[dict] = []
    for f in all_files:
        rel = f.relative_to(src)
        posix_path = str(PurePosixPath(rel))
        if posix_path == "strategy.json":
            continue
        data = f.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        integrity_files.append(
            {"path": posix_path, "sha256": sha, "size": len(data)}
        )

    # Update integrity in strategy.json
    strategy_data["integrity"] = {"files": integrity_files}
    updated_json = json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n"

    # Determine output path
    out_path = Path(output) if output else Path(f"{strategy_name}.qys")

    # Create ZIP
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write updated strategy.json
        zf.writestr("strategy.json", updated_json)
        # Write all other files
        for f in all_files:
            rel = f.relative_to(src)
            posix_path = str(PurePosixPath(rel))
            if posix_path == "strategy.json":
                continue
            zf.write(f, posix_path)

    # Auto-validate the built package
    result = do_validate(out_path)
    if result["valid"]:
        click.echo(f"✅ 打包完成: {out_path}")
    else:
        click.echo(f"⚠️ 打包完成但验证发现问题: {out_path}", err=True)
        for err in result["errors"]:
            click.echo(f"  ❌ {err}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# migrate
# ---------------------------------------------------------------------------

CURRENT_SCHEMA_VERSION = "1.0"

MIGRATIONS: dict[str, Callable] = {
    # "0.9->1.0": migrate_0_9_to_1_0,  # placeholder
}


@cli.command()
@click.argument("path", type=click.Path())
def migrate(path: str) -> None:
    """将策略包升级至最新 schema 版本"""
    p = Path(path)
    if not p.exists():
        click.echo(f"路径不存在: {path}", err=True)
        sys.exit(2)

    # Locate strategy.json — handle directory, .qys file, or bare json
    is_qys = p.is_file() and p.suffix == ".qys"

    if is_qys:
        _migrate_qys(p)
        return

    if p.is_dir():
        strategy_json_path = p / "strategy.json"
    else:
        strategy_json_path = p

    if not strategy_json_path.exists():
        click.echo(f"❌ 未找到 strategy.json: {strategy_json_path}", err=True)
        sys.exit(1)

    strategy_data = json.loads(strategy_json_path.read_text(encoding="utf-8"))
    current_version = strategy_data.get("schemaVersion", "")

    if current_version == CURRENT_SCHEMA_VERSION:
        click.echo(f"已是最新版本（{CURRENT_SCHEMA_VERSION}）")
    else:
        click.echo(
            f"当前版本 {current_version} → 最新版本 {CURRENT_SCHEMA_VERSION}"
        )
        strategy_data["schemaVersion"] = CURRENT_SCHEMA_VERSION
        strategy_json_path.write_text(
            json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        click.echo("✅ 迁移完成")


def _migrate_qys(qys_path: Path) -> None:
    """对 .qys 包执行就地 schema 版本迁移。"""
    try:
        zf_in = zipfile.ZipFile(qys_path, "r")
    except zipfile.BadZipFile:
        click.echo("❌ 无效的 .qys 文件（非 ZIP 格式）", err=True)
        sys.exit(1)

    with zf_in:
        if "strategy.json" not in zf_in.namelist():
            click.echo("❌ .qys 包中缺少 strategy.json", err=True)
            sys.exit(1)

        strategy_data = json.loads(zf_in.read("strategy.json"))
        current_version = strategy_data.get("schemaVersion", "")

        if current_version == CURRENT_SCHEMA_VERSION:
            click.echo(f"已是最新版本（{CURRENT_SCHEMA_VERSION}）")
            return

        click.echo(
            f"当前版本 {current_version} → 最新版本 {CURRENT_SCHEMA_VERSION}"
        )
        strategy_data["schemaVersion"] = CURRENT_SCHEMA_VERSION
        updated_json = json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n"

        # Rewrite the .qys with updated strategy.json
        all_entries = zf_in.namelist()

    # Re-open for reading (context manager closed above), write to temp then replace
    tmp_path = qys_path.with_suffix(".qys.tmp")
    with zipfile.ZipFile(qys_path, "r") as zf_in, \
         zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf_out:
        for entry in zf_in.namelist():
            if entry == "strategy.json":
                zf_out.writestr("strategy.json", updated_json)
            else:
                zf_out.writestr(entry, zf_in.read(entry))

    tmp_path.replace(qys_path)
    click.echo("✅ 迁移完成")


# ---------------------------------------------------------------------------
# backtest (stub)
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("path", type=click.Path())
def backtest(path: str) -> None:
    """提交策略回测任务（桩实现）"""
    click.echo("本地回测功能将在后续版本集成（Epic 3）。请使用 Web 平台提交回测任务。")


# ---------------------------------------------------------------------------
# import (stub)
# ---------------------------------------------------------------------------


@cli.command("import")
@click.argument("path", type=click.Path())
def import_cmd(path: str) -> None:
    """将策略包导入到平台策略库（桩实现）"""
    click.echo("策略导入功能将在后续版本集成（Epic 5）。请使用 Web 平台导入策略。")


if __name__ == "__main__":
    cli()
