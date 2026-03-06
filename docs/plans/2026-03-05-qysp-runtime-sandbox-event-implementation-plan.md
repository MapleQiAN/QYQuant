# QYSP Runtime Sandbox Event Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement QYSP strategy dynamic loading, secure sandbox execution, event-driven backtest runtime, and custom strategy parameters for backtest-only workflows.

**Architecture:** Extend the current backtest pipeline with a strategy runtime layer that loads `.qys` strategy packages from `strategy_versions`, validates manifest+params, and executes callbacks in an isolated subprocess sandbox. Keep backward compatibility by preserving current backtest behavior when strategy fields are absent.

**Tech Stack:** Flask, Celery, Python multiprocessing, zipfile/json/hashlib/ast, pytest.

---

### Task 1: Add runtime contract tests (RED)

**Files:**
- Create: `backend/tests/test_strategy_runtime.py`
- Modify: `backend/tests/test_backtests.py`

**Step 1: Write failing tests for params validation and strategy execution path**
- Add test: invalid param range returns `400` from `/api/backtests/run`.
- Add test: missing strategy version returns `400`.
- Add test: event strategy runs and returns non-empty `trades` plus summary.

**Step 2: Run focused tests and verify failure**
- Run: `pytest backend/tests/test_strategy_runtime.py -q`
- Expected: failing due to missing runtime modules/fields.

### Task 2: Implement runtime package loading and param validation (GREEN)

**Files:**
- Create: `backend/app/strategy_runtime/__init__.py`
- Create: `backend/app/strategy_runtime/errors.py`
- Create: `backend/app/strategy_runtime/manifest.py`
- Create: `backend/app/strategy_runtime/params.py`
- Create: `backend/app/strategy_runtime/loader.py`

**Step 1: Implement manifest parsing + file guards**
- Read `.qys` from `File.path`, parse `strategy.json`, validate `entrypoint`.
- Reject zip-slip/absolute paths and missing entry file.

**Step 2: Implement params schema normalization and validation**
- Merge defaults + user overrides.
- Enforce type/range/enum/required constraints from `parameters`.

**Step 3: Run runtime tests and verify progress**
- Run: `pytest backend/tests/test_strategy_runtime.py::test_param_validation_range_error -q`

### Task 3: Implement subprocess sandbox and event executor

**Files:**
- Create: `backend/app/strategy_runtime/sandbox.py`
- Create: `backend/app/strategy_runtime/events.py`
- Create: `backend/app/strategy_runtime/executor.py`

**Step 1: Build AST guard and restricted builtins policy**
- Reject high-risk imports and dangerous builtins.

**Step 2: Build child-process event loop**
- Load entry callable/class, run `on_init/on_bar/on_order/on_trade/on_risk/on_timer/on_error/on_finish`.
- Return trades and event diagnostics to parent process.

**Step 3: Build parent runner with timeout enforcement**
- Kill worker on timeout and emit runtime error codes.

**Step 4: Run focused tests and verify pass**
- Run: `pytest backend/tests/test_strategy_runtime.py::test_runtime_executes_strategy_package -q`

### Task 4: Integrate runtime into API/task/engine

**Files:**
- Modify: `backend/app/blueprints/backtests.py`
- Modify: `backend/app/tasks/backtests.py`
- Modify: `backend/app/backtest/engine.py`

**Step 1: Extend request and task signatures**
- Add `strategyId`, `strategyVersion`, `strategyParams` support.

**Step 2: Add runtime branch in engine**
- If strategy fields provided: load+validate+execute via sandbox runtime.
- Else fallback to existing provider summary logic.

**Step 3: Add API error mapping for runtime errors**
- Return deterministic `400` for user-input/runtime contract errors.

### Task 5: Validate safety and compatibility

**Files:**
- Modify: `backend/tests/test_backtests.py`

**Step 1: Add compatibility test**
- Existing run endpoint without strategy still returns job id and success.

**Step 2: Add security test**
- Strategy package with forbidden import should fail predictably.

**Step 3: Run all backend tests**
- Run: `pytest backend/tests -q`
- Expected: all pass.

### Task 6: Document runtime contract

**Files:**
- Modify: `docs/strategy-format/README.md`

**Step 1: Add `event_v1` runtime callback contract and params override rules**

**Step 2: Add backtest API payload example**

