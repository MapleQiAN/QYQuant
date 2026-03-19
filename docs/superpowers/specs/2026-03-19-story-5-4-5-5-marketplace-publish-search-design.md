# Story 5.4 + 5.5 Marketplace Publish And Search Design

**Goal:** Add the free-share marketplace publish workflow for user-owned strategies and expand the marketplace list into a server-side search and filter experience backed by PostgreSQL full-text search with `zhparser`.

## Scope

- Add a publish workflow for user-owned strategies from the strategy library.
- Add authenticated marketplace publish and publish-status APIs.
- Persist publish metadata on the existing `strategies` records instead of introducing a separate publish table.
- Add a minimal notifications foundation sufficient for "strategy submitted for review" messages.
- Record marketplace publish submissions in `audit_logs`.
- Expand `GET /api/v1/marketplace/strategies` to support keyword search, filter combinations, ranking, and pagination.
- Add PostgreSQL full-text search infrastructure using `zhparser`, `tsvector`, and GIN indexes.
- Add marketplace search UI, filter chips, result count, and empty-state handling.
- Add publish entry buttons and review-status badges in the private strategy library.
- Cover both backend and frontend behavior with focused automated tests.

## Out of Scope

- Admin review UI and moderator approval/rejection actions.
- Notification inbox UI, unread counters, or notification management pages.
- Elasticsearch or any search infrastructure outside PostgreSQL.
- Reworking the existing marketplace detail and import flows beyond the contract changes required to coexist with search and publish.
- Replacing the existing private strategy-library page structure with a new information architecture.

## Product Decisions

- Publish entry lives in the strategy-library row, but the actual publish flow runs in a three-step drawer or modal flow.
- A strategy in `pending` or `approved` state cannot be submitted again from the UI.
- A strategy in `rejected` state can reopen the publish flow and resubmit.
- Publish submission never makes a strategy public immediately. Visibility still depends on later admin approval.
- Search and filters are server-side only. The frontend sends query params and renders returned results.
- Search input is debounced by 300 ms.
- Category and metric chips can be combined. Selecting "all" clears the other quick filters.

## Existing Constraints

- Marketplace read concerns already live in `backend/app/blueprints/marketplace.py`.
- Private library management already lives in `backend/app/blueprints/strategies.py` and `frontend/src/views/StrategyLibraryView.vue`.
- `Strategy` already contains the key marketplace fields:
  - `title`
  - `description`
  - `category`
  - `is_public`
  - `is_verified`
  - `review_status`
  - `display_metrics`
- Current visibility rules are already centralized as `is_public = true` and `review_status = 'approved'`.
- The repository already stores `tags` as a JSON list. This design preserves that storage shape and adds tag filtering against the existing representation instead of introducing a same-story column rewrite.

## Backend Architecture

- Keep marketplace concerns in `backend/app/blueprints/marketplace.py`.
- Split the file internally by responsibility to avoid a single monolithic handler section:
  - marketplace list and search
  - publish submission
  - publish-status lookup
  - detail and import helpers
  - shared validation and query helpers
- Keep user-owned strategy listing and deletion in `backend/app/blueprints/strategies.py`.
- Add notification persistence to the shared model layer in `backend/app/models.py`.
- Reuse `audit_logs` instead of creating a marketplace-specific audit mechanism.

## Publish Workflow Design

### User Flow

1. User opens the private strategy library.
2. A row-level "Publish to Marketplace" button is shown for eligible strategies.
3. The publish drawer opens.
4. Step 1 collects:
   - title
   - description
   - tags
   - category
   - display metrics
5. Step 2 shows code-protection and IP-agreement text and requires an explicit confirmation checkbox.
6. Submit triggers the publish API.
7. On success, the UI moves to a success state that confirms review submission.
8. The strategy row now shows `pending`.

### Publish State Rules

- Unpublished or editable draft strategy:
  - button enabled
- `pending`:
  - button disabled
  - status badge shown
- `approved`:
  - button disabled
  - status badge shown
- `rejected`:
  - button enabled
  - previous published fields are editable and resubmittable

### Server Validation Rules

- Request requires authentication.
- `strategy_id` must belong to the current user.
- Strategy must have at least one completed backtest job with a non-null result storage key.
- Required fields:
  - `title`
  - `description`
  - `tags` with at least one entry
  - `category`
  - `display_metrics`
- `display_metrics` must contain at least:
  - `sharpe_ratio`
  - `max_drawdown`
  - `total_return`
- `category` must be one of:
  - `trend-following`
  - `mean-reversion`
  - `momentum`
  - `multi-indicator`
  - `other`
- The backend remains the source of truth for publish eligibility even if the frontend disables buttons proactively.

## Data Model Changes

### `Strategy`

No new publish table is introduced. Publish metadata is written back to the existing strategy record:

- `title`
- `description`
- `tags`
- `category`
- `display_metrics`
- `review_status`

Submission updates:

