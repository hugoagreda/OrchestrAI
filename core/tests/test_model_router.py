# python -m core.tests.test_model_router
import unittest
import asyncio

from core.action.capability_kernel import CapabilityKernel
from core.action.model_router import ModelRouter
from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.runtime_step import RuntimeStep


class ModelRouterIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.kernel = CapabilityKernel()
        self.context = ExecutionContext()

    def _make_step(self, topic="AI"):
        return RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": topic, "tone": "neutral"},
            "metadata": {},
        })

    def test_model_decision_logged_on_execute(self):
        step = self._make_step("unit test")

        self.kernel.execute(step, self.context)

        decisions = self.context.model_decisions()
        self.assertEqual(len(decisions), 1)

        decision = decisions[0]
        self.assertIn("provider", decision)
        self.assertIn("model", decision)
        self.assertIn("reason", decision)

    def test_model_decision_logged_on_execute_async(self):
        step = self._make_step("async")

        asyncio.run(self.kernel.execute_async(step, self.context))

        decisions = self.context.model_decisions()
        self.assertEqual(len(decisions), 1)

    def test_execution_output_not_affected(self):
        step = self._make_step("output test")

        self.kernel.execute(step, self.context)

        # Validar que el handler sigue funcionando
        result = self.context.get("script_raw")
        self.assertIsNotNone(result)


