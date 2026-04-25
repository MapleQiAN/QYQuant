# AI Strategy End-to-End Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken AI strategy pipeline so users can generate → preview → edit code → save → backtest in one seamless flow.

**Architecture:** Add a backend endpoint to fetch draft source code, modify confirm to accept code edits, replace the read-only code preview with Monaco editor in StrategyPreviewView, fix navigation bugs, and wire AI suggestion actions.

**Tech Stack:** Python/Flask (backend), Vue 3 + TypeScript + Monaco Editor (frontend), Vitest + pytest (tests)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/app/blueprints/strategies.py` | Modify | Add `GET /v1/strategy-imports/{id}/code` endpoint |
| `backend/app/services/strategy_import_confirm.py` | Modify | Accept optional `codeOverride`, validate, write to source file |
| `frontend/src/api/strategies.ts` | Modify | Add `fetchDraftCode()`, update confirm payload type |
| `frontend/src/types/Strategy.ts` | Modify | Add `codeOverride` to `StrategyImportConfirmPayload` |
| `frontend/src/views/StrategyPreviewView.vue` | Modify | Fix code fetching, backRoute, add Monaco editor, wire suggestions |
| `frontend/src/api/strategies.test.ts` | Modify | Add test for `fetchDraftCode` |
| `backend/tests/test_strategies.py` | Modify | Add tests for draft code endpoint + code override confirm |

---

### Task 1: Backend — Add draft code endpoint

**Files:**
- Modify: `backend/app/blueprints/strategies.py:186-222`
- Test: `backend/tests/test_strategies.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_strategies.py`:

```python
def test_fetch_draft_code_returns_source_for_python_file(client, app):
    token, user_id = _login_user(client, phone="13800138041", nickname="CodeFetchUser")
    source = "class Strategy:\n    def on_bar(self, ctx, bar):\n        return []\n"

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(source.encode("utf-8")), "my_strategy.py")},
        content_type="multipart/form-data",
    )
    assert analyze_response.status_code == 200
    draft_id = analyze_response.json["data"]["draftImportId"]

    response = client.get(
        f"/api/v1/strategy-imports/{draft_id}/code",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json["data"]
    assert data["code"] == source
    assert data["filename"] == "my_strategy.py"


def test_fetch_draft_code_returns_404_for_missing_draft(client):
    token, _ = _login_user(client, phone="13800138042", nickname="CodeFetchMissing")
    response = client.get(
        "/api/v1/strategy-imports/nonexistent-draft-id/code",
        headers=_auth_headers(token),
    )
    assert response.status_code == 404


def test_fetch_draft_code_rejects_other_users_draft(client, app):
    token_a, _ = _login_user(client, phone="13800138043", nickname="CodeOwnerA")
    source = "def on_bar(ctx, bar): return []"

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token_a),
        data={"file": (io.BytesIO(source.encode("utf-8")), "test.py")},
        content_type="multipart/form-data",
    )
    draft_id = analyze_response.json["data"]["draftImportId"]

    token_b, _ = _login_user(client, phone="13800138044", nickname="CodeOwnerB")
    response = client.get(
        f"/api/v1/strategy-imports/{draft_id}/code",
        headers=_auth_headers(token_b),
    )
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_strategies.py::test_fetch_draft_code_returns_source_for_python_file tests/test_strategies.py::test_fetch_draft_code_returns_404_for_missing_draft tests/test_strategies.py::test_fetch_draft_code_rejects_other_users_draft -v`
Expected: 3 FAILED — endpoint returns 404 (not registered yet)

- [ ] **Step 3: Implement the endpoint**

Add to `backend/app/blueprints/strategies.py`, before the `@bp.post("/v1/strategy-imports/analyze")` block (around line 186).

> Note: `_resolve_source_and_manifest` is already imported at line 36 of this file.

```python
@bp.get("/v1/strategy-imports/<draft_import_id>/code")
@jwt_required()
def fetch_draft_code_v1(draft_import_id):
    user_id = get_jwt_identity()
    draft = db.session.get(StrategyImportDraft, draft_import_id)
    if draft is None or draft.owner_id != user_id:
        return error_response("DRAFT_NOT_FOUND", "Import draft not found", 404)

    source_file = db.session.get(File, draft.source_file_id)
    if source_file is None or not source_file.path:
        return error_response("SOURCE_NOT_FOUND", "Source file not found", 404)

    raw_payload = Path(source_file.path).read_bytes()

    # For python_file drafts, selected_path is ignored by _resolve_source_and_manifest.
    # For archive drafts, use the first entrypoint candidate path if available.
    selected_path = "src/strategy.py"
    entrypoint_candidates = []
    if isinstance(draft.analysis_payload, dict):
        entrypoint_candidates = draft.analysis_payload.get("entrypointCandidates") or []
    if entrypoint_candidates:
        selected_path = entrypoint_candidates[0].get("path", selected_path)

    try:
        source_text, _ = _resolve_source_and_manifest(
            raw_payload, draft.source_type, selected_path,
        )
    except StrategyImportConfirmError:
        return error_response("SOURCE_READ_ERROR", "Could not read strategy source", 422)

    return ok({"code": source_text, "filename": source_file.filename})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_strategies.py::test_fetch_draft_code_returns_source_for_python_file tests/test_strategies.py::test_fetch_draft_code_returns_404_for_missing_draft tests/test_strategies.py::test_fetch_draft_code_rejects_other_users_draft -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/blueprints/strategies.py backend/tests/test_strategies.py
