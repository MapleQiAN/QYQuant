# Strategy Source Import Design

Date: 2026-03-28

## Goal
Make strategy import easier for two user groups without breaking the current QYSP workflow:

- Python users who want to upload source directly
- non-packaging users who want one-step import

The platform should continue to support the existing CLI and `.qys` package flow.

## Scope
- Support three import sources:
  - single `strategy.py`
  - source project zip
  - existing `.qys`
- Keep the platform runtime based on standard `.qys` artifacts
- Preserve the current CLI workflow and reuse its build and validation rules
- Add an import confirmation step before a strategy becomes runnable

## Product Decisions
- Supported project model: controlled strategy projects only
- Dependency model: no arbitrary dependency installation
- Entrypoint detection: auto-detect common patterns, then let the user map once if needed
- Metadata extraction: partial auto-fill, then ask the user to fill gaps
- Storage model: keep both original uploaded source and generated `.qys`
- Completion flow: import goes through a confirmation page before creating the final strategy version

## UX Flow
Create a unified import wizard instead of the current file-only upload entry.

### Step 1: Choose source
- Upload Python file
- Upload source project zip
- Upload `.qys`

### Step 2: Analyze
The backend analyzes the upload and returns:
- detected source type
- file summary
- entrypoint candidates
- extracted strategy metadata
- extracted parameter candidates
- warnings and blocking errors

### Step 3: Confirm
Show a confirmation page with four sections:
- import summary
- entrypoint mapping
- strategy metadata and parameters
- build result preview

Only missing or low-confidence fields should require user input.

### Step 4: Build and import
After confirmation, the backend:
- normalizes the source into a standard project layout
- generates or completes `strategy.json`
- builds a standard `.qys`
- validates schema and integrity
- stores both original input and generated package
- creates `Strategy` and `StrategyVersion`
- redirects the user to the parameter page or backtest flow

## Backend Architecture
Do not treat import as "upload a `.qys` file". Treat it as a normalization pipeline:

`input source -> analyzer -> normalized project -> user confirmation -> qys build -> validation -> persistence`

### Normalized project
All import inputs should be converted into one internal structure:

- `raw/`: original uploaded file
- `project/strategy.json`: generated or completed manifest
- `project/src/strategy.py`: normalized entrypoint source
- `project/assets/`: allowed assets
- `analysis.json`: extracted metadata, candidates, warnings, confidence

This lets Web import, package import, and CLI import converge on one build path.

## API Design
Split the flow into analysis and confirmation.

### Analyze import
New endpoint for upload analysis only.

Returns:
- `draft_import_id`
- source type
- file summary
- entrypoint candidates
- metadata candidates
- parameter candidates
- warnings
- blocking errors

### Confirm import
New endpoint for final import.

Input:
- `draft_import_id`
- selected entrypoint mapping
- user-corrected metadata
- user-corrected parameter definitions

Output:
- created strategy payload
- created version payload
- redirect target

### Compatibility
Keep the current `.qys` import endpoint for compatibility, but migrate it internally onto the same pipeline over time.

## Data Model Changes
Add a temporary import draft record, for example `StrategyImportDraft`, to store:
- owner
- source file reference
- detected source type
- analysis result
- current status
- expiration time

Extend final strategy storage to keep:
- original source file reference
- built package file reference

Runtime and backtest execution should continue to use only the built `.qys` package.

## Validation Rules
For the first version:
- accept only controlled project structures
- ignore unsupported files such as dependency manifests
- reject multiple ambiguous runtime entrypoints unless the user resolves them
- do not execute build scripts
- do not install dependencies
- keep using QYSP schema and integrity validation as the final gate

## CLI Strategy
Preserve `qys init`, `qys build`, and `qys validate`.

Later, connect `qys import` to the same backend protocol so CLI and Web use the same normalization and validation behavior.

## MVP Delivery Order
1. Extract reusable QYSP build and validation logic from CLI-oriented code into shared library functions
2. Add backend analyze-import flow and draft persistence
3. Add backend confirm-import flow and final package generation
4. Replace current frontend upload UI with a unified import wizard and confirmation page
5. Connect CLI `qys import` to the same backend flow

## Non-Goals
- arbitrary pip dependency support
- in-browser IDE or full source editor
- custom build hooks
- non-Python strategy sources

