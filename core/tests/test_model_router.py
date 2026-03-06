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