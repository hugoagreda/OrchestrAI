# python -m core.tests.test_execution_trace
import unittest

from core.execution_layer.execution_trace import (
    DEFAULT_BASELINE_MODEL,
    compute_savings,
    estimate_cost,
)


class ExecutionTraceCostTests(unittest.TestCase):
    def test_estimate_cost_is_deterministic(self):
        cost = estimate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=500)
        self.assertGreater(cost, 0.0)
        self.assertAlmostEqual(cost, estimate_cost("gpt-4o-mini", 1000, 500))

    def test_compute_savings_positive_when_selected_is_cheaper(self):
        result = compute_savings(
            selected_model="gpt-4o-mini",
            baseline_model=DEFAULT_BASELINE_MODEL,
            tokens={"input_tokens": 1200, "output_tokens": 600},
        )
        self.assertGreater(result["savings"], 0.0)
        self.assertGreater(result["savings_ratio"], 0.0)

    def test_compute_savings_zero_when_same_model(self):
        result = compute_savings(
            selected_model="gpt-4o-mini",
            baseline_model="gpt-4o-mini",
            tokens=900,
        )
        self.assertEqual(result["savings"], 0.0)
        self.assertEqual(result["savings_ratio"], 0.0)
        self.assertEqual(result["decision_flag"], "non_optimized")

    def test_decision_flag_low_impact_for_small_savings_ratio(self):
        result = compute_savings(
            selected_model="claude-3-haiku",
            baseline_model="openrouter/auto",
            tokens={"input_tokens": 100, "output_tokens": 1000},
        )

        self.assertGreater(result["savings"], 0.0)
        self.assertLess(result["savings_ratio"], 0.2)
        self.assertEqual(result["decision_flag"], "low_impact")

    def test_decision_flag_high_impact_for_large_savings_ratio(self):
        result = compute_savings(
            selected_model="gpt-4o-mini",
            baseline_model=DEFAULT_BASELINE_MODEL,
            tokens={"input_tokens": 1200, "output_tokens": 600},
        )

        self.assertGreaterEqual(result["savings_ratio"], 0.2)
        self.assertEqual(result["decision_flag"], "high_impact")


if __name__ == "__main__":
    unittest.main()
