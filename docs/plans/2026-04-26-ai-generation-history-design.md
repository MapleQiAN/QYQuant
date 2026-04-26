# AI Strategy Generation History - Design Document

## Problem

AI-generated strategy conversations and results are ephemeral. When users navigate away from the AI Lab, all messages and draft analysis are lost. No way to review past generation attempts or reload drafts.

## Solution

Persist complete AI generation sessions (conversation + results) to database. Add history panel in AI Lab for browsing, reloading, and deleting past sessions.

## Data Model

### New Table: `ai_generation_sessions`

```python
class AiGenerationSession(db.Model):
    __tablename__ = 'ai_generation_sessions'

    id            = db.Column(db.String, primary_key=True, default=gen_id)
    owner_id      = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    title         = db.Column(db.String(200))            # Auto-extracted from first user message
    messages      = db.Column(db.JSON, nullable=False)    # [{role: "user"|"assistant", content: "..."}]
    analysis      = db.Column(db.JSON, nullable=True)     # Latest analysis result (with draftImportId)
    draft_id      = db.Column(db.String, nullable=True)   # Associated StrategyImportDraft.id
    model_name    = db.Column(db.String(100))             # AI model used
    message_count = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at    = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    __table_args__ = (
        db.Index('ix_ai_gen_sessions_owner_updated', 'owner_id', 'updated_at'),
    )
```

### Schema Details

- `messages`: Full conversation array `[{role, content}]`. Grows with each generation call.
- `analysis`: The latest `StrategyImportAnalysis` JSON from the most recent generation.
- `title`: Extracted from first user message (truncated to 200 chars). Used in history list.
- `draft_id`: References `StrategyImportDraft.id` for reload capability.

## API Changes

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/ai-sessions` | List user sessions (paginated, ordered by `updated_at` desc) |
| `GET` | `/v1/ai-sessions/:id` | Get session detail (messages + analysis) |
| `DELETE` | `/v1/ai-sessions/:id` | Delete a session |

#### GET /v1/ai-sessions

**Query params**: `page` (default 1), `per_page` (default 20)

**Response**:
```json
{
  "sessions": [
    {
      "id": "...",
      "title": "RSI 超买超卖策略",
      "messageCount": 4,
      "modelName": "gpt-4o",
      "hasDraft": true,
      "createdAt": "...",
      "updatedAt": "..."
    }
  ],
  "total": 15,
  "page": 1,
  "perPage": 20
}
```

#### GET /v1/ai-sessions/:id

**Response**:
```json
{
  "id": "...",
  "title": "RSI 超买超卖策略",
  "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "analysis": { ... },
  "draftId": "...",
  "modelName": "gpt-4o",
  "createdAt": "...",
  "updatedAt": "..."
}
```

#### DELETE /v1/ai-sessions/:id

**Response**: `204 No Content`

### Modified Endpoint

#### POST /v1/strategy-ai/generate

**New optional field**: `sessionId` (string)

- With `sessionId`: Append messages to existing session, update analysis
- Without `sessionId`: Create new session

**New response field**: `sessionId` (string)

```json
{
  "reply": "...",
  "analysis": { ... },
  "sessionId": "sess_abc123"
}
```

## Frontend Changes

### History Panel in AiStrategyLabView

Add collapsible history panel on the left side of the AI Lab view.

**Layout**:
```
┌──────────┬──────────────────────────────────────┐
│ History  │  Existing AI Lab layout               │
│ ┌──────┐ │  (Brief | Console | Draft)            │
│ │新对话 │ │                                       │
│ └──────┘ │                                       │
│          │                                       │
│ Session3 │                                       │
│  RSI策略 │                                       │
│  4条消息 │                                       │
│          │                                       │
│ Session2 │                                       │
│  均线策略 │                                       │
│          │                                       │
│ Session1 │                                       │
│  删除 🗑 │                                       │
└──────────┴───────────────────────────────────────┘
```

**New reactive state**:
```typescript
const sessions = ref<AiSessionSummary[]>([])
const activeSessionId = ref<string | null>(null)
const historyLoaded = ref(false)
```

**Interactions**:
1. **Click history item** → Load messages + analysis into current panels, set `activeSessionId`
2. **Click "新对话"** → Clear `aiMessages`, `aiLatestAnalysis`, set `activeSessionId = null`. Next generate creates new session.
3. **Click delete** → Confirm dialog, DELETE API call, remove from list. If active session deleted, clear state.
4. **Auto-save** → After each successful `handleGenerate`, the backend persists automatically via `sessionId`

### i18n Keys

Add under `aiLab` namespace:
- `historyTitle`: "历史记录" / "History"
- `newSession`: "新对话" / "New Session"
- `messageCount`: "{n} 条消息" / "{n} messages"
- `deleteConfirm`: "确定删除此记录？" / "Delete this session?"
- `loadError`: "加载失败" / "Failed to load"
- `deleteError`: "删除失败" / "Failed to delete"

## Implementation Steps

1. Add `AiGenerationSession` model to `models.py`, create migration
2. Add new API endpoints in `blueprints/strategies.py`
3. Modify `generate_strategy_draft()` to accept/save session data
4. Add `aiSessions` API functions in `frontend/src/api/strategies.ts`
5. Add `AiSessionSummary` type in `frontend/src/types/Strategy.ts`
6. Add history panel component in `AiStrategyLabView.vue`
7. Add i18n keys for zh/en
8. Write tests

## Edge Cases

- **Session draft expired**: `StrategyImportDraft` has 24h TTL. When loading old session, draft may be gone. UI should show "草稿已过期" and allow re-generation.
- **Concurrent sessions**: User can only have one active session at a time. History panel switches between them.
- **Title extraction**: First user message truncated to 50 chars for title, full content stored in messages array.
