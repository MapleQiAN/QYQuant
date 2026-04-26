# Strategy Auto-Review Bot Design

## Overview

Auto-review system for marketplace strategy publishing. 100% server-side, zero client dependencies. Uses existing Celery + Redis infrastructure for async processing.

## Architecture

```
User publishes strategy
    ↓
POST /marketplace/strategies/<id>/publish
    ↓ review_status = "pending"
    ↓ dispatch Celery task (async, non-blocking)
    ↓ immediate response: { review_status: "pending" }

Celery Worker (separate process)
    ↓
review_strategy_task(strategy_id)
    ↓
[Phase 1: Base Review] (always runs, < 1s)
    - Code safety scan (AST analysis)
    - Metrics threshold check
    - Metadata completeness check
    ↓ all pass? → Phase 2
    ↓ any CRITICAL? → reject immediately

[Phase 2: AI Enhancement] (optional, when configured)
    - Strategy code logic analysis
    - Risk assessment
    - Generate review notes
    ↓ failure → fallback to base result only

[Result]
    ↓ approved → strategy.is_public = true
    ↓ rejected → notification with reasons
```

## New Files

```
backend/app/tasks/review_tasks.py      # Celery task definition
backend/app/services/strategy_review.py # Review logic (base + AI)
```

## New DB Model: StrategyReview

```python
class StrategyReview(db.Model):
    __tablename__ = 'strategy_reviews'

    id           = Column(String, primary_key=True, default=gen_id)
    strategy_id  = Column(String, ForeignKey('strategies.id'), nullable=False)
    status       = Column(String(20), nullable=False, default='pending')
    # 'pending' | 'approved' | 'rejected'

    # Base review results
    code_safety   = Column(JSON, nullable=True)      # {passed, issues[]}
    metrics_check = Column(JSON, nullable=True)       # {passed, issues[]}
    metadata_check = Column(JSON, nullable=True)      # {passed, issues[]}

    # AI enhancement results (nullable = not run)
    ai_analysis   = Column(JSON, nullable=True)       # {summary, risks[], score}
    ai_enabled    = Column(Boolean, default=False)

    # Final result
    verdict       = Column(String(20), nullable=True) # 'approved' | 'rejected'
    review_notes  = Column(Text, nullable=True)       # Human-readable summary

    reviewed_at   = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=now_utc)
```

## Configuration (Server-side env vars)

```bash
# Base review thresholds
REVIEW_MIN_WIN_RATE=0.4           # Minimum win rate (40%)
REVIEW_MIN_RETURNS=-0.5           # Minimum returns (-50%)
REVIEW_MAX_DRAWDOWN=0.8           # Maximum drawdown (80%)

# AI enhancement (optional, omit to disable)
REVIEW_AI_PROVIDER=               # "openai" | "anthropic" | etc.
REVIEW_AI_MODEL=                  # e.g. "gpt-4o-mini"
REVIEW_AI_API_KEY=                # Server-side API key
REVIEW_AI_BASE_URL=               # Optional custom endpoint

# Celery
REVIEW_TASK_SOFT_TIME_LIMIT=120   # 2 min soft limit
REVIEW_TASK_TIME_LIMIT=180        # 3 min hard limit
```

## Phase 1: Base Review Rules

### Code Safety Scan
AST-based detection of dangerous patterns:
- `import os`, `import subprocess`, `import sys`
- `os.system()`, `os.exec*()`, `subprocess.*`
- `eval()`, `exec()`, `compile()`
- `__import__()`, `importlib.import_module()`
- `open()` in write mode, `shutil.rmtree()`
- Network calls: `socket.*`, `requests.*`, `urllib.*`
- File path traversal patterns

Severity levels:
- **CRITICAL** (auto-reject): `os.system`, `subprocess`, `eval`, `exec`
- **WARNING** (flag, don't auto-reject): `open()`, `import os`

### Metrics Threshold Check
- `win_rate >= REVIEW_MIN_WIN_RATE` (default 40%)
- `returns >= REVIEW_MIN_RETURNS` (default -50%)
- `max_drawdown <= REVIEW_MAX_DRAWDOWN` (default 80%)
- At least 1 completed backtest exists

### Metadata Completeness
- `title` present, length >= 5
- `description` present, length >= 20
- `tags` has at least 1 tag
- `category` present
- `display_metrics` not empty

## Phase 2: AI Enhancement

Only runs when `REVIEW_AI_PROVIDER` and `REVIEW_AI_API_KEY` are configured.

Prompt to AI:
```
Review this trading strategy code for the marketplace.
Check for:
1. Logical errors or impossible conditions
2. Risk management adequacy (stop-loss, position sizing)
3. Potential overfitting signals
4. Code quality and maintainability
5. Any deceptive or misleading patterns

Strategy metadata: {title, description, category, metrics}
Strategy code:
{code}

Return JSON: {score: 0-100, risks: [...], summary: "...", recommendation: "approve"|"reject"}
```

AI result interpretation:
- `score >= 60` and `recommendation == "approve"` → approve
- `score < 40` or `recommendation == "reject"` → reject
- In between → approve with warnings (flagged for human review if admin available)

AI failure fallback: Use base review result only. Log error. Do NOT reject because AI failed.

## Celery Integration

### Task Definition

```python
# backend/app/tasks/review_tasks.py

@celery_app.task(
    bind=True,
    name='app.tasks.review_tasks.review_strategy',
    queue='review',
    soft_time_limit=120,
    time_limit=180,
)
def review_strategy(self, strategy_id):
    # Ensure Flask app context
    # Run base review
    # Optionally run AI enhancement
    # Update StrategyReview + Strategy.review_status
    # Dispatch notification
```

### Queue Registration

In `celery_app.py`, add to task routes:
```python
'app.tasks.review_tasks.*': {'queue': 'review'},
```

In `imports`, add:
```python
'app.tasks.review_tasks',
```

### Trigger Point

In `marketplace.py` publish endpoint, after setting `review_status = "pending"`:
```python
from ..tasks.review_tasks import review_strategy
review_strategy.delay(strategy.id)
```

## Notification

On completion, dispatch existing notification task:
```python
from .notification_tasks import send_notification
send_notification.delay(
    user_id=strategy.owner_id,
    type="strategy_review",
    title=f"Strategy {'Approved' if approved else 'Rejected'}",
    content=review_notes,
)
```

## API Endpoints

No new endpoints needed. Existing:
- `GET /marketplace/strategies/<id>/publish-status` — returns current review_status
- Admin endpoints unchanged (manual override still works)

## Error Handling

- Celery task failure → StrategyReview stays `pending`, can be re-triggered
- AI timeout → soft_time_limit catches it, fallback to base result
- Missing code → reject with reason "source_code_unavailable"
- Already reviewed → skip (idempotent)

## Migration

```python
# New table: strategy_reviews
# No changes to existing Strategy model
```
