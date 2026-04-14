from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _candidate_chromium_paths() -> list[Path]:
    candidates: list[Path] = []

    explicit = os.getenv("BACKTEST_REPORT_CHROMIUM_PATH")
    if explicit:
        candidates.append(Path(explicit))

    local_app_data = Path(os.getenv("LOCALAPPDATA", ""))
    if local_app_data:
        playwright_root = local_app_data / "ms-playwright"
        if playwright_root.exists():
            for directory in sorted(playwright_root.glob("chromium-*"), reverse=True):
                candidates.append(directory / "chrome-win64" / "chrome.exe")

    program_files = Path(os.getenv("ProgramFiles", r"C:\Program Files"))
    program_files_x86 = Path(os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    candidates.extend(
        [
            program_files / "Google" / "Chrome" / "Application" / "chrome.exe",
            program_files_x86 / "Google" / "Chrome" / "Application" / "chrome.exe",
            program_files / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            program_files_x86 / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
    )

    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        normalized = str(candidate).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(candidate)
    return deduped


def find_chromium_executable() -> Path:
    for candidate in _candidate_chromium_paths():
        if candidate.exists():
            return candidate
    raise RuntimeError("chromium_executable_not_found")


def render_backtest_report_pdf(job_id: str, html: str, filename: str | None = None) -> Path:
    chromium_path = find_chromium_executable()
    workdir = Path(tempfile.mkdtemp(prefix=f"backtest-report-{job_id}-"))
    html_path = workdir / "report.html"
    pdf_name = filename or f"backtest-report-{job_id}.pdf"
    pdf_path = workdir / pdf_name

    html_path.write_text(html, encoding="utf-8")

    command = [
        str(chromium_path),
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0 or not pdf_path.exists():
        shutil.rmtree(workdir, ignore_errors=True)
        raise RuntimeError("pdf_export_failed")

    return pdf_path
