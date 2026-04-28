import json
from pathlib import Path

from qysp.validator import validate

from app.qsga.compiler.qyir_to_qysp import compile_qyir_to_qysp_project


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "qsga"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_compile_trend_following_qyir_to_valid_qysp_project(tmp_path):
    project_dir = compile_qyir_to_qysp_project(load_fixture("trend_following_basic.json"), tmp_path / "trend")

    manifest = json.loads((project_dir / "strategy.json").read_text(encoding="utf-8"))
    source = (project_dir / "src" / "strategy.py").read_text(encoding="utf-8")

    assert validate(project_dir)["valid"]
    assert manifest["kind"] == "QYStrategy"
    assert manifest["entrypoint"]["callable"] == "on_bar"
    assert manifest["ui"]["category"] == "trend-following"
    assert manifest["universe"]["symbols"] == ["XAUUSD"]
    assert manifest["risk"]["maxPositionPct"] == 30
    assert "def on_bar" in source


def test_compile_momentum_qyir_to_valid_qysp_project(tmp_path):
    project_dir = compile_qyir_to_qysp_project(load_fixture("momentum_basic.json"), tmp_path / "momentum")

    manifest = json.loads((project_dir / "strategy.json").read_text(encoding="utf-8"))

    assert validate(project_dir)["valid"]
    assert manifest["ui"]["category"] == "momentum"
    assert manifest["data"]["resolution"] == "1h"
    assert {param["key"]: param["default"] for param in manifest["parameters"]}["ema_period"] == 12
    assert {param["key"]: param["default"] for param in manifest["parameters"]}["signal_period"] == 26

