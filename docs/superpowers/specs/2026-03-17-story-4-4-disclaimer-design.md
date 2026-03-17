# Story 4.4 Disclaimer Design

**Goal:** Add layered compliance disclaimers across the frontend with immediate rollout on the backtest result page and reusable components for later registration and simulation flows.

## Scope

- Add a centralized disclaimer content module for all four disclaimer contexts.
- Add four reusable Vue components:
  - backtest footer disclaimer
  - earnings disclaimer tooltip
  - registration agreement disclaimer
  - simulation risk acknowledgment modal
- Integrate the footer disclaimer into the backtest result page.
- Add a `showDisclaimer` extension point to the shared `StatCard` component for future strategy-detail usage.
- Cover the new behavior with focused Vitest component and view tests.

## Out of Scope

- Building or wiring a real registration page.
- Enabling the simulation disclaimer modal in `BotsView.vue`.
- Integrating the disclaimer tooltip into `StrategyDetailView.vue`.
- Adding backend APIs or persistence beyond localStorage-based MVP support inside the modal component.

## Architecture

- Disclaimer copy is stored once in `frontend/src/data/disclaimer-content.ts` as Chinese constants plus a typed lookup helper.
- Presentation stays split by responsibility:
  - `DisclaimerFooter.vue` for persistent page-level legal copy
  - `DisclaimerTooltip.vue` for inline earnings-context disclosure
  - `RegistrationDisclaimer.vue` for checkbox-style consent capture
  - `SimulationDisclaimerModal.vue` for one-time acknowledgement flows
- Existing help tooltip behavior remains separate. Disclaimer tooltip follows the same lightweight implementation style but is not coupled to metric-explanation content.
- `BacktestResultView.vue` becomes the only active integration point in this story: it renders a fixed footer disclaimer after the report content and passes `showDisclaimer` only to earnings-related stat cards.

## UX and Interaction Rules

- Footer disclaimer is always rendered in the DOM and visually sits at the bottom of the report content with subdued 12px muted text.
- Disclaimer tooltip:
  - desktop: opens on hover/focus after 300ms
  - mobile: toggles on click
  - remains implemented without third-party libraries
- Registration disclaimer exposes only consent state and links. Parent pages remain responsible for disabling submit actions.
- Simulation modal uses `Teleport` to `body`, explicit close controls, no outside-click dismissal, and a checkbox-gated confirm CTA.

## Accessibility

- Footer uses `role="contentinfo"` and `aria-label="免责声明"`.
- Tooltip uses `role="tooltip"` with `aria-describedby` linkage from the trigger button.
- Registration checkbox is label-associated and marked `aria-required="true"`.
- Simulation modal uses `role="alertdialog"`, `aria-modal="true"`, focus capture on open, and focus restoration on close.
- Interactive controls respect a minimum 44x44 hit area and visible focus outline.

## Main File Boundaries

- `frontend/src/data/disclaimer-content.ts`: disclaimer constants, type, and lookup map.
- `frontend/src/components/disclaimer/DisclaimerFooter.vue`: persistent muted footer text.
- `frontend/src/components/disclaimer/DisclaimerTooltip.vue`: delayed inline tooltip with SVG info icon.
- `frontend/src/components/disclaimer/RegistrationDisclaimer.vue`: consent checkbox and agreement links.
- `frontend/src/components/disclaimer/SimulationDisclaimerModal.vue`: reusable one-time acknowledgment modal with localStorage support.
- `frontend/src/components/StatCard.vue`: optional disclaimer trigger slot replacement via `showDisclaimer`.
- `frontend/src/views/BacktestResultView.vue`: footer integration and earnings-card prewiring.

## Testing

- Validate disclaimer constants are non-empty and type-safe.
- Verify footer renders the expected text and stays mounted.
- Verify tooltip delay, open/close behavior, and accessibility attributes.
- Verify registration checkbox v-model behavior and agreement links.
- Verify modal button gating, focus behavior, and non-dismissible overlay behavior.
- Verify the backtest result view renders the footer disclaimer and earnings-card disclaimer triggers.
