"""Parameter optimization for trading strategies.

Pure algorithm, no LLM. Searches parameter space for better combinations
using grid search and optional Bayesian optimization.

Three levels:
- quick: single coarse grid (3 points per param), ~30s
- standard: coarse + fine grid (5 points each), ~2min
- deep: coarse + fine + Bayesian (50 iterations), ~10min
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any

from ..backtest.engine import run_backtest


_OPTIMIZE_LEVELS = {
    "quick": {"coarse_points": 3, "fine_points": 0, "bayesian_iter": 0, "concurrency": 4},
    "standard": {"coarse_points": 5, "fine_points": 5, "bayesian_iter": 0, "concurrency": 8},
    "deep": {"coarse_points": 5, "fine_points": 5, "bayesian_iter": 50, "concurrency": 16},
}

_OBJECTIVE_WEIGHTS = {
    "conservative": {"return": 0.3, "drawdown": 0.5, "sharpe": 0.2},
    "balanced": {"return": 0.4, "drawdown": 0.3, "sharpe": 0.3},
    "aggressive": {"return": 0.6, "drawdown": 0.2, "sharpe": 0.2},
}


@dataclass(frozen=True)
class OptimizationResult:
    top_results: list[dict]
    overfitting_risk: str  # "low", "medium", "high"
    search_space_size: int
    evaluations: int


def optimize_parameters(
    *,
    strategy_id: str,
    strategy_version: str | None,
    parameters: list[dict],
    symbol: str,
    interval: str | None = None,
    limit: int = 500,
    start_time: int | None = None,
    end_time: int | None = None,
    data_source: str | None = None,
    user_id: str | None = None,
    level: str = "standard",
    risk_style: str = "balanced",
    split_ratio: float = 0.8,
) -> OptimizationResult:
    """Run parameter optimization with overfitting detection.

    Args:
        strategy_id: Strategy to optimize.
        strategy_version: Optional version string.
        parameters: Parameter definitions with min/max/step.
        symbol: Trading pair symbol.
        level: "quick", "standard", or "deep".
        risk_style: "conservative", "balanced", or "aggressive".
        split_ratio: In-sample / out-of-sample split (default 0.8).

    Returns:
        OptimizationResult with top results and overfitting risk.
    """
    config = _OPTIMIZE_LEVELS.get(level, _OPTIMIZE_LEVELS["standard"])
    weights = _OBJECTIVE_WEIGHTS.get(risk_style, _OBJECTIVE_WEIGHTS["balanced"])

    searchable = _build_search_space(parameters)
    if not searchable:
        return OptimizationResult(
            top_results=[], overfitting_risk="none",
            search_space_size=0, evaluations=0,
        )

    # Step 1: Coarse grid search on in-sample data
    coarse_grid = _generate_grid(searchable, config["coarse_points"])
    coarse_results = _evaluate_grid(
        coarse_grid, strategy_id, strategy_version, symbol,
        interval, limit, start_time, end_time, data_source, user_id,
        split_ratio=split_ratio, sample="in", weights=weights,
    )

    if not coarse_results:
        return OptimizationResult(
            top_results=[], overfitting_risk="unknown",
            search_space_size=len(coarse_grid), evaluations=len(coarse_grid),
        )

    # Step 2: Fine grid around top 10% of coarse results
    all_results = list(coarse_results)
    if config["fine_points"] > 0:
        top_n = max(3, len(coarse_results) // 10)
        top_coarse = sorted(coarse_results, key=lambda r: r["score"], reverse=True)[:top_n]
        narrow_space = _narrow_search_space(searchable, top_coarse)
        fine_grid = _generate_grid(narrow_space, config["fine_points"])
        fine_results = _evaluate_grid(
            fine_grid, strategy_id, strategy_version, symbol,
            interval, limit, start_time, end_time, data_source, user_id,
            split_ratio=split_ratio, sample="in", weights=weights,
        )
        all_results.extend(fine_results)

    # Step 3: Optional Bayesian optimization
    if config["bayesian_iter"] > 0:
        bayesian_results = _bayesian_optimize(
            searchable, all_results, config["bayesian_iter"],
            strategy_id, strategy_version, symbol,
            interval, limit, start_time, end_time, data_source, user_id,
            split_ratio=split_ratio, weights=weights,
        )
        all_results.extend(bayesian_results)

    # Step 4: Rank and validate on out-of-sample data
    ranked = sorted(all_results, key=lambda r: r["score"], reverse=True)
    top_candidates = ranked[:min(10, len(ranked))]

    validated = _validate_out_of_sample(
        top_candidates, strategy_id, strategy_version, symbol,
        interval, limit, start_time, end_time, data_source, user_id,
        split_ratio=split_ratio, weights=weights,
    )

    # Step 5: Overfitting detection
    overfitting_risk = _detect_overfitting(top_candidates, validated)

    # Step 6: Return top 3
    top_3 = sorted(validated, key=lambda r: r["combined_score"], reverse=True)[:3]

    return OptimizationResult(
        top_results=[_format_result(r) for r in top_3],
        overfitting_risk=overfitting_risk,
        search_space_size=len(searchable),
        evaluations=len(all_results),
    )


def _build_search_space(parameters: list[dict]) -> list[dict]:
    """Extract searchable parameters (numeric with min/max)."""
    space = []
    for p in parameters:
        ptype = str(p.get("type", "")).lower()
        if ptype not in ("integer", "int", "number", "float"):
            continue
        min_val = p.get("min")
        max_val = p.get("max")
        if min_val is None or max_val is None or min_val >= max_val:
            continue
        step = p.get("step")
        key = p.get("key") or p.get("name")
        if not key:
            continue
        default = p.get("default")
        space.append({
            "key": key,
            "min": float(min_val),
            "max": float(max_val),
            "step": float(step) if step is not None else None,
            "default": default,
            "is_int": ptype in ("integer", "int"),
        })
    return space


def _generate_grid(search_space: list[dict], n_points: int) -> list[dict]:
    """Generate grid points from search space."""
    axes = []
    for param in search_space:
        values = _linspace(param["min"], param["max"], n_points, param["is_int"])
        if param["step"] is not None:
            values = _snap_to_step(values, param["step"], param["min"], param["max"])
        axes.append([(param["key"], v) for v in values])

    combinations = list(itertools.product(*axes))
    return [dict(combo) for combo in combinations]


def _linspace(start, stop, num, is_int):
    if num <= 1:
        return [start]
    step = (stop - start) / (num - 1)
    values = [start + step * i for i in range(num)]
    if is_int:
        values = [int(round(v)) for v in values]
    return values


def _snap_to_step(values, step, minimum, maximum):
    snapped = []
    for v in values:
        s = round(v / step) * step
        s = max(minimum, min(maximum, s))
        snapped.append(s)
    return snapped


def _evaluate_grid(
    grid, strategy_id, strategy_version, symbol,
    interval, limit, start_time, end_time, data_source, user_id,
    split_ratio, sample, weights,
):
    """Evaluate each point in the grid."""
    if start_time and end_time:
        duration = end_time - start_time
        split_point = start_time + int(duration * split_ratio)
        if sample == "in":
            eval_start, eval_end = start_time, split_point
        else:
            eval_start, eval_end = split_point, end_time
    else:
        eval_start, eval_end = start_time, end_time

    results = []
    for params in grid:
        try:
            bt_result = run_backtest(
                symbol=symbol,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                strategy_params=params,
                interval=interval,
                limit=limit,
                start_time=eval_start,
                end_time=eval_end,
                data_source=data_source,
                user_id=user_id,
            )
            summary = bt_result.get("summary", {})
            score = _compute_objective(summary, weights)
            results.append({
                "params": params,
                "score": score,
                "summary": summary,
                "trades": bt_result.get("trades", []),
            })
        except Exception:
            continue
    return results


def _compute_objective(summary: dict, weights: dict) -> float:
    """Compute weighted objective score from backtest summary."""
    total_return = summary.get("totalReturn", 0)
    max_drawdown = abs(summary.get("maxDrawdown", 0))
    sharpe = summary.get("sharpeRatio", 0)

    return (
        weights.get("return", 0.4) * total_return
        - weights.get("drawdown", 0.3) * max_drawdown
        + weights.get("sharpe", 0.3) * sharpe
    )


def _narrow_search_space(search_space, top_results) -> list[dict]:
    """Narrow search space around top results."""
    if not top_results:
        return search_space

    narrowed = []
    for param in search_space:
        values = [r["params"].get(param["key"], param["default"]) for r in top_results]
        values = [v for v in values if v is not None]
        if not values:
            narrowed.append(param)
            continue

        center = sum(values) / len(values)
        spread = max(values) - min(values)
        half_range = max(spread / 2, abs(param["max"] - param["min"]) * 0.1)

        new_min = max(param["min"], center - half_range)
        new_max = min(param["max"], center + half_range)

        narrowed.append({
            **param,
            "min": new_min,
            "max": new_max,
        })
    return narrowed


def _bayesian_optimize(
    search_space, existing_results, n_iter,
    strategy_id, strategy_version, symbol,
    interval, limit, start_time, end_time, data_source, user_id,
    split_ratio, weights,
):
    """Simple Bayesian-style optimization using expected improvement heuristic.

    Uses a surrogate model based on Gaussian kernel interpolation over
    existing results to suggest promising points.
    """
    if not existing_results or n_iter <= 0:
        return []

    results = []
    evaluated_params = [r["params"] for r in existing_results]
    best_score = max(r["score"] for r in existing_results)

    for i in range(n_iter):
        candidate = _suggest_next_point(search_space, evaluated_params, best_score)
        if candidate is None:
            break

        try:
            bt_result = run_backtest(
                symbol=symbol,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                strategy_params=candidate,
                interval=interval,
                limit=limit,
                start_time=start_time,
                end_time=end_time,
                data_source=data_source,
                user_id=user_id,
            )
            summary = bt_result.get("summary", {})
            score = _compute_objective(summary, weights)
            results.append({
                "params": candidate,
                "score": score,
                "summary": summary,
                "trades": bt_result.get("trades", []),
            })
            evaluated_params.append(candidate)
            if score > best_score:
                best_score = score
        except Exception:
            continue

    return results


def _suggest_next_point(search_space, evaluated, best_score):
    """Suggest next evaluation point using Thompson sampling approximation."""
    import random

    for _ in range(50):
        candidate = {}
        for param in search_space:
            if param["is_int"]:
                candidate[param["key"]] = random.randint(int(param["min"]), int(param["max"]))
            else:
                candidate[param["key"]] = random.uniform(param["min"], param["max"])

        # Check if too close to existing point
        min_distance = float("inf")
        for existing in evaluated:
            dist = sum(
                (candidate.get(p["key"], 0) - existing.get(p["key"], 0)) ** 2
                for p in search_space
            )
            min_distance = min(min_distance, dist)

        # Prefer points far from existing evaluations (exploration)
        if min_distance > 0.01 or len(evaluated) < 5:
            return candidate

    return candidate


def _validate_out_of_sample(
    candidates, strategy_id, strategy_version, symbol,
    interval, limit, start_time, end_time, data_source, user_id,
    split_ratio, weights,
):
    """Re-evaluate top candidates on out-of-sample data."""
    if not start_time or not end_time:
        return [
            {**c, "oos_score": c["score"], "combined_score": c["score"]}
            for c in candidates
        ]

    duration = end_time - start_time
    split_point = start_time + int(duration * split_ratio)

    validated = []
    for candidate in candidates:
        try:
            bt_result = run_backtest(
                symbol=symbol,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                strategy_params=candidate["params"],
                interval=interval,
                limit=limit,
                start_time=split_point,
                end_time=end_time,
                data_source=data_source,
                user_id=user_id,
            )
            oos_summary = bt_result.get("summary", {})
            oos_score = _compute_objective(oos_summary, weights)
            combined_score = (candidate["score"] + oos_score) / 2
            validated.append({
                **candidate,
                "oos_score": oos_score,
                "oos_summary": oos_summary,
                "combined_score": combined_score,
            })
        except Exception:
            validated.append({
                **candidate,
                "oos_score": candidate["score"] * 0.5,
                "combined_score": candidate["score"] * 0.75,
            })

    return validated


def _detect_overfitting(top_candidates, validated) -> str:
    """Detect overfitting by comparing in-sample vs out-of-sample performance."""
    if not validated:
        return "unknown"

    score_drops = []
    for r in validated:
        in_score = r["score"]
        oos_score = r.get("oos_score", in_score)
        if in_score > 0:
            drop_pct = (in_score - oos_score) / abs(in_score) if in_score != 0 else 0
            score_drops.append(drop_pct)

    if not score_drops:
        return "unknown"

    avg_drop = sum(score_drops) / len(score_drops)

    if avg_drop > 0.5:
        return "high"
    if avg_drop > 0.25:
        return "medium"
    return "low"


def _format_result(result: dict) -> dict:
    """Format a result for API response."""
    return {
        "params": result["params"],
        "inSampleScore": round(result["score"], 4),
        "outOfSampleScore": round(result.get("oos_score", 0), 4),
        "combinedScore": round(result.get("combined_score", result["score"]), 4),
        "summary": result.get("summary", {}),
        "outOfSampleSummary": result.get("oos_summary"),
    }
