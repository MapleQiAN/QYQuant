"""Extract and format qysp API documentation for LLM prompt injection.

Reads source files from the qysp package and formats them into a structured
reference string suitable for including in strategy generation prompts.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from textwrap import dedent


_REPO_ROOT = Path(__file__).resolve().parents[3]
_QYSP_SRC = _REPO_ROOT / "packages" / "qysp" / "src" / "qysp"
_DOCS_DIR = _REPO_ROOT / "docs" / "strategy-format"

_SOURCE_FILES = [
    _QYSP_SRC / "indicators.py",
    _QYSP_SRC / "context.py",
    _QYSP_SRC / "parameters.py",
]

_DOC_FILES = [
    _DOCS_DIR / "README.md",
]

_MAX_TOTAL_CHARS = 16000


def build_api_reference() -> str:
    """Build a complete API reference string for prompt injection."""
    parts: list[str] = []

    for path in _SOURCE_FILES:
        content = _read_file(path)
        if not content:
            continue
        section = _extract_public_api(path.name, content)
        if section:
            parts.append(section)

    for path in _DOC_FILES:
        content = _read_file(path)
        if not content:
            continue
        parts.append(_extract_doc_section(path.name, content))

    combined = "\n\n".join(parts)
    if len(combined) > _MAX_TOTAL_CHARS:
        combined = combined[:_MAX_TOTAL_CHARS]
    return combined


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _extract_public_api(filename: str, source: str) -> str:
    """Extract function signatures and docstrings from a Python source file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return f"[{filename}]\n(source unavailable)\n"

    entries: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue

        sig = _render_signature(node)
        doc = ast.get_docstring(node)
        if doc:
            doc = dedent(doc).strip()
            doc = "\n".join(f"  {line}" for line in doc.split("\n"))
            entries.append(f"{sig}\n{doc}")
        else:
            entries.append(sig)

    if not entries:
        return ""
    header = f"[{filename} — available API]"
    return header + "\n" + "\n\n".join(entries) + "\n"


def _render_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render a function signature from an AST node."""
    args: list[str] = []
    for arg in node.args.args:
        name = arg.arg
        annotation = _render_annotation(arg.annotation)
        if annotation:
            args.append(f"{name}: {annotation}")
        else:
            args.append(name)

    defaults_offset = len(node.args.args) - len(node.args.defaults)
    rendered_parts: list[str] = []
    for i, arg_str in enumerate(args):
        default_index = i - defaults_offset
        if default_index >= 0 and default_index < len(node.args.defaults):
            default_val = _render_literal(node.args.defaults[default_index])
            rendered_parts.append(f"{arg_str}={default_val}")
        else:
            rendered_parts.append(arg_str)

    returns = _render_annotation(node.returns)
    return_sig = f" -> {returns}" if returns else ""
    return f"def {node.name}({', '.join(rendered_parts)}){return_sig}"


def _render_annotation(node: ast.expr | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_render_annotation(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        value = _render_annotation(node.value)
        slice_val = _render_annotation(node.slice) if isinstance(node.slice, ast.expr) else ""
        return f"{value}[{slice_val}]"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return f"{_render_annotation(node.left)} | {_render_annotation(node.right)}"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Tuple):
        inner = ", ".join(_render_annotation(elt) for elt in node.elts)
        return f"({inner})"
    return ""


def _render_literal(node: ast.expr) -> str:
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return f"-{_render_literal(node.operand)}"
    return "..."


def _extract_doc_section(filename: str, content: str) -> str:
    """Extract key sections from markdown docs."""
    lines = content.split("\n")
    in_code_block = False
    filtered: list[str] = []
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            filtered.append(line)
            continue
        filtered.append(line)
    text = "\n".join(filtered)
    return f"[{filename}]\n{text}\n"


# Cache the result after first build
_cached_reference: str | None = None


def get_api_reference() -> str:
    """Get the API reference, building and caching on first call."""
    global _cached_reference
    if _cached_reference is None:
        _cached_reference = build_api_reference()
    return _cached_reference
