# Story 6.1 + 6.2 + 6.3 Community Core Design

**Goal:** Deliver the first complete community interaction chain on top of the existing project by adding post publishing, like and collect interactions, and post comments while preserving the legacy forum stack.

## Scope

- Implement Story 6.1, Story 6.2, and Story 6.3 as one coherent delivery slice.
- Add backend persistence and APIs for:
  - publishing community posts
  - listing community posts
  - reading a single post
  - liking and collecting posts
  - listing and creating comments
- Upgrade the existing `/forum` frontend route into the new community home.
- Add a dedicated post detail page under `/forum/posts/:postId`.
- Add frontend state management, API bindings, and components for the new community flow.
- Add focused backend and frontend automated tests for the new APIs and store behavior.

## Out of Scope

- Story 6.4 user-profile pages and `/api/v1/users/:id/strategies|posts`.
- Reworking or deleting the legacy `forum.py` endpoints.
- Migrating legacy forum posts into the new community schema.
- Notification, follow, or social graph features.
- Infinite scrolling. This delivery uses a "Load More" interaction.
- Moderation or reporting workflows.

## Product Decisions

- The existing `/forum` route becomes the user-visible entry for the new community experience.
- The new backend contract lives under `/api/v1/posts*`, not `/api/forum/*`.
- A dedicated post detail page is required because comments are shown and created in the detail context.
- Pagination uses explicit "Load More" buttons on both posts and comments.
- The old forum stack remains available in code and database shape for compatibility, but the upgraded frontend route will point to the new community APIs.
- Like and collect interactions are toggles.
- Comment creation uses optimistic UI on the frontend.
- Like and collect also use optimistic UI with rollback on failure.

## Existing Constraints

- `backend/app/models.py` currently defines a legacy `Post` model backed by `posts` with old fields:
  - `title`
  - `author`
  - `avatar`
  - `likes`
  - `comments`
  - `timestamp`
  - `tags`
  - `user_id`
- `backend/app/blueprints/forum.py` still depends on the legacy `Post`, `Comment`, `Like`, and `Favorite` models and must not be broken.
- `frontend/src/views/ForumView.vue` is currently just a placeholder page.
- `frontend/src/stores/forum.ts` and `frontend/src/api/forum.ts` still target the legacy forum contract.
- `Strategy.is_public` already exists in the current model, so optional strategy linkage for posts can reuse it without adding another strategy visibility field.
- User public-profile APIs already exist in `backend/app/blueprints/users.py`; this design does not change them.

## Architecture Summary

- Keep the legacy forum implementation intact.
- Extend the existing `posts` table with new nullable community fields instead of replacing the table.
- Add two new tables:
  - `post_interactions`
  - `post_comments`
- Add a new `backend/app/blueprints/community.py` blueprint registered under `/api/v1`.
- Create a new frontend community state layer rather than reusing the old forum store.
- Reuse the `/forum` route as the new community home and add `/forum/posts/:postId` for detail.

## Data Model Design

### `Post`

Preserve all legacy fields and add the community-specific fields below:

- `content: Text | nullable`
- `strategy_id: String | nullable | foreign key to strategies.id`
- `likes_count: Integer | not null default 0`
- `comments_count: Integer | not null default 0`
- `created_at: DateTime(timezone=True) | nullable`

Design rules:

- The new fields are additive only.
- Legacy rows may have `content = NULL` and `created_at = NULL`.
- New community code only reads and writes the new fields for community behavior.
- Legacy `forum.py` continues to use the old fields.

### `PostInteraction`

Add a new model backed by `post_interactions`:

- `id`
- `user_id`
- `post_id`
- `type`
- `created_at`

Constraints:

- `UNIQUE(user_id, post_id, type)`
- index on `user_id`
- index on `post_id`

Allowed values:

- `like`
- `collect`

### `PostComment`

Add a new model backed by `post_comments`:

- `id`
- `post_id`
- `user_id`
- `content`
- `created_at`

Constraints:

- index on `post_id`
- index on `created_at`

This table is separate from the legacy `comments` table and does not replace it.

## Migration Plan

Create three new migrations in this order:

1. Extend `posts`
   - add `content`
   - add `strategy_id`
   - add `likes_count`
   - add `comments_count`
   - add `created_at`
   - add indexes for `created_at` and `user_id`
2. Create `post_interactions`
3. Create `post_comments`

Migration rules:

- Do not drop or rename legacy `posts` columns.
- Do not modify or drop legacy `likes`, `favorites`, or `comments` tables.
- `content` and `created_at` must remain nullable for backward compatibility with old rows.

## Backend API Design

Create a new blueprint at `backend/app/blueprints/community.py` and register it in `backend/app/__init__.py`.

### `POST /api/v1/posts`

Authenticated endpoint used by the composer.

Request:

```json
{
  "content": "This strategy performed well in a volatile market...",
  "strategy_id": "optional-strategy-id"
}
```

Validation rules:

- authentication required
- `content` required after trim
- `content` length must be `<= 2000`
- `strategy_id` optional
- if `strategy_id` is provided, the strategy must exist