- `review_status = 'pending'`
- `is_public` remains unchanged and must not be set to `true` during submit
- `updated_at` and `last_update` should reflect the submission

### `Notification`

Add a `Notification` model to `backend/app/models.py`:

- `id`
- `user_id`
- `type`
- `title`
- `content`
- `is_read`
- `created_at`

This story uses it only to persist the review-submitted notification. It does not require any notification read API or UI.

### Audit Logging

Add an `AuditLog` row when a publish submission is accepted:

- `operator_id = current user`
- `action = 'marketplace_strategy_submitted'`
- `target_type = 'strategy'`
- `target_id = strategy_id`
- `details` includes the submitted public metadata snapshot

## Migration Plan

Create one migration for notifications:

- create `notifications`
- create the unread partial index on `(user_id, is_read)` for unread rows

Create one migration for PostgreSQL full-text search:

- `CREATE EXTENSION IF NOT EXISTS zhparser`
- create text search configuration `chinese`
- add `title_tsv` and `description_tsv` columns
- add GIN indexes for both tsvector columns
- add update logic so inserts and updates keep vectors fresh

The migration targets PostgreSQL as required by the story. This design does not provide a SQLite fallback for search infrastructure.

## API Contract

### `POST /api/v1/marketplace/strategies`

Authenticated endpoint used by the strategy-library publish flow.

Request:

```json
{
  "strategy_id": "strategy-id",
  "title": "Moving Average Trend Pro",
  "description": "Markdown-compatible description",
  "tags": ["trend", "medium-frequency", "risk-control"],
  "category": "trend-following",
  "display_metrics": {
    "sharpe_ratio": 1.45,
    "max_drawdown": -15.2,
    "total_return": 45.6,
    "win_rate": 62.3,
    "annual_return": 24.8
  }
}
```

Success response:

```json
{
  "data": {
    "strategy_id": "strategy-id",
    "review_status": "pending"
  }
}
```

Failure cases:

- `401` unauthenticated
- `403` strategy not owned by current user
- `404` strategy does not exist
- `422` no successful backtest record
- `422` invalid or incomplete publish payload

### `GET /api/v1/marketplace/strategies/<strategy_id>/publish-status`

Authenticated owner-only endpoint used by the strategy library to show the current review state.

Success response:

```json
{
  "data": {
    "review_status": "pending",
    "is_public": false
  }
}
```

### `GET /api/v1/marketplace/strategies`

Extend the existing list endpoint rather than adding a second search route.

Supported query params:

- `page`
- `page_size`
- `featured`
- `tag`
- `q`
- `category`
- `tags`
- `verified`
- `max_drawdown_lte`
- `annual_return_gte`

Behavior rules:

- `featured=true` keeps the current featured-list behavior and ignores ranking-only logic that applies to search mode.
- `tag=onboarding` keeps the current onboarding seed behavior.
- default listing remains restricted to public approved strategies.
- when `q` is present:
  - match against `title_tsv` and `description_tsv`
  - order by `ts_rank` first, then deterministic secondary ordering
- when `q` is absent:
  - keep the current time-based ordering
- filters can be combined with search

## Search Query Design

### PostgreSQL Full-Text Search

- Use `plainto_tsquery('chinese', q)` for the user query string.
- Search predicate:
  - `title_tsv @@ query OR description_tsv @@ query`
- Relevance sorting:
  - `ts_rank(title_tsv, query) + ts_rank(description_tsv, query)` or equivalent combined score
- Search only within strategies already visible to the marketplace:
  - `is_public = true`
  - `review_status = 'approved'`

### Filters

- `category`:
  - exact match on `Strategy.category`
- `verified`:
  - `Strategy.is_verified = true`
- `tags`:
  - filter against the existing JSON tag representation in PostgreSQL
  - match means at least one overlap with the requested tag list
- `max_drawdown_lte`:
  - compare against `display_metrics['max_drawdown']`
  - because drawdown values are negative, the implementation must define and test the comparison carefully to match the product wording
- `annual_return_gte`:
  - compare against `display_metrics['annual_return']`
- JSON metric filters must guard against null or missing values before casting

### Metric Comparison Rule

- Product wording uses thresholds like "drawdown < 10%".
- Stored values are expected to be negative percentages such as `-8.4`.
- The implementation must interpret `max_drawdown_lte=10` as "absolute drawdown is less than or equal to 10%", which means comparing the stored value safely and consistently.
- Tests must pin this rule down so the API contract is not ambiguous.

## Frontend Architecture

- Keep marketplace list state in `frontend/src/stores/useMarketplaceStore.ts`.
- Extend `frontend/src/api/strategies.ts` with:
  - publish API function
  - publish-status API function
  - additional marketplace query params
- Add `frontend/src/components/strategy/StrategyPublishFlow.vue` for the drawer flow.
- Extend `frontend/src/views/StrategyLibraryView.vue` to:
  - show publish buttons
  - fetch or render publish status
  - host the publish drawer
