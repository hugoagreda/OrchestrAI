"""CLI simulation report for OrchestrAI."""

from __future__ import annotations

import sys
from pathlib import Path

from core.simulation.simulation_engine import simulate_execution


def _read_inputs(file_path: str) -> list[str]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    lines: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line:
                lines.append(line)

    return lines


def _flag_distribution(traces: list[dict]) -> dict:
    total = len(traces)
    if total == 0:
        return {
            "high_impact_pct": 0.0,
            "low_impact_pct": 0.0,
            "non_optimized_pct": 0.0,
        }

    counts = {
        "high_impact": 0,
        "low_impact": 0,
        "non_optimized": 0,
    }

    for trace in traces:
        flag = str((trace or {}).get("decision_flag") or "non_optimized")
        if flag not in counts:
            flag = "non_optimized"
        counts[flag] += 1

    return {
        "high_impact_pct": round((counts["high_impact"] * 100.0) / total, 2),
        "low_impact_pct": round((counts["low_impact"] * 100.0) / total, 2),
        "non_optimized_pct": round((counts["non_optimized"] * 100.0) / total, 2),
    }


def _print_report(summary: dict, distribution: dict) -> None:
    print("\n=== OrchestrAI Simulation Report ===")
    print(f"total_requests: {summary.get('total_requests', 0)}")
    print(f"total_cost: {summary.get('total_cost', 0.0)}")
    print(f"baseline_cost: {summary.get('baseline_cost', 0.0)}")
    print(f"savings: {summary.get('total_savings', 0.0)}")
    print(f"savings_ratio: {summary.get('savings_ratio', 0.0)}")
    print(f"high_impact %: {distribution.get('high_impact_pct', 0.0)}")
    print(f"low_impact %: {distribution.get('low_impact_pct', 0.0)}")
    print(f"non_optimized %: {distribution.get('non_optimized_pct', 0.0)}")


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])

    if len(args) != 1:
        print("Usage: python -m core.cli.simulate_cli <input_file>")
        return 1

    input_file = args[0]

    try:
        inputs = _read_inputs(input_file)
    except FileNotFoundError as error:
        print(str(error))
        return 1

    result = simulate_execution(inputs, policy="balanced", return_details=True)
    summary = result.get("summary", {})
    traces = result.get("traces", [])

    distribution = _flag_distribution(traces)
    _print_report(summary, distribution)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
