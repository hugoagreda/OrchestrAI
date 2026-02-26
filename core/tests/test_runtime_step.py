import unittest

from core.execution_layer.runtime_step import RuntimeStep


class RuntimeStepTests(unittest.TestCase):
    def test_capability_key_builds_namespace_action(self):
        step = RuntimeStep({"capability": "content", "action": "generate_script"})
        self.assertEqual(step.capability_key(), "content.generate_script")

    def test_legacy_key_fallback(self):
        step = RuntimeStep({"action": "generate_script"})
        self.assertEqual(step.legacy_key(), "generate_script")


if __name__ == "__main__":
    unittest.main()