Behavior:

- create a `Post` using only the new community fields
- initialize `likes_count = 0`
- initialize `comments_count = 0`
- set `created_at = now_utc()`
- return Beijing time via `format_beijing_iso`

Success response shape:

```json
{
  "data": {
    "id": "post-id",
    "content": "This strategy performed well in a volatile market...",
    "user_id": "user-id",
    "strategy_id": null,
    "likes_count": 0,
    "comments_count": 0,
    "created_at": "2026-03-20T12:00:00+08:00",
    "author": {
      "nickname": "nickname",
      "avatar_url": ""
    },
    "strategy": null,
    "liked": false,
    "collected": false
  }
}
```

### `GET /api/v1/posts`

Public paginated feed endpoint.

Supported query params:

- `page`
- `per_page`

Behavior:

- only return community posts where `content IS NOT NULL`
- order by `created_at DESC`, then deterministic tie-breaker if needed
- include author info
- include linked strategy summary when `strategy_id` exists
- when the requester is authenticated, also include `liked` and `collected`

Success response shape:

```json
{
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "per_page": 20
  }
}
```

### `GET /api/v1/posts/<post_id>`

Public single-post endpoint used by the detail page.

Behavior:

- return 404 when the target post does not exist or is not a community post
- include the same payload shape as feed items but with full content
- include `liked` and `collected` when the requester is authenticated

This endpoint is added intentionally even though Story 6.1 does not list it explicitly, because the accepted frontend flow uses a dedicated detail page for comments.

### `POST /api/v1/posts/<post_id>/like`

Authenticated toggle endpoint.

Behavior:

- return 404 when the post does not exist or is not a community post
- insert `PostInteraction(type='like')` when absent
- delete it when present
- update `Post.likes_count` atomically in SQLAlchemy query form
- never write to legacy `Post.likes`

Success response:

```json
{
  "data": {
    "liked": true,
    "likes_count": 15
  }
}
```

### `POST /api/v1/posts/<post_id>/collect`

Authenticated toggle endpoint.

Behavior:

- return 404 when the post does not exist or is not a community post
- insert or delete `PostInteraction(type='collect')`
- return the current collected state

Success response:

```json
{
  "data": {
    "collected": true
  }
}
```

### `GET /api/v1/posts/<post_id>/comments`

Public paginated comments endpoint.

Supported query params:

- `page`
- `per_page`

Behavior:

- return 404 when the post does not exist or is not a community post
- order comments by `created_at ASC`
- include comment author info

### `POST /api/v1/posts/<post_id>/comments`

Authenticated create-comment endpoint.

Request:

```json
{
  "content": "Great approach."
}
```

Validation rules:

- authentication required
- trimmed content required
- content length must be `<= 500`

Behavior:

- return 404 when the post does not exist or is not a community post
- insert `PostComment`
- update `Post.comments_count` atomically
- return Beijing time and author info

## Shared Backend Helpers

The new blueprint should centralize a few shared helpers:

- fetch a community post or return 404
- serialize a strategy summary for a linked strategy
- serialize author info
- compute current-user liked and collected state efficiently
- normalize pagination inputs

The blueprint should avoid N+1 patterns where practical by batching user and interaction lookups for feed pages.

## Backend Error Handling

- `401` for unauthenticated create, like, collect, and comment-create calls
- `404` for missing or non-community posts
- `404` for missing linked strategy on create
- `422` for empty or too-long content
- all success responses use `ok(...)`
- error responses use the project's existing `error_response(...)` conventions

## Frontend Architecture

### Routes

Keep the existing route path and replace the page implementation:

- `/forum` -> community home
- `/forum/posts/:postId` -> post detail

This avoids exposing two different community entry points at the same time.

### State Layer

Create a dedicated store at `frontend/src/stores/useCommunityStore.ts`.

State shape should include:

- `posts`
- `postsTotal`
- `currentPage`
- `hasMorePosts`
- `postDetailById`
- `likedPostIds`
- `collectedPostIds`
- `commentsByPostId`
- `commentTotalsByPostId`
- `commentPagesByPostId`
- `loadingFeed`
- `loadingPostDetail`
- `submittingPost`
- `submittingComment`
- `togglingPostIds`
- `error`

Rationale:

- the legacy `forum` store is incompatible with the new data contract
- the detail page requires per-post comment caches
- like and collect optimistic updates need local state that is independent from server refresh cycles

### API Layer

Add `frontend/src/api/community.ts` with functions for:

- `createPost`
- `getPosts`
- `getPostDetail`
- `likePost`
- `collectPost`
- `getComments`
- `createComment`

### Type Layer

Split or extend the current post types so the new community types do not corrupt the legacy forum contract.

Recommended new types:

- `CommunityPostAuthor`
- `CommunityPostStrategy`
- `CommunityPost`
- `CommunityComment`
- `PaginatedCommunityPosts`
- `PaginatedCommunityComments`

This design deliberately avoids mutating the legacy `frontend/src/types/Post.ts` in place if that would break existing consumers.

