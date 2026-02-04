# Market Color Style Toggle Design

## Goal
Add a settings option to switch market color semantics between A-share style (red up, green down) and US style (green up, red down), affecting only price-movement visuals (not general success/error states).

## Context
The app already uses a Settings page with a two-option toggle pattern for language. Color usage currently relies on global CSS variables such as `--color-success` and `--color-danger`. We need a separate, market-specific mapping so that only price-movement indicators flip when the user changes style.

## UX
- Location: Settings page, under the language card.
- Control: Two-button toggle matching the existing style.
- Labels:
  - A-share style (red up, green down)
  - US style (green up, red down)

## Architecture
- Store: extend `useUserStore` with `marketStyle: 'cn' | 'us'`.
- Persist: `localStorage` under `qyquant_market_style` with a safe resolver that defaults to `'cn'` if missing or invalid.
- Apply: a small helper (e.g. `src/styles/marketStyle.ts`) sets `document.documentElement.dataset.marketStyle` and persists changes.
- Bootstrap: `main.ts` loads the initial value via the store and applies it at startup.

## Styling
- Introduce market-specific variables:
  - `--color-up`, `--color-up-bg`
  - `--color-down`, `--color-down-bg`
- Default (`cn`): `--color-up` = red, `--color-down` = green.
- US override: when `[data-market-style="us"]` is present, swap `--color-up` and `--color-down` (and backgrounds).
- Keep `--color-success` / `--color-danger` unchanged to preserve semantic meaning for status/error states.

## Scope of Changes
- Update price-movement visuals to use `--color-up` / `--color-down` instead of `--color-success` / `--color-danger`.
- Candidates include:
  - K-line placeholder candlesticks and buy/sell signals.
  - ROI / PnL / price delta text and badges in recent lists and cards.
- Non-goals: do not change status chips (running/paused/error) or generic success/error alerts.

## i18n
Add keys under `settings.*`:
- `marketStyle`: “Market Color Style” / “行情颜色风格”
- `marketStyleHint`: “Choose how price moves are colored.” / “选择涨跌颜色显示方式。”
- `marketStyleCn`: “A-share style (red up, green down)” / “A股风格（红涨绿跌）”
- `marketStyleUs`: “US style (green up, red down)” / “美股风格（绿涨红跌）”

## Error Handling
- If an invalid value is found in storage, fall back to `'cn'`.
- If DOM is not available (SSR or tests), the apply helper should no-op.

## Testing
Not requested for this change.

## Rollout
Single release. The default remains A-share style (`cn`) unless a stored preference exists.
