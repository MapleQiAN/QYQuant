# Gold Strategy Import Design

Date: 2026-02-04

## Goal
Import `backend/GoldStratagy(Step-By-Step).py` into the system per QYSP v1 and register it in the backend so it appears as a strategy with a version and file record.

## Scope
- Create a QYSP example under `docs/strategy-format/examples/GoldStepByStep/`.
- Package a `.qys` (ZIP) under a backend strategy storage folder.
- Seed DB entries for `Strategy`, `File`, and `StrategyVersion`.

## Design Summary
- QYSP directory structure:
  - `strategy.json`
  - `src/strategy.py`
  - `README.md` (optional)
- `.qys` package mirrors the above directory structure.
- `strategy.json` fields:
  - `schemaVersion`: "1.0"
  - `kind`: "QYStrategy"
  - `id`: UUID
  - `name`: "黄金策略 Step-By-Step"
  - `version`: "0.1.0"
  - `language`: "python"
  - `runtime`: `{ name: "python", version: "3.11" }`
  - `entrypoint`: `{ path: "src/strategy.py", callable: "main", interface: "event_v1" }`
  - `tags`: `["gold", "breakout", "step-by-step"]`
  - Optional: `description`, `author`, `createdAt`, `updatedAt`
  - `integrity.files`: list of `strategy.json` and `src/strategy.py` with sha256 and size
- Source compatibility:
  - Preserve original logic; wrap into a `main()` function to satisfy entrypoint.
  - Ensure UTF-8 encoding in packaged files.
- Backend DB seeding:
  - `Strategy`: `name`, `symbol` ("IAU"), `status` ("draft"), `tags`, `last_update`, `trades`.
  - `File`: `.qys` filename, content type `application/zip`, file size, storage path.
  - `StrategyVersion`: `strategy_id`, `version` ("0.1.0"), `file_id`, `checksum` (sha256 of `.qys`).

## Error Handling & Validation
- Validate `strategy.json` against `docs/strategy-format/qysp.schema.json`.
- Verify `.qys` can be unzipped and file hashes match `integrity.files`.

## Testing
- Lightweight schema validation and integrity check script (run once; not committed if temporary).

## Notes
- No DB migration changes.
- No runtime execution changes beyond wrapping entrypoint for QYSP compliance.
