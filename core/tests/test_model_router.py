import unittest
import asyncio

from core.action.capability_kernel import CapabilityKernel
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