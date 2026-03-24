"""Deterministic cost aggregation utilities."""

from __future__ import annotations


def _as_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def aggregate_costs(traces: list[dict]) -> dict:
    """Aggregate cost and savings metrics from execution traces."""
    total_requests = len(traces or [])

    total_cost = 0.0
    baseline_cost = 0.0
    total_savings = 0.0

    for trace in traces or []:
        if not isinstance(trace, dict):
            continue

        total_cost += _as_float(trace.get("estimated_cost"))
        baseline_cost += _as_float(trace.get("baseline_cost"))

        # Trust explicit savings when present, otherwise derive safely.
        explicit_savings = trace.get("savings")
        if explicit_savings is None:
            derived = _as_float(trace.get("baseline_cost")) - _as_float(trace.get("estimated_cost"))
            total_savings += max(0.0, derived)
        else:
            total_savings += max(0.0, _as_float(explicit_savings))

    total_cost = round(total_cost, 8)
    baseline_cost = round(baseline_cost, 8)
    total_savings = round(total_savings, 8)
    savings_ratio = round((total_savings / baseline_cost), 8) if baseline_cost > 0 else 0.0

    return {
        "total_requests": total_requests,
        "total_cost": total_cost,
        "baseline_cost": baseline_cost,
        "total_savings": total_savings,
        "savings_ratio": savings_ratio,
    }
