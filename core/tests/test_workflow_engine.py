# python -m core.tests.test_workflow_engine
import unittest
from unittest.mock import patch

import yaml

from core.execution_layer.runtime_step import RuntimeStep
from core.workflow_engine.workflow_engine import WorkflowEngine


class WorkflowEngineTests(unittest.TestCase):
    def test_workflow_loading_parses_yaml_steps(self):
        engine = WorkflowEngine()

        workflow_data = engine._load_workflow("generic")

        self.assertIn("strategies", workflow_data)
        self.assertIn("default", workflow_data["strategies"])
        self.assertGreaterEqual(len(workflow_data["strategies"]["default"]["steps"]), 1)

    def test_step_ordering_follows_workflow_definition(self):
        engine = WorkflowEngine()
        intent = {
            "content_type": "short_video",
            "capability_map": {
                "scriptwriter": "content",
                "media": "media",
                "publisher": "publishing",
                "strategist": "publishing",
                "analytics": "analytics",
            },
            "workflow_profile": {"analytics_feedback": False},
        }

        workflow = engine.build_workflow(intent)

        ordered_actions = [step["action"] for step in workflow["steps"]]
        self.assertEqual(ordered_actions, ["generate_script", "generate_media", "prepare_publish"])

    def test_workflow_steps_map_to_runtime_step_instances(self):
        engine = WorkflowEngine()
        intent = {
            "content_type": "generic",
            "capability_map": {
                "scriptwriter": "content",
                "media": "media",
                "publisher": "publishing",
                "strategist": "publishing",
                "analytics": "analytics",
            },
            "workflow_profile": {"analytics_feedback": True},
        }

        workflow = engine.build_workflow(intent)
        runtime_steps = [RuntimeStep(step) for step in workflow["steps"]]

        self.assertEqual(len(runtime_steps), len(workflow["steps"]))
        self.assertTrue(all(step.capability_key() for step in runtime_steps))

    def test_invalid_workflow_raises_explicit_failure(self):
        engine = WorkflowEngine()

        with patch.object(engine, "_load_workflow", side_effect=yaml.YAMLError("malformed YAML")):
            with self.assertRaises(yaml.YAMLError) as error:
                engine.build_workflow({"content_type": "generic", "capability_map": {}})

        self.assertIn("malformed YAML", str(error.exception))

    def test_deterministic_execution_same_input_same_step_sequence(self):
        engine = WorkflowEngine()
        intent = {
            "content_type": "short_video",
            "capability_map": {
                "scriptwriter": "content",
                "media": "media",
                "publisher": "publishing",
                "strategist": "publishing",
                "analytics": "analytics",
            },
            "workflow_profile": {
                "media_generation": "enabled",
                "publishing": "enabled",
                "analytics_feedback": False,
            },
            "platform": "tiktok",
        }

        first = engine.build_workflow(intent)
        second = engine.build_workflow(intent)

        first_sequence = [(step["capability"], step["action"]) for step in first["steps"]]
        second_sequence = [(step["capability"], step["action"]) for step in second["steps"]]
        self.assertEqual(first_sequence, second_sequence)

    def test_build_workflow_normalizes_to_runtime_abi(self):
        engine = WorkflowEngine()
        intent = {
            "content_type": "generic",
            "capability_map": {
                "scriptwriter": "content",
                "media": "media",
                "publisher": "publishing",
                "analytics": "analytics",
            },
            "platform": "generic",
        }

        workflow = engine.build_workflow(intent)
        self.assertIn("steps", workflow)
        self.assertGreaterEqual(len(workflow["steps"]), 1)

        first = workflow["steps"][0]
        self.assertIn("capability", first)
        self.assertIn("action", first)


if __name__ == "__main__":
    unittest.main()
