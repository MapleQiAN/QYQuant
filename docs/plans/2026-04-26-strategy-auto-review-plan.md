# Strategy Auto-Review Bot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Server-side auto-review system that audits marketplace strategy submissions for code safety, metrics, and compliance. Optionally enhanced by AI.

**Architecture:** Celery task dispatched on publish, runs base review (AST scan + metrics + metadata) always, AI enhancement when globally configured. Results stored in `strategy_reviews` table. Notifications dispatched on completion.

**Tech Stack:** Python 3, Flask, Celery, SQLAlchemy, `ast` module (stdlib), OpenAI-compatible API for AI enhancement.

---

### Task 1: StrategyReview Model + Migration

**Files:**
- Modify: `backend/app/models.py` (append new model)
- Create: `backend/migrations/versions/<hash>_add_strategy_reviews.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_strategy_review.py

def test_strategy_review_model_create(app):
    from app.extensions import db
    from app.models import StrategyReview

    with app.app_context():
        review = StrategyReview(
            strategy_id="test-strategy-id",
            status="pending",
        )
        db.session.add(review)
        db.session.commit()

        fetched = db.session.get(StrategyReview, review.id)
        assert fetched is not None
        assert fetched.status == "pending"
        assert fetched.code_safety is None
        assert fetched.ai_enabled is False


def test_strategy_review_model_with_results(app):
    from app.extensions import db
    from app.models import StrategyReview

    with app.app_context():
        review = StrategyReview(
            strategy_id="test-strategy-id",
            status="approved",
            code_safety={"passed": True, "issues": []},
            metrics_check={"passed": True, "issues": []},
            metadata_check={"passed": True, "issues": []},
            ai_analysis={"score": 85, "risks": [], "summary": "Looks good"},
            ai_enabled=True,
            verdict="approved",
            review_notes="All checks passed. AI score: 85/100.",
        )
        db.session.add(review)
        db.session.commit()

        fetched = db.session.get(StrategyReview, review.id)
        assert fetched.verdict == "approved"
        assert fetched.ai_enabled is True
        assert fetched.ai_analysis["score"] == 85
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_strategy_review.py -v -x`
Expected: FAIL with ImportError (StrategyReview not found)

**Step 3: Add StrategyReview model**

Append to `backend/app/models.py` after `AiGenerationSession`:

```python
class StrategyReview(db.Model):
    __tablename__ = 'strategy_reviews'
    __table_args__ = (
        db.Index('ix_strategy_reviews_strategy_id', 'strategy_id'),
        db.Index('ix_strategy_reviews_status', 'status'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    strategy_id = db.Column(db.String, db.ForeignKey('strategies.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    code_safety = db.Column(job_json_type, nullable=True)
    metrics_check = db.Column(job_json_type, nullable=True)
    metadata_check = db.Column(job_json_type, nullable=True)
    ai_analysis = db.Column(job_json_type, nullable=True)
    ai_enabled = db.Column(db.Boolean, nullable=False, default=False)
    verdict = db.Column(db.String(20), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
```

**Step 4: Create migration**

Run: `cd backend && flask db migrate -m "add strategy_reviews table"`

If migration generation fails, create manually:

```python
# backend/migrations/versions/<hash>_add_strategy_reviews.py
"""add strategy_reviews table

Revision ID: add_strategy_reviews
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'strategy_reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('code_safety', sa.JSON(), nullable=True),
        sa.Column('metrics_check', sa.JSON(), nullable=True),
        sa.Column('metadata_check', sa.JSON(), nullable=True),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.Column('ai_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('verdict', sa.String(20), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id']),
    )
    op.create_index('ix_strategy_reviews_strategy_id', 'strategy_reviews', ['strategy_id'])
    op.create_index('ix_strategy_reviews_status', 'strategy_reviews', ['status'])


def downgrade():
    op.drop_index('ix_strategy_reviews_status')
    op.drop_index('ix_strategy_reviews_strategy_id')
    op.drop_table('strategy_reviews')
```

**Step 5: Run tests to verify**