## Frontend UI Design

### `ForumView.vue`

Upgrade the page into the community home:

- top section: page title and brief intro
- composer shown only for authenticated users
- feed list rendered with `PostCard`
- explicit "Load More" button under the list
- empty state for no posts
- loading and request-failure states

### `PostComposer.vue`

Responsibilities:

- multiline textarea for post content
- 2000-character counter
- optional strategy selector populated from the user's strategies
- publish button disabled for invalid state
- clear the form on success

### `PostCard.vue`

Responsibilities:

- author avatar and nickname
- Beijing-time publish timestamp
- post content
- optional strategy card preview
- like button with count
- collect button
- comment count
- click-through entry to the detail page

Behavior:

- like and collect buttons trigger store actions
- button state reflects `liked` and `collected`
- detail navigation should be possible without accidentally breaking the like and collect buttons

### `PostDetailView.vue`

Responsibilities:

- fetch a single post by route param
- render full post content
- host `CommentSection`
- handle missing-post state

### `CommentSection.vue`

Responsibilities:

- render comment list in ascending time order
- render a textarea and send button for authenticated users
- keep the input hidden or disabled for anonymous users
- support "Load More" for comments
- optimistically append new comments and replace temporary items after success

## Optimistic Update Rules

### Like

- update `likedPostIds` immediately
- update the local post's `likes_count` immediately
- call the API
- reconcile with server truth on success
- rollback local state on failure

### Collect

- update `collectedPostIds` immediately
- call the API
- rollback on failure

### Comment

- append a temporary comment object to the target post comment list
- increment the target post's `comments_count`
- replace temporary comment with the server response on success
- remove temporary comment and rollback count on failure

## Testing Strategy

### Backend

Create `backend/tests/test_community.py` and cover:

- create post success with and without `strategy_id`
- create post rejects unauthenticated calls
- create post rejects empty content
- create post rejects content longer than 2000
- create post rejects unknown strategy
- feed returns newest-first ordering and pagination metadata
- feed excludes legacy rows where `content IS NULL`
- post detail returns a single post and 404 for missing targets
- like toggles on and off correctly
- collect toggles on and off correctly
- like and collect return 404 for missing post
- comments list returns ascending ordering and pagination metadata
- create comment succeeds
- create comment rejects unauthenticated calls
- create comment rejects empty content
- create comment rejects content longer than 500
- create comment returns 404 for missing post

### Frontend

Create or extend:

- `frontend/src/api/community.test.ts`
- `frontend/src/stores/useCommunityStore.test.ts`

Cover:

- API request mapping for all community endpoints
- store feed fetch and page append behavior
- store detail fetch behavior
- optimistic like success and rollback
- optimistic collect success and rollback
- optimistic comment append, replace, and rollback
- create-post success inserts the new post at the top of the feed

Component-level tests are optional for this slice if store and API coverage already pins down the critical behavior, but route and rendering smoke coverage for the new views should be added when practical.

## Risks And Mitigations

- Risk: mixing legacy and new post fields causes accidental regressions.
  - Mitigation: keep community serialization helpers explicit and never write to legacy counters.
- Risk: frontend type collisions between old forum and new community models.
  - Mitigation: introduce new community-specific types and store instead of mutating the old forum store in place.
- Risk: count drift under concurrent like or comment activity.
  - Mitigation: use atomic SQLAlchemy update expressions, not Python object increment only.
- Risk: detail page has no stable contract if only the list endpoint exists.
  - Mitigation: add `GET /api/v1/posts/<post_id>` as a first-class endpoint.
- Risk: strategy linkage exposes private strategies incorrectly.
  - Mitigation: validate existence only for create in this slice and serialize only safe summary fields in post responses.

## Implementation Order

1. Add backend tests for the community post creation and listing contract.
2. Add the `posts` additive migration and extend the `Post` model.
3. Implement `community.py` post create, feed list, and detail endpoints.
4. Add backend tests for like, collect, and comments.
5. Add `post_interactions` and `post_comments` migrations plus new models.
6. Implement like, collect, comment-list, and comment-create endpoints.
7. Add frontend community API tests and store tests.
8. Implement new community types, API bindings, and `useCommunityStore`.
9. Replace `ForumView.vue` with the new community home and add `PostComposer.vue` and `PostCard.vue`.
10. Add `PostDetailView.vue` and `CommentSection.vue`.
11. Run focused backend and frontend verification.

## Acceptance Mapping

- Story 6.1 is satisfied by the additive `Post` schema, `POST /api/v1/posts`, `GET /api/v1/posts`, the feed composer, and the feed card rendering.
- Story 6.2 is satisfied by `post_interactions`, toggle endpoints, optimistic like and collect behavior, and optional collections-ready internal state.
- Story 6.3 is satisfied by `post_comments`, detail-page comments, optimistic comment creation, and comment pagination.

## Deferred Follow-Up

- Story 6.4 can later consume the new `Post.content`, `likes_count`, `comments_count`, and `created_at` fields through new user-resource endpoints without reopening the core community design.
