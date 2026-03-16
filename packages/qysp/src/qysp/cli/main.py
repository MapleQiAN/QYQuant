"""QYS CLI - QYQuant Strategy Protocol command line tool."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

import click

from qysp import __version__
from qysp.templates import load_template_files


@click.group()
@click.version_option(version=__version__, prog_name="qys")
def cli() -> None:
    """QYS - QYQuant Strategy Protocol CLI."""


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


@cli.command()
@click.argument("name")
@click.option(
    "--template",
    default="trend-following",
    type=click.Choice(
        ["trend-following", "mean-reversion", "momentum", "multi-indicator"]
    ),
    help="Built-in strategy template",
)
def init(name: str, template: str) -> None:
    """Create a new strategy project from a template."""
    if not _VALID_NAME_RE.match(name):
        click.echo(
            (
                f"Invalid strategy name '{name}': only letters, digits, dots, "
                "dashes and underscores are allowed, and it must start with "
                "a letter or digit"
            ),
            err=True,
        )
        sys.exit(1)

    target = Path(name)
    if target.exists():
        click.echo(f"Directory '{name}' already exists")
        sys.exit(1)

    target.mkdir(parents=True)
    (target / "src").mkdir()

    template_files = load_template_files(template)

    strategy_data = dict(template_files["strategy.json"])
    strategy_data["name"] = name
    strategy_data["id"] = str(uuid.uuid4())
    (target / "strategy.json").write_text(
        json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (target / "src" / "strategy.py").write_text(
        template_files["strategy.py"], encoding="utf-8"
    )

    (target / "README.md").write_text(
        template_files["README.md"], encoding="utf-8"
    )

    click.echo(f"Strategy project '{name}' created successfully (template: {template})")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("path", type=click.Path())
def validate(path: str) -> None:
    """Validate a strategy package or directory."""
    from qysp.validator import validate as do_validate

    p = Path(path)
    if not p.exists():
        click.echo(f"Path does not exist: {path}", err=True)
        sys.exit(2)

    result = do_validate(p)
    if result["valid"]:
        click.echo("Validation passed")
    else:
        for err in result["errors"]:
            click.echo(f"ERROR: {err}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default=None, help="Output file path")
def build(source_dir: str, output: str | None) -> None:
    """Package a strategy directory into a .qys file."""
    from qysp.validator import validate as do_validate

    src = Path(source_dir)
    strategy_json_path = src / "strategy.json"
    strategy_py_path = src / "src" / "strategy.py"

    if not strategy_json_path.exists():
        click.echo("ERROR: missing strategy.json", err=True)
        sys.exit(1)
    if not strategy_py_path.exists():
        click.echo("ERROR: missing src/strategy.py", err=True)
        sys.exit(1)

    strategy_data = json.loads(strategy_json_path.read_text(encoding="utf-8"))
    strategy_name = strategy_data.get("name", src.name)

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

    strategy_data["integrity"] = {"files": integrity_files}
    updated_json = json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n"

    out_path = Path(output) if output else Path(f"{strategy_name}.qys")

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("strategy.json", updated_json)
        for f in all_files:
            rel = f.relative_to(src)
            posix_path = str(PurePosixPath(rel))
            if posix_path == "strategy.json":
                continue
            zf.write(f, posix_path)

    result = do_validate(out_path)
    if result["valid"]:
        click.echo(f"Package built: {out_path}")
    else:
        click.echo(f"Package built but validation failed: {out_path}", err=True)
        for err in result["errors"]:
            click.echo(f"  ERROR: {err}", err=True)
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
    """Upgrade a strategy package to the latest schema version."""
    p = Path(path)
    if not p.exists():
        click.echo(f"Path does not exist: {path}", err=True)
        sys.exit(2)

    is_qys = p.is_file() and p.suffix == ".qys"

    if is_qys:
        _migrate_qys(p)
        return

    if p.is_dir():
        strategy_json_path = p / "strategy.json"
    else:
        strategy_json_path = p

    if not strategy_json_path.exists():
        click.echo(f"ERROR: strategy.json not found: {strategy_json_path}", err=True)
        sys.exit(1)

    strategy_data = json.loads(strategy_json_path.read_text(encoding="utf-8"))
    current_version = strategy_data.get("schemaVersion", "")

    if current_version == CURRENT_SCHEMA_VERSION:
        click.echo(f"Already latest schema version ({CURRENT_SCHEMA_VERSION})")
    else:
        click.echo(
            f"Migrating schemaVersion {current_version} -> {CURRENT_SCHEMA_VERSION}"
        )
        strategy_data["schemaVersion"] = CURRENT_SCHEMA_VERSION
        strategy_json_path.write_text(
            json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        click.echo("Migration completed")


def _migrate_qys(qys_path: Path) -> None:
    """Migrate schema version in-place for a .qys package."""
    try:
        zf_in = zipfile.ZipFile(qys_path, "r")
    except zipfile.BadZipFile:
        click.echo("ERROR: invalid .qys file (not a ZIP archive)", err=True)
        sys.exit(1)

    with zf_in:
        if "strategy.json" not in zf_in.namelist():
            click.echo("ERROR: strategy.json is missing from .qys package", err=True)
            sys.exit(1)

        strategy_data = json.loads(zf_in.read("strategy.json"))
        current_version = strategy_data.get("schemaVersion", "")

        if current_version == CURRENT_SCHEMA_VERSION:
            click.echo(f"Already latest schema version ({CURRENT_SCHEMA_VERSION})")
            return

        click.echo(
            f"Migrating schemaVersion {current_version} -> {CURRENT_SCHEMA_VERSION}"
        )
        strategy_data["schemaVersion"] = CURRENT_SCHEMA_VERSION
        updated_json = json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n"

    tmp_path = qys_path.with_suffix(".qys.tmp")
    with zipfile.ZipFile(qys_path, "r") as zf_read, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as zf_write:
        for entry in zf_read.namelist():
            if entry == "strategy.json":
                zf_write.writestr("strategy.json", updated_json)
            else:
                zf_write.writestr(entry, zf_read.read(entry))

    tmp_path.replace(qys_path)
    click.echo("Migration completed")


# ---------------------------------------------------------------------------
# backtest (stub)
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("path", type=click.Path())
def backtest(path: str) -> None:
    """Submit a strategy backtest task (stub)."""
    click.echo("Backtest command will be integrated in a later version (Epic 3).")


# ---------------------------------------------------------------------------
# import (stub)
# ---------------------------------------------------------------------------


@cli.command("import")
@click.argument("path", type=click.Path())
def import_cmd(path: str) -> None:
    """Import a strategy package to the platform strategy library (stub)."""
    click.echo("Import command will be integrated in a later version (Epic 5).")


if __name__ == "__main__":
    cli()
