# Strategy Source Import Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a unified strategy import flow that accepts `strategy.py`, source project zips, and `.qys` packages, then normalizes them into validated QYSP artifacts before creating final strategy records.

**Architecture:** Reuse one backend import pipeline for all inputs by splitting the workflow into `analyze` and `confirm` phases. Extract reusable QYSP build and validation helpers from the CLI package, persist temporary import drafts in the backend, and replace the current frontend file-only upload with a guided confirmation flow. Keep runtime and backtests dependent on built `.qys` packages only.

**Tech Stack:** Flask, SQLAlchemy, Alembic, Marshmallow, Vue 3, Vue Router, Vitest, pytest, Click, zipfile/json/hashlib/ast.

---

### Task 1: Extract reusable QYSP build helpers

**Files:**
- Create: `packages/qysp/src/qysp/builder.py`
- Modify: `packages/qysp/src/qysp/cli/main.py`
- Modify: `packages/qysp/tests/test_cli.py`
- Create: `packages/qysp/tests/test_builder.py`

**Step 1: Write failing builder tests**
- Add tests for:
  - building a `.qys` from a normalized project directory
  - generating `integrity.files` automatically
  - rejecting missing `strategy.json` or `src/strategy.py`
- Run: `uv run pytest packages/qysp/tests/test_builder.py -q`
- Expected: FAIL because `qysp.builder` does not exist.

**Step 2: Implement shared builder helpers**
- Move directory scanning, integrity generation, and archive creation out of `qys build` into `qysp.builder`.
- Keep CLI behavior unchanged by making `qys build` call the shared helper instead of keeping its own copy of the packaging logic.

**Step 3: Verify CLI compatibility**
- Run: `uv run pytest packages/qysp/tests/test_builder.py packages/qysp/tests/test_cli.py -q`
- Expected: PASS.

