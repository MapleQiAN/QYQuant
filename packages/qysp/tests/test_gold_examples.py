from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from qysp.cli.main import cli
from qysp.validator import validate


REPO_ROOT = Path(__file__).resolve().parents[3]
GOLD_TREND_ATR_DIR = REPO_ROOT / "docs" / "strategy-format" / "examples" / "GoldTrendATR"


def test_gold_trend_atr_example_validates() -> None:
    result = validate(GOLD_TREND_ATR_DIR)
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["metadata"]["name"] == "Gold Trend ATR"


def test_gold_trend_atr_example_builds_qys(tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "gold-trend-atr.qys"

    result = runner.invoke(
        cli,
        ["build", str(GOLD_TREND_ATR_DIR), "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()

    validation = validate(output)
    assert validation["valid"] is True
    assert validation["errors"] == []
