"""Built-in strategy templates for qys init."""

from __future__ import annotations

import importlib.resources as pkg_resources
import json
from pathlib import Path
from typing import Any

_TEMPLATE_NAME_MAP = {
    "trend-following": "trend_following",
    "mean-reversion": "mean_reversion",
    "momentum": "momentum",
    "multi-indicator": "multi_indicator",
}


def _normalize_template_name(template_name: str) -> str:
    """Normalize CLI template name."""
    return template_name.strip().lower()


def get_template_path(template_name: str) -> Path:
    """Return the on-disk path of a built-in template directory."""
    normalized = _normalize_template_name(template_name)
    folder = _TEMPLATE_NAME_MAP.get(normalized)
    if folder is None:
        available = ", ".join(sorted(_TEMPLATE_NAME_MAP))
        raise ValueError(
            f"Unknown template '{template_name}'. Available templates: {available}"
        )

    template_dir = pkg_resources.files("qysp.templates").joinpath(folder)
    if not template_dir.is_dir():
        raise ValueError(f"Template directory not found: {folder}")
    return Path(str(template_dir))


def load_template_files(template_name: str) -> dict[str, Any]:
    """Load strategy.json / strategy.py / README.md for a template."""
    normalized = _normalize_template_name(template_name)
    folder = _TEMPLATE_NAME_MAP.get(normalized)
    if folder is None:
        available = ", ".join(sorted(_TEMPLATE_NAME_MAP))
        raise ValueError(
            f"Unknown template '{template_name}'. Available templates: {available}"
        )

    template_dir = pkg_resources.files("qysp.templates").joinpath(folder)
    strategy_json = json.loads(
        template_dir.joinpath("strategy.json").read_text(encoding="utf-8")
    )
    strategy_py = template_dir.joinpath("strategy.py").read_text(encoding="utf-8")
    readme = template_dir.joinpath("README.md").read_text(encoding="utf-8")
    return {
        "strategy.json": strategy_json,
        "strategy.py": strategy_py,
        "README.md": readme,
    }


__all__ = ["get_template_path", "load_template_files"]