git commit -m "feat: add GET /v1/strategy-imports/{id}/code endpoint"
```

---

### Task 2: Backend — Accept code override on confirm

**Files:**
- Modify: `backend/app/services/strategy_import_confirm.py:30-126`
- Modify: `backend/app/blueprints/strategies.py:203-222`
- Test: `backend/tests/test_strategies.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_strategies.py`:

```python
def test_confirm_strategy_import_with_code_override(client, app):
    token, user_id = _login_user(client, phone="13800138045", nickname="CodeOverrideUser")
    source = "def on_bar(ctx, bar):\n    return []\n"

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(source.encode("utf-8")), "override.py")},
        content_type="multipart/form-data",
    )
    draft_id = analyze_response.json["data"]["draftImportId"]

    override_code = "def on_bar(ctx, bar):\n    # modified\n    return []\n"
    response = client.post(
        "/api/v1/strategy-imports/confirm",
        headers=_auth_headers(token),
        json={
            "draftImportId": draft_id,
            "selectedEntrypoint": {
                "path": "override.py",
                "callable": "on_bar",
                "interface": "event_v1",
            },
            "metadata": {"name": "Override Test", "symbol": "BTCUSDT"},
            "codeOverride": override_code,
        },
    )
    assert response.status_code == 200
    strategy_id = response.json["data"]["strategy"]["id"]

    with app.app_context():
        strategy = db.session.get(Strategy, strategy_id)
        built_file = db.session.get(File, strategy.built_package_file_id)
        with zipfile.ZipFile(built_file.path, "r") as archive:
            saved_code = archive.read("src/strategy.py").decode("utf-8")
        assert override_code in saved_code


