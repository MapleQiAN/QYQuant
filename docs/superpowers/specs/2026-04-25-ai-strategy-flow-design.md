# AI Strategy End-to-End Flow Fix & Enhancement

## Problem

The AI strategy generation pipeline has three broken/incomplete links:

1. **Preview page shows no code** — `strategyCode` computed always returns empty string. `StrategyImportAnalysis.fileSummary` contains only `{filename, size, entries[]}`, not the actual source code. No backend endpoint exists to fetch draft code.

2. **Back route wrong** — After preview from AI Lab, "Back" button goes to `/strategies/new` instead of `/strategies/ai-lab`.

3. **Code not editable** — Users cannot modify AI-generated code before saving. No inline editor exists in preview.

4. **AI suggestions are placeholder** — `handleApplySuggestion` shows a toast but doesn't modify code or params.

## Design

### 1. Backend: New Draft Code Endpoint

**`GET /v1/strategy-imports/{draftImportId}/code`**

- Requires JWT auth, verifies ownership
- Loads `StrategyImportDraft` → `source_file_id` → `File` → reads file from disk
- Returns `{ code: string, filename: string }`
- For `.py` files: return raw text
- For `.zip`/`.qys` archives: extract `src/strategy.py` content

### 2. Backend: Accept Code Override on Confirm

Modify `POST /v1/strategy-imports/confirm` to accept optional `codeOverride: string` field.

When present:
- Write the new code to the source file (or create a new file record)
- Re-run syntax validation
- If syntax invalid, return error with details

### 3. Frontend API Layer

Add to `frontend/src/api/strategies.ts`:

```ts
export function fetchDraftCode(draftImportId: string): Promise<{ code: string; filename: string }> {
  return client.request({
    method: 'get',
    url: `/v1/strategy-imports/${draftImportId}/code`,
  })
}
```

Update `StrategyImportConfirmPayload` to include optional `codeOverride?: string`.

### 4. Frontend: StrategyPreviewView Fixes

**4a. Fix `strategyCode` computed:**

```ts
const rawCode = ref('')
const codeLoading = ref(false)

onMounted(async () => {
  if (draftImportId) {
    codeLoading.value = true
    try {
      const result = await fetchDraftCode(draftImportId)
      rawCode.value = result.code
    } catch { /* error handled inline */ }
    finally { codeLoading.value = false }
  }
})
```

**4b. Fix backRoute:**

```ts
const backRoute = computed(() => {
  if (source === 'ai') return '/strategies/ai-lab'
  if (source === 'template') return '/strategies/new'
  return '/strategies/import'
})
```

**4c. Add Monaco editor to code tab:**

- Import Monaco editor (already used in `StrategyEditorView`)
- Code tab shows read-write Monaco instance with `rawCode` as model
- User edits tracked in `editedCode` ref
- Save action includes `codeOverride` if code was modified

**4d. Wire AI suggestions:**

Each suggestion maps to a concrete action:
- "Tighten stop loss" → navigate back to AI Lab with a refine prompt
- "Optimize params" → navigate to strategy parameters page after save
- "Run backtest" → navigate to backtest config after save

### 5. Complete User Flow

```
AI Lab (brief → generate → adopt draft)
  ↓
StrategyPreviewView (view report, edit code, adjust params)
  ↓ Save
StrategyDetailView (configure backtest)
  ↓ Run
BacktestResultView (view results)
```

## Files Changed

| File | Change |
|------|--------|
| `backend/app/blueprints/strategies.py` | Add `GET /v1/strategy-imports/{id}/code`, accept `codeOverride` in confirm |
| `backend/app/services/strategy_import_confirm.py` | Handle code override write + re-validation |
| `frontend/src/api/strategies.ts` | Add `fetchDraftCode()`, update confirm payload type |
| `frontend/src/types/Strategy.ts` | Add `codeOverride` to `StrategyImportConfirmPayload` |
| `frontend/src/views/StrategyPreviewView.vue` | Fix strategyCode, backRoute; add Monaco editor; wire suggestions |

## Out of Scope

- AI-powered code refinement in preview (future: send edited code back to AI for review)
- Version history / diff view for code edits
- Syntax error highlighting in preview (Monaco handles this natively)
