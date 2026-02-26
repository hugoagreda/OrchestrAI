import unittest

from core.planner_layer.intent_step import IntentStep
from core.strategy_engine.strategy_engine import StrategyEngine


class StrategyEngineTests(unittest.TestCase):
    def test_apply_strategy_injects_capability_map(self):
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


if __name__ == "__main__":
    unittest.main()
