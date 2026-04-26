import ast
import json
import logging
import os

logger = logging.getLogger(__name__)

# --- Code Safety Scanner ---

CRITICAL_IMPORTS = {
    "subprocess": "subprocess",
    "socket": "socket (network access)",
    "requests": "requests (HTTP client)",
    "urllib": "urllib (URL access)",
}

CRITICAL_ATTR_CHAINS = {
    ("os", "system"),
    ("os", "execvp"), ("os", "execvpe"), ("os", "execl"), ("os", "execle"),
    ("os", "execlp"), ("os", "execlpe"), ("os", "execv"), ("os", "execve"),
    ("os", "popen"),
    ("subprocess", "run"), ("subprocess", "call"), ("subprocess", "Popen"),
    ("subprocess", "check_output"), ("subprocess", "check_call"),
    ("shutil", "rmtree"),
    ("requests", "get"), ("requests", "post"), ("requests", "put"),
    ("requests", "delete"), ("requests", "patch"), ("requests", "head"),
    ("urllib", "request"), ("http", "client"),
    ("socket", "socket"),
}

WARNING_IMPORTS = {
    "os": "os (filesystem access)",
    "sys": "sys (system access)",
    "pathlib": "pathlib (filesystem access)",
}


def _get_attr_chain(node):
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return tuple(reversed(parts))


def scan_code_safety(code: str) -> dict:
    if not code or not code.strip():
        return {"passed": True, "issues": []}

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "passed": False,
            "issues": [{
                "type": "syntax_error",
                "severity": "critical",
                "pattern": "syntax_error",
                "message": f"Code has syntax error at line {exc.lineno}: {exc.msg}",
                "line": exc.lineno,
            }],
        }

    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module in CRITICAL_IMPORTS:
                    issues.append({
                        "type": "import",
                        "severity": "critical",
                        "pattern": root_module,
                        "message": f"Blocked import: {alias.name} ({CRITICAL_IMPORTS[root_module]})",
                        "line": node.lineno,
                    })
                elif root_module in WARNING_IMPORTS:
                    issues.append({
                        "type": "import",
                        "severity": "warning",
                        "pattern": root_module,
                        "message": f"Caution: import {alias.name} ({WARNING_IMPORTS[root_module]})",
                        "line": node.lineno,
                    })

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                if root_module in CRITICAL_IMPORTS:
                    issues.append({
                        "type": "import",
                        "severity": "critical",
                        "pattern": root_module,
                        "message": f"Blocked import: from {node.module} ({CRITICAL_IMPORTS[root_module]})",
                        "line": node.lineno,
                    })

        elif isinstance(node, ast.Call):
            chain = _get_attr_chain(node.func)
            if chain and chain in CRITICAL_ATTR_CHAINS:
                issues.append({
                    "type": "call",
                    "severity": "critical",
                    "pattern": ".".join(chain),
                    "message": f"Blocked call: {'.'.join(chain)}",
                    "line": node.lineno,
                })

            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                issues.append({
                    "type": "call",
                    "severity": "critical",
                    "pattern": node.func.id,
                    "message": f"Blocked call: {node.func.id} (arbitrary code execution)",
                    "line": node.lineno,
                })

            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                issues.append({
                    "type": "call",
                    "severity": "critical",
                    "pattern": "__import__",
                    "message": "__import__ (dynamic import)",
                    "line": node.lineno,
                })

    has_critical = any(i["severity"] == "critical" for i in issues)
    return {"passed": not has_critical, "issues": issues}


# --- Metrics Check ---

def check_metrics(display_metrics: dict) -> dict:
    if not display_metrics:
        return {"passed": False, "issues": [{
            "field": "display_metrics",
            "severity": "critical",
            "message": "No display metrics provided",
        }]}

    min_win_rate = float(os.getenv("REVIEW_MIN_WIN_RATE", "0.4"))
    min_returns = float(os.getenv("REVIEW_MIN_RETURNS", "-0.5"))
    max_drawdown = float(os.getenv("REVIEW_MAX_DRAWDOWN", "0.8"))

    issues = []

    win_rate = display_metrics.get("win_rate")
    if win_rate is not None and float(win_rate) < min_win_rate:
        issues.append({
            "field": "win_rate",
            "severity": "critical",
            "message": f"Win rate {float(win_rate):.1%} below minimum {min_win_rate:.0%}",
            "value": float(win_rate),
            "threshold": min_win_rate,
        })

    returns = display_metrics.get("returns")
    if returns is not None and float(returns) < min_returns:
        issues.append({
            "field": "returns",
            "severity": "critical",
            "message": f"Returns {float(returns):.1%} below minimum {min_returns:.0%}",
            "value": float(returns),
            "threshold": min_returns,
        })

    dd = display_metrics.get("max_drawdown")
    if dd is not None and float(dd) > max_drawdown:
        issues.append({
            "field": "max_drawdown",
            "severity": "critical",
            "message": f"Max drawdown {float(dd):.1%} exceeds limit {max_drawdown:.0%}",
            "value": float(dd),
            "threshold": max_drawdown,
        })

    return {"passed": len(issues) == 0, "issues": issues}


