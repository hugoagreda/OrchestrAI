# python -m core.tests.test_simulate_cli
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from core.cli.simulate_cli import main


class SimulateCliTests(unittest.TestCase):
    def test_cli_report_output_structure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            input_path.write_text(
                "Summarize this short paragraph.\n"
                "Analyze these KPI trends and provide recommendations.\n",
                encoding="utf-8",
            )

            captured = io.StringIO()
            with redirect_stdout(captured):
                exit_code = main([str(input_path)])

            output = captured.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("OrchestrAI Simulation Report", output)
        self.assertIn("total_requests:", output)
        self.assertIn("total_cost:", output)
        self.assertIn("baseline_cost:", output)
        self.assertIn("savings:", output)
        self.assertIn("savings_ratio:", output)
        self.assertIn("high_impact %:", output)
        self.assertIn("low_impact %:", output)
        self.assertIn("non_optimized %:", output)


if __name__ == "__main__":
    unittest.main()
