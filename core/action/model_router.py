# Summary: Implements model router logic for the OrchestrAI runtime.
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.execution_layer.execution_context import ExecutionContext


class ModelRouter:
    """
    Enrutador determinista de modelos con conciencia de política y presupuesto.
    """

    DEFAULT_DECISION = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "reason": "default_policy",
    }

    MODEL_REGISTRY = [
        {
            "name": "gpt-4o-mini",
            "provider": "openai",
            "cost_score": 1.0,
            "latency_score": 3.0,
            "quality_score": 6.0,
        },
        {
            "name": "gpt-4.1",
            "provider": "openai",
            "cost_score": 6.0,
            "latency_score": 5.0,
            "quality_score": 9.0,
        },
        {
            "name": "claude-3-haiku",
            "provider": "anthropic",
            "cost_score": 2.0,
            "latency_score": 4.0,
            "quality_score": 7.0,
        },
        {
            "name": "claude-3-opus",
            "provider": "anthropic",
            "cost_score": 8.0,
            "latency_score": 6.0,
            "quality_score": 10.0,
        },
        {
            "name": "gemini-2.0-flash",
            "provider": "google",
            "cost_score": 1.2,
            "latency_score": 3.4,
            "quality_score": 7.0,
        },
        {
            "name": "mistral-large",
            "provider": "mistral",
            "cost_score": 2.5,
            "latency_score": 3.0,
            "quality_score": 8.0,
        },
        {
            "name": "openrouter/auto",
            "provider": "openrouter",
            "cost_score": 2.0,
            "latency_score": 3.5,
            "quality_score": 7.5,
        },
    ]

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

    POLICY_WEIGHTS = {
        "fast": {"latency": 0.6, "cost": 0.3, "quality": 0.1},
        "balanced": {"latency": 0.34, "cost": 0.33, "quality": 0.33},
        "maximum_quality": {"latency": 0.1, "cost": 0.15, "quality": 0.75},
    }

    COMPLEXITY_QUALITY_BOOST = 0.7
    LOW_COMPLEXITY_COST_BOOST = 0.35
    LARGE_TOKEN_COST_BOOST = 0.35
    HIGH_USAGE_COST_BOOST = 0.4
    BUDGET_PRESSURE_COST_BOOST = 0.8
    EXTREME_BUDGET_PRESSURE_COST_BOOST = 1.2
    LARGE_TOKEN_THRESHOLD = 2500
    HIGH_USAGE_THRESHOLD = 0.7
    BUDGET_PRESSURE_THRESHOLD = 0.8
    EXTREME_BUDGET_PRESSURE_THRESHOLD = 0.95

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
        for model in self.MODEL_REGISTRY:
            provider = model.get("provider")
            model_name = model.get("name")
            cost = model.get("cost_score")
            quality = model.get("quality_score")
            latency = model.get("latency_score")

            if not provider or not model_name:
                continue

            if cost is None or quality is None or latency is None:
                continue

            entries.append({
                "provider": provider,
                "model": model_name,
                "cost": float(cost),
                "quality": float(quality),
                "latency": float(latency),
                "cost_score": float(cost),
                "quality_score": float(quality),
                "latency_score": float(latency),
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

    def _normalize_weights(self, weights: dict) -> dict:
        cleaned = {
            "cost": max(0.0, float(weights.get("cost", 0.0) or 0.0)),
            "latency": max(0.0, float(weights.get("latency", 0.0) or 0.0)),
            "quality": max(0.0, float(weights.get("quality", 0.0) or 0.0)),
        }

        total = cleaned["cost"] + cleaned["latency"] + cleaned["quality"]
        if total <= 0:
            return self.POLICY_WEIGHTS["balanced"].copy()

        return {
            metric: cleaned[metric] / total
            for metric in self.OPTIMIZE_METRICS
        }

    def _policy_weights(self, routing_policy: str | None) -> dict:
        policy = (routing_policy or "balanced").strip().lower()
        return self.POLICY_WEIGHTS.get(policy, self.POLICY_WEIGHTS["balanced"]).copy()

    def _build_weights_for_context(
        self,
        base_weights: dict,
        policy: str,
        task_type: str,
        token_size: int,
        budget_ratio: float | None,
        apply_low_complexity_bias: bool = True,
    ) -> tuple[dict, list[str]]:
        weights = self._normalize_weights(base_weights)
        adjustments: list[str] = []

        normalized_task = (task_type or "text_generation").strip().lower()
        if normalized_task in self.COMPLEX_TASKS:
            weights["quality"] += self.COMPLEXITY_QUALITY_BOOST
            weights["quality"] = max(weights["quality"], 0.7)
            weights["cost"] = min(weights["cost"], 0.2)
            adjustments.append("complexity_quality_boost")

        if (
            apply_low_complexity_bias
            and
            normalized_task in self.SIMPLE_TASKS
            and int(token_size or 0) <= 700
            and policy != "maximum_quality"
        ):
            weights["cost"] += self.LOW_COMPLEXITY_COST_BOOST
            weights["cost"] = max(weights["cost"], 0.6)
            weights["quality"] = min(weights["quality"], 0.2)
            adjustments.append("low_complexity_cost_boost")

        if (
            int(token_size or 0) >= self.LARGE_TOKEN_THRESHOLD
            and policy != "maximum_quality"
            and normalized_task not in self.COMPLEX_TASKS
        ):
            weights["cost"] += self.LARGE_TOKEN_COST_BOOST
            weights["cost"] = max(weights["cost"], 0.65)
            adjustments.append("large_tokens_cost_boost")

        if budget_ratio is not None:
            usage_ratio = 1.0 - budget_ratio
            if usage_ratio >= self.EXTREME_BUDGET_PRESSURE_THRESHOLD:
                return self._normalize_weights({"cost": 1.0, "latency": 0.0, "quality": 0.0}), [
                    *adjustments,
                    "extreme_budget_pressure_cost_boost",
                ]
            elif usage_ratio >= self.BUDGET_PRESSURE_THRESHOLD:
                weights["cost"] += self.BUDGET_PRESSURE_COST_BOOST
                weights["cost"] = max(weights["cost"], 0.85)
                weights["quality"] = min(weights["quality"], 0.1)
                weights["latency"] = min(weights["latency"], 0.15)
                adjustments.append("budget_pressure_cost_boost")
            elif usage_ratio >= self.HIGH_USAGE_THRESHOLD:
                weights["cost"] += self.HIGH_USAGE_COST_BOOST
                weights["cost"] = max(weights["cost"], 0.65)
                adjustments.append("high_budget_usage_cost_boost")

        return self._normalize_weights(weights), adjustments

    def _metric_bounds(self, candidates: list[dict], metric: str) -> tuple[float, float]:
        values = [float(candidate.get(metric, 0.0)) for candidate in candidates]
        return min(values), max(values)

    def _metric_utility(self, value: float, lower: float, upper: float, minimize: bool) -> float:
        if upper <= lower:
            return 1.0

        normalized = (value - lower) / (upper - lower)
        return (1.0 - normalized) if minimize else normalized

    def _score_candidates(self, candidates: list[dict], weights: dict) -> list[dict]:
        if not candidates:
            return []

        cost_min, cost_max = self._metric_bounds(candidates, "cost_score")
        latency_min, latency_max = self._metric_bounds(candidates, "latency_score")
        quality_min, quality_max = self._metric_bounds(candidates, "quality_score")

        scored: list[dict] = []
        for candidate in candidates:
            cost_utility = self._metric_utility(
                float(candidate["cost_score"]),
                cost_min,
                cost_max,
                minimize=True,
            )
            latency_utility = self._metric_utility(
                float(candidate["latency_score"]),
                latency_min,
                latency_max,
                minimize=True,
            )
            quality_utility = self._metric_utility(
                float(candidate["quality_score"]),
                quality_min,
                quality_max,
                minimize=False,
            )

            contributions = {
                "cost": weights["cost"] * cost_utility,
                "latency": weights["latency"] * latency_utility,
                "quality": weights["quality"] * quality_utility,
            }
            total_score = contributions["cost"] + contributions["latency"] + contributions["quality"]

            scored.append({
                "candidate": candidate,
                "score": total_score,
                "contributions": contributions,
                "utilities": {
                    "cost": cost_utility,
                    "latency": latency_utility,
                    "quality": quality_utility,
                },
            })

        return scored

    def _top_factors(self, contributions: dict, max_items: int = 2) -> list[str]:
        ordered = sorted(
            contributions.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        return [factor for factor, value in ordered[:max_items] if value > 0]

    def _winner_tag(self, policy: str, top_factors: list[str]) -> str:
        if top_factors and top_factors[0] == "quality":
            return "quality_priority"
        if top_factors and top_factors[0] == "cost":
            return "best_cost_efficiency"
        if top_factors and top_factors[0] == "latency":
            return "speed_priority"
        if policy == "maximum_quality":
            return "quality_priority"
        if policy == "fast":
            return "speed_priority"
        return "balanced_compromise"

    def _scoring_decision_reason(
        self,
        policy: str,
        weighted_factors: dict,
        adjustments: list[str],
        top_factors: list[str],
    ) -> dict:
        return {
            "policy": policy,
            "top_scoring_factors": top_factors,
            "factor_weights": {
                metric: round(weighted_factors.get(metric, 0.0), 4)
                for metric in self.OPTIMIZE_METRICS
            },
            "context_adjustments": adjustments,
            "winner_tag": self._winner_tag(policy, top_factors),
        }

    def _resolve_scored_decision(
        self,
        candidates: list[dict],
        routing_policy: str,
        task_type: str,
        token_size: int,
        context: "ExecutionContext | None" = None,
        base_weights: dict | None = None,
        reason_prefix: str = "deterministic_scoring",
        include_winner_tag: bool = True,
        apply_low_complexity_bias: bool = True,
    ) -> dict | None:
        if not candidates:
            return None

        policy = (routing_policy or "balanced").strip().lower()
        budget_ratio = self._budget_ratio(context)

        policy_weights = self._normalize_weights(base_weights or self._policy_weights(policy))
        adjusted_weights, adjustments = self._build_weights_for_context(
            base_weights=policy_weights,
            policy=policy,
            task_type=task_type,
            token_size=token_size,
            budget_ratio=budget_ratio,
            apply_low_complexity_bias=apply_low_complexity_bias,
        )

        scored = self._score_candidates(candidates, adjusted_weights)
        if not scored:
            return None

        # Deterministic tie-breaking: score > quality > cost utility > lexical name.
        winner = max(
            scored,
            key=lambda item: (
                item["score"],
                item["utilities"]["quality"],
                item["utilities"]["cost"],
                item["utilities"]["latency"],
                f"{item['candidate']['provider']}:{item['candidate']['model']}",
            ),
        )

        top_factors = self._top_factors(winner["contributions"])
        reason_meta = self._scoring_decision_reason(
            policy=policy,
            weighted_factors=adjusted_weights,
            adjustments=adjustments,
            top_factors=top_factors,
        )

        winner_tag = reason_meta["winner_tag"]
        reason_value = f"{reason_prefix}_{winner_tag}" if include_winner_tag else reason_prefix
        decision = {
            "provider": winner["candidate"]["provider"],
            "model": winner["candidate"]["model"],
            "reason": reason_value,
            "decision_reason": reason_meta,
            "routing_policy": policy,
            "task_type": task_type,
            "token_size": int(token_size or 0),
        }
        return self._finalize_decision_with_budget(decision, context)

    def _reason_prefix_for_default(
        self,
        routing_policy: str,
        task_type: str,
        token_size: int,
        budget_ratio: float | None,
    ) -> str:
        policy = (routing_policy or "balanced").strip().lower()
        normalized_task = (task_type or "text_generation").strip().lower()
        token_input = int(token_size or 0)

        if policy == "fast":
            return "deterministic_policy_fast_response"
        if policy == "maximum_quality":
            return "deterministic_policy_override_high_quality"

        if budget_ratio is not None:
            usage_ratio = 1.0 - budget_ratio
            if usage_ratio >= self.EXTREME_BUDGET_PRESSURE_THRESHOLD:
                return "deterministic_extreme_budget_pressure_low_cost"
            if usage_ratio >= self.BUDGET_PRESSURE_THRESHOLD:
                return "deterministic_budget_pressure_low_cost"

        if normalized_task in self.COMPLEX_TASKS:
            return "deterministic_high_complexity_high_quality"
        if token_input >= self.LARGE_TOKEN_THRESHOLD:
            return "deterministic_large_tokens_low_cost"
        if normalized_task in self.SIMPLE_TASKS and token_input <= 700:
            return "deterministic_low_complexity_low_cost"

        return "deterministic_balanced_default"

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
        task_type: str = "text_generation",
        token_size: int = 0,
        routing_policy: str = "balanced",
    ) -> dict | None:
        optimize_for = optimize_for or {}
        custom_weights = {
            "cost": float(optimize_for.get("cost", 0.0) or 0.0),
            "latency": float(optimize_for.get("latency", 0.0) or 0.0),
            "quality": float(optimize_for.get("quality", 0.0) or 0.0),
        }
        return self._resolve_scored_decision(
            candidates=candidates,
            routing_policy=routing_policy,
            task_type=task_type,
            token_size=token_size,
            context=context,
            base_weights=custom_weights,
            reason_prefix=(
                "budget_survival_mode"
                if (self._budget_ratio(context) or 1.0) < 0.3
                else "budget_conservative_mode"
                if (self._budget_ratio(context) or 1.0) < 0.6
                else "objective_multi_criteria"
            ),
            include_winner_tag=False,
            apply_low_complexity_bias=False,
        )

    def _resolve_policy_entry(
        self,
        entry: dict,
        default_reason: str,
        candidates: list[dict],
        context: "ExecutionContext | None" = None,
        task_type: str = "text_generation",
        token_size: int = 0,
        routing_policy: str = "balanced",
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
                task_type=task_type,
                token_size=token_size,
                routing_policy=routing_policy,
            )
            if optimized_decision:
                return optimized_decision

        objective = decision.get("objective")
        if objective in self.OBJECTIVE_METRIC:
            objective_weights = {
                "low_cost": {"cost": 0.8, "latency": 0.15, "quality": 0.05},
                "high_quality": {"cost": 0.05, "latency": 0.05, "quality": 0.9},
                "fast_response": {"cost": 0.2, "latency": 0.75, "quality": 0.05},
            }
            weighted_decision = self._resolve_scored_decision(
                candidates=candidates,
                routing_policy=routing_policy,
                task_type=task_type,
                token_size=token_size,
                context=context,
                base_weights=objective_weights.get(objective, self.POLICY_WEIGHTS["balanced"]),
                reason_prefix=f"objective_{objective}",
                include_winner_tag=False,
                apply_low_complexity_bias=False,
            )
            if weighted_decision:
                return weighted_decision

        decision.setdefault("reason", default_reason)
        return self._finalize_decision_with_budget(decision, context)

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
                task_type=task_type or "text_generation",
                token_size=int(token_size or 0),
                routing_policy=routing_policy or posture.get("routing_policy") or "balanced",
            )

        if task_type is None and token_size is None and routing_policy is None and context is None:
            return self.DEFAULT_DECISION.copy()

        policy_input = routing_policy or posture.get("routing_policy") or "balanced"
        task_input = task_type or "text_generation"
        token_input = int(token_size or 0)
        budget_ratio = self._budget_ratio(context)
        reason_prefix = self._reason_prefix_for_default(
            routing_policy=policy_input,
            task_type=task_input,
            token_size=token_input,
            budget_ratio=budget_ratio,
        )

        scored_decision = self._resolve_scored_decision(
            candidates=candidates,
            routing_policy=policy_input,
            task_type=task_input,
            token_size=token_input,
            context=context,
            reason_prefix=reason_prefix,
            include_winner_tag=False,
        )
        if scored_decision is not None:
            return scored_decision

        return self._finalize_decision_with_budget(self.DEFAULT_DECISION.copy(), context)