def test_confirm_strategy_import_rejects_invalid_syntax_override(client, app):
    token, _ = _login_user(client, phone="13800138046", nickname="BadSyntaxUser")
    source = "def on_bar(ctx, bar):\n    return []\n"

    analyze_response = client.post(
        "/api/v1/strategy-imports/analyze",
        headers=_auth_headers(token),
        data={"file": (io.BytesIO(source.encode("utf-8")), "badsyntax.py")},
        content_type="multipart/form-data",
    )
    draft_id = analyze_response.json["data"]["draftImportId"]

    response = client.post(
        "/api/v1/strategy-imports/confirm",
        headers=_auth_headers(token),
        json={
            "draftImportId": draft_id,
            "selectedEntrypoint": {
                "path": "badsyntax.py",
                "callable": "on_bar",
                "interface": "event_v1",
            },
            "metadata": {"name": "Bad Syntax", "symbol": "BTCUSDT"},
            "codeOverride": "def on_bar(ctx, bar):\n this is not valid python {{{",
        },
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_strategies.py::test_confirm_strategy_import_with_code_override tests/test_strategies.py::test_confirm_strategy_import_rejects_invalid_syntax_override -v`
Expected: FAIL

- [ ] **Step 3: Implement code override**

In `backend/app/services/strategy_import_confirm.py`, **insert** the code override block between lines 66 and 68 (after `_resolve_source_and_manifest` returns `source_text, base_manifest`, and before `_build_manifest` is called). Do NOT remove lines 68-81 — those remain unchanged.

Insert this block between the `_resolve_source_and_manifest` call and the `_build_manifest` call:

```python
        # Apply code override if provided
        code_override = payload.get("codeOverride")
        if code_override is not None:
            if not isinstance(code_override, str) or not code_override.strip():
                raise StrategyImportConfirmError(
                    "INVALID_CODE_OVERRIDE", "Code override must be non-empty string", 400
                )
            try:
                compile(code_override, "<code-override>", "exec")
            except SyntaxError as exc:
                raise StrategyImportConfirmError(
                    "CODE_OVERRIDE_SYNTAX_ERROR",
                    f"Code override has syntax error: {exc.msg}",
                    422,
                    details={"line": exc.lineno, "msg": exc.msg},
                ) from exc
            source_text = code_override
```

After insertion, the sequence in the `try` block should read: `raw_payload → _resolve_source_and_manifest → [new override block] → _build_manifest → _validate_manifest → write files → build package`. Lines 77-126 (file writes, build, cleanup) remain untouched.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_strategies.py::test_confirm_strategy_import_with_code_override tests/test_strategies.py::test_confirm_strategy_import_rejects_invalid_syntax_override -v`
Expected: 2 PASSED

- [ ] **Step 5: Run full strategy test suite to ensure no regressions**

Run: `cd backend && python -m pytest tests/test_strategies.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/strategy_import_confirm.py backend/tests/test_strategies.py
git commit -m "feat: accept codeOverride on strategy import confirm with syntax validation"
```

---

### Task 3: Frontend — Add API function and update types

**Files:**
- Modify: `frontend/src/types/Strategy.ts:80-96`
- Modify: `frontend/src/api/strategies.ts:392-409`
- Test: `frontend/src/api/strategies.test.ts`

- [ ] **Step 1: Write the failing test**

Add to `frontend/src/api/strategies.test.ts`:

```ts
it('calls fetchDraftCode endpoint', async () => {
  requestMock.mockResolvedValueOnce({ code: 'def on_bar(): pass', filename: 'strategy.py' })
  const result = await strategies.fetchDraftCode('draft-123')
  expect(result).toEqual({ code: 'def on_bar(): pass', filename: 'strategy.py' })
  expect(requestMock).toHaveBeenCalledWith({
    method: 'get',
    url: '/v1/strategy-imports/draft-123/code',
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/api/strategies.test.ts`
Expected: FAIL — `fetchDraftCode` is not exported

- [ ] **Step 3: Add type + API function**

In `frontend/src/types/Strategy.ts`, update `StrategyImportConfirmPayload` (line 80-96), add `codeOverride`:

```ts
export interface StrategyImportConfirmPayload {
  draftImportId: string
  selectedEntrypoint: {
    path: string
    callable: string
    interface?: string
  }
  metadata: {
    name: string
    description?: string
    category?: string
    tags?: string[]
    symbol?: string
    version?: string
  }
  parameterDefinitions?: StrategyParameter[]
  codeOverride?: string
}
```

In `frontend/src/api/strategies.ts`, add after `confirmStrategyImport` (around line 409):

```ts
export function fetchDraftCode(draftImportId: string): Promise<{ code: string; filename: string }> {
  return client.request({
    method: 'get',
    url: `/v1/strategy-imports/${draftImportId}/code`,
  })
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/api/strategies.test.ts`
Expected: PASS (including new test)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/Strategy.ts frontend/src/api/strategies.ts frontend/src/api/strategies.test.ts
git commit -m "feat: add fetchDraftCode API and codeOverride type"
```

---

### Task 4: Frontend — Fix StrategyPreviewView (backRoute + code fetching + Monaco editor + suggestions)

**Files:**
- Modify: `frontend/src/views/StrategyPreviewView.vue`

This is the largest task. Five changes in one file, tested together.

> **Order matters:** Steps 2-4 are tightly coupled (template imports, computed refs, and Monaco init must be consistent). Apply them as a batch.

- [ ] **Step 1: Fix backRoute (line 215-219)**

Change:
```ts
const backRoute = computed(() => {
  if (source === 'ai') return '/strategies/new'
  if (source === 'template') return '/strategies/new'
  return '/strategies/import'
})
```
To:
```ts
const backRoute = computed(() => {
  if (source === 'ai') return '/strategies/ai-lab'
  if (source === 'template') return '/strategies/new'
  return '/strategies/import'
})
```

- [ ] **Step 2: Update imports**

Replace the import line:
```ts
import { computed, h, ref } from 'vue'
```
With:
```ts
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
```

Replace:
```ts
import { confirmStrategyImport, exportStrategy } from '../api/strategies'
```
With:
```ts
import { confirmStrategyImport, exportStrategy, fetchDraftCode } from '../api/strategies'
```

Remove the now-unused import (line 164):
```ts
import StrategyCodePreview from '../components/strategy/StrategyCodePreview.vue'
```
(Delete this line entirely — the template no longer uses `<StrategyCodePreview>`.)

- [ ] **Step 3: Replace strategyCode computed + add code fetching + Monaco editor**

Replace the broken `strategyCode` computed block (lines 209-213) with this complete block. This combines code fetching, Monaco init, and cleanup in one step:

```ts
const rawCode = ref('')
const codeLoading = ref(false)
const codeError = ref('')
const editedCode = ref('')
const codeDirty = ref(false)
const editorContainer = ref<HTMLElement | null>(null)
let editor: any = null

async function initEditor() {
  if (!editorContainer.value || !rawCode.value) return
  const monaco = await import('monaco-editor')
  editor = monaco.editor.create(editorContainer.value, {
    value: editedCode.value,
    language: 'python',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 13,
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    automaticLayout: true,
    padding: { top: 12 },
  })
  editor.onDidChangeModelContent(() => {
    editedCode.value = editor.getValue()
    codeDirty.value = editedCode.value !== rawCode.value
  })
}

onMounted(async () => {
  if (!draftImportId) return
  codeLoading.value = true
  try {
    const result = await fetchDraftCode(draftImportId)
    rawCode.value = result.code
    editedCode.value = result.code
  } catch (err: any) {
    codeError.value = err?.message || 'Failed to load strategy code'
  } finally {
    codeLoading.value = false
    await initEditor()
  }
})

onBeforeUnmount(() => {
  editor?.dispose()
})
```

Replace the code tab template content (lines 115-117):
```html
<div v-if="activeTab === 'code'" class="tab-content">
  <StrategyCodePreview :code="strategyCode" filename="strategy.py" />
</div>
```
With:
```html
<div v-if="activeTab === 'code'" class="tab-content">
  <div v-if="codeLoading" class="code-loading">{{ $t('strategyPreview.loadingCode') }}</div>
  <div v-else-if="codeError" class="code-error">{{ codeError }}</div>
  <div v-else ref="editorContainer" class="code-editor"></div>
</div>
```

- [ ] **Step 4: Include codeOverride in save action**

Modify `handleSave` (around line 294-339). Replace the `confirmStrategyImport({...})` call block with:

```ts
    const confirmPayload: StrategyImportConfirmPayload = {
      draftImportId: analysis.value.draftImportId,
      selectedEntrypoint: {
        path: entrypoint.path,
        callable: entrypoint.callable,
        interface: entrypoint.interface || 'event_v1',
      },
      metadata: {
        name: metadata.value.name,
        description: metadata.value.description,
        category: metadata.value.category,
        symbol: metadata.value.symbol,
        tags: metadata.value.tags || [],
        version: metadata.value.version,
      },
      parameterDefinitions: mergedAnalysis.parameterCandidates as StrategyParameter[],
    }
    if (codeDirty.value) {
      confirmPayload.codeOverride = editedCode.value
    }
    const result = await confirmStrategyImport(confirmPayload)
```

Also add `StrategyImportConfirmPayload` and `StrategyParameter` to the type imports at line 162:
```ts
import type { AiStrategyMetadata, StrategyImportAnalysis, StrategyImportConfirmPayload, StrategyParameter } from '../types/Strategy'
```

- [ ] **Step 5: Wire AI suggestions to real actions**

Replace `handleApplySuggestion` (lines 341-343) with:

```ts
async function handleApplySuggestion(suggestion: string) {
  if (suggestion === t('strategyPreview.suggestTightenStop') || suggestion === t('strategyPreview.suggestRelaxStop')) {
    await router.push({ path: '/strategies/ai-lab', query: { refine: suggestion } })
  } else if (suggestion === t('strategyPreview.suggestOptimize') || suggestion === t('strategyPreview.suggestBacktest')) {
    await handleSave()
  } else {
    toast.info(t('strategyPreview.suggestionApplied', { suggestion }))
  }
}
```

- [ ] **Step 6: Add CSS for Monaco editor container**

Add to `<style scoped>`:

```css
.code-loading {
  padding: var(--spacing-xl);
  text-align: center;
  color: var(--color-text-muted);
}

.code-error {
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-danger);
}

