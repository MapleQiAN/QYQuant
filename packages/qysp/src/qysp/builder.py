"""Shared QYSP package builder helpers."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


PACKAGE_EXCLUDE_DIRS = {"__pycache__", ".git", ".svn", ".hg", ".venv", "node_modules"}
PACKAGE_EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
PACKAGE_EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", ".gitignore"}


class PackageBuildError(Exception):
    """Raised when a strategy project cannot be packaged."""


def build_package(source_dir: str | Path, output: str | Path | None = None) -> Path:
    """Build a .qys archive from a normalized strategy project directory."""
    src = Path(source_dir)
    strategy_json_path = src / "strategy.json"
    strategy_py_path = src / "src" / "strategy.py"

    if not strategy_json_path.exists():
        raise PackageBuildError("missing strategy.json")
    if not strategy_py_path.exists():
        raise PackageBuildError("missing src/strategy.py")

    strategy_data = json.loads(strategy_json_path.read_text(encoding="utf-8"))
    strategy_name = strategy_data.get("name", src.name)

    all_files = collect_package_files(src)
    integrity_files = build_integrity_files(all_files, src)
    strategy_data["integrity"] = {"files": integrity_files}
    updated_json = json.dumps(strategy_data, indent=2, ensure_ascii=False) + "\n"

    out_path = Path(output) if output else Path(f"{strategy_name}.qys")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("strategy.json", updated_json)
        for file_path in all_files:
            rel = file_path.relative_to(src)
            posix_path = str(PurePosixPath(rel))
            if posix_path == "strategy.json":
                continue
            zf.write(file_path, posix_path)

    return out_path


def collect_package_files(source_dir: str | Path) -> list[Path]:
    """Return files that should be included in the package archive."""
    src = Path(source_dir)

    files: list[Path] = []
    for file_path in sorted(src.rglob("*")):
        if not file_path.is_file():
            continue
        rel_parts = set(file_path.relative_to(src).parts)
        if rel_parts & PACKAGE_EXCLUDE_DIRS:
            continue
        if file_path.suffix in PACKAGE_EXCLUDE_SUFFIXES:
            continue
        if file_path.name in PACKAGE_EXCLUDE_NAMES:
            continue
        files.append(file_path)
    return files


def build_integrity_files(file_paths: list[Path], source_dir: str | Path) -> list[dict]:
    """Build the integrity manifest entries for a packaged project."""
    src = Path(source_dir)
    integrity_files: list[dict] = []

    for file_path in file_paths:
        rel = file_path.relative_to(src)
        posix_path = str(PurePosixPath(rel))
        if posix_path == "strategy.json":
            continue

        data = file_path.read_bytes()
        integrity_files.append(
            {
                "path": posix_path,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        )

    return integrity_files
