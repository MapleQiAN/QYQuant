"""Tests for qysp.cli command-line behaviors."""

from __future__ import annotations

import json
import os
import zipfile
from uuid import UUID

from click.testing import CliRunner

from qysp.cli.main import cli
from qysp.templates import get_template_path, load_template_files


class TestCLI:
    """Top-level CLI entry tests."""

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

    def test_help_lists_all_commands(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        for cmd in ["init", "validate", "build", "backtest", "import", "migrate"]:
            assert cmd in result.output, f"Missing command: {cmd}"


class TestInit:
    """qys init command tests."""

    def test_init_creates_directory(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "my-strategy"])
            assert result.exit_code == 0
            assert os.path.isdir("my-strategy")
            assert os.path.isfile("my-strategy/strategy.json")
            assert os.path.isfile("my-strategy/src/strategy.py")
            assert os.path.isfile("my-strategy/README.md")

    def test_init_strategy_json_valid(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strategy"])
            with open("my-strategy/strategy.json", encoding="utf-8") as f:
                data = json.load(f)
            assert data["name"] == "my-strategy"
            assert data["entrypoint"]["interface"] == "event_v1"
            assert len(data["parameters"]) >= 1

    def test_init_with_template_option(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli, ["init", "test-strat", "--template", "mean-reversion"]
            )
            assert result.exit_code == 0
            with open("test-strat/strategy.json", encoding="utf-8") as f:
                data = json.load(f)
            assert data["ui"]["category"] == "mean-reversion"

    def test_init_all_templates_can_validate(self, tmp_path: object) -> None:
        runner = CliRunner()
        templates = ["trend-following", "mean-reversion", "momentum", "multi-indicator"]
        with runner.isolated_filesystem(temp_dir=tmp_path):
            for index, template in enumerate(templates):
                name = f"strategy-{index}"
                init_result = runner.invoke(cli, ["init", name, "--template", template])
                assert init_result.exit_code == 0

                validate_result = runner.invoke(cli, ["validate", name])
                assert validate_result.exit_code == 0

    def test_init_strategy_json_name_and_id(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "alpha", "--template", "momentum"])
            with open("alpha/strategy.json", encoding="utf-8") as f:
                data_alpha = json.load(f)

            runner.invoke(cli, ["init", "beta", "--template", "momentum"])
            with open("beta/strategy.json", encoding="utf-8") as f:
                data_beta = json.load(f)

            assert data_alpha["name"] == "alpha"
            assert data_beta["name"] == "beta"
            UUID(data_alpha["id"])
            UUID(data_beta["id"])
            assert data_alpha["id"] != data_beta["id"]

    def test_init_strategy_py_uses_sdk_types(self, tmp_path: object) -> None:
        runner = CliRunner()
        templates = ["trend-following", "mean-reversion", "momentum", "multi-indicator"]
        with runner.isolated_filesystem(temp_dir=tmp_path):
            for index, template in enumerate(templates):
                name = f"strategy-{index}"
                runner.invoke(cli, ["init", name, "--template", template])
                content = open(f"{name}/src/strategy.py", encoding="utf-8").read()
                assert "from qysp.context import StrategyContext, BarData" in content
                assert "def on_bar(ctx: StrategyContext, data: BarData) -> list:" in content
                assert "ctx.parameters.get(" in content

    def test_init_existing_directory_fails(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.makedirs("my-strategy")
            result = runner.invoke(cli, ["init", "my-strategy"])
            assert result.exit_code != 0
            assert "already exists" in result.output

    def test_init_default_template(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strategy"])
            with open("my-strategy/strategy.json", encoding="utf-8") as f:
                data = json.load(f)
            assert data["ui"]["category"] == "trend-following"

    def test_init_invalid_name_rejected(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "../hack"])
            assert result.exit_code != 0

    def test_init_invalid_name_with_spaces(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "bad name"])
            assert result.exit_code != 0


