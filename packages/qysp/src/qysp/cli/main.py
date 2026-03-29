"""QYS CLI - QYQuant Strategy Protocol command line tool."""

from __future__ import annotations

import io
import json
import os
import re
import sys
import uuid
import zipfile
from pathlib import Path
from typing import Callable
from urllib import error as urllib_error
from urllib import request as urllib_request

import click

from qysp import __version__
from qysp.builder import PackageBuildError, build_package
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

    try:
        out_path = build_package(source_dir, output)
    except PackageBuildError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

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
@click.argument("path", type=click.Path(exists=True))
def import_cmd(path: str) -> None:
    """Import a strategy source or package to the platform strategy library."""
    api_base_url = os.getenv("QYQUANT_API_BASE_URL", "").rstrip("/")
    api_token = os.getenv("QYQUANT_API_TOKEN", "").strip()
    if not api_base_url:
        click.echo("ERROR: QYQUANT_API_BASE_URL is required", err=True)
        sys.exit(2)
    if not api_token:
        click.echo("ERROR: QYQUANT_API_TOKEN is required", err=True)
        sys.exit(2)

    source_path = Path(path)
    filename, payload = _prepare_import_upload(source_path)
    analysis = _api_post_multipart(
        f"{api_base_url}/api/v1/strategy-imports/analyze",
        token=api_token,
        field_name="file",
        filename=filename,
        payload=payload,
    )

    warnings = analysis.get("warnings") or []
    for warning in warnings:
        click.echo(f"WARNING: {warning}", err=True)

    errors = analysis.get("errors") or []
    if errors:
        for item in errors:
            click.echo(f"ERROR: {item}", err=True)
        sys.exit(1)

    candidates = analysis.get("entrypointCandidates") or []
    if not candidates:
        click.echo("ERROR: No supported strategy entrypoint candidates found", err=True)
        sys.exit(1)
    if len(candidates) > 1:
        click.echo("ERROR: Multiple entrypoint candidates detected; use the web import confirmation flow", err=True)
        sys.exit(1)

    result = _api_post_json(
        f"{api_base_url}/api/v1/strategy-imports/confirm",
        token=api_token,
        payload=_build_cli_confirm_payload(analysis, candidates[0]),
    )
    strategy = result.get("strategy") or {}
    click.echo(f"Imported strategy: {strategy.get('id') or ''}".rstrip())
    if result.get("next"):
        click.echo(f"Next: {result['next']}")


def _prepare_import_upload(path: Path) -> tuple[str, bytes]:
    if path.is_dir():
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
                archive.write(file_path, file_path.relative_to(path).as_posix())
        return f"{path.name}.zip", payload.getvalue()

    return path.name, path.read_bytes()


def _build_cli_confirm_payload(analysis: dict, entrypoint_candidate: dict) -> dict:
    metadata = dict(analysis.get("metadataCandidates") or {})
    if metadata.get("symbol") == "N/A":
        metadata.pop("symbol")
    if not metadata.get("name"):
        metadata["name"] = "Imported Strategy"
    return {
        "draftImportId": analysis["draftImportId"],
        "selectedEntrypoint": {
            "path": entrypoint_candidate["path"],
            "callable": entrypoint_candidate["callable"],
            "interface": entrypoint_candidate.get("interface") or "event_v1",
        },
        "metadata": metadata,
        "parameterDefinitions": analysis.get("parameterCandidates") or [],
    }


def _api_post_multipart(url: str, *, token: str, field_name: str, filename: str, payload: bytes) -> dict:
    boundary = f"qysp-{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")
    request = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    return _read_api_response(request)


def _api_post_json(url: str, *, token: str, payload: dict) -> dict:
    request = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    return _read_api_response(request)


def _read_api_response(request: urllib_request.Request) -> dict:
    try:
        with urllib_request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            click.echo(f"ERROR: Request failed with status {exc.code}", err=True)
            sys.exit(1)
        _raise_api_error(payload)
        raise AssertionError("unreachable")
    except urllib_error.URLError as exc:
        click.echo(f"ERROR: Unable to reach API: {exc.reason}", err=True)
        sys.exit(1)

    if "error" in payload:
        _raise_api_error(payload)
    return payload.get("data") or {}


def _raise_api_error(payload: dict) -> None:
    error_payload = payload.get("error") or {}
    message = error_payload.get("message") or "Request failed"
    details = error_payload.get("details")
    click.echo(f"ERROR: {message}", err=True)
    if details:
        click.echo(json.dumps(details, ensure_ascii=False), err=True)
    sys.exit(1)


if __name__ == "__main__":
    cli()
