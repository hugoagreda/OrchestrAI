# python -m core.tests.test_execution_layer
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
        print("[profiling.metrics]", metrics)
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

    def test_execute_records_decision_critical_trace(self):
        kernel = CapabilityKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()

        workflow = {
            "steps": [
                {
                    "capability": "content",
                    "action": "generate_script",
                    "payload": {"topic": "trace validation", "tone": "neutral"},
                    "metadata": {},
                }
            ]
        }

        layer.execute(workflow, context)

        traces = context.execution_traces()
        self.assertEqual(len(traces), 1)

        trace = traces[0]
        print("[execution.trace]", trace)
        self.assertIn("classification", trace)
        self.assertIn("routing", trace)
        self.assertIn("selected_model", trace)
        self.assertIn("decision_reason", trace)

        self.assertIsInstance(trace["classification"], str)
        self.assertTrue(trace["classification"])

        self.assertIsInstance(trace["routing"], dict)
        self.assertIn("policy", trace["routing"])
        self.assertIn("provider", trace["routing"])
        self.assertIn("model", trace["routing"])

        self.assertIsInstance(trace["selected_model"], str)
        self.assertTrue(trace["selected_model"])

        self.assertIsInstance(trace["decision_reason"], str)
        self.assertTrue(trace["decision_reason"])

        if "estimated_tokens" in trace:
            self.assertIsInstance(trace["estimated_tokens"], int)
            self.assertGreaterEqual(trace["estimated_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
