import asyncio
import unittest

from core.action.capability_kernel import CapabilityKernel
from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.execution_layer import ExecutionLayer


class ExecutionLayerTests(unittest.TestCase):
    def test_execute_with_profiling_records_pipeline_profile(self):
        kernel = CapabilityKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()

        workflow = {
            "steps": [
                {
                    "capability": "content",
                    "action": "generate_script",
                    "payload": {"topic": "profiling", "tone": "neutral"},
                    "metadata": {},
                },
                {
                    "capability": "media",
                    "action": "generate_media",
                    "payload": {"style": "default"},
                    "metadata": {},
                },
            ]
        }

        layer.execute(workflow, context, enable_profiling=True)

        metrics = context.metrics()
        self.assertTrue(metrics["profiling"]["enabled"])
        self.assertGreater(metrics["profiling"]["pipeline_duration_ms"], 0)
        self.assertIsNotNone(metrics["profiling"]["slowest_step"])
        self.assertGreaterEqual(metrics["kernel_cache"]["size"], 1)

    def test_execute_async_runs_workflow(self):
        kernel = CapabilityKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()

        workflow = {
            "steps": [
                {
                    "capability": "content",
                    "action": "generate_script",
                    "payload": {"topic": "async", "tone": "natural"},
                    "metadata": {},
                }
            ]
        }

        asyncio.run(layer.execute_async(workflow, context, enable_profiling=True))

        self.assertIsNotNone(context.get("script_raw"))
        self.assertEqual(context.metrics()["successful_steps"], 1)


if __name__ == "__main__":
    unittest.main()
