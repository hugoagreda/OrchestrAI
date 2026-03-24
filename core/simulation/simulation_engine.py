"""Deterministic simulation engine for cost-savings estimation."""

from __future__ import annotations

from core.action.model_router import ModelRouter
from core.action.task_classifier import TaskClassifier
from core.execution_layer.cost_aggregator import aggregate_costs
from core.execution_layer.execution_trace import DEFAULT_BASELINE_MODEL, compute_savings
from core.execution_layer.runtime_step import RuntimeStep


def simulate_execution(
    inputs: list[str],
    policy: str = "balanced",
    return_details: bool = False,
) -> dict:
    """Simulate end-to-end routing/costs without real model execution."""
    if not inputs:
        summary = aggregate_costs([])
        if return_details:
            return {
                "summary": summary,
                "traces": [],
            }
        return summary

    classifier = TaskClassifier()
    router = ModelRouter()

    traces: list[dict] = []

    for raw_input in inputs:
        prompt = raw_input if isinstance(raw_input, str) else str(raw_input)

        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {
                "prompt": prompt,
                "topic": prompt,
                "tone": "neutral",
            },
            "metadata": {},
        })

        classification = classifier.classify(step)
        model_decision = router.resolve(
            namespace=step.capability,
            action=step.action,
            posture={},
            context=None,
            task_type=classification.get("task_type"),
            token_size=classification.get("token_estimate"),
            routing_policy=policy,
        )

        token_estimate = int(classification.get("token_estimate") or 0)
        savings = compute_savings(
            selected_model=str(model_decision.get("model") or ""),
            baseline_model=DEFAULT_BASELINE_MODEL,
            tokens={
                "input_tokens": token_estimate,
                "output_tokens": token_estimate // 2,
            },
        )

        traces.append({
            "selected_model": savings.get("selected_model"),
            "estimated_cost": savings.get("estimated_cost"),
            "baseline_cost": savings.get("baseline_cost"),
            "savings": savings.get("savings"),
            "savings_ratio": savings.get("savings_ratio"),
            "decision_flag": savings.get("decision_flag"),
        })

    summary = aggregate_costs(traces)

    if return_details:
        return {
            "summary": summary,
            "traces": traces,
        }

    return summary
