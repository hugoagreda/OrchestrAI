# python -m core.tests.test_strategy_engine
import unittest

from core.execution_layer.execution_context import ExecutionContext
from core.planner_layer.intent_step import IntentStep
from core.strategy_engine.strategy_engine import StrategyEngine


class StrategyEngineTests(unittest.TestCase):
    def test_strategy_loading_applies_pack_configuration(self):
        engine = StrategyEngine()
        intent = IntentStep({
            "content_type": "short_video",
            "objective": "create_content",
        })

        runtime_entity = {
            "strategy_pack": "creator_low_autonomy",
            "workflow_profile": {"analytics_feedback": "enabled"},
        }

        result = engine.apply_strategy(intent, runtime_entity)
        data = result.to_dict()

        self.assertIn("capability_map", data)
        self.assertEqual(data["capability_map"]["scriptwriter"], "content")
        self.assertTrue(data.get("analytics_enabled"))
        self.assertEqual(data.get("autonomy"), "low")
        self.assertIn("media.*", data.get("restricted_capabilities", []))
        self.assertIn("generate_script", data.get("allowed_actions", []))

    def test_strategy_layer_does_not_execute_actions_or_routing(self):
        engine = StrategyEngine()
        intent = IntentStep({"content_type": "short_video", "query": "hola"})
        runtime_entity = {"strategy_pack": "creator_low_autonomy"}

        strategized = engine.apply_strategy(intent, runtime_entity)
        data = strategized.to_dict()

        self.assertNotIn("steps", data)
        self.assertNotIn("execution_result", data)
        self.assertNotIn("selected_model", data)

    def test_strategy_influences_execution_posture_policy(self):
        engine = StrategyEngine()
        context = ExecutionContext()
        strategized_plan = {
            "restricted_capabilities": ["publishing.*"],
            "allowed_actions": ["generate_script"],
            "autonomy": "medium",
            "model_policy": {
                "content.generate_script": {
                    "provider": "anthropic",
                    "model": "claude-3-haiku",
                }
            },
        }

        posture = engine.inject_execution_posture(context, strategized_plan)

        self.assertEqual(posture["autonomy"], "medium")
        self.assertEqual(posture["allowed_actions"], ["generate_script"])
        self.assertEqual(
            context.get_posture()["model_policy"]["content.generate_script"]["provider"],
            "anthropic",
        )

    def test_multiple_strategies_do_not_leak_state(self):
        engine = StrategyEngine()
        first_intent = IntentStep({"content_type": "generic"})
        second_intent = IntentStep({"content_type": "generic"})

        first = engine.apply_strategy(first_intent, {"strategy_pack": "creator_low_autonomy"})
        second = engine.apply_strategy(second_intent, {"strategy_pack": "enterprise_guarded"})

        first_data = first.to_dict()
        second_data = second.to_dict()

        self.assertIn("media.*", first_data.get("restricted_capabilities", []))
        self.assertIn("publishing.*", second_data.get("restricted_capabilities", []))
        self.assertNotEqual(
            first_data.get("allowed_actions", []),
            second_data.get("allowed_actions", []),
        )


if __name__ == "__main__":
    unittest.main()
