import unittest

from core.workflow_engine.workflow_engine import WorkflowEngine


class WorkflowEngineTests(unittest.TestCase):
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
