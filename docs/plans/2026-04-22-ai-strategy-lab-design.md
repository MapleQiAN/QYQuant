# AI Strategy Lab Design

## Background

AI strategy generation is the core differentiator of QYQuant, but the current flow presents it as a large card plus modal inside `NewStrategyView.vue`. That structure works for an auxiliary feature, but it underplays a product-defining workflow.

The redesign should promote AI strategy generation into a dedicated professional workspace: users describe strategy intent, AI turns it into a verifiable draft, and the product makes validation, risk constraints, and adoption visibly trustworthy.

## Goals

- Make AI strategy generation feel like the primary product workflow, not a secondary modal.
- Preserve the existing generation backend contract first, especially `generateAiStrategyDraft({ integrationId, messages })`.
- Make generated drafts auditable before adoption.
- Support professional quant users with dense, scannable controls instead of a generic chatbot layout.
- Keep the current import, preview, and confirmation flow reusable.

## Non-Goals

- Do not redesign the AI backend protocol in the first pass.
- Do not replace the existing strategy preview and import confirmation pages.
- Do not add real-time backtest execution inside the AI Lab initially.
- Do not create a marketing-style landing page for AI generation.

## Recommended Approach

Create a dedicated route:

```text
/strategies/ai-lab
```

`/strategies/new` keeps the existing creation choices, but the AI card navigates to the AI Lab instead of opening an in-page modal. Template, import, and manual editor entries remain available as secondary creation paths.

This approach gives the core workflow enough space for structured intent capture, AI collaboration, verification, and draft adoption.

## Information Architecture

```text
AI Strategy Lab
├─ Header
│  ├─ Back action
│  ├─ AI connection status
│  ├─ Generation stage state
│  └─ Primary action
├─ Strategy Brief Panel
│  ├─ Mode switch
│  ├─ Market and symbol
│  ├─ Timeframe and frequency
│  ├─ Strategy style
│  ├─ Direction
│  ├─ Risk constraints
│  └─ Free-form constraints
├─ AI Research Console
│  ├─ Stage rail
│  ├─ Research log / conversation
│  ├─ Quick refine actions
│  └─ Prompt composer
└─ Verified Draft Panel
   ├─ Draft summary
   ├─ Rule breakdown
   ├─ Parameter table
   ├─ Validation checklist
   ├─ Risk warnings
   └─ Adopt / preview actions
```

## Layout

Desktop layout uses three columns:

- Left: `300-340px` fixed width for structured strategy brief.
- Center: flexible main area for AI research console.
- Right: `360-420px` fixed width for draft verification.

Mobile layout uses tabs:

```text
Brief | Console | Draft
```

The mobile experience should keep one primary action visible at a time and avoid forcing users through a three-column squeeze.

## Component Plan

```text
AiStrategyLabView.vue
├─ AiLabHeader.vue
├─ GenerationStageRail.vue
├─ StrategyBriefPanel.vue
│  ├─ StrategyModeSwitch.vue
│  ├─ MarketUniversePicker.vue
│  ├─ StrategyStyleSelector.vue
│  ├─ RiskConstraintForm.vue
│  └─ BriefQualityMeter.vue
├─ AiResearchConsole.vue
│  ├─ AiConversationList.vue
│  ├─ AiSuggestionBar.vue
│  ├─ QuickRefineChips.vue
│  └─ AiPromptComposer.vue
└─ VerifiedDraftPanel.vue
   ├─ DraftSummaryCard.vue
   ├─ DraftRuleTabs.vue
   ├─ DraftParameterTable.vue
   ├─ DraftValidationChecklist.vue
   └─ DraftActionFooter.vue
```

Existing components to reuse or upgrade:

- `StrategyModeSwitch.vue`
- `AiSuggestionBar.vue`
- `StrategyReportCard.vue` where metadata rendering overlaps with the draft panel

## State Model

```ts
type GenerationStage = 'brief' | 'clarify' | 'design' | 'validate' | 'package'

interface StrategyBriefState {
  mode: 'guided' | 'mixed' | 'expert'
  market: string
  symbol: string
  timeframe: string
  strategyStyle: string
  direction: string
  riskLimits: {
    maxDrawdownPct?: number
    maxSingleLossPct?: number
    positionRatio?: number
    consecutiveLossPatience?: number
  }
  constraints: string[]
  notes: string
}

interface AiLabState {
  stage: GenerationStage
  loading: boolean
  error: string | null
  messages: AiStrategyMessage[]
  latestDraft: AiStrategyDraftResult | null
  selectedIntegrationId: string
}
```

In the first implementation pass, `StrategyBriefState` is compiled into a user message and sent through the existing `generateAiStrategyDraft` API. This avoids backend churn while still creating a more professional frontend workflow.

## Data Flow

