"""Utilities for deterministic execution cost attribution and savings."""

from __future__ import annotations


# USD per 1K tokens (input/output).
MODEL_PRICING = {
    "gpt-4o": {"input": 0.0050, "output": 0.0150},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4.1": {"input": 0.0100, "output": 0.0300},
    "claude-3-haiku": {"input": 0.0008, "output": 0.0040},
    "claude-3-opus": {"input": 0.0150, "output": 0.0750},
    "gemini-2.0-flash": {"input": 0.0002, "output": 0.0008},
    "mistral-large": {"input": 0.0030, "output": 0.0090},
    "openrouter/auto": {"input": 0.0010, "output": 0.0040},
}

DEFAULT_BASELINE_MODEL = "gpt-4o"


def _safe_tokens(value: int | float | None) -> int:
    if value is None:
        return 0
    return max(0, int(value))


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a model given input/output token counts."""
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0

    in_tokens = _safe_tokens(input_tokens)
    out_tokens = _safe_tokens(output_tokens)

    in_cost = (in_tokens / 1000.0) * float(pricing.get("input", 0.0))
    out_cost = (out_tokens / 1000.0) * float(pricing.get("output", 0.0))
    total_cost = round(in_cost + out_cost, 8)

    print(
        "[EXEC TRACE] estimate_cost",
        {
            "model": model,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "estimated_cost": total_cost,
        },
    )

    return total_cost


def _resolve_token_pair(tokens: int | dict | None) -> tuple[int, int]:
    if isinstance(tokens, dict):
        return (
            _safe_tokens(tokens.get("input_tokens")),
            _safe_tokens(tokens.get("output_tokens")),
        )

    total = _safe_tokens(tokens)
    # Simple deterministic split for coarse estimates.
    input_tokens = total
    output_tokens = total // 2
    return input_tokens, output_tokens


def _decision_flag(savings: float, savings_ratio: float) -> str:
    if savings <= 0:
        return "non_optimized"
    if savings_ratio < 0.2:
        return "low_impact"
    return "high_impact"


def compute_savings(selected_model: str, baseline_model: str, tokens: int | dict) -> dict:
    """Compute deterministic savings against a baseline model."""
    input_tokens, output_tokens = _resolve_token_pair(tokens)

    selected_cost = estimate_cost(selected_model, input_tokens, output_tokens)
    baseline_cost = estimate_cost(baseline_model, input_tokens, output_tokens)

    savings = round(max(0.0, baseline_cost - selected_cost), 8)
    savings_ratio = round((savings / baseline_cost), 8) if baseline_cost > 0 else 0.0
    decision_flag = _decision_flag(savings, savings_ratio)

    result = {
        "selected_model": selected_model,
        "baseline_model": baseline_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": selected_cost,
        "baseline_cost": baseline_cost,
        "savings": savings,
        "savings_ratio": savings_ratio,
        "decision_flag": decision_flag,
    }

    print("[EXEC TRACE] compute_savings", result)
    return result
