from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.execution_layer.execution_context import ExecutionContext


class ModelRouter:
    """
    Deterministic model router with policy and budget awareness.
    """

    DEFAULT_DECISION = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "reason": "default_policy",
    }

    MODEL_CATALOG = {
        "openai:gpt-4o-mini": {"cost": 1.0, "quality": 6.0, "latency": 3.0},
        "openai:gpt-4.1": {"cost": 6.0, "quality": 9.0, "latency": 5.0},
        "anthropic:claude-3-haiku": {"cost": 2.0, "quality": 7.0, "latency": 4.0},
        "anthropic:claude-3-opus": {"cost": 8.0, "quality": 10.0, "latency": 6.0},
        "google:gemini-2.0-flash": {"cost": 1.2, "quality": 7.0, "latency": 3.4},
        "mistral:mistral-large": {"cost": 2.5, "quality": 8.0, "latency": 3.0},
        "openrouter:openrouter/auto": {"cost": 2.0, "quality": 7.5, "latency": 3.5},
    }

    OBJECTIVE_METRIC = {
        "low_cost": "cost",
        "high_quality": "quality",
        "fast_response": "latency",
    }

    OBJECTIVE_MINIMIZE = {
        "low_cost": True,
        "high_quality": False,
        "fast_response": True,
    }

    OPTIMIZE_METRICS = ("cost", "quality", "latency")
    SIMPLE_TASKS = {"summarization", "classification", "translation", "text_generation"}
    COMPLEX_TASKS = {"coding", "analysis", "question_answering"}

    def _budget_ratio(self, context: "ExecutionContext | None") -> float | None:
        if context is None or not hasattr(context, "get_budget"):
            return None

        budget = context.get_budget()
        if not isinstance(budget, dict):
            return None

        total = budget.get("total")
        remaining = budget.get("remaining")
        if total is None or remaining is None:
            return None

        total = float(total)
        if total <= 0:
            return None

        remaining = float(remaining)
        return remaining / total

    def _budget_remaining(self, context: "ExecutionContext | None") -> float | None:
        if context is None or not hasattr(context, "get_budget"):
            return None

        budget = context.get_budget()
        if not isinstance(budget, dict):
            return None

        remaining = budget.get("remaining")
        if remaining is None:
            return None

        return float(remaining)

    def _catalog_entries(self) -> list[dict]:
        entries = []
        for key, meta in self.MODEL_CATALOG.items():
            if ":" not in key:
                continue

            provider, model = key.split(":", 1)
            cost = meta.get("cost")
            quality = meta.get("quality")
            latency = meta.get("latency")

            if cost is None or quality is None or latency is None:
                continue

            entries.append({
                "provider": provider,
                "model": model,
                "cost": float(cost),
                "quality": float(quality),
                "latency": float(latency),
            })

        return entries

    def _attach_budget_metadata(
        self,
        decision: dict,
        context: "ExecutionContext | None",
        remaining: float | None = None,
    ) -> dict:
        decision_with_budget = decision.copy()

        if remaining is None:
            remaining = self._budget_remaining(context)

        if remaining is not None:
            decision_with_budget["budget_remaining"] = remaining

        ratio = self._budget_ratio(context)
        if ratio is not None:
            decision_with_budget["budget_ratio"] = ratio

        return decision_with_budget

    def _find_catalog_meta(self, provider: str, model: str) -> dict | None:
        key = f"{provider}:{model}"
        meta = self.MODEL_CATALOG.get(key)
        if isinstance(meta, dict):
            return meta
        return None

    def _finalize_decision_with_budget(
        self,
        decision: dict,
        context: "ExecutionContext | None",
    ) -> dict:
        decision_out = decision.copy()

        provider = decision_out.get("provider")
        model = decision_out.get("model")

        if provider and model:
            meta = self._find_catalog_meta(provider, model)
            if isinstance(meta, dict):
                decision_out["estimated_cost"] = meta.get("cost")
                decision_out["estimated_latency"] = meta.get("latency")

        remaining = self._budget_remaining(context)
        ratio = self._budget_ratio(context)

        if remaining is not None and provider and model:
            meta = self._find_catalog_meta(provider, model)
            model_cost = float(meta.get("cost", 0.0)) if isinstance(meta, dict) else 0.0

            if model_cost > 0:
                if model_cost > remaining:
                    affordable = [entry for entry in self._catalog_entries() if entry["cost"] <= remaining]
                    if affordable:
                        fallback = min(affordable, key=lambda entry: entry["cost"])
                        provider = fallback["provider"]
                        model = fallback["model"]
                        decision_out["provider"] = provider
                        decision_out["model"] = model
                        decision_out["reason"] = f"{decision_out.get('reason', 'policy')}_budget_downgrade"
                        decision_out["estimated_cost"] = fallback["cost"]
                        decision_out["estimated_latency"] = fallback["latency"]
                        model_cost = fallback["cost"]
                    else:
                        decision_out["reason"] = f"{decision_out.get('reason', 'policy')}_budget_soft_overrun"

                if context is not None and hasattr(context, "consume_budget"):
                    context.consume_budget(model_cost)

        updated_remaining = self._budget_remaining(context)
        decision_out = self._attach_budget_metadata(decision_out, context, updated_remaining)

        if ratio is not None:
            decision_out["budget_status"] = (
                "constrained" if ratio < 0.3 else "healthy"
            )

        return decision_out

    def _resolve_optimize_for(
        self,
        optimize_for: dict,
        candidates: list[dict],
        context: "ExecutionContext | None" = None,
    ) -> dict | None:
        optimize_for = optimize_for or {}

        weights = {
            "cost": float(optimize_for.get("cost", 0) or 0),
            "quality": float(optimize_for.get("quality", 0) or 0),
            "latency": float(optimize_for.get("latency", 0) or 0),
        }

        budget_ratio = self._budget_ratio(context)
        if budget_ratio is not None and budget_ratio < 0.3:
            weights["cost"] += 0.5
            weights["quality"] *= 0.5
            reason = "budget_survival_mode"
        elif budget_ratio is not None and budget_ratio < 0.6:
            weights["cost"] += 0.2
            reason = "budget_conservative_mode"
        else:
            reason = "objective_multi_criteria"

        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {
                metric: weights.get(metric, 0) / total_weight
                for metric in self.OPTIMIZE_METRICS
            }
        else:
            weights = {metric: 0.0 for metric in self.OPTIMIZE_METRICS}

        best_candidate = None
        best_score = None

        for candidate in candidates:
            cost = candidate["cost"]
            latency = candidate["latency"]
            quality = candidate["quality"]

            score = (
                weights["cost"] * (1 / max(cost, 0.001)) +
                weights["latency"] * (1 / max(latency, 0.001)) +
                weights["quality"] * quality
            )

            if best_score is None or score > best_score:
                best_score = score
                best_candidate = candidate

        if best_candidate:
            decision = {
                "provider": best_candidate["provider"],
                "model": best_candidate["model"],
                "reason": reason,
            }
            return self._finalize_decision_with_budget(decision, context)

        return None

    def _resolve_policy_entry(
        self,
        entry: dict,
        default_reason: str,
        candidates: list[dict],
        context: "ExecutionContext | None" = None,
    ) -> dict:
        decision = (entry or {}).copy()

        if "provider" in decision and "model" in decision:
            decision.setdefault("reason", default_reason)
            return self._finalize_decision_with_budget(decision, context)

        optimize_for = decision.get("optimize_for")
        if isinstance(optimize_for, dict):
            optimized_decision = self._resolve_optimize_for(
                optimize_for,
                candidates,
                context=context,
            )
            if optimized_decision:
                return optimized_decision

        objective = decision.get("objective")
        if objective in self.OBJECTIVE_METRIC:
            metric = self.OBJECTIVE_METRIC[objective]
            minimize = self.OBJECTIVE_MINIMIZE[objective]
            comparator = min if minimize else max

            scored_candidates = []
            for candidate in candidates:
                scored_candidates.append((
                    candidate["provider"],
                    candidate["model"],
                    candidate[metric],
                ))

            if scored_candidates:
                provider, model, _ = comparator(scored_candidates, key=lambda item: item[2])
                objective_decision = {
                    "provider": provider,
                    "model": model,
                    "reason": f"objective_{objective}",
                }
                return self._finalize_decision_with_budget(objective_decision, context)

        decision.setdefault("reason", default_reason)
        return self._finalize_decision_with_budget(decision, context)

    def _deterministic_objective(
        self,
        task_type: str,
        token_size: int,
        routing_policy: str,
        budget_ratio: float | None,
    ) -> tuple[str, str]:
        policy = (routing_policy or "balanced").strip().lower()

        if policy == "fast":
            return "fast_response", "policy_fast"

        if policy == "maximum_quality":
            return "high_quality", "policy_maximum_quality"

        if budget_ratio is not None and budget_ratio < 0.3:
            return "low_cost", "budget_constrained"

        normalized_task = (task_type or "text_generation").strip().lower()
        if normalized_task in self.COMPLEX_TASKS:
            return "high_quality", "complex_task"

        if token_size >= 2500:
            return "high_quality", "large_context"

        if normalized_task in self.SIMPLE_TASKS and token_size <= 700:
            return "low_cost", "simple_task"

        return "low_cost", "balanced_default"

    def resolve(
        self,
        namespace: str,
        action: str,
        posture: dict | None = None,
        context: "ExecutionContext | None" = None,
        task_type: str | None = None,
        token_size: int | None = None,
        routing_policy: str | None = None,
    ) -> dict:
        posture = posture or {}
        policy = posture.get("model_policy", {}) if posture else {}
        if not isinstance(policy, dict):
            policy = {}

        candidates = self._catalog_entries()

        exact_key = f"{namespace}.{action}"
        wildcard_key = f"{namespace}.*"

        rule = None
        default_reason = "default_policy"
        if exact_key in policy:
            rule = policy[exact_key]
            default_reason = "strategy_exact_match"
        elif wildcard_key in policy:
            rule = policy[wildcard_key]
            default_reason = "strategy_wildcard_match"

        if rule is not None:
            return self._resolve_policy_entry(
                rule,
                default_reason=default_reason,
                candidates=candidates,
                context=context,
            )

        if task_type is None and token_size is None and routing_policy is None and context is None:
            return self.DEFAULT_DECISION.copy()

        budget_ratio = self._budget_ratio(context)
        policy_input = routing_policy or posture.get("routing_policy") or "balanced"
        task_input = task_type or "text_generation"
        token_input = int(token_size or 0)

        objective, reason_tag = self._deterministic_objective(
            task_type=task_input,
            token_size=token_input,
            routing_policy=policy_input,
            budget_ratio=budget_ratio,
        )

        metric = self.OBJECTIVE_METRIC.get(objective, "cost")
        minimize = self.OBJECTIVE_MINIMIZE.get(objective, True)
        comparator = min if minimize else max

        selected = comparator(candidates, key=lambda item: item[metric]) if candidates else None
        if selected is None:
            return self._finalize_decision_with_budget(self.DEFAULT_DECISION.copy(), context)

        decision = {
            "provider": selected["provider"],
            "model": selected["model"],
            "reason": f"deterministic_{reason_tag}_{objective}",
            "routing_policy": policy_input,
            "task_type": task_input,
            "token_size": token_input,
        }

        return self._finalize_decision_with_budget(decision, context)
