from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.execution_layer.execution_context import ExecutionContext


class ModelRouter:
    """
    Policy-aware model resolver (minimal deterministic version).
    """

    DEFAULT_DECISION = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "reason": "default_policy",
    }

    MODEL_CATALOG = {
        "openai:gpt-4o-mini": {"cost": 1.0, "quality": 6.0, "latency": 3.0},
        "openai:gpt-4o": {"cost": 5.0, "quality": 9.0, "latency": 5.0},
        "anthropic:claude-3-haiku": {"cost": 2.0, "quality": 7.0, "latency": 4.0},
        "anthropic:claude-3-opus": {"cost": 8.0, "quality": 10.0, "latency": 6.0},
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

    def _catalog_entries(self, remaining: float | None = None) -> list[dict]:
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

            if remaining is not None and cost > remaining:
                continue

            entries.append({
                "provider": provider,
                "model": model,
                "cost": cost,
                "quality": quality,
                "latency": latency,
            })

        return entries

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

    def _budget_exceeded_decision(self, remaining: float | None) -> dict:
        decision = {
            "provider": "none",
            "model": "none",
            "reason": "budget_exceeded",
        }

        if remaining is not None:
            decision["budget_remaining"] = remaining

        return decision

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

    def _finalize_decision_with_budget(
        self,
        decision: dict,
        context: "ExecutionContext | None",
    ) -> dict:
        remaining = self._budget_remaining(context)
        if remaining is None:
            return decision

        provider = decision.get("provider")
        model = decision.get("model")
        if not provider or not model:
            return self._attach_budget_metadata(decision, context, remaining)

        model_meta = self.MODEL_CATALOG.get(f"{provider}:{model}")
        if not isinstance(model_meta, dict):
            return self._attach_budget_metadata(decision, context, remaining)

        model_cost = model_meta.get("cost")
        if model_cost is None:
            return self._attach_budget_metadata(decision, context, remaining)

        if model_cost > remaining:
            budget_exceeded = self._budget_exceeded_decision(remaining)
            return self._attach_budget_metadata(budget_exceeded, context, remaining)

        if hasattr(context, "consume_budget"):
            context.consume_budget(model_cost)

        updated_remaining = self._budget_remaining(context)
        return self._attach_budget_metadata(decision, context, updated_remaining)
    
    def _resolve_optimize_for(
        self,
        optimize_for: dict,
        candidates: list[dict],
        context: "ExecutionContext | None" = None,
    ) -> dict | None:
    
        optimize_for = optimize_for or {}
    
        base_weights = {
            "cost": float(optimize_for.get("cost", 0) or 0),
            "quality": float(optimize_for.get("quality", 0) or 0),
            "latency": float(optimize_for.get("latency", 0) or 0),
        }
    
        weights = base_weights.copy()
    
        # -------------------------------------------------
        # Budget Extraction
        # -------------------------------------------------
        budget = context.get_budget() if context else None
        remaining_budget = None
        ratio = None
    
        if budget and budget.get("total", 0) > 0:
            remaining_budget = budget["remaining"]
            ratio = remaining_budget / budget["total"]
    
        # -------------------------------------------------
        # Hard Stop
        # -------------------------------------------------
        if remaining_budget is not None and remaining_budget <= 0:
            return {
                "provider": "none",
                "model": "none",
                "reason": "budget_exceeded",
                "budget_remaining": 0,
                "budget_ratio": 0,
            }
    
        # -------------------------------------------------
        # Economic Mode
        # -------------------------------------------------
        if ratio is None:
            mode = "balanced"
        elif ratio < 0.3:
            mode = "survival"
            weights["cost"] += 0.5
            weights["quality"] *= 0.5
        elif ratio < 0.6:
            mode = "conservative"
            weights["cost"] += 0.2
        else:
            mode = "balanced"
    
        reason = f"budget_{mode}_mode"
    
        # -------------------------------------------------
        # Normalize Weights
        # -------------------------------------------------
        total_weight = sum(weights.values())
    
        if total_weight > 0:
            weights = {
                metric: weights.get(metric, 0) / total_weight
                for metric in self.OPTIMIZE_METRICS
            }
        else:
            weights = {metric: 0.0 for metric in self.OPTIMIZE_METRICS}
    
        # -------------------------------------------------
        # Scoring Loop (Hybrid)
        # -------------------------------------------------
        best_candidate = None
        best_score = None
    
        for candidate in candidates:
            cost = candidate["cost"]
            latency = candidate["latency"]
            quality = candidate["quality"]
    
            score = (
                weights["cost"] * (1 / cost) +
                weights["latency"] * (1 / latency) +
                weights["quality"] * quality
            )
    
            # -------------------------
            # Progressive Budget Penalty
            # -------------------------
            if remaining_budget is not None and cost > remaining_budget:
            
                if mode == "balanced":
                    score -= cost
    
                elif mode == "conservative":
                    score -= cost * 2
    
                elif mode == "survival":
                    score -= cost * 5
    
            if best_score is None or score > best_score:
                best_score = score
                best_candidate = candidate
    
        # -------------------------------------------------
        # Final Decision
        # -------------------------------------------------
        if best_candidate:
            provider = best_candidate["provider"]
            model = best_candidate["model"]
    
            # Consume budget
            if context and hasattr(context, "consume_budget"):
                context.consume_budget(best_candidate["cost"])
    
            updated_budget = context.get_budget() if context else budget
            updated_ratio = None
    
            if updated_budget and updated_budget.get("total", 0) > 0:
                updated_ratio = (
                    updated_budget["remaining"] / updated_budget["total"]
                )
    
            return {
                "provider": provider,
                "model": model,
                "reason": reason,
                "budget_remaining": (
                    updated_budget["remaining"] if updated_budget else None
                ),
                "budget_ratio": updated_ratio,
            }
    
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
                return self._finalize_decision_with_budget(optimized_decision, context)

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

    def resolve(
        self,
        namespace: str,
        action: str,
        posture: dict | None = None,
        context: "ExecutionContext | None" = None,
    ) -> dict:
        posture = posture or {}
        policy = posture.get("model_policy", {}) if posture else {}
        if not isinstance(policy, dict):
            policy = {}

        remaining_budget = self._budget_remaining(context)
        if remaining_budget is not None and remaining_budget <= 0:
            decision = self._budget_exceeded_decision(remaining_budget)
            return self._attach_budget_metadata(decision, context, remaining_budget)

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
            optimize_for = rule.get("optimize_for") if isinstance(rule, dict) else None
            if isinstance(optimize_for, dict):
                base_weights = optimize_for.copy()
                weights = {
                    "cost": float(base_weights.get("cost", 0) or 0),
                    "quality": float(base_weights.get("quality", 0) or 0),
                    "latency": float(base_weights.get("latency", 0) or 0),
                }

                budget = context.get_budget() if context else None
                ratio = None
                if budget and budget.get("total", 0) > 0 and remaining_budget is not None:
                    ratio = remaining_budget / budget["total"]

                mode = "balanced"
                if ratio is not None:
                    if ratio > 0.6:
                        mode = "balanced"
                    elif ratio > 0.3:
                        mode = "conservative"
                    else:
                        mode = "survival"

                reason = "objective_multi_criteria"

                if ratio is not None:
                    if ratio < 0.3:
                        reason = "budget_survival_mode"
                        weights["cost"] = weights.get("cost", 0) + 0.5
                        weights["quality"] = weights.get("quality", 0) * 0.5
                    elif ratio < 0.6:
                        reason = "budget_conservative_mode"
                        weights["cost"] = weights.get("cost", 0) + 0.2

                total = sum(weights.values())
                if total > 0:
                    weights = {k: v / total for k, v in weights.items()}
                else:
                    weights = {"cost": 0.0, "quality": 0.0, "latency": 0.0}

                selected_provider = None
                selected_model = None
                selected_model_cost = None
                best_score = None

                for candidate in candidates:
                    cost = candidate["cost"]
                    latency = candidate["latency"]
                    quality = candidate["quality"]

                    score = (
                        (weights["cost"] * (1 / cost)) +
                        (weights["latency"] * (1 / latency)) +
                        (weights["quality"] * quality)
                    )

                    if remaining_budget is not None and cost > remaining_budget:
                        if mode == "balanced":
                            score -= cost
                        elif mode == "conservative":
                            score -= cost * 2
                        else:
                            score -= cost * 5

                    if best_score is None or score > best_score:
                        best_score = score
                        selected_provider = candidate["provider"]
                        selected_model = candidate["model"]
                        selected_model_cost = cost

                if selected_model_cost is not None and context and hasattr(context, "consume_budget"):
                    context.consume_budget(selected_model_cost)
                    budget = context.get_budget() if hasattr(context, "get_budget") else budget

                budget_ratio = ratio
                if budget and budget.get("total", 0) > 0:
                    budget_ratio = budget["remaining"] / budget["total"]

                decision = {
                    "provider": selected_provider or "none",
                    "model": selected_model or "none",
                    "reason": reason if selected_provider else "budget_exceeded",
                    "budget_remaining": budget["remaining"] if budget else None,
                    "budget_ratio": budget_ratio,
                }
                return decision

            return self._resolve_policy_entry(
                rule,
                default_reason=default_reason,
                candidates=candidates,
                context=context,
            )

        return self._finalize_decision_with_budget(self.DEFAULT_DECISION.copy(), context)