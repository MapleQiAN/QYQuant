from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from qysp import builder


def _write_strategy_project(base: Path, *, include_readme: bool = True) -> Path:
    project_dir = base / "sample-strategy"
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True)

    strategy_json = {
        "schemaVersion": "1.0",
        "kind": "QYStrategy",
        "id": "sample-strategy",
        "name": "Sample Strategy",
        "version": "0.1.0",
        "language": "python",
        "runtime": {"name": "python", "version": "3.11"},
        "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
    }
    (project_dir / "strategy.json").write_text(
        json.dumps(strategy_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (src_dir / "strategy.py").write_text(
        "class Strategy:\n    def on_bar(self, ctx, bar):\n        return None\n",
        encoding="utf-8",
    )
    if include_readme:
        (project_dir / "README.md").write_text("Sample strategy", encoding="utf-8")
    return project_dir


def test_build_package_creates_archive_and_integrity_manifest(tmp_path: Path) -> None:
    project_dir = _write_strategy_project(tmp_path)
    output_path = tmp_path / "Sample Strategy.qys"

    result = builder.build_package(project_dir, output=output_path)

    assert result == output_path
    assert output_path.exists()

    with zipfile.ZipFile(output_path, "r") as archive:
        manifest = json.loads(archive.read("strategy.json").decode("utf-8"))

    assert manifest["integrity"]["files"]
    recorded_paths = {entry["path"] for entry in manifest["integrity"]["files"]}
    assert "src/strategy.py" in recorded_paths
    assert "README.md" in recorded_paths


def test_build_package_requires_strategy_json(tmp_path: Path) -> None:
    project_dir = tmp_path / "missing-manifest"
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "src" / "strategy.py").write_text("print('noop')\n", encoding="utf-8")

    with pytest.raises(builder.PackageBuildError, match="missing strategy.json"):
        builder.build_package(project_dir, output=tmp_path / "missing-manifest.qys")


def test_build_package_requires_strategy_source(tmp_path: Path) -> None:
    project_dir = tmp_path / "missing-source"
    project_dir.mkdir()
    (project_dir / "strategy.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "kind": "QYStrategy",
                "id": "missing-source",
                "name": "Missing Source",
                "version": "0.1.0",
                "language": "python",
                "runtime": {"name": "python", "version": "3.11"},
                "entrypoint": {"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"},
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(builder.PackageBuildError, match="missing src/strategy.py"):
        builder.build_package(project_dir, output=tmp_path / "missing-source.qys")
