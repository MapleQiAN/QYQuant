# Settings Page + i18n v11 Design

## Goal
Move the language toggle into a dedicated Settings page and standardize all UI text through vue-i18n with English and Chinese support.

## Context
The dashboard currently exposes a language toggle in TopNav and uses i18n keys for most static text. Some legacy mock data and UI strings were previously hardcoded or contained garbled characters. The new requirement is to move locale control into a Settings page and ensure all visible UI strings are localized cleanly.

## Proposed UX
- Add a new Settings page at `/settings`.
- Use the existing Dashboard "Settings" button to route to this page.
- Remove the language toggle from TopNav to avoid duplicate entry points.
- Settings page includes a single language section with a two-option toggle (中文 / EN) and a short helper text.

## Architecture
- Keep `useUserStore().locale` as the single source of truth.
- `setLocale()` updates both store and vue-i18n `global.locale`, persisted to `localStorage`.
- Introduce `SettingsView.vue` and route it via `src/router/index.ts`.
- Add i18n keys under `settings.*` and ensure all Settings UI text is served from messages.

## Dependencies
- Upgrade `vue-i18n` to v11 (from v9) to align with supported versions.
- Continue to use `createI18n({ legacy: false, globalInjection: true })`.

## Testing
- Add a SettingsView test that verifies language switching calls `setLocale` and updates state.
- Keep existing DashboardView test to ensure localized headers render.