class ModelRouterObjectivePolicyTests(unittest.TestCase):

    def setUp(self):
        self.router = ModelRouter()

    def test_exact_objective_low_cost_selects_min_cost(self):
        posture = {
            "model_policy": {
                "content.generate_script": {
                    "objective": "low_cost"
                }
            }
        }

        decision = self.router.resolve("content", "generate_script", posture)

        self.assertEqual(decision["provider"], "openai")
        self.assertEqual(decision["model"], "gpt-4o-mini")
        self.assertEqual(decision["reason"], "objective_low_cost")

    def test_wildcard_objective_high_quality_selects_max_quality(self):
        posture = {
            "model_policy": {
                "analytics.*": {
                    "objective": "high_quality"
                }
            }
        }

        decision = self.router.resolve("analytics", "analyze_metrics", posture)

        self.assertEqual(decision["provider"], "anthropic")
        self.assertEqual(decision["model"], "claude-3-opus")
        self.assertEqual(decision["reason"], "objective_high_quality")

    def test_objective_fast_response_selects_min_latency(self):
        posture = {
            "model_policy": {
                "content.*": {
                    "objective": "fast_response"
                }
            }
        }

        decision = self.router.resolve("content", "generate_script", posture)

        self.assertEqual(decision["provider"], "openai")
        self.assertEqual(decision["model"], "gpt-4o-mini")
        self.assertEqual(decision["reason"], "objective_fast_response")

    def test_explicit_provider_model_keeps_current_behavior(self):
        posture = {
            "model_policy": {
                "content.generate_script": {
                    "provider": "anthropic",
                    "model": "claude-3-haiku",
                }
            }
        }

        decision = self.router.resolve("content", "generate_script", posture)

        self.assertEqual(decision["provider"], "anthropic")
        self.assertEqual(decision["model"], "claude-3-haiku")
        self.assertEqual(decision["reason"], "strategy_exact_match")

    def test_no_match_uses_default_decision_unchanged(self):
        decision = self.router.resolve("unknown", "action", posture={})

        self.assertEqual(decision, ModelRouter.DEFAULT_DECISION)

    def test_budget_consumed_on_selected_model(self):
        context = ExecutionContext()
        context.set_budget(3.0)

        posture = {
            "model_policy": {
                "content.generate_script": {
                    "objective": "low_cost"
                }
            }
        }

        decision = self.router.resolve(
            "content",
            "generate_script",
            posture,
            context=context,
        )

        self.assertEqual(decision["provider"], "openai")
        self.assertEqual(decision["model"], "gpt-4o-mini")
        self.assertEqual(decision["reason"], "objective_low_cost")
        self.assertEqual(decision["budget_remaining"], 2.0)
        self.assertAlmostEqual(decision["budget_ratio"], 2.0 / 3.0)
        self.assertEqual(context.get_budget()["spent"], 1.0)

    def test_budget_exceeded_when_no_model_fits(self):
        context = ExecutionContext()
        context.set_budget(0.5)

        posture = {
            "model_policy": {
                "content.*": {
                    "optimize_for": {
                        "cost": 1.0,
                    }
                }
            }
        }

        decision = self.router.resolve(
            "content",
            "generate_script",
            posture,
            context=context,
        )

        self.assertEqual(decision["provider"], "openai")
        self.assertEqual(decision["model"], "gpt-4o-mini")
        self.assertIn("budget_soft_overrun", decision["reason"])
        self.assertEqual(decision["budget_remaining"], 0.0)
        self.assertEqual(decision["budget_ratio"], 0.0)

    def test_deterministic_signals_route_to_max_quality_for_complex_task(self):
        context = ExecutionContext()
        context.set_budget(20.0)

        decision = self.router.resolve(
            "content",
            "generate_script",
            posture={},
            context=context,
            task_type="analysis",
            token_size=3200,
            routing_policy="balanced",
        )

        self.assertEqual(decision["provider"], "anthropic")
        self.assertEqual(decision["model"], "claude-3-opus")
        self.assertIn("high_quality", decision["reason"])

    def test_deterministic_signals_route_to_fast_policy(self):
        context = ExecutionContext()
        context.set_budget(20.0)

        decision = self.router.resolve(
            "content",
            "generate_script",
            posture={},
            context=context,
            task_type="text_generation",
            token_size=500,
            routing_policy="fast",
        )

        self.assertEqual(decision["provider"], "openai")
        self.assertEqual(decision["model"], "gpt-4o-mini")
        self.assertIn("fast_response", decision["reason"])

    def test_optimize_for_uses_conservative_reason_when_budget_mid_ratio(self):
        context = ExecutionContext()
        context.set_budget(5.0)
        context.consume_budget(2.5)  # ratio = 0.5

        posture = {
            "model_policy": {
                "content.*": {
                    "optimize_for": {
                        "cost": 0.4,
                        "quality": 0.4,
                        "latency": 0.2,
                    }
                }
            }
        }

        decision = self.router.resolve(
            "content",
            "generate_script",
            posture,
            context=context,
        )

        self.assertIn("budget_conservative_mode", decision["reason"])
        self.assertIn("budget_ratio", decision)
        self.assertLess(decision["budget_ratio"], 0.5)

    def test_optimize_for_uses_survival_reason_when_budget_low_ratio(self):
        context = ExecutionContext()
        context.set_budget(10.0)
        context.consume_budget(8.0)  # ratio = 0.2

        posture = {
            "model_policy": {
                "content.*": {
                    "optimize_for": {
                        "cost": 1.0,
                        "quality": 0.0,
                        "latency": 0.0,
                    }
                }
            }
        }

        decision = self.router.resolve(
            "content",
            "generate_script",
            posture,
            context=context,
        )

        self.assertEqual(decision["reason"], "budget_survival_mode")
        self.assertIn("budget_ratio", decision)
        self.assertLess(decision["budget_ratio"], 0.2)

    def test_budget_pressure_changes_model_without_blocking_execution(self):
        posture = {
            "model_policy": {
                "content.*": {
                    "optimize_for": {
                        "cost": 0.0,
                        "quality": 0.1,
                        "latency": 0.9,
                    }
                }
            }
        }

        baseline = self.router.resolve(
            "content",
            "generate_script",
            posture,
            task_type="text_generation",
            token_size=120,
            routing_policy="balanced",
        )
        model_baseline = baseline["model"]
        baseline_cost = self.router.MODEL_CATALOG[
            f"{baseline['provider']}:{baseline['model']}"
        ]["cost"]

        pressured_context = ExecutionContext()
        pressured_context.set_budget(10.0)
        pressured_context.consume_budget(9.0)  # usage_ratio = 0.9, budget_ratio = 0.1

        pressured = self.router.resolve(
            "content",
            "generate_script",
            posture,
            context=pressured_context,
            task_type="text_generation",
            token_size=120,
            routing_policy="balanced",
        )

        selected_model = pressured["model"]
        pressured_cost = self.router.MODEL_CATALOG[
            f"{pressured['provider']}:{pressured['model']}"
        ]["cost"]

        self.assertNotEqual(selected_model, model_baseline)
        self.assertLess(pressured_cost, baseline_cost)

        # El enrutamiento debe degradar de forma suave: siempre hay modelo.
        self.assertIsNotNone(pressured.get("provider"))
        self.assertIsNotNone(pressured.get("model"))


