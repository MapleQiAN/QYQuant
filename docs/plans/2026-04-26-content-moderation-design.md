# Content Moderation Design

## Overview

Post-publication content moderation for all UGC content (posts, comments, nickname, bio). Uses local sensitive word library with AC automaton for fast matching. Three-strike punishment policy.

## Architecture

- **Mode**: Post-then-review (先发后审)
- **Detection**: Local sensitive word library + AC automaton (pyahocorasick)
- **Punishment**: Three-strike auto-ban
- **Scope**: All UGC content

## Data Models

### SensitiveWord

```python
class SensitiveWord(db.Model):
    __tablename__ = 'sensitive_words'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    word = db.Column(db.String, nullable=False, unique=True)
    category = db.Column(db.String(32), nullable=False)  # political/porn/violence/spam/other
    level = db.Column(db.String(16), nullable=False, default='medium')  # low/medium/high
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
```

### UserModerationRecord

```python
class UserModerationRecord(db.Model):
    __tablename__ = 'user_moderation_records'
    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.String(32), nullable=False)  # post/comment/nickname/bio
    target_id = db.Column(db.String, nullable=False)
    matched_words = db.Column(db.JSON, default=list)
    action_taken = db.Column(db.String(32), nullable=False)  # taken_down/warned/banned
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
```

### User modifications

- Add `warning_count` column (Integer, default=0)

### Post / PostComment modifications

- Add `is_hidden` column (Boolean, default=False)

## Moderation Flow

```
User submits content → Save to DB → Return success immediately
                          ↓
          Celery async task triggers moderation
                          ↓
          ModerationService.scan(text) via AC automaton
                          ↓
       ┌── No match → Done
       └── Match found → Punishment flow:
            1. Mark content is_hidden=True
            2. Create UserModerationRecord
            3. user.warning_count += 1
            4. Send Notification warning
            5. if warning_count >= 3 → user.is_banned = True
```

## ModerationService

- Use `pyahocorasick` for O(n) AC automaton matching
- Load active words into memory on startup
- Cache automaton instance, rebuild on word updates
- Redis pub/sub to notify workers to rebuild on updates

## Admin API

- `GET /admin/sensitive-words` — Paginated list
- `POST /admin/sensitive-words` — Add words (batch supported)
- `DELETE /admin/sensitive-words/<id>` — Remove word
- `GET /admin/moderation-records` — View moderation records
- `POST /admin/moderation-records/<id>/appeal` — Manual appeal handling

## Frontend Changes

- Hidden comments: Show "该评论因违规已被隐藏"
- Hidden posts: Show "该内容因违规已被隐藏"
- Admin panel: New sensitive word management page, moderation records page
- Notification display for warnings

## Files to Create/Modify

### Backend

- `models.py` — Add SensitiveWord, UserModerationRecord, modify User/Post/PostComment
- `services/moderation.py` — ModerationService with AC automaton
- `tasks.py` — Celery async moderation task
- `admin.py` — Admin API endpoints
- `community.py` — Trigger moderation after create

### Frontend

- `CommentSection.vue` — Handle hidden comments display
- `PostCard.vue` — Handle hidden posts display
- Admin components — Word management, moderation records

### Migration

- New tables: sensitive_words, user_moderation_records
- New columns: users.warning_count, posts.is_hidden, post_comments.is_hidden
