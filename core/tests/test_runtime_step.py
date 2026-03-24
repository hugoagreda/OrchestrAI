# python -m core.tests.test_runtime_step
import unittest
from unittest.mock import Mock

from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.execution_layer import ExecutionLayer
from core.execution_layer.runtime_step import RuntimeStep


class RuntimeStepTests(unittest.TestCase):
    def test_capability_key_builds_namespace_action(self):
        step = RuntimeStep({"capability": "content", "action": "generate_script"})
        self.assertEqual(step.capability_key(), "content.generate_script")

    def test_legacy_key_fallback(self):
        step = RuntimeStep({"action": "generate_script"})
        self.assertEqual(step.legacy_key(), "generate_script")

    def test_execution_order_is_classification_routing_dispatch(self):
        from core.action.capability_kernel import CapabilityKernel

        kernel = CapabilityKernel()
        context = ExecutionContext()
        order = []

        kernel.task_classifier.classify = Mock(side_effect=lambda step: (
            order.append("classification") or {
                "task_type": "text_generation",
                "token_estimate": 40,
                "confidence": 0.9,
            }
        ))
        kernel.model_router.resolve = Mock(side_effect=lambda **kwargs: (
            order.append("routing") or {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "reason": "test_route",
            }
        ))
        kernel.adapter_registry.get = Mock(return_value=Mock(prepare_request=Mock(return_value={
            "provider": "openai",
            "model": "gpt-4o-mini",
        })))

        def dispatch_handler(step, ctx):
            order.append("dispatch")
            ctx.set("script_raw", "ordered")

        kernel._resolve_handler = Mock(return_value=dispatch_handler)

        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "order", "tone": "neutral"},
        })

        kernel.execute(step, context)
        self.assertEqual(order, ["classification", "routing", "dispatch"])

    def test_posture_blocking_prevents_kernel_execution(self):
        class TrackingKernel:
            def __init__(self):
                self.calls = []

            def execute(self, step, context):
                self.calls.append((step.capability, step.action))

            def cache_stats(self):
                return {"hits": 0, "misses": 0, "size": 0}

        kernel = TrackingKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()
        context.set_posture({"restricted_capabilities": ["content.*"]})

        workflow = {
            "steps": [
                {
                    "capability": "content",
                    "action": "generate_script",
                    "payload": {"topic": "blocked", "tone": "neutral"},
                }
            ]
        }

        layer.execute(workflow, context)

        self.assertEqual(kernel.calls, [])
        self.assertEqual(context.metrics()["failed_steps"], 1)
        self.assertIn("restricted", context.metrics()["last_error"])

    def test_step_output_integrity_between_steps(self):
        class ChainedKernel:
            def execute(self, step, context):
                if step.action == "first":
                    context.set("first_output", {"status": "ok", "id": "A-1"})
                    return

                previous = context.get("first_output")
                context.set("second_observed", previous)

            def cache_stats(self):
                return {"hits": 0, "misses": 0, "size": 0}

        kernel = ChainedKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()

        workflow = {
            "steps": [
                {"capability": "content", "action": "first", "payload": {}},
                {"capability": "content", "action": "second", "payload": {}},
            ]
        }

        layer.execute(workflow, context)

        self.assertEqual(context.get("second_observed"), {"status": "ok", "id": "A-1"})
        self.assertEqual(context.metrics()["successful_steps"], 2)

    def test_failure_handling_captures_error_and_finishes_step(self):
        class FailingKernel:
            def execute(self, step, context):
                raise RuntimeError("simulated runtime failure")

            def cache_stats(self):
                return {"hits": 0, "misses": 0, "size": 0}

        kernel = FailingKernel()
        layer = ExecutionLayer(kernel)
        context = ExecutionContext()

        workflow = {
            "steps": [
                {
                    "capability": "content",
                    "action": "generate_script",
                    "payload": {"topic": "fail", "tone": "neutral"},
                }
            ]
        }

        layer.execute(workflow, context)

        metrics = context.metrics()
        self.assertEqual(metrics["failed_steps"], 1)
        self.assertIn("simulated runtime failure", metrics["last_error"])

        event_types = [event["type"] for event in context.events()]
        self.assertIn("STEP_CRITICAL_FAILURE", event_types)
        self.assertIn("STEP_FINISHED", event_types)


if __name__ == "__main__":
    unittest.main()