class ModelRouterRoutingQualityTests(unittest.TestCase):

    CHEAP_MODELS = {"gpt-4o-mini", "claude-3-haiku", "gemini-2.0-flash"}
    HIGH_TIER_MODELS = {"gpt-4.1", "claude-3-opus"}
    TOP_TIER_MODELS = {"claude-3-opus"}

    def setUp(self):
        self.router = ModelRouter()

    def _token_size_from_classification(self, classification: dict) -> int:
        expected_tokens = (classification.get("expected_tokens") or "small").strip().lower()
        if expected_tokens == "large":
            return 3500
        return 500

    def _task_type_from_classification(self, classification: dict) -> str:
        complexity = (classification.get("complexity") or "low").strip().lower()
        base_task_type = (classification.get("task_type") or "text_generation").strip().lower()

        if complexity == "high":
            return "analysis"

        return base_task_type

    def _context_from_budget_status(self, budget_status: dict | None) -> ExecutionContext | None:
        if not isinstance(budget_status, dict) or "usage_ratio" not in budget_status:
            return None

        usage_ratio = float(budget_status.get("usage_ratio") or 0.0)
        usage_ratio = min(max(usage_ratio, 0.0), 1.0)

        context = ExecutionContext()
        context.set_budget(100.0)
        context.consume_budget(usage_ratio * 100.0)
        return context

    def _resolve_from_mock_inputs(
        self,
        classification: dict,
        policy: str,
        budget_status: dict | None,
    ) -> dict:
        decision = self.router.resolve(
            "content",
            "generate_script",
            posture={},
            context=self._context_from_budget_status(budget_status),
            task_type=self._task_type_from_classification(classification),
            token_size=self._token_size_from_classification(classification),
            routing_policy=policy,
        )

        # Determinismo: con mismas entradas debe dar exactamente la misma salida.
        repeat = self.router.resolve(
            "content",
            "generate_script",
            posture={},
            context=self._context_from_budget_status(budget_status),
            task_type=self._task_type_from_classification(classification),
            token_size=self._token_size_from_classification(classification),
            routing_policy=policy,
        )
        self.assertEqual(decision, repeat)

        return decision

    def _decision_reason_text(self, decision: dict) -> str:
        return (decision.get("reason") or "").lower().replace("_", " ")

    def test_low_complexity_routes_to_cheap_model(self):
        classification = {
            "task_type": "summarization",
            "complexity": "low",
            "expected_tokens": "small",
            "latency_sensitivity": "low",
        }
        policy = "balanced"
        budget_status = {"usage_ratio": 0.2}

        decision = self._resolve_from_mock_inputs(classification, policy, budget_status)

        self.assertIn(decision["model"], self.CHEAP_MODELS)
        self.assertIn("low complexity", self._decision_reason_text(decision))

    def test_high_complexity_routes_to_high_tier_model(self):
        classification = {
            "task_type": "summarization",
            "complexity": "high",
            "expected_tokens": "small",
            "latency_sensitivity": "low",
        }

        decision = self._resolve_from_mock_inputs(
            classification,
            policy="balanced",
            budget_status={"usage_ratio": 0.2},
        )

        self.assertIn(decision["model"], self.HIGH_TIER_MODELS)
        self.assertIn("high complexity", self._decision_reason_text(decision))

    def test_large_tokens_avoids_top_tier_unless_maximum_quality(self):
        classification = {
            "task_type": "summarization",
            "complexity": "low",
            "expected_tokens": "large",
            "latency_sensitivity": "low",
        }

        decision_balanced = self._resolve_from_mock_inputs(
            classification,
            policy="balanced",
            budget_status={"usage_ratio": 0.2},
        )
        self.assertNotIn(decision_balanced["model"], self.TOP_TIER_MODELS)

        decision_max_quality = self._resolve_from_mock_inputs(
            classification,
            policy="maximum_quality",
            budget_status={"usage_ratio": 0.2},
        )
        self.assertIn(decision_max_quality["model"], self.TOP_TIER_MODELS)

    def test_maximum_quality_policy_override_selects_best_model(self):
        classification = {
            "task_type": "summarization",
            "complexity": "low",
            "expected_tokens": "small",
            "latency_sensitivity": "low",
        }

        decision = self._resolve_from_mock_inputs(
            classification,
            policy="maximum_quality",
            budget_status={"usage_ratio": 0.2},
        )

        self.assertEqual(decision["model"], "claude-3-opus")
        self.assertIn("policy override", self._decision_reason_text(decision))

    def test_budget_pressure_applies_soft_downgrade(self):
        classification = {
            "task_type": "analysis",
            "complexity": "high",
            "expected_tokens": "small",
            "latency_sensitivity": "low",
        }

        baseline = self._resolve_from_mock_inputs(
            classification,
            policy="balanced",
            budget_status={"usage_ratio": 0.2},
        )
        pressured = self._resolve_from_mock_inputs(
            classification,
            policy="balanced",
            budget_status={"usage_ratio": 0.85},
        )

        self.assertIn(baseline["model"], self.HIGH_TIER_MODELS)
        self.assertIn(pressured["model"], self.CHEAP_MODELS)
        self.assertNotEqual(pressured["model"], baseline["model"])
        self.assertIn("budget pressure", self._decision_reason_text(pressured))

    def test_extreme_budget_pressure_selects_cheapest_viable_model(self):
        classification = {
            "task_type": "analysis",
            "complexity": "high",
            "expected_tokens": "small",
            "latency_sensitivity": "low",
        }

        decision = self._resolve_from_mock_inputs(
            classification,
            policy="balanced",
            budget_status={"usage_ratio": 0.97},
        )

        self.assertEqual(decision["model"], "gpt-4o-mini")


if __name__ == "__main__":
    unittest.main(verbosity=2)