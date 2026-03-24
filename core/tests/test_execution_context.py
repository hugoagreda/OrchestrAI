# python -m core.tests.test_execution_context
import unittest

from core.execution_layer.execution_context import ExecutionContext


class ExecutionContextTests(unittest.TestCase):
    def test_initialization_contains_input_policy_budget_status_and_trace(self):
        context = ExecutionContext()
        context.set_runtime("input", {"query": "hello"})
        context.set_runtime("policy", {"routing_policy": "balanced"})
        context.set_runtime("budget_status", "healthy")

        dump = context.dump()

        self.assertIn("input", dump["state"]["runtime"])
        self.assertIn("policy", dump["state"]["runtime"])
        self.assertEqual(dump["state"]["runtime"]["budget_status"], "healthy")
        self.assertEqual(context.execution_traces(), [])

    def test_trace_accumulates_without_overwriting(self):
        context = ExecutionContext()
        classification_trace = {
            "stage": "classification",
            "task_type": "analysis",
        }
        routing_trace = {
            "stage": "routing",
            "provider": "openai",
            "model": "gpt-4o-mini",
        }

        context.log_execution_trace(classification_trace)
        context.log_execution_trace(routing_trace)

        traces = context.execution_traces()
        self.assertEqual(len(traces), 2)
        self.assertEqual(traces[0]["stage"], "classification")
        self.assertEqual(traces[1]["stage"], "routing")

    def test_input_immutability_after_execution_updates(self):
        context = ExecutionContext()
        original_input = {"query": "immutable", "options": {"tone": "neutral"}}
        snapshot = {
            "query": "immutable",
            "options": {"tone": "neutral"},
        }

        context.set_runtime("input", dict(original_input))
        context.log_execution_trace({"stage": "classification"})
        context.set("script_raw", "some result")
        context.start_pipeline(1)
        context.finish_pipeline()

        self.assertEqual(original_input, snapshot)

    def test_budget_status_propagates_across_steps(self):
        context = ExecutionContext()
        context.set_runtime("budget_status", "healthy")

        context.log_execution_trace({"stage": "classification"})
        self.assertEqual(context.get_runtime("budget_status"), "healthy")

        context.log_execution_trace({"stage": "routing"})
        self.assertEqual(context.get_runtime("budget_status"), "healthy")

    def test_context_isolation_between_executions(self):
        first = ExecutionContext()
        second = ExecutionContext()

        first.set_runtime("input", {"query": "first"})
        first.log_execution_trace({"execution_id": "A"})

        second.set_runtime("input", {"query": "second"})
        second.log_execution_trace({"execution_id": "B"})

        self.assertEqual(first.get_runtime("input")["query"], "first")
        self.assertEqual(second.get_runtime("input")["query"], "second")
        self.assertEqual(first.execution_traces()[0]["execution_id"], "A")
        self.assertEqual(second.execution_traces()[0]["execution_id"], "B")


if __name__ == "__main__":
    unittest.main()
