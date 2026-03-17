# Story 5.1 Marketplace Design

**Goal:** Build the public marketplace page with a dedicated marketplace backend blueprint, a featured recommendation strip, a paginated public strategy grid, and real author identity on every card.

## Scope

- Add marketplace-facing metadata to `Strategy` and persist it via a migration.
- Add a dedicated backend blueprint at `backend/app/blueprints/marketplace.py`.
- Expose `GET /api/v1/marketplace/strategies` for both paginated list mode and featured mode.
- Return real author `nickname` and `avatar_url` from `users`.
- Add a dedicated frontend marketplace store, page, route, and card components.
- Render featured strategies as wider editorial cards and normal strategies as standard grid cards.
- Keep CTA buttons display-only in this story. No navigation or business action is wired.
- Cover backend and frontend behavior with focused automated tests.

## Out of Scope

- Strategy detail or backtest-entry navigation from marketplace cards.
- Admin or operations workflows for approving, verifying, or featuring strategies.
- Filtering chips, search, category filtering, infinite scroll, or recommendation algorithms.
- Reworking existing private strategy-library flows.
- Changing `tags` storage from the current JSON list to PostgreSQL `TEXT[]`.

## Product Decisions

- Marketplace layout follows the approved structure:
  - top page header
  - independent featured recommendation strip
  - standard paginated strategy grid below
- Featured strategies use a dedicated wide card, not the same visual treatment as normal list cards.
- The page is display-first: buttons render but do not navigate in this story.
- Author identity is mandatory in responses and UI. Cards show real `nickname` and `avatar_url`.

## Backend Architecture

- Keep private strategy management in `backend/app/blueprints/strategies.py`.
- Add a new read-only public blueprint in `backend/app/blueprints/marketplace.py`.
- Register the blueprint in `backend/app/__init__.py` so public marketplace concerns remain isolated from authenticated personal-library behavior.
- The new blueprint owns only public listing concerns for this story:
  - default marketplace listing
  - featured listing via query flag
  - pagination and response metadata

## Data Model Changes

Add the following missing fields to `backend/app/models.py` `Strategy`:

- `title`: optional display title, used by marketplace cards when present and falling back to `name`
- `is_public`: boolean, defaults to `false`
- `is_featured`: boolean, defaults to `false`
- `is_verified`: boolean, defaults to `false`
- `review_status`: string, defaults to `pending`
- `display_metrics`: JSON/JSONB-compatible object for direct card rendering

Do not re-add fields already present in the repository:

- `description`
- `category`
- `source`
- `storage_key`

Do not migrate `tags` away from the current JSON list type in this story. The acceptance criteria can still be met without a storage-type rewrite, and preserving the current shape keeps the migration low risk.

## Migration Plan

Create one Alembic migration that:

- adds the missing marketplace columns to `strategies`
- adds indexes for:
  - `category`
  - `is_featured` partial index where `is_featured = true`
  - `(is_public, is_verified)` partial index where `is_public = true`
- leaves `tags` indexing unchanged for this story because the current JSON representation does not justify a same-story storage conversion

The migration must support clean upgrade/downgrade behavior.

## API Contract

### Endpoint

- `GET /api/v1/marketplace/strategies`

### Default list mode

- Query params:
  - `page`, default `1`
  - `page_size`, default `20`
- Filters:
  - `is_public = true`
  - `review_status = 'approved'`
- Sorting:
  - featured list is separate, so normal list should sort by newest public marketplace content first
  - use deterministic secondary ordering to avoid unstable pagination

### Featured mode

- Same endpoint with `featured=true`
- Additional filter:
  - `is_featured = true`
- Hard cap:
  - maximum `6` items
- Still limited to public approved strategies

### Response shape

Both modes return:

```json
{
  "data": [],
  "meta": {
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### Card DTO shape

Each returned item should already be UI-ready:

```json
{
  "id": "strategy-id",
  "title": "Display title",
  "name": "Internal name fallback",
  "description": "Short summary",
  "category": "trend-following",
  "tags": ["gold", "momentum"],
  "is_verified": true,
  "display_metrics": {
    "annualized_return": 18.2,
    "max_drawdown": -9.4,
    "sharpe_ratio": 1.42
  },
  "author": {
    "nickname": "Alice",
    "avatar_url": "https://..."
  }
}
```

The serializer must not expose `code_encrypted`.

## Serialization Rules

- Add a marketplace-focused serializer on `Strategy`, for example `to_card_dict()`.
- `title` falls back to `name` if not explicitly set.
- `tags` must always serialize as a string array.
- `display_metrics` must always serialize as an object, defaulting to `{}`.
- `author` is constructed from the joined `User` row.
- No code, storage, or internal-encryption fields are included.

## Query Strategy

- Join `strategies` to `users` on `owner_id`.
- Marketplace records without a valid author should be excluded or treated as invalid data for this story, because the UI contract requires real author identity.
- The backend should normalize pagination bounds and keep response metadata consistent.
- Featured and normal list queries should share the same base visibility filter to prevent divergence.

## Frontend Architecture

- Add `frontend/src/stores/useMarketplaceStore.ts` for marketplace-only state.
- Extend `frontend/src/api/strategies.ts` to support marketplace params and the `{ data, meta }` envelope while reusing the existing shared HTTP client in `frontend/src/api/http.ts`.
- Add a dedicated page `frontend/src/views/Marketplace.vue`.
- Add the route `/marketplace` in `frontend/src/router/index.ts`.

## Frontend Components

### `FeaturedStrategyCard.vue`

- Wide editorial card for the top recommendation strip.
- Shows:
  - title
  - summary text
  - verified badge if applicable
  - author avatar and nickname
  - key display metrics
  - visual CTA button with no click behavior in this story

### `StrategyCard.vue`

- Standard marketplace grid card.
- Shows:
  - title
  - category/tags
  - verified badge if applicable
  - key display metrics summary
  - author avatar and nickname
  - visual CTA button with no click behavior in this story

### `VerifiedBadge.vue`

- Shared badge component for `is_verified`.
- Marketplace-specific blue treatment per the story notes.

## Marketplace Page Behavior

- On mount, fetch featured strategies and page 1 of normal strategies.
- Featured area is rendered only when featured results exist.
- Normal grid supports pagination controls.
- CTA buttons are presentational only and do not navigate.
- Empty list state is shown only for the normal grid area.
- Featured area remains separate from the standard grid to preserve editorial hierarchy.

## Styling Rules

- Preserve the existing application visual language instead of introducing a new design system.
- Featured strip:
  - horizontal, high-emphasis, wider cards
  - visually distinct from the normal grid
- Normal grid:
  - 3 columns on desktop
  - 2 columns on tablet
  - 1 column on mobile
- Verified badge uses the approved blue token family.
- Card surfaces stay light, structured, and finance-dashboard-like.

## Testing Strategy

### Backend

Add tests that first fail, then drive implementation for:

- only public approved strategies appear in marketplace list mode
- featured mode only returns featured public approved strategies
- featured mode returns at most six items
- pagination returns stable `meta.total`, `meta.page`, `meta.page_size`
- author `nickname` and `avatar_url` are present
- encrypted/internal fields are absent from the response

### Frontend

Add tests that first fail, then drive implementation for:

- marketplace store parses `{ data, meta }` correctly
- featured and normal list requests are loaded separately
- `Marketplace.vue` renders featured strip and normal grid from store data
- featured section is hidden when no featured strategies exist
- normal empty state renders when the list is empty
- router contains `/marketplace`
- `StrategyCard` and `FeaturedStrategyCard` render author identity and metrics

## Risks and Constraints

- The story artifact assumes schema additions that partly already exist in the repository. Implementation must add only missing columns.
- The current repository stores `tags` as JSON, not `TEXT[]`; this is a deliberate deviation from the story draft to keep the change bounded.
- There is already an older marketplace endpoint inside `strategies.py`; implementation should retire or stop using that path logic to avoid dual ownership and response-shape drift.
- Existing unrelated worktree changes must not be reverted.

## Implementation Order

1. Add failing backend tests for marketplace visibility, featured mode, pagination, author identity, and serialization.
2. Add the migration and model changes needed to satisfy the tests.
3. Add `backend/app/blueprints/marketplace.py` and register it.
4. Add failing frontend API/store/router/component tests.
5. Implement the store, API changes, new components, page, and route.
6. Run focused backend and frontend verification before any completion claim.