- Extend `frontend/src/views/Marketplace.vue` to:
  - show the search bar
  - show filter chips
  - display the result count
  - display empty-state messaging with a clear-filters action

## Publish UI Design

### Row-Level Entry

Each strategy row in the private library shows:

- publish CTA when eligible
- review-status badge when previously submitted
- disabled publish CTA for `pending` and `approved`
- enabled re-submit CTA for `rejected`

### `StrategyPublishFlow.vue`

The component owns the full three-step experience:

1. Metadata form
2. Code-protection and IP-agreement confirmation
3. Success state

It should receive:

- the source strategy identity
- current publish status if available
- callbacks or store actions for submit and close

It should not own list reloading policy directly; the parent view should refresh the library row state after success.

### Form Behavior

- `title`: max 200 characters
- `description`: textarea with markdown-friendly copy
- `tags`: multi-entry chip input
- `category`: select input bound to the approved enum
- `display_metrics`: selected from the strategy's latest successful backtest results and rendered as chosen summary metrics
- Agreement checkbox is required before submit is enabled

## Marketplace Search UI Design

### Search Bar

- Add a rounded search input at the top of `Marketplace.vue`.
- Search hint text should follow the story intent: search by strategy name, symbol, or tag-like terms.
- Input changes are debounced by 300 ms.
- Clearing the input returns the list to the normal unfiltered marketplace results.

### Filter Chips

Quick chips include:

- `All`
- `Trend Following`
- `Mean Reversion`
- `Momentum`
- `Multi Indicator`
- `Annual Return > 20%`
- `Drawdown < 10%`
- `Verified`

Rules:

- chips are multi-select except `All`
- selecting `All` clears the other quick filters
- changing filters resets pagination to page 1

### Result and Empty States

- show current result count near the list title
- no-result state shows explanatory copy and a "Clear Filters" action
- empty state must distinguish between:
  - loading
  - request failure
  - genuine no-result response

## Error Handling

### Publish Flow

- unauthenticated:
  - redirect to login or surface the existing auth error handling path
- forbidden ownership:
  - show a non-retryable error
- no successful backtest:
  - show a specific message explaining why publish is blocked
- invalid fields:
  - keep the drawer open and render inline or top-level validation errors
- submit failure:
  - do not advance to success step

### Search Flow

- request failure keeps existing results only if that matches current page conventions; otherwise clear and show error explicitly
- empty results should not be treated as an error
- malformed filter values should never be generated by the UI, but the backend still validates them

## Testing Strategy

### Backend

Add tests that drive:

- publish succeeds for an owned strategy with at least one completed backtest
- publish rejects non-owned strategies with `403`
- publish rejects missing successful backtest with `422`
- publish rejects incomplete payloads with `422`
- publish writes `review_status = 'pending'`
- publish does not set `is_public = true`
- publish creates a notification row
- publish creates an audit-log row
- publish-status returns owner-visible status data
- marketplace list supports Chinese full-text search over title and description
- marketplace list supports category filtering
- marketplace list supports metric filtering
- marketplace list supports combined search and filter usage
- marketplace list preserves pagination metadata and deterministic ordering

### Frontend

Add tests that drive:

- library rows show publish buttons and review-status badges correctly
- `pending` and `approved` rows disable publish
- `rejected` rows allow re-submit
- publish drawer step transitions work
- agreement checkbox blocks submit until checked
- publish success updates the row state after refresh
- marketplace search input debounces requests
- chip selection updates filter state and refetches page 1
- result count updates from store metadata
- empty-state clear action resets filters and refetches

## Risks and Constraints

- `zhparser` must be installed in the PostgreSQL environment. Migration and deploy documentation need to assume that dependency explicitly.
- Search infrastructure is PostgreSQL-only in this story. Tests and local verification must run against PostgreSQL, not a SQLite fallback.
- `marketplace.py` already handles list, detail, import, and onboarding seed logic. Adding publish and search without internal refactoring would increase maintenance risk.
- `display_metrics` keys are not strongly typed at the schema level today. Publish validation and search filters must pin the required key names down explicitly.
- Drawdown threshold wording is easy to implement incorrectly because stored values are negative while product copy is phrased in positive percentages.

## Implementation Order

1. Add failing backend tests for publish validation, notification creation, audit logging, and publish-status.
2. Add the notification migration and model.
3. Implement the publish endpoints and supporting helpers in `marketplace.py`.
4. Add failing backend tests for Chinese search, filter combinations, ranking, and pagination.
5. Add the PostgreSQL search migration and update the marketplace list query.
6. Add failing frontend tests for library publish entry states and the publish drawer.
7. Implement `StrategyPublishFlow.vue` and the strategy-library integration.
8. Add failing frontend tests for marketplace search and filter behavior.
9. Implement store, API, and `Marketplace.vue` search and filter changes.
10. Run focused backend and frontend verification against PostgreSQL before any implementation-complete claim.