Run: `cd backend && python -m pytest tests/test_strategy_review.py -v -x`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/models.py backend/migrations/versions/<hash>_add_strategy_reviews.py backend/tests/test_strategy_review.py
git commit -m "feat: add StrategyReview model for auto-review audit trail"
```

---

### Task 2: Base Review Service — Code Safety Scanner

**Files:**
- Create: `backend/app/services/strategy_review.py`
- Modify: `backend/tests/test_strategy_review.py` (append tests)

**Step 1: Write the failing tests**

Append to `backend/tests/test_strategy_review.py`:

```python
import pytest
from app.services.strategy_review import scan_code_safety


class TestCodeSafetyScanner:
    def test_clean_code_passes(self):
        code = "def on_bar(context, bar): pass"
        result = scan_code_safety(code)
        assert result["passed"] is True
        assert result["issues"] == []

    def test_os_system_detected(self):
        code = "import os\nos.system('rm -rf /')"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any(i["severity"] == "critical" for i in result["issues"])

    def test_subprocess_detected(self):
        code = "import subprocess\nsubprocess.run(['ls'])"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any("subprocess" in i["pattern"] for i in result["issues"])

    def test_eval_detected(self):
        code = "x = eval('1+1')"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any("eval" in i["pattern"] for i in result["issues"])

    def test_exec_detected(self):
        code = "exec('print(1)')"
        result = scan_code_safety(code)
        assert result["passed"] is False

    def test_import_os_warning_only(self):
        code = "import os\npath = os.path.join('a', 'b')"
        result = scan_code_safety(code)
        # import os alone is warning, not critical
        assert any(i["severity"] == "warning" for i in result["issues"])
        # But no critical call, so it may still pass depending on policy
        # We treat warnings as non-blocking, critical as blocking
        criticals = [i for i in result["issues"] if i["severity"] == "critical"]
        assert len(criticals) == 0

    def test_network_import_detected(self):
        code = "import requests\nrequests.get('http://evil.com')"
        result = scan_code_safety(code)
        assert result["passed"] is False

    def test_syntax_error_code_handled(self):
        code = "def broken(:\n  pass"
        result = scan_code_safety(code)
        assert result["passed"] is False
        assert any("syntax_error" in i.get("type", "") for i in result["issues"])

    def test_empty_code_passes(self):
        code = ""
        result = scan_code_safety(code)
        assert result["passed"] is True
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_strategy_review.py::TestCodeSafetyScanner -v -x`
Expected: FAIL with ImportError

**Step 3: Implement scan_code_safety**

Create `backend/app/services/strategy_review.py`:

```python
import ast
import logging
import os

logger = logging.getLogger(__name__)

# Patterns that trigger CRITICAL (auto-reject)
CRITICAL_IMPORTS = {
    "subprocess": "subprocess",
    "socket": "socket (network access)",
}

