# python -m core.tests.test_simulation_engine
import unittest

from core.simulation.simulation_engine import simulate_execution


class SimulationEngineTests(unittest.TestCase):
    def test_multiple_inputs_aggregate(self):
        result = simulate_execution(
            [
                "Summarize this short paragraph.",
                "Analyze these KPI trends and provide recommendations.",
                "Rewrite this sentence clearly.",
            ],
            policy="balanced",
        )

        self.assertEqual(result["total_requests"], 3)
        self.assertIn("total_cost", result)
        self.assertIn("baseline_cost", result)
        self.assertIn("total_savings", result)
        self.assertIn("savings_ratio", result)

    def test_empty_inputs_returns_zeros(self):
        result = simulate_execution([], policy="balanced")

        self.assertEqual(result["total_requests"], 0)
        self.assertEqual(result["total_cost"], 0.0)
        self.assertEqual(result["baseline_cost"], 0.0)
        self.assertEqual(result["total_savings"], 0.0)
        self.assertEqual(result["savings_ratio"], 0.0)

    def test_savings_positive_when_cheaper_model_selected(self):
        result = simulate_execution(
            [
                "Quickly summarize this note.",
                "Rephrase this sentence.",
            ],
            policy="fast",
        )

        self.assertGreater(result["total_savings"], 0.0)


if __name__ == "__main__":
    unittest.main()