### Task 2: Add backend draft import persistence

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/schemas.py`
- Create: `backend/migrations/versions/6f0c1cf637c2_add_strategy_import_drafts.py`
- Modify: `backend/tests/conftest.py`

**Step 1: Write failing persistence tests**
- Extend backend fixtures or add focused tests that expect:
  - `StrategyImportDraft` rows to persist analysis payloads
  - `Strategy` to keep references to both original source and built package files
- Run: `uv run pytest backend/tests/test_strategies.py -k import_draft -q`
- Expected: FAIL because new model fields and table are missing.

**Step 2: Implement schema and model changes**
- Add `StrategyImportDraft` with owner, source file id, source type, analysis payload, status, and expiry fields.
- Add `original_source_file_id` and `built_package_file_id` to `Strategy`.
- Add response schemas for draft analysis and confirmation payloads.

**Step 3: Add migration**
- Create the Alembic migration with forward and downgrade paths.

**Step 4: Verify persistence layer**
- Run: `uv run pytest backend/tests/test_strategies.py -k import_draft -q`
- Expected: PASS.

### Task 3: Implement backend analyze-import service and endpoint

**Files:**
- Create: `backend/app/services/strategy_import_analysis.py`
- Modify: `backend/app/services/strategy_import.py`
- Modify: `backend/app/blueprints/strategies.py`
- Modify: `backend/tests/test_strategies.py`

**Step 1: Write failing API tests**
- Add tests for `POST /api/v1/strategy-imports/analyze` covering:
  - single `strategy.py`
  - source zip with and without `strategy.json`
  - existing `.qys`
  - unsupported files or blocked layouts
- Assert that the response returns `draftImportId`, source type, entrypoint candidates, metadata candidates, parameter candidates, warnings, and errors.
- Run: `uv run pytest backend/tests/test_strategies.py -k analyze_import -q`
- Expected: FAIL because the endpoint does not exist.

**Step 2: Implement source analyzers**
- Detect input type from extension and archive contents.
- For controlled project zips, extract allowed files into a temporary workspace and ignore unsupported dependency manifests.
- For `.qys`, parse `strategy.json` and current entrypoint info directly.
- For Python source, inspect AST for likely entrypoint candidates such as `on_bar(...)` or `Strategy`.

**Step 3: Persist draft analysis**
- Save the uploaded source file and analysis payload into `StrategyImportDraft`.

**Step 4: Verify analyze flow**
- Run: `uv run pytest backend/tests/test_strategies.py -k analyze_import -q`
- Expected: PASS.

### Task 4: Implement backend confirm-import flow

**Files:**
- Create: `backend/app/services/strategy_import_confirm.py`
- Modify: `backend/app/services/strategy_import.py`
- Modify: `backend/app/blueprints/strategies.py`
- Modify: `backend/tests/test_strategies.py`

**Step 1: Write failing confirmation tests**
- Add tests for `POST /api/v1/strategy-imports/confirm` covering:
  - filling missing metadata from confirmation payload
  - resolving ambiguous entrypoint candidates
  - generating a normalized project and final `.qys`
  - storing both original and built package files
  - returning the redirect target to strategy parameters
- Run: `uv run pytest backend/tests/test_strategies.py -k confirm_import -q`
- Expected: FAIL because confirmation flow is missing.

**Step 2: Build normalized project + package generation**
- Convert the selected draft into the internal normalized layout.
- Generate or complete `strategy.json`.
- Call the shared `qysp.builder` helper to build the final `.qys`.
- Run schema and integrity validation before persistence.

**Step 3: Create final strategy records**
- Store `File`, `Strategy`, and `StrategyVersion` rows.
- Link `original_source_file_id`, `built_package_file_id`, and `storage_key`.
- Mark the draft as completed.

**Step 4: Verify confirm flow**
- Run: `uv run pytest backend/tests/test_strategies.py -k confirm_import -q`
- Expected: PASS.

### Task 5: Refactor legacy package import onto the same pipeline

**Files:**
- Modify: `backend/app/blueprints/strategies.py`
- Modify: `backend/app/services/strategy_import.py`
- Modify: `backend/tests/test_strategies.py`

**Step 1: Write regression tests**
- Add tests asserting that existing `.qys` upload endpoints still work and now reuse the draft/confirm pipeline internally.
- Run: `uv run pytest backend/tests/test_strategies.py -k legacy_import -q`
- Expected: FAIL until the refactor is in place.

**Step 2: Wire old endpoints through the new flow**
- Keep `POST /api/v1/strategies/import` as the compatibility endpoint.
- Internally route `.qys` uploads through analyze + confirm helpers without changing the external response shape more than necessary.

**Step 3: Verify import compatibility**
- Run: `uv run pytest backend/tests/test_strategies.py -k "legacy_import or import_strategy" -q`
- Expected: PASS.

### Task 6: Add frontend import draft types and API clients

**Files:**
- Modify: `frontend/src/types/Strategy.ts`
- Modify: `frontend/src/api/strategies.ts`
- Modify: `frontend/src/api/strategies.test.ts`

**Step 1: Write failing frontend API tests**
- Add tests for:
  - `analyzeStrategyImport(file)`
  - `confirmStrategyImport(payload)`
  - preserving the current `importStrategy(file)` compatibility path
- Run: `npm test -- src/api/strategies.test.ts`
- Expected: FAIL because new client methods and types do not exist.

**Step 2: Implement draft API types**
- Add types for:
  - `StrategyImportSourceType`
  - `StrategyImportDraftAnalysis`
  - `StrategyImportEntrypointCandidate`
  - `StrategyImportConfirmPayload`
- Implement the two new client methods against `/v1/strategy-imports/analyze` and `/v1/strategy-imports/confirm`.

**Step 3: Verify frontend API layer**
- Run: `npm test -- src/api/strategies.test.ts`
- Expected: PASS.

### Task 7: Build the unified frontend import wizard and confirmation page

**Files:**
- Create: `frontend/src/views/StrategyImportView.vue`
- Create: `frontend/src/views/StrategyImportConfirmView.vue`
- Create: `frontend/src/views/StrategyImportView.test.ts`
- Create: `frontend/src/views/StrategyImportConfirmView.test.ts`
- Modify: `frontend/src/views/StrategyLibraryView.vue`
- Modify: `frontend/src/views/NewStrategyView.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/router/index.test.ts`
- Modify: `frontend/src/i18n/messages/zh.ts`
- Modify: `frontend/src/i18n/messages/en.ts`

**Step 1: Write failing route and view tests**
- Add tests for:
  - import source selection
  - analyze submission
  - rendering detected entrypoint candidates and warnings
  - editing missing metadata and parameters
  - confirm redirect to the parameter page
- Run: `npm test -- src/views/StrategyImportView.test.ts src/views/StrategyImportConfirmView.test.ts src/router/index.test.ts`
- Expected: FAIL because new routes and views do not exist.

**Step 2: Implement import source selection**
- Replace the current file-only mental model with a dedicated import entry.
- Support three source choices: `strategy.py`, source zip, `.qys`.

**Step 3: Implement confirmation UI**
- Render:
  - import summary
  - entrypoint mapping
  - strategy metadata and parameter editing
  - build preview and ignored-file warnings
- Only require edits for missing or ambiguous fields.

**Step 4: Verify frontend flow**
- Run: `npm test -- src/views/StrategyImportView.test.ts src/views/StrategyImportConfirmView.test.ts src/views/StrategyLibraryView.test.ts src/router/index.test.ts`
- Expected: PASS.

### Task 8: Connect CLI import to the backend protocol

**Files:**
- Modify: `packages/qysp/src/qysp/cli/main.py`
- Modify: `packages/qysp/tests/test_cli.py`
- Modify: `docs/strategy-format/README.md`

**Step 1: Write failing CLI tests**
- Add tests that expect `qys import <path>` to:
  - upload a source directory or `.qys`
  - call analyze/confirm steps through the backend API
  - print the created strategy id or redirect path
- Run: `uv run pytest packages/qysp/tests/test_cli.py -k import -q`
- Expected: FAIL because the command is still a stub.

**Step 2: Implement CLI import**
- Replace the stub with a real flow using the same backend protocol.
- Keep existing `init`, `build`, and `validate` behavior unchanged.

**Step 3: Document the new source import workflow**
- Update the strategy format docs with:
  - supported inputs
  - controlled project restrictions
  - confirmation flow expectations

**Step 4: Verify CLI + docs**
- Run: `uv run pytest packages/qysp/tests/test_cli.py -k import -q`
- Expected: PASS.

### Task 9: Run final integration verification

**Files:**
- Modify: `backend/tests/test_strategies.py`
- Modify: `frontend/src/views/StrategyLibraryView.test.ts`

**Step 1: Add end-to-end regression coverage**
- Backend:
  - analyze `strategy.py`
  - confirm import
  - read parameters for the new strategy
- Frontend:
  - library entry to import wizard
  - confirm page redirect after successful import

**Step 2: Run full focused verification**
- Run: `uv run pytest backend/tests/test_strategies.py packages/qysp/tests/test_builder.py packages/qysp/tests/test_cli.py packages/qysp/tests/test_validator.py`
- Expected: PASS.
- Run: `npm test -- src/api/strategies.test.ts src/views/StrategyImportView.test.ts src/views/StrategyImportConfirmView.test.ts src/views/StrategyLibraryView.test.ts src/router/index.test.ts`
- Expected: PASS.

**Step 3: Commit implementation slices**
- Commit after each completed task group instead of one large final commit.