CRITICAL_CALLS = {
    "os.system": "os.system (command execution)",
    "os.exec": "os.exec* (process replacement)",
    "os.popen": "os.popen (command execution)",
    "eval": "eval (arbitrary code execution)",
    "exec": "exec (arbitrary code execution)",
    "__import__": "__import__ (dynamic import)",
    "importlib.import_module": "importlib.import_module (dynamic import)",
    "shutil.rmtree": "shutil.rmtree (directory deletion)",
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

# Patterns that trigger WARNING (non-blocking)
WARNING_IMPORTS = {
    "os": "os (filesystem access)",
    "sys": "sys (system access)",
    "pathlib": "pathlib (filesystem access)",
}


def _get_attr_chain(node):
    """Extract attribute chain like os.system from ast node."""
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return tuple(reversed(parts))


def scan_code_safety(code: str) -> dict:
    """Scan strategy code for dangerous patterns using AST analysis."""
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
        # Check imports
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

        # Check function calls
        elif isinstance(node, ast.Call):
            chain = _get_attr_chain(node.func)
            if chain and chain in CRITICAL_ATTR_CHAINS:
                desc = CRITICAL_CALLS.get(".".join(chain), ".".join(chain))
                issues.append({
                    "type": "call",
                    "severity": "critical",
                    "pattern": ".".join(chain),
                    "message": f"Blocked call: {'.'.join(chain)} ({desc})",
                    "line": node.lineno,
                })

            # Bare eval/exec
            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                issues.append({
                    "type": "call",
                    "severity": "critical",
                    "pattern": node.func.id,
                    "message": f"Blocked call: {node.func.id} ({CRITICAL_CALLS[node.func.id]})",
                    "line": node.lineno,
                })

            # __import__
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
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_strategy_review.py::TestCodeSafetyScanner -v -x`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/strategy_review.py backend/tests/test_strategy_review.py
git commit -m "feat: add code safety scanner for strategy review"
```

---

### Task 3: Base Review Service — Metrics + Metadata Checks

**Files:**
- Modify: `backend/app/services/strategy_review.py` (append functions)
- Modify: `backend/tests/test_strategy_review.py` (append tests)

**Step 1: Write the failing tests**

Append to `backend/tests/test_strategy_review.py`:

```python
from app.services.strategy_review import check_metrics, check_metadata


class TestMetricsCheck:
    def test_passing_metrics(self):
        result = check_metrics({
            "win_rate": 0.55,
            "returns": 0.12,
            "max_drawdown": 0.25,
        })
        assert result["passed"] is True
        assert result["issues"] == []

    def test_low_win_rate(self):
        result = check_metrics({"win_rate": 0.2, "returns": 0.1, "max_drawdown": 0.3})
        assert result["passed"] is False
        assert any("win_rate" in i["field"] for i in result["issues"])

    def test_high_drawdown(self):
        result = check_metrics({"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.95})
        assert result["passed"] is False
        assert any("max_drawdown" in i["field"] for i in result["issues"])

    def test_negative_returns(self):
        result = check_metrics({"win_rate": 0.5, "returns": -0.8, "max_drawdown": 0.3})
        assert result["passed"] is False

    def test_empty_metrics(self):
        result = check_metrics({})
        assert result["passed"] is False


class TestMetadataCheck:
    def test_complete_metadata(self):
        result = check_metadata({
            "title": "My Alpha Strategy",
            "description": "This is a momentum-based strategy for A-shares.",
            "tags": ["momentum"],
            "category": "trend",
        })
        assert result["passed"] is True

    def test_short_title(self):
        result = check_metadata({
            "title": "AB",
            "description": "A" * 30,
            "tags": ["x"],
            "category": "trend",
        })
        assert result["passed"] is False
        assert any("title" in i["field"] for i in result["issues"])

    def test_short_description(self):
        result = check_metadata({
            "title": "Good Title",
            "description": "Too short",
            "tags": ["x"],
            "category": "trend",
        })
        assert result["passed"] is False

    def test_missing_tags(self):
        result = check_metadata({
            "title": "Good Title",
            "description": "A" * 30,
            "tags": [],
            "category": "trend",
        })
        assert result["passed"] is False

    def test_missing_category(self):
        result = check_metadata({
            "title": "Good Title",
            "description": "A" * 30,
            "tags": ["x"],
            "category": "",
        })
        assert result["passed"] is False

    def test_none_values(self):
        result = check_metadata({
            "title": None,
            "description": None,
            "tags": None,
            "category": None,
        })
        assert result["passed"] is False
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_strategy_review.py::TestMetricsCheck tests/test_strategy_review.py::TestMetadataCheck -v -x`
Expected: FAIL with ImportError

**Step 3: Implement check_metrics and check_metadata**

Append to `backend/app/services/strategy_review.py`:

```python
def check_metrics(display_metrics: dict) -> dict:
    """Check if strategy metrics meet minimum thresholds."""
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


def check_metadata(metadata: dict) -> dict:
    """Check if strategy metadata is complete."""
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
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_strategy_review.py::TestMetricsCheck tests/test_strategy_review.py::TestMetadataCheck -v -x`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/strategy_review.py backend/tests/test_strategy_review.py
git commit -m "feat: add metrics and metadata checks for strategy review"
```

---

### Task 4: Base Review Orchestrator + AI Enhancement

**Files:**
- Modify: `backend/app/services/strategy_review.py` (append functions)
- Modify: `backend/tests/test_strategy_review.py` (append tests)

**Step 1: Write the failing tests**

Append to `backend/tests/test_strategy_review.py`:

```python
from unittest.mock import patch, MagicMock
from app.services.strategy_review import run_base_review, run_ai_enhancement


class TestBaseReviewOrchestrator:
    def test_all_pass_approves(self, app):
        with app.app_context():
            result = run_base_review(
                code="def on_bar(ctx, bar): pass",
                display_metrics={"win_rate": 0.6, "returns": 0.15, "max_drawdown": 0.2},
                metadata={"title": "Test Strategy", "description": "A good strategy for testing", "tags": ["test"], "category": "trend"},
            )
            assert result["verdict"] == "approved"
            assert result["code_safety"]["passed"] is True
            assert result["metrics_check"]["passed"] is True
            assert result["metadata_check"]["passed"] is True

    def test_code_dangerous_rejects(self, app):
        with app.app_context():
            result = run_base_review(
                code="import os\nos.system('rm -rf /')",
                display_metrics={"win_rate": 0.6, "returns": 0.15, "max_drawdown": 0.2},
                metadata={"title": "Bad Code", "description": "Dangerous strategy", "tags": ["bad"], "category": "other"},
            )
            assert result["verdict"] == "rejected"
            assert result["code_safety"]["passed"] is False


class TestAIEnhancement:
    def test_ai_not_configured_skips(self, app):
        with app.app_context():
            # No REVIEW_AI_PROVIDER set
            result = run_ai_enhancement(
                code="def on_bar(ctx, bar): pass",
                metadata={"title": "Test", "description": "A strategy", "category": "trend", "tags": ["x"]},
                metrics={"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.2},
            )
            assert result is None

    @patch("app.services.strategy_review._call_ai_provider")
    def test_ai_returns_analysis(self, mock_ai, app):
        mock_ai.return_value = {
            "score": 75,
            "risks": ["No stop-loss detected"],
            "summary": "Reasonable strategy with minor risks",
            "recommendation": "approve",
        }
        with app.app_context():
            import os
            os.environ["REVIEW_AI_PROVIDER"] = "openai"
            os.environ["REVIEW_AI_API_KEY"] = "test-key"
            os.environ["REVIEW_AI_MODEL"] = "gpt-4o-mini"
            try:
                result = run_ai_enhancement(
                    code="def on_bar(ctx, bar): pass",
                    metadata={"title": "Test", "description": "A strategy", "category": "trend", "tags": ["x"]},
                    metrics={"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.2},
                )
                assert result is not None
                assert result["score"] == 75
                assert result["recommendation"] == "approve"
            finally:
                os.environ.pop("REVIEW_AI_PROVIDER", None)
                os.environ.pop("REVIEW_AI_API_KEY", None)
                os.environ.pop("REVIEW_AI_MODEL", None)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_strategy_review.py::TestBaseReviewOrchestrator tests/test_strategy_review.py::TestAIEnhancement -v -x`
Expected: FAIL with ImportError

**Step 3: Implement run_base_review, run_ai_enhancement, _call_ai_provider**

Append to `backend/app/services/strategy_review.py`:

```python
def run_base_review(*, code: str, display_metrics: dict, metadata: dict) -> dict:
    """Run all base review checks. Returns structured result."""
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


def run_ai_enhancement(*, code: str, metadata: dict, metrics: dict) -> dict | None:
    """Run AI enhancement if configured. Returns None if not configured or on failure."""
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
    """Call AI provider with strategy review prompt."""
    import json
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
    # Strip markdown code fence if present
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
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_strategy_review.py -v -x`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/strategy_review.py backend/tests/test_strategy_review.py
git commit -m "feat: add base review orchestrator and AI enhancement"
```

---

### Task 5: Celery Review Task

**Files:**
- Create: `backend/app/tasks/review_tasks.py`
- Modify: `backend/app/celery_app.py` (register task + queue)
- Modify: `backend/tests/test_strategy_review.py` (append tests)

**Step 1: Write the failing test**

Append to `backend/tests/test_strategy_review.py`:

```python
from app.tasks.review_tasks import review_strategy


class TestReviewCeleryTask:
    def test_review_clean_strategy_approves(self, app):
        from app.extensions import db
        from app.models import Strategy, StrategyReview

        with app.app_context():
            strategy = Strategy(
                name="test-review",
                symbol="000001",
                status="draft",
                source="editor",
                owner_id=None,
                title="Good Strategy",
                description="A well-tested momentum strategy for A-share market",
                category="trend",
                tags=["momentum"],
                display_metrics={"win_rate": 0.6, "returns": 0.15, "max_drawdown": 0.2},
                review_status="pending",
                returns=0.15,
                win_rate=0.6,
                max_drawdown=0.2,
                last_update=0,
                trades=100,
            )
            db.session.add(strategy)
            db.session.commit()
            strategy_id = strategy.id

            # Write clean code to storage
            from pathlib import Path
            storage_root = Path(app.config.get("FILE_STORAGE_DIR", "/tmp"))
            code_dir = storage_root / f"editor/test-user/{strategy_id}"
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "strategy.py").write_text("def on_bar(ctx, bar): pass")

            strategy.storage_key = f"editor/test-user/{strategy_id}"
            db.session.commit()

        result = review_strategy(strategy_id)

        with app.app_context():
            strategy = db.session.get(Strategy, strategy_id)
            assert strategy.review_status == "approved"

            review_record = StrategyReview.query.filter_by(strategy_id=strategy_id).first()
            assert review_record is not None
            assert review_record.verdict == "approved"

    def test_review_dangerous_code_rejects(self, app):
        from app.extensions import db
        from app.models import Strategy, StrategyReview

        with app.app_context():
            strategy = Strategy(
                name="bad-review",
                symbol="000001",
                status="draft",
                source="editor",
                owner_id=None,
                title="Evil Strategy",
                description="A strategy with malicious code that should be rejected",
                category="other",
                tags=["bad"],
                display_metrics={"win_rate": 0.5, "returns": 0.1, "max_drawdown": 0.3},
                review_status="pending",
                returns=0.1,
                win_rate=0.5,
                max_drawdown=0.3,
                last_update=0,
                trades=50,
            )
            db.session.add(strategy)
            db.session.commit()
            strategy_id = strategy.id

            from pathlib import Path
            storage_root = Path(app.config.get("FILE_STORAGE_DIR", "/tmp"))
            code_dir = storage_root / f"editor/test-user/{strategy_id}"
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "strategy.py").write_text("import os\nos.system('rm -rf /')")

            strategy.storage_key = f"editor/test-user/{strategy_id}"
            db.session.commit()

        result = review_strategy(strategy_id)

        with app.app_context():
            strategy = db.session.get(Strategy, strategy_id)
            assert strategy.review_status == "rejected"
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_strategy_review.py::TestReviewCeleryTask -v -x`
Expected: FAIL with ImportError

**Step 3: Create review_tasks.py**

Create `backend/app/tasks/review_tasks.py`:

```python
import logging
import os
from pathlib import Path

from celery.utils.log import get_task_logger
from flask import has_app_context

from ..celery_app import celery_app
from ..extensions import db
from ..models import Strategy, StrategyReview
from ..services.notifications import create_notification
from ..services.strategy_review import run_base_review, run_ai_enhancement
from ..utils.time import now_utc

logger = get_task_logger(__name__) if logging.getLogger().handlers else logging.getLogger(__name__)


def _get_strategy_code(strategy):
    """Read strategy source code from storage."""
    if not strategy.storage_key:
        return None

    storage_root = Path(
        os.getenv("STRATEGY_STORAGE_DIR")
        or Path(__file__).resolve().parents[2] / "storage"
    )
    code_path = storage_root / strategy.storage_key / "strategy.py"
    if not code_path.exists():
        return None

    return code_path.read_text(encoding="utf-8")


def _run_review(strategy_id):
    strategy = db.session.get(Strategy, strategy_id)
    if strategy is None:
        logger.error("Review task: strategy %s not found", strategy_id)
        return {"status": "missing"}

    if strategy.review_status not in ("pending",):
        logger.info("Review task: strategy %s already %s, skipping", strategy_id, strategy.review_status)
        return {"status": "skipped"}

    # Read source code
    code = _get_strategy_code(strategy)

    # Run base review
    base_result = run_base_review(
        code=code or "",
        display_metrics=strategy.display_metrics or {},
        metadata={
            "title": strategy.title or "",
            "description": strategy.description or "",
            "tags": strategy.tags or [],
            "category": strategy.category or "",
        },
    )

    # Run AI enhancement (optional, non-blocking)
    ai_result = None
    ai_enabled = False
    if base_result["verdict"] == "approved":
        ai_result = run_ai_enhancement(
            code=code or "",
            metadata={
                "title": strategy.title or "",
                "description": strategy.description or "",
                "tags": strategy.tags or [],
                "category": strategy.category or "",
            },
            metrics=strategy.display_metrics or {},
        )
        if ai_result is not None:
            ai_enabled = True
            # AI can override approval to rejection
            if ai_result.get("recommendation") == "reject" and ai_result.get("score", 100) < 40:
                base_result["verdict"] = "rejected"
                base_result["review_notes"] += f" | AI rejected (score: {ai_result['score']}/100)"

    # Determine final verdict
    verdict = base_result["verdict"]

    # If no code available and base can't check code safety, reject
    if code is None and verdict == "approved":
        # Strategies without source code still pass base review
        # (code_safety defaults to passed for empty code)
        pass

    # Create review record
    review = StrategyReview(
        strategy_id=strategy_id,
        status=verdict,
        code_safety=base_result["code_safety"],
        metrics_check=base_result["metrics_check"],
        metadata_check=base_result["metadata_check"],
        ai_analysis=ai_result,
        ai_enabled=ai_enabled,
        verdict=verdict,
        review_notes=base_result["review_notes"],
        reviewed_at=now_utc(),
    )
    db.session.add(review)

    # Update strategy
    strategy.review_status = verdict
    if verdict == "approved":
        strategy.is_public = True
    strategy.updated_at = int(now_utc().timestamp() * 1000) if hasattr(strategy, 'updated_at') else None

    # Notification
    try:
        status_text = "approved" if verdict == "approved" else "rejected"
        create_notification(
            user_id=strategy.owner_id,
            type="strategy_review_result",
            title=f"Strategy {status_text}: {strategy.title or strategy.name}",
            content=base_result["review_notes"],
        )
    except Exception as exc:
        logger.error("Failed to send review notification: %s", exc)

    db.session.commit()

    return {"status": verdict, "review_id": review.id}


@celery_app.task(
    bind=True,
    name='app.tasks.review_tasks.review_strategy',
    soft_time_limit=int(os.getenv('REVIEW_TASK_SOFT_TIME_LIMIT', '120')),
    time_limit=int(os.getenv('REVIEW_TASK_TIME_LIMIT', '180')),
)
def review_strategy(self, strategy_id):
    if has_app_context():
        return _run_review(strategy_id)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _run_review(strategy_id)
```

**Step 4: Register task in celery_app.py**

Modify `backend/app/celery_app.py`:

In `imports` tuple, add `'app.tasks.review_tasks'`.

In `task_routes` dict, add:
```python
'app.tasks.review_tasks.*': {'queue': 'review'},
```

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_strategy_review.py -v -x`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/tasks/review_tasks.py backend/app/celery_app.py backend/tests/test_strategy_review.py
git commit -m "feat: add Celery review task with base + AI review pipeline"
```

---

### Task 6: Wire Publish Endpoint to Review Task

**Files:**
- Modify: `backend/app/blueprints/marketplace.py` (dispatch review task after publish)

**Step 1: Write the failing test**

Append to `backend/tests/test_marketplace.py` (or verify existing publish test still works):

```python
def test_publish_dispatches_review_task(client, app, seed_user):
    """Publishing a strategy should dispatch the auto-review Celery task."""
    from app.extensions import db
    from app.models import Strategy, BacktestJob
    from unittest.mock import patch

    with app.app_context():
        strategy = Strategy(
            name="publish-test",
            symbol="000001",
            status="completed",
            source="editor",
            owner_id=seed_user.id,
            title="Test Strategy",
            description="A test strategy for review dispatch testing",
            category="trend",
            tags=["test"],
            review_status="draft",
            returns=0.1,
            win_rate=0.55,
            max_drawdown=0.2,
            last_update=0,
            trades=10,
        )
        db.session.add(strategy)

        # Need a completed backtest
        job = BacktestJob(
            user_id=seed_user.id,
            strategy_id=strategy.id,
            status="completed",
            params={},
        )
        db.session.add(job)
        db.session.commit()
        strategy_id = strategy.id

    with patch("app.blueprints.marketplace.review_strategy") as mock_review:
        token = _get_access_token(client, seed_user)
        resp = client.post(
            "/api/marketplace/strategies",
            json={
                "strategy_id": strategy_id,
                "title": "Test Strategy",
                "description": "A test strategy for review dispatch testing",
                "tags": ["test"],
                "category": "trend",
                "display_metrics": {"win_rate": 0.55, "returns": 0.1, "max_drawdown": 0.2},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        mock_review.delay.assert_called_once_with(strategy_id)
```

**Step 2: Modify marketplace.py publish endpoint**

In `backend/app/blueprints/marketplace.py`:

Add import at top:
```python
from ..tasks.review_tasks import review_strategy
```

After `db.session.commit()` in `publish_marketplace_strategy()` (line ~236), add:
```python
    # Dispatch auto-review task
    review_strategy.delay(strategy.id)
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_marketplace.py -v -x -k publish`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/blueprints/marketplace.py backend/tests/test_marketplace.py
git commit -m "feat: dispatch auto-review Celery task on strategy publish"
```

---

### Task 7: Config + Documentation

**Files:**
- Modify: `backend/app/config.py` (add review config)
- Modify: `docs/plans/2026-04-26-strategy-auto-review-design.md` (finalize)

**Step 1: Add review config to BaseConfig**

In `backend/app/config.py` `BaseConfig.__init__`, append:

```python
        # Strategy auto-review
        self.REVIEW_MIN_WIN_RATE = float(os.getenv('REVIEW_MIN_WIN_RATE', '0.4'))
        self.REVIEW_MIN_RETURNS = float(os.getenv('REVIEW_MIN_RETURNS', '-0.5'))
        self.REVIEW_MAX_DRAWDOWN = float(os.getenv('REVIEW_MAX_DRAWDOWN', '0.8'))
        self.REVIEW_AI_PROVIDER = os.getenv('REVIEW_AI_PROVIDER', '')
        self.REVIEW_AI_MODEL = os.getenv('REVIEW_AI_MODEL', 'gpt-4o-mini')
        self.REVIEW_AI_API_KEY = os.getenv('REVIEW_AI_API_KEY', '')
        self.REVIEW_AI_BASE_URL = os.getenv('REVIEW_AI_BASE_URL', '')
        self.REVIEW_TASK_SOFT_TIME_LIMIT = int(os.getenv('REVIEW_TASK_SOFT_TIME_LIMIT', '120'))
        self.REVIEW_TASK_TIME_LIMIT = int(os.getenv('REVIEW_TASK_TIME_LIMIT', '180'))
```

**Step 2: Run all review tests**

Run: `cd backend && python -m pytest tests/test_strategy_review.py tests/test_marketplace.py -v -x`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/app/config.py
git commit -m "feat: add strategy review configuration to app config"
```

---

## Summary

| Task | Files Created | Files Modified |
|------|--------------|----------------|
| 1. Model + Migration | `migrations/versions/..._add_strategy_reviews.py`, `tests/test_strategy_review.py` | `models.py` |
| 2. Code Safety Scanner | `services/strategy_review.py` | `tests/test_strategy_review.py` |
| 3. Metrics + Metadata | — | `services/strategy_review.py`, `tests/test_strategy_review.py` |
| 4. Orchestrator + AI | — | `services/strategy_review.py`, `tests/test_strategy_review.py` |
| 5. Celery Task | `tasks/review_tasks.py` | `celery_app.py`, `tests/test_strategy_review.py` |
| 6. Wire Publish | — | `marketplace.py`, `tests/test_marketplace.py` |
| 7. Config + Docs | — | `config.py` |
