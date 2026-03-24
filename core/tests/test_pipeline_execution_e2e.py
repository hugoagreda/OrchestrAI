# python -m core.tests.test_pipeline_execution_e2e

import unittest
from unittest.mock import Mock

from core.action.capability_kernel import CapabilityKernel
from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.execution_layer import ExecutionLayer


class PipelineExecutionE2ETests(unittest.TestCase):
    def test_pipeline_execution_end_to_end_balanced_policy_uses_cheap_tier(self):
        kernel = CapabilityKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()
        context.set_posture({"routing_policy": "balanced"})

        fake_adapter = Mock()

        def _prepare_request(step, model_decision):
            return {
                "provider": model_decision.get("provider"),
                "model": model_decision.get("model"),
                "capability": step.capability,
                "action": step.action,
            }

        fake_adapter.prepare_request = Mock(side_effect=_prepare_request)
        kernel.adapter_registry.get = Mock(return_value=fake_adapter)

        workflow = {
            "steps": [
                {
                    "capability": "content",
                    "action": "generate_script",
                    "payload": {
                        "topic": "Summarize this short paragraph",
                        "tone": "neutral",
                    },
                    "metadata": {},
                }
            ]
        }

        layer.execute(workflow, context)

        metrics = context.metrics()
        self.assertEqual(metrics["total_steps"], 1)
        self.assertEqual(metrics["successful_steps"], 1)
        self.assertEqual(metrics["failed_steps"], 0)
        self.assertTrue(any(event["type"] == "PIPELINE_FINISHED" for event in context.events()))

        traces = context.execution_traces()
        self.assertGreaterEqual(len(traces), 1)
        first_trace = traces[0]
        self.assertIn("task_type", first_trace)
        self.assertIn("classification_confidence", first_trace)

        decisions = context.model_decisions()
        self.assertGreaterEqual(len(decisions), 1)
        decision = decisions[0]
        self.assertIn("provider", decision)
        self.assertIn("model", decision)
        self.assertIn("reason", decision)

        self.assertEqual(decision["provider"], "openai")
        self.assertEqual(decision["model"], "gpt-4o-mini")

        self.assertIn("selected_provider", first_trace)
        self.assertIn("selected_model", first_trace)
        self.assertIn("routing_reason", first_trace)

        kernel.adapter_registry.get.assert_called_once_with("openai")
        fake_adapter.prepare_request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
