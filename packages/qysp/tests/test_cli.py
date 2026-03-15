"""tests for qysp.cli — CLI 骨架回归测试。"""

from click.testing import CliRunner

from qysp.cli.main import cli


class TestCLI:
    """qys CLI 入口测试。"""

    def test_help_exits_zero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_help_contains_description(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "QYS" in result.output

    def test_version_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
