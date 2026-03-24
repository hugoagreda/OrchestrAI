# python -m core.tests.test_capability_kernel
import copy
import unittest
from unittest.mock import Mock

from core.action.capability_kernel import (
    ActionNotFoundError,
    CapabilityKernel,
    PayloadValidationError,
)
from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.runtime_step import RuntimeStep


class CapabilityKernelTests(unittest.TestCase):
    def _build_kernel_with_deterministic_router(self):
        kernel = CapabilityKernel()
        kernel.model_router.resolve = Mock(return_value={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "reason": "test_policy",
        })
        kernel.adapter_registry.get = Mock(return_value=Mock(prepare_request=Mock(return_value={
            "provider": "openai",
            "model": "gpt-4o-mini",
        })))
        return kernel

    def test_valid_action_resolution_from_manifest(self):
        kernel = CapabilityKernel()
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "manifest", "tone": "neutral"},
        })

        handler = kernel._resolve_handler(step)

        self.assertTrue(callable(handler))
        self.assertEqual(handler.__name__, "generate_script")
        self.assertEqual(handler.__module__, "core.action.content.content_actions")

    def test_invalid_action_rejection_includes_namespace_and_action(self):
        kernel = CapabilityKernel()
        step = RuntimeStep({
            "capability": "content",
            "action": "not_declared",
            "payload": {"topic": "x", "tone": "y"},
        })

        with self.assertRaises(ActionNotFoundError) as error:
            kernel._resolve_handler(step)

        self.assertIn("not_declared", str(error.exception))
        self.assertIn("content", str(error.exception))

    def test_payload_validation_happens_before_routing(self):
        kernel = self._build_kernel_with_deterministic_router()
        context = ExecutionContext()
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "missing tone"},
        })

        with self.assertRaises(PayloadValidationError):
            kernel.execute(step, context)

        kernel.model_router.resolve.assert_not_called()
        self.assertEqual(context.execution_traces(), [])

    def test_kernel_does_not_create_or_modify_external_classification(self):
        kernel = self._build_kernel_with_deterministic_router()
        context = ExecutionContext()
        classification = {"task_type": "external", "confidence": 1.0}
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "classification", "tone": "neutral"},
            "metadata": {"classification": classification},
        })
        original = copy.deepcopy(classification)

        kernel.execute(step, context)

        self.assertEqual(classification, original)
        self.assertIsNone(context.get("classification"))

    def test_kernel_uses_posture_policy_without_overriding_it(self):
        kernel = self._build_kernel_with_deterministic_router()
        context = ExecutionContext()
        posture = {
            "routing_policy": "high_quality",
            "allowed_actions": ["generate_script"],
        }
        context.set_posture(posture)
        before = copy.deepcopy(context.get_posture())

        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "policy", "tone": "neutral"},
        })

        kernel.execute(step, context)

        self.assertEqual(context.get_posture(), before)
        self.assertEqual(
            kernel.model_router.resolve.call_args.kwargs["routing_policy"],
            "high_quality",
        )

    def test_execution_trace_includes_cost_and_savings_fields(self):
        kernel = self._build_kernel_with_deterministic_router()
        context = ExecutionContext()
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "cost trace", "tone": "neutral"},
        })

        kernel.execute(step, context)

        trace = context.execution_traces()[-1]
        self.assertIn("selected_model", trace)
        self.assertIn("estimated_cost", trace)
        self.assertIn("baseline_cost", trace)
        self.assertIn("savings", trace)
        self.assertIn("savings_ratio", trace)
        self.assertIn("decision_flag", trace)

    def test_execution_trace_respects_baseline_override(self):
        kernel = self._build_kernel_with_deterministic_router()
        context = ExecutionContext()
        context.set_runtime("baseline_model", "gpt-4o-mini")

        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "baseline override", "tone": "neutral"},
        })

        kernel.execute(step, context)
        trace = context.execution_traces()[-1]

        self.assertEqual(trace.get("baseline_model"), "gpt-4o-mini")
        self.assertEqual(trace.get("savings"), 0.0)


if __name__ == "__main__":
    unittest.main()
