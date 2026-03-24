# python -m core.tests.test_cost_aggregator
import unittest

from core.execution_layer.cost_aggregator import aggregate_costs


class CostAggregatorTests(unittest.TestCase):
    def test_multiple_traces_aggregate_correctly(self):
        traces = [
            {
                "estimated_cost": 0.002,
                "baseline_cost": 0.005,
                "savings": 0.003,
            },
            {
                "estimated_cost": 0.004,
                "baseline_cost": 0.006,
                "savings": 0.002,
            },
        ]

        result = aggregate_costs(traces)
        print("[COST AGGREGATOR][multiple]", result)

        self.assertEqual(result["total_requests"], 2)
        self.assertEqual(result["total_cost"], 0.006)
        self.assertEqual(result["baseline_cost"], 0.011)
        self.assertEqual(result["total_savings"], 0.005)

    def test_empty_input_returns_zeros(self):
        result = aggregate_costs([])
        print("[COST AGGREGATOR][empty]", result)

        self.assertEqual(result["total_requests"], 0)
        self.assertEqual(result["total_cost"], 0.0)
        self.assertEqual(result["baseline_cost"], 0.0)
        self.assertEqual(result["total_savings"], 0.0)
        self.assertEqual(result["savings_ratio"], 0.0)

    def test_savings_ratio_computed_correctly(self):
        traces = [
            {
                "estimated_cost": 0.001,
                "baseline_cost": 0.004,
                "savings": 0.003,
            },
            {
                "estimated_cost": 0.002,
                "baseline_cost": 0.004,
                "savings": 0.002,
            },
        ]

        result = aggregate_costs(traces)
        print("[COST AGGREGATOR][ratio]", result)

        self.assertAlmostEqual(result["savings_ratio"], 0.625)


if __name__ == "__main__":
    unittest.main()
