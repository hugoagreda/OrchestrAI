import unittest

from core.execution_layer.execution_context import ExecutionContext


class ExecutionContextTests(unittest.TestCase):
    def test_metrics_lifecycle(self):
        context = ExecutionContext()
        context.start_pipeline(2)
        context.record_step_success("content", "generate_script", 12.5)
        context.record_step_failure("media", "generate_media", 8.2, "boom")
        context.finish_pipeline()

        metrics = context.metrics()
        self.assertEqual(metrics["total_steps"], 2)
        self.assertEqual(metrics["successful_steps"], 1)
        self.assertEqual(metrics["failed_steps"], 1)
        self.assertEqual(metrics["last_error"], "boom")

    def test_budget_lifecycle(self):
        context = ExecutionContext()
        context.set_budget(10.0)

        budget = context.get_budget()
        self.assertIsNotNone(budget)
        self.assertEqual(budget["total"], 10.0)
        self.assertEqual(budget["remaining"], 10.0)
        self.assertEqual(budget["spent"], 0.0)

        context.consume_budget(3.5)
        budget = context.get_budget()
        self.assertEqual(budget["remaining"], 6.5)
        self.assertEqual(budget["spent"], 3.5)


if __name__ == "__main__":
    unittest.main()