# --- Metadata Check ---

def check_metadata(metadata: dict) -> dict:
    issues = []

    title = (metadata.get("title") or "").strip()
    if len(title) < 5:
        issues.append({
            "field": "title",
            "severity": "critical",
            "message": "Title must be at least 5 characters",
            "value": title,
        })

    description = (metadata.get("description") or "").strip()
    if len(description) < 20:
        issues.append({
            "field": "description",
            "severity": "critical",
            "message": "Description must be at least 20 characters",
            "value": description[:50] if description else "",
        })

    tags = metadata.get("tags") or []
    if not isinstance(tags, list) or len(tags) < 1:
        issues.append({
            "field": "tags",
            "severity": "critical",
            "message": "At least 1 tag is required",
        })

    category = (metadata.get("category") or "").strip()
    if not category:
        issues.append({
            "field": "category",
            "severity": "critical",
            "message": "Category is required",
        })

    return {"passed": len(issues) == 0, "issues": issues}


# --- Base Review Orchestrator ---

def run_base_review(*, code: str, display_metrics: dict, metadata: dict) -> dict:
    code_safety = scan_code_safety(code)
    metrics_result = check_metrics(display_metrics)
    metadata_result = check_metadata(metadata)

    all_passed = (
        code_safety["passed"]
        and metrics_result["passed"]
        and metadata_result["passed"]
    )

    parts = []
    if not code_safety["passed"]:
        criticals = [i for i in code_safety["issues"] if i["severity"] == "critical"]
        parts.append(f"Code safety: {len(criticals)} critical issue(s)")
    if not metrics_result["passed"]:
        parts.append(f"Metrics: {len(metrics_result['issues'])} issue(s)")
    if not metadata_result["passed"]:
        parts.append(f"Metadata: {len(metadata_result['issues'])} issue(s)")

    review_notes = "All base checks passed." if all_passed else "Rejected: " + "; ".join(parts)

    return {
        "verdict": "approved" if all_passed else "rejected",
        "code_safety": code_safety,
        "metrics_check": metrics_result,
        "metadata_check": metadata_result,
        "review_notes": review_notes,
    }


# --- AI Enhancement ---

def run_ai_enhancement(*, code: str, metadata: dict, metrics: dict) -> dict | None:
    provider = os.getenv("REVIEW_AI_PROVIDER", "").strip()
    api_key = os.getenv("REVIEW_AI_API_KEY", "").strip()
    if not provider or not api_key:
        return None

    model = os.getenv("REVIEW_AI_MODEL", "gpt-4o-mini").strip()
    base_url = os.getenv("REVIEW_AI_BASE_URL", "").strip() or None

    try:
        return _call_ai_provider(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            code=code,
            metadata=metadata,
            metrics=metrics,
        )
    except Exception as exc:
        logger.error("AI enhancement failed: %s", exc)
        return None


def _call_ai_provider(*, provider, api_key, model, base_url, code, metadata, metrics):
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = f"""Review this trading strategy code for the marketplace.
Check for:
1. Logical errors or impossible conditions
2. Risk management adequacy (stop-loss, position sizing)
3. Potential overfitting signals
4. Code quality and maintainability
5. Any deceptive or misleading patterns

Strategy metadata:
- Title: {metadata.get('title', 'N/A')}
- Description: {metadata.get('description', 'N/A')}
- Category: {metadata.get('category', 'N/A')}
- Metrics: {json.dumps(metrics)}

Strategy code:
{code}

Return JSON only: {{"score": 0-100, "risks": [...], "summary": "...", "recommendation": "approve" or "reject"}}"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    result = json.loads(content)

    return {
        "score": int(result.get("score", 50)),
        "risks": result.get("risks", []),
        "summary": result.get("summary", ""),
        "recommendation": result.get("recommendation", "approve"),
    }
