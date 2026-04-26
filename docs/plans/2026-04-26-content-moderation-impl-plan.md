# Content Moderation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add post-publication content moderation for all UGC using sensitive word matching with AC automaton, three-strike auto-ban policy.

**Architecture:** Content is published immediately. A Celery async task scans it against an in-memory sensitive word automaton. Violations trigger content takedown, user warning, and auto-ban after 3 strikes.

**Tech Stack:** Python/Flask, pyahocorasick (AC automaton), Celery, PostgreSQL, Vue 3

---

### Task 1: Add dependency + data models

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/models.py`

**Step 1: Add pyahocorasick to requirements**

Append to `backend/requirements.txt`:
```
pyahocorasick>=2.0.0,<3.0.0
```

**Step 2: Add new models and columns to `backend/app/models.py`**

After the `Notification` class (line 97), add:

```python
class SensitiveWord(db.Model):
    __tablename__ = 'sensitive_words'
    __table_args__ = (
        db.Index('ix_sensitive_words_category', 'category'),
        db.Index('ix_sensitive_words_is_active', 'is_active'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    word = db.Column(db.String, nullable=False, unique=True)
    category = db.Column(db.String(32), nullable=False)
    level = db.Column(db.String(16), nullable=False, default='medium')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class UserModerationRecord(db.Model):
    __tablename__ = 'user_moderation_records'
    __table_args__ = (
        db.Index('ix_user_moderation_records_user_id', 'user_id'),
        db.Index('ix_user_moderation_records_created_at', 'created_at'),
    )

    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.String(32), nullable=False)
    target_id = db.Column(db.String, nullable=False)
    matched_words = db.Column(db.JSON, nullable=False, default=list)
    action_taken = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
```

In `User` class, add after `is_banned` (line 38):
```python
    warning_count = db.Column(db.Integer, nullable=False, default=0)
```

In `Post` class, add after `created_at` (line 585):
```python
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
```

In `PostComment` class, add after `created_at` (line 614):
```python
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
```

**Step 3: Generate migration**

Run:
```bash
cd backend && flask db migrate -m "add content moderation tables and columns"
```

**Step 4: Apply migration**

Run:
```bash
cd backend && flask db upgrade
```

**Step 5: Install dependency**

Run:
```bash
cd backend && pip install pyahocorasick
```

**Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/models.py backend/migrations/
git commit -m "feat: add content moderation data models"
```

---

### Task 2: Build ModerationService

**Files:**
- Create: `backend/app/services/moderation.py`

**Step 1: Create ModerationService**

```python
import logging
import threading

import ahocorasick

from ..extensions import db
from ..models import SensitiveWord

logger = logging.getLogger(__name__)

_automaton_lock = threading.Lock()
_automaton: ahocorasick.Automaton | None = None


def _build_automaton() -> ahocorasick.Automaton:
    auto = ahocorasick.Automaton()
    words = (
        db.session.query(SensitiveWord.word)
        .filter(SensitiveWord.is_active.is_(True))
        .all()
    )
    for (word,) in words:
        auto.add_word(word, word)
    auto.make_automaton()
    return auto


def get_automaton() -> ahocorasick.Automaton:
    global _automaton
    with _automaton_lock:
        if _automaton is None:
            _automaton = _build_automaton()
        return _automaton


def reload_automaton():
    global _automaton
    with _automaton_lock:
        _automaton = _build_automaton()
    logger.info("Moderation automaton reloaded")


def scan(text: str) -> list[str]:
    auto = get_automaton()
    if auto is None or len(auto) == 0:
        return []
    found = set()
    for _, matched in auto.iter(text):
        found.add(matched)
    return sorted(found)
```

**Step 2: Commit**

```bash
git add backend/app/services/moderation.py
git commit -m "feat: add ModerationService with AC automaton"
```

---

### Task 3: Create Celery moderation task

**Files:**
- Create: `backend/app/tasks/moderation_tasks.py`
- Modify: `backend/app/celery_app.py`

**Step 1: Create moderation task**

```python
import logging
import os

from celery.utils.log import get_task_logger
from flask import has_app_context

from ..celery_app import celery_app
from ..extensions import db
from ..models import Post, PostComment, User, UserModerationRecord
from ..services.moderation import scan
from ..services.notifications import create_notification
from ..utils.auth import blacklist_refresh_tokens, revoke_all_user_tokens

logger = get_task_logger(__name__) if logging.getLogger().handlers else logging.getLogger(__name__)

MAX_WARNINGS = 3


def _moderate(user_id: str, target_type: str, target_id: str, content: str):
    matched = scan(content)
    if not matched:
        return {"status": "clean"}

    user = db.session.get(User, user_id)
    if user is None:
        return {"status": "user_not_found"}

    # Hide content
    if target_type == "post":
        db.session.query(Post).filter_by(id=target_id).update({Post.is_hidden: True})
    elif target_type == "comment":
        db.session.query(PostComment).filter_by(id=target_id).update({PostComment.is_hidden: True})
    elif target_type in ("nickname", "bio"):
        pass  # handled below

    # Increment warning count
    user.warning_count = (user.warning_count or 0) + 1
    action_taken = "warned"

    # Record
    record = UserModerationRecord(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        matched_words=matched,
        action_taken=action_taken,
    )
    db.session.add(record)

    # Auto-ban on 3rd strike
    if user.warning_count >= MAX_WARNINGS:
        user.is_banned = True
        action_taken = "banned"
        record.action_taken = action_taken
        try:
            active_tokens = revoke_all_user_tokens(user.id, reason="auto_ban_moderation")
            blacklist_refresh_tokens(active_tokens)
        except Exception:
            logger.exception("Failed to revoke tokens for user %s", user.id)

    # Send notification
    if action_taken == "banned":
        title = "账号已被封禁"
        notification_content = (
            f"您发布的内容包含违规词汇（{', '.join(matched[:5])}），已被下架。"
            f"累计违规{user.warning_count}次，账号已被自动封禁。"
        )
    else:
        title = "内容违规警告"
        remaining = MAX_WARNINGS - user.warning_count
        notification_content = (
            f"您发布的内容包含违规词汇（{', '.join(matched[:5])}），已被下架。"
            f"这是第{user.warning_count}次警告，还剩{remaining}次将被封禁。"
        )

    create_notification(
        user_id=user_id,
        type="moderation_warning",
        title=title,
        content=notification_content,
    )

    db.session.commit()
    return {"status": "flagged", "matched": matched, "action": action_taken}


@celery_app.task(
    bind=True,
    name="app.tasks.moderation_tasks.moderate_content",
    soft_time_limit=30,
    time_limit=60,
)
def moderate_content(self, user_id: str, target_type: str, target_id: str, content: str):
    if has_app_context():
        return _moderate(user_id, target_type, target_id, content)

    from .. import create_app

    app = create_app()
    with app.app_context():
        return _moderate(user_id, target_type, target_id, content)
```

**Step 2: Register task module in celery_app.py**

In `backend/app/celery_app.py`, add to `imports` tuple (line 53):
```python
        'app.tasks.moderation_tasks',
```

**Step 3: Commit**

```bash
git add backend/app/tasks/moderation_tasks.py backend/app/celery_app.py
git commit -m "feat: add Celery moderation task with auto-ban"
```

---

### Task 4: Trigger moderation from community API

**Files:**
- Modify: `backend/app/blueprints/community.py`

**Step 1: Add import at top of community.py**

```python
from ..tasks.moderation_tasks import moderate_content
```

**Step 2: Trigger moderation after post creation**

In `create_post()` function, after `db.session.commit()` (line 147), add:

```python
    moderate_content.delay(
        user_id=user.id,
        target_type="post",
        target_id=post.id,
        content=content,
    )
```

**Step 3: Trigger moderation after comment creation**

In `create_comment()` function, after `db.session.commit()` (line 372), add:

```python
    moderate_content.delay(
        user_id=user_id,
        target_type="comment",
        target_id=comment.id,
        content=content,
    )
```

**Step 4: Filter hidden posts in get_posts**

In `get_posts()`, change `base_query` (line 159) to:

```python
    base_query = Post.query.filter(Post.content.isnot(None), Post.is_hidden.is_(False))
```

**Step 5: Filter hidden comments in get_comments**

In `get_comments()`, change query (line 331) to:

```python
    query = PostComment.query.filter_by(post_id=post.id, is_hidden=False)
```

**Step 6: Filter hidden posts in get_my_collections**

In `get_my_collections()`, add to filter (line 293):

```python
            Post.is_hidden.is_(False),
```

**Step 7: Commit**

```bash
git add backend/app/blueprints/community.py
git commit -m "feat: trigger moderation on post/comment creation, filter hidden content"
```

---

### Task 5: Admin API for sensitive words and moderation records

**Files:**
- Modify: `backend/app/blueprints/admin.py`

**Step 1: Add imports**

In `admin.py` imports (line 12), add to the models import:

```python
from ..models import AuditLog, BacktestJob, BacktestJobStatus, File, Report, SensitiveWord, Strategy, StrategyVersion, User, UserModerationRecord
```

Add new import:

```python
from ..services.moderation import reload_automaton
```

**Step 2: Add sensitive words CRUD endpoints**

Append to `admin.py` before the private helper functions:

```python
# ─── Sensitive Words Management ──────────────────────────────────────


@bp.get("/sensitive-words")
@require_admin
def list_sensitive_words():
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=50, minimum=1, maximum=200)
    category = (request.args.get("category") or "").strip()

    query = SensitiveWord.query
    if category:
        query = query.filter(SensitiveWord.category == category)

    total = query.count()
    items = (
        query.order_by(SensitiveWord.created_at.desc(), SensitiveWord.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return ok(
        [_serialize_sensitive_word(w) for w in items],
        meta={"total": total, "page": page, "per_page": per_page},
    )


@bp.post("/sensitive-words")
@require_admin
def create_sensitive_words():
    payload = request.get_json() or {}
    words_data = payload.get("words")

    if isinstance(words_data, list):
        items = words_data
    else:
        items = [payload]

    admin_id = _current_admin_id()
    created = []
    errors = []

    for item in items:
        word = str(item.get("word") or "").strip()
        category = str(item.get("category") or "other").strip()
        level = str(item.get("level") or "medium").strip()

        if not word:
            errors.append({"word": "", "error": "word is required"})
            continue

        existing = SensitiveWord.query.filter_by(word=word).first()
        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.category = category
                existing.level = level
                created.append(_serialize_sensitive_word(existing))
            else:
                errors.append({"word": word, "error": "already exists"})
            continue

        sw = SensitiveWord(word=word, category=category, level=level)
        db.session.add(sw)
        created.append(_serialize_sensitive_word(sw))

    db.session.commit()

    if created:
        reload_automaton()
        log_audit(
            operator_id=admin_id,
            action="sensitive_words_add",
            target_type="sensitive_word",
            target_id="batch",
            details={"count": len(created)},
        )

    return ok({"created": created, "errors": errors})


@bp.delete("/sensitive-words/<word_id>")
@require_admin
def delete_sensitive_word(word_id):
    word = db.session.get(SensitiveWord, word_id)
    if word is None:
        return error_response("WORD_NOT_FOUND", "Sensitive word not found", 404)

    admin_id = _current_admin_id()
    db.session.delete(word)
    log_audit(
        operator_id=admin_id,
        action="sensitive_word_delete",
        target_type="sensitive_word",
        target_id=word.id,
        details={"word": word.word, "category": word.category},
    )
    db.session.commit()
    reload_automaton()
    return ok({"id": word_id, "deleted": True})


# ─── Moderation Records ──────────────────────────────────────────────


@bp.get("/moderation-records")
@require_admin
def list_moderation_records():
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=100)
    user_id = (request.args.get("user_id") or "").strip()

    query = db.session.query(UserModerationRecord, User).outerjoin(
        User, UserModerationRecord.user_id == User.id
    )
    if user_id:
        query = query.filter(UserModerationRecord.user_id == user_id)

    total = query.count()
    items = (
        query.order_by(
            UserModerationRecord.created_at.desc(), UserModerationRecord.id.desc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return ok(
        [_serialize_moderation_record(r, u) for r, u in items],
        meta={"total": total, "page": page, "per_page": per_page},
    )


@bp.patch("/moderation-records/<record_id>/appeal")
@require_admin
def appeal_moderation_record(record_id):
    record = db.session.get(UserModerationRecord, record_id)
    if record is None:
        return error_response("RECORD_NOT_FOUND", "Moderation record not found", 404)

    payload = request.get_json() or {}
    action = str(payload.get("action") or "").strip().lower()
    if action not in ("restore", "uphold"):
        return error_response("INVALID_ACTION", "Action must be 'restore' or 'uphold'", 422)

    admin_id = _current_admin_id()

    if action == "restore":
        # Un-hide the content
        if record.target_type == "post":
            db.session.query(Post).filter_by(id=record.target_id).update(
                {Post.is_hidden: False}
            )
        elif record.target_type == "comment":
            db.session.query(PostComment).filter_by(id=record.target_id).update(
                {PostComment.is_hidden: False}
            )

        user = db.session.get(User, record.user_id)
        if user and user.warning_count > 0:
            user.warning_count -= 1
            if user.warning_count < MAX_WARNINGS_VAL and user.is_banned:
                user.is_banned = False

        record.action_taken = "appealed_restored"
        create_notification(
            user_id=record.user_id,
            type="moderation_appeal",
            title="内容申诉通过",
            content="您的内容经人工审核后已恢复。",
        )

    else:
        record.action_taken = "appealed_upheld"

    log_audit(
        operator_id=admin_id,
        action=f"moderation_{action}",
        target_type="moderation_record",
        target_id=record.id,
        details={"original_action": record.action_taken, "appeal_action": action},
    )
    db.session.commit()
    return ok({"record_id": record.id, "action": action})
```

**Step 3: Add serializers**

In the private helpers section:

```python
def _serialize_sensitive_word(word):
    return {
        "id": word.id,
        "word": word.word,
        "category": word.category,
        "level": word.level,
        "is_active": word.is_active,
        "created_at": format_beijing_iso(word.created_at),
    }


def _serialize_moderation_record(record, user):
    return {
        "id": record.id,
        "user_id": record.user_id,
        "user_nickname": getattr(user, "nickname", None),
        "target_type": record.target_type,
        "target_id": record.target_id,
        "matched_words": record.matched_words,
        "action_taken": record.action_taken,
        "created_at": format_beijing_iso(record.created_at),
    }


MAX_WARNINGS_VAL = 3
```

**Step 4: Add imports for Post, PostComment in admin.py**

Update the import line to include:

```python
from ..models import AuditLog, BacktestJob, BacktestJobStatus, File, Post, PostComment, Report, SensitiveWord, Strategy, StrategyVersion, User, UserModerationRecord
```

**Step 5: Commit**

```bash
git add backend/app/blueprints/admin.py
git commit -m "feat: add admin API for sensitive words and moderation records"
```

---

### Task 6: Frontend — filter hidden content in display

**Files:**
- Modify: `frontend/src/components/community/CommentSection.vue`
- Modify: `frontend/src/components/community/PostCard.vue`

**Step 1: Read current CommentSection.vue to understand structure**

Read the file, then adjust the comment rendering to handle `is_hidden` field.

If the API already filters hidden comments (which it does after Task 4), no frontend change needed for the comment list itself. But if the admin wants to see them, that's a separate admin view.

**Step 2: No frontend change needed for regular users**

Since the backend now filters `is_hidden=True` from API responses, regular users won't see hidden content. The frontend changes are only needed if you want to show placeholder text like "该内容因违规已被隐藏" — but this would require the API to return hidden items with a flag instead of filtering them out.

**Decision: Backend filtering is sufficient. No frontend change for regular users.**

**Step 3: Commit (skip if no changes)**

No commit needed for this task.

---

### Task 7: Seed initial sensitive words

**Files:**
- Create: `backend/app/utils/seed_sensitive_words.py`

**Step 1: Create seed utility**

```python
"""Seed the sensitive_words table with a baseline list.

Run: python -m app.utils.seed_sensitive_words
"""

from ..extensions import db
from ..models import SensitiveWord


BASELINE_WORDS: list[dict] = [
    # political
    # violence
    # porn
    # spam
    # other
]

# NOTE: The actual word list should be maintained by the admin team.
# This file provides the mechanism; populate BASELINE_WORDS as needed.


def seed_sensitive_words():
    existing = {row.word for row in db.session.query(SensitiveWord.word).all()}
    added = 0
    for entry in BASELINE_WORDS:
        word = entry.get("word", "").strip()
        if not word or word in existing:
            continue
        db.session.add(SensitiveWord(
            word=word,
            category=entry.get("category", "other"),
            level=entry.get("level", "medium"),
        ))
        added += 1
    db.session.commit()
    return added


if __name__ == "__main__":
    from .. import create_app

    app = create_app()
    with app.app_context():
        count = seed_sensitive_words()
        print(f"Seeded {count} sensitive words")
```

**Step 2: Commit**

```bash
git add backend/app/utils/seed_sensitive_words.py
git commit -m "feat: add sensitive word seed utility"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Data models + migration | requirements.txt, models.py |
| 2 | ModerationService | services/moderation.py |
| 3 | Celery task | tasks/moderation_tasks.py, celery_app.py |
| 4 | Community API triggers | community.py |
| 5 | Admin API | admin.py |
| 6 | Frontend (skipped) | — |
| 7 | Seed utility | utils/seed_sensitive_words.py |