1. User opens `/strategies/ai-lab`.
2. Frontend loads saved AI integrations through the existing integration store.
3. If no AI integration exists, the lab shows a blocked state and routes the user to Settings.
4. User completes the Strategy Brief panel or writes directly into the console.
5. Frontend compiles the structured brief into a natural-language user message.
6. Frontend calls `generateAiStrategyDraft({ integrationId, messages })`.
7. AI response is appended to the research console.
8. `latestDraft.analysis` and `latestDraft.metadata` populate the Verified Draft panel.
9. User applies quick refinements, which append new messages and regenerate the draft.
10. When validation passes or warnings are accepted, user adopts the draft.
11. Adoption routes into the existing strategy preview flow.

## Generation Stages

```text
Brief     User intent collected
Clarify   Missing inputs requested
Design    Strategy logic generated
Validate  Entrypoint, parameters, and risks checked
Package   Draft ready for preview/import
```

The stage rail should always explain where the workflow is blocked. A blocked or warning state should appear in the draft panel and the header action.

## Visual Direction

The interface should feel like a professional quant research terminal with an AI assistant built into it.

Use the current QYQuant design language, but tune it toward software-workbench density:

- Warm gray background and white surfaces.
- Black hard borders, but lighter than the current heavy marketing cards where possible.
- Gold for generative actions.
- Blue for system validation and model status.
- Red / green for market and risk semantics, respecting existing market-style tokens.
- Mono typography for parameters, numeric thresholds, and validation details.
- Card radius around `8px` for the lab surface and panels.
- No generic purple AI gradients.
- No decorative orb backgrounds.

The memorable product signal should be the right-side "Verified Draft" panel: users see the strategy become auditable as AI generates it.

## Interaction Details

### Strategy Brief Panel

The left panel should encourage structured inputs without making the flow feel like a long form.

Recommended controls:

- Segmented control for mode.
- Selects for market, symbol, timeframe, and strategy style.
- Toggle or segmented control for direction.
- Numeric inputs for risk thresholds.
- Chips for constraints.
- Textarea for custom thesis or extra rules.

The panel should show a brief quality indicator:

```text
Incomplete -> Enough for draft -> Strong brief
```

### AI Research Console

The center panel should look like a research log, not a consumer chatbot.

Each assistant response should support:

- Short headline
- Generated or requested action
- Key assumptions
- Blocking questions if any
- Link to affected draft section when available

Quick refine chips should be context-specific:

- Lower drawdown
- Add stop loss
- Reduce trade frequency
- Use daily timeframe
- Make logic explainable
- Tighten parameter bounds

### Verified Draft Panel

The right panel should be the trust layer.

Sections:

- Summary: name, symbol, timeframe, risk level, style.
- Rules: entry, exit, risk, sizing.
- Parameters: key, label, default, range if available.
- Validation: entrypoint, parameters, warnings, errors.
- Actions: adopt draft, continue refining, open preview.

Validation states:

```text
pass   Adopt allowed
warn   Adopt allowed with warning copy
block  Adopt disabled
```

## Error Handling

- No AI integration: show setup-required state and a Settings action.
- Generation timeout: keep brief and messages, offer retry.
- Backend error: show normalized message in console and keep previous draft if one exists.
- Missing strategy details: move stage to `clarify`; AI asks for the smallest missing set.
- Validation warning: allow adoption but label action as warning-aware.
- Validation error: disable adoption and list the exact blocking item.

## Accessibility

- All panel controls must have visible labels.
- Stage state must not rely on color alone.
- Keyboard focus should move predictably across left, center, and right regions.
- Mobile tabs must preserve headings and primary action labels.
- Text must not scale with viewport width.

## Testing Plan

Frontend tests should cover:

- `/strategies/new` AI card routes to `/strategies/ai-lab`.
- AI Lab blocks generation when no AI integration exists.
- Structured brief compiles into the expected message payload.
- Successful generation renders assistant message and Verified Draft content.
- Validation errors disable adoption.
- Validation warnings keep adoption available with warning copy.
- Adopting a draft routes to existing strategy preview flow.
- Mobile tab labels render and switch panels.

## Implementation Order

1. Add `AiStrategyLabView.vue` with static three-panel layout.
2. Add route and update `NewStrategyView.vue` AI card navigation.
3. Extract existing AI modal state and generation logic into the new view.
4. Build `StrategyBriefPanel.vue` and compile brief to messages.
5. Build `VerifiedDraftPanel.vue` from existing draft metadata and analysis.
6. Add validation state handling for `pass`, `warn`, and `block`.
7. Add responsive tabs for mobile.
8. Add focused tests for route, generation, draft rendering, and adoption.

## Open Questions

- Should AI Lab become the default route for "New Strategy", with template/import/manual as secondary tabs?
- Should expert mode expose raw prompt editing earlier than guided mode?
- Should quick refine actions be localized in i18n now or introduced as local component constants first?
- Should the lab store in-progress brief/messages in local storage to survive accidental navigation?

