import unittest

from core.action.capability_kernel import CapabilityKernel
from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.runtime_step import RuntimeStep


class CapabilityKernelTests(unittest.TestCase):
    def test_execute_known_action_updates_context(self):
        kernel = CapabilityKernel()
        context = ExecutionContext()
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "unit test", "tone": "neutral"},
        })

        kernel.execute(step, context)
        self.assertIsNotNone(context.get("script_raw"))

    def test_handler_cache_stats_track_hits_and_misses(self):
        kernel = CapabilityKernel()
        context = ExecutionContext()
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "cache test", "tone": "neutral"},
        })

        kernel.execute(step, context)
        kernel.execute(step, context)

        stats = kernel.cache_stats()
        self.assertGreaterEqual(stats["misses"], 1)
        self.assertGreaterEqual(stats["hits"], 1)
        self.assertGreaterEqual(stats["size"], 1)


if __name__ == "__main__":
    unittest.main()