.code-editor {
  min-height: 400px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
```

- [ ] **Step 7: Run frontend test suite for regressions**

Run: `cd frontend && npx vitest run`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add frontend/src/views/StrategyPreviewView.vue
git commit -m "feat: fix preview code display, add Monaco editor, fix backRoute, wire suggestions"
```

---

### Task 5: Frontend — Add i18n keys for new UI strings

**Files:**
- Modify: `frontend/src/i18n/messages/en.ts` (and `zh.ts` if exists)

- [ ] **Step 1: Find and add missing i18n keys**

Check what keys are referenced but might be missing. The only new key is `strategyPreview.loadingCode`.

Find the strategyPreview section in `frontend/src/i18n/messages/en.ts` and add:

```ts
loadingCode: 'Loading strategy code...',
```

If a `zh.ts` file exists, add:

```ts
loadingCode: '正在加载策略代码...',
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/i18n/
git commit -m "feat: add i18n keys for strategy preview code loading"
```

---

### Task 6: Integration verification

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && python -m pytest tests/test_strategies.py -v`
Expected: All PASS

- [ ] **Step 2: Run full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: All PASS

- [ ] **Step 3: Final commit (if any test fixes needed)**

```bash
git add -A
git commit -m "fix: resolve test failures from AI strategy flow changes"
```