class TestValidate:
    """qys validate command tests."""

    def _create_valid_strategy_dir(self, base: str, name: str = "test-strat") -> str:
        """Helper: create a valid strategy directory via init."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=base):
            runner.invoke(cli, ["init", name])
        return os.path.join(base, name)

    def test_validate_valid_directory(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "valid-strat"])
            result = runner.invoke(cli, ["validate", "valid-strat"])
            assert result.exit_code == 0
            assert "Validation passed" in result.output

    def test_validate_invalid_directory(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.makedirs("bad-strat")
            with open("bad-strat/strategy.json", "w", encoding="utf-8") as f:
                json.dump({"name": "bad"}, f)
            result = runner.invoke(cli, ["validate", "bad-strat"])
            assert result.exit_code == 1

    def test_validate_valid_qys_file(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            result = runner.invoke(cli, ["build", "my-strat"])
            assert result.exit_code == 0
            result = runner.invoke(cli, ["validate", "my-strat.qys"])
            assert result.exit_code == 0
            assert "Validation passed" in result.output

    def test_validate_invalid_qys_file(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.makedirs("bad")
            with open("bad/strategy.json", "w", encoding="utf-8") as f:
                json.dump({"name": "bad"}, f)
            with zipfile.ZipFile("bad.qys", "w") as zf:
                zf.write("bad/strategy.json", "strategy.json")
            result = runner.invoke(cli, ["validate", "bad.qys"])
            assert result.exit_code == 1

    def test_validate_nonexistent_path(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["validate", "nonexistent"])
            assert result.exit_code == 2


class TestBuild:
    """qys build command tests."""

    def test_build_creates_qys_file(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            result = runner.invoke(cli, ["build", "my-strat"])
            assert result.exit_code == 0
            assert os.path.isfile("my-strat.qys")

    def test_build_integrity_valid(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            runner.invoke(cli, ["build", "my-strat"])
            result = runner.invoke(cli, ["validate", "my-strat.qys"])
            assert result.exit_code == 0

    def test_build_custom_output(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            result = runner.invoke(cli, ["build", "my-strat", "--output", "custom.qys"])
            assert result.exit_code == 0
            assert os.path.isfile("custom.qys")

    def test_build_records_additional_files_in_integrity_manifest(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            with open("my-strat/README.md", "w", encoding="utf-8") as handle:
                handle.write("Strategy notes\n")

            result = runner.invoke(cli, ["build", "my-strat"])

            assert result.exit_code == 0
            with zipfile.ZipFile("my-strat.qys", "r") as archive:
                manifest = json.loads(archive.read("strategy.json").decode("utf-8"))
            recorded_paths = {entry["path"] for entry in manifest["integrity"]["files"]}
            assert "README.md" in recorded_paths

    def test_build_missing_strategy_json(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.makedirs("empty-dir")
            result = runner.invoke(cli, ["build", "empty-dir"])
            assert result.exit_code != 0
            assert "strategy.json" in result.output

    def test_build_missing_strategy_py(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.makedirs("no-py")
            with open("no-py/strategy.json", "w", encoding="utf-8") as f:
                json.dump({"name": "test"}, f)
            result = runner.invoke(cli, ["build", "no-py"])
            assert result.exit_code != 0


class TestMigrate:
    """qys migrate command tests."""

    def test_migrate_already_latest(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            result = runner.invoke(cli, ["migrate", "my-strat"])
            assert result.exit_code == 0
            assert "Already latest schema version" in result.output

    def test_migrate_older_version_dir(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            sj = os.path.join("my-strat", "strategy.json")
            with open(sj, encoding="utf-8") as f:
                data = json.load(f)
            data["schemaVersion"] = "0.9"
            with open(sj, "w", encoding="utf-8") as f:
                json.dump(data, f)
            result = runner.invoke(cli, ["migrate", "my-strat"])
            assert result.exit_code == 0
            assert "Migration completed" in result.output
            with open(sj, encoding="utf-8") as f:
                updated = json.load(f)
            assert updated["schemaVersion"] == "1.0"

    def test_migrate_qys_already_latest(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            runner.invoke(cli, ["build", "my-strat"])
            result = runner.invoke(cli, ["migrate", "my-strat.qys"])
            assert result.exit_code == 0
            assert "Already latest schema version" in result.output

    def test_migrate_qys_older_version(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "my-strat"])
            runner.invoke(cli, ["build", "my-strat"])
            with zipfile.ZipFile("my-strat.qys", "r") as zf_in:
                entries = {n: zf_in.read(n) for n in zf_in.namelist()}
            sj = json.loads(entries["strategy.json"])
            sj["schemaVersion"] = "0.9"
            entries["strategy.json"] = json.dumps(sj).encode()
            with zipfile.ZipFile("my-strat.qys", "w") as zf_out:
                for name, content in entries.items():
                    zf_out.writestr(name, content)
            result = runner.invoke(cli, ["migrate", "my-strat.qys"])
            assert result.exit_code == 0
            assert "Migration completed" in result.output
            with zipfile.ZipFile("my-strat.qys", "r") as zf:
                updated = json.loads(zf.read("strategy.json"))
            assert updated["schemaVersion"] == "1.0"

    def test_migrate_nonexistent_path(self, tmp_path: object) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["migrate", "nonexistent"])
            assert result.exit_code != 0


class TestBacktest:
    """qys backtest command tests."""

    def test_backtest_stub_exits_zero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["backtest", "some-path"])
        assert result.exit_code == 0

    def test_backtest_stub_shows_message(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["backtest", "some-path"])
        assert "Epic 3" in result.output


class TestImport:
    """qys import command tests."""

    def test_import_qys_calls_analyze_and_confirm(self, tmp_path: object, monkeypatch) -> None:
        runner = CliRunner()
        calls: list[tuple[str, str, object]] = []

        def fake_post_multipart(url: str, *, token: str, field_name: str, filename: str, payload: bytes):
            calls.append(("multipart", url, {"token": token, "field": field_name, "filename": filename, "payload": payload}))
            return {
                "draftImportId": "draft-1",
                "sourceType": "qys_package",
                "entrypointCandidates": [{"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"}],
                "metadataCandidates": {"name": "CLI Imported Strategy", "category": "trend-following", "tags": ["cli"]},
                "parameterCandidates": [],
                "warnings": [],
                "errors": [],
            }

        def fake_post_json(url: str, *, token: str, payload: dict):
            calls.append(("json", url, {"token": token, "payload": payload}))
            return {
                "strategy": {"id": "strategy-123", "name": "CLI Imported Strategy"},
                "next": "/strategies/strategy-123/parameters",
            }

        monkeypatch.setenv("QYQUANT_API_BASE_URL", "https://qyquant.example")
        monkeypatch.setenv("QYQUANT_API_TOKEN", "token-123")
        monkeypatch.setattr("qysp.cli.main._api_post_multipart", fake_post_multipart)
        monkeypatch.setattr("qysp.cli.main._api_post_json", fake_post_json)

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("demo.qys", "wb") as handle:
                handle.write(b"PK\x03\x04demo")

            result = runner.invoke(cli, ["import", "demo.qys"])

        assert result.exit_code == 0
        assert "strategy-123" in result.output
        assert "/strategies/strategy-123/parameters" in result.output
        assert calls[0][0] == "multipart"
        assert calls[0][1] == "https://qyquant.example/api/v1/strategy-imports/analyze"
        assert calls[0][2]["filename"] == "demo.qys"
        assert calls[1][0] == "json"
        assert calls[1][1] == "https://qyquant.example/api/v1/strategy-imports/confirm"
        assert calls[1][2]["payload"]["draftImportId"] == "draft-1"
        assert calls[1][2]["payload"]["selectedEntrypoint"]["callable"] == "Strategy"

    def test_import_directory_uploads_source_zip(self, tmp_path: object, monkeypatch) -> None:
        runner = CliRunner()
        uploads: list[dict] = []

        def fake_post_multipart(url: str, *, token: str, field_name: str, filename: str, payload: bytes):
            uploads.append({"url": url, "token": token, "field": field_name, "filename": filename, "payload": payload})
            return {
                "draftImportId": "draft-dir",
                "sourceType": "source_zip",
                "entrypointCandidates": [{"path": "src/strategy.py", "callable": "Strategy", "interface": "event_v1"}],
                "metadataCandidates": {"name": "Dir Imported Strategy"},
                "parameterCandidates": [],
                "warnings": [],
                "errors": [],
            }

        def fake_post_json(url: str, *, token: str, payload: dict):
            return {
                "strategy": {"id": "strategy-dir", "name": "Dir Imported Strategy"},
                "next": "/strategies/strategy-dir/parameters",
            }

        monkeypatch.setenv("QYQUANT_API_BASE_URL", "https://qyquant.example")
        monkeypatch.setenv("QYQUANT_API_TOKEN", "token-123")
        monkeypatch.setattr("qysp.cli.main._api_post_multipart", fake_post_multipart)
        monkeypatch.setattr("qysp.cli.main._api_post_json", fake_post_json)

        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "dir-strat"])

            result = runner.invoke(cli, ["import", "dir-strat"])

        assert result.exit_code == 0
        assert uploads[0]["filename"] == "dir-strat.zip"
        assert uploads[0]["field"] == "file"
        assert uploads[0]["payload"].startswith(b"PK")


class TestTemplates:
    """Template loader tests."""

    def test_get_template_path_valid(self) -> None:
        mapping = {
            "trend-following": "trend_following",
            "mean-reversion": "mean_reversion",
            "momentum": "momentum",
            "multi-indicator": "multi_indicator",
        }
        for template_name, folder_name in mapping.items():
            template_path = get_template_path(template_name)
            assert template_path.is_dir()
            assert template_path.name == folder_name

    def test_get_template_path_invalid(self) -> None:
        try:
            get_template_path("does-not-exist")
            assert False, "Expected ValueError for invalid template name"
        except ValueError as exc:
            assert "Unknown template" in str(exc)

    def test_load_template_files_all(self) -> None:
        templates = ["trend-following", "mean-reversion", "momentum", "multi-indicator"]
        for template_name in templates:
            files = load_template_files(template_name)
            assert set(files.keys()) == {"strategy.json", "strategy.py", "README.md"}

            strategy_json = files["strategy.json"]
            assert strategy_json["entrypoint"]["interface"] == "event_v1"
            assert strategy_json["ui"]["category"] == template_name
            assert len(strategy_json["parameters"]) >= 1
            assert "on_bar" in files["strategy.py"]
            assert len(files["README.md"]) > 0
