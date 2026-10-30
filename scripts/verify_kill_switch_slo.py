"""Verify <200ms SLO from load test results.

Per the Stage B Verification Suite spec §1.6.
Exit non-zero if SLO not met. This is the gate check — non-negotiable.
"""

import json
import sys
import argparse
from pathlib import Path


def verify_slo(input_path: str, threshold_ms: int = 200):
    """Verify <200ms SLO from load test results. Exit 1 if not met."""
    path = Path(input_path)
    if not path.exists():
        print(f"ERROR: Results file not found: {input_path}")
        sys.exit(2)

    with open(path) as f:
        results = json.load(f)

    if "error" in results:
        print(f"ERROR: {results['error']}")
        print("Gate is RED — no disconnects recorded.")
        sys.exit(1)

    p99 = results["results"]["p99_ms"]
    slo_met = results["results"]["slo_met"]

    print("<200ms SLO Verification:")
    print(f"  p99: {p99:.2f}ms")
    print(f"  Threshold: {threshold_ms}ms")
    print(f"  SLO Met: {slo_met}")
    print(f"  Disconnects recorded: {results['results']['disconnects_recorded']}")

    if not slo_met:
        print(f"\nFAILED: p99 ({p99:.2f}ms) exceeds threshold ({threshold_ms}ms)")
        print("Gate is RED. Do NOT proceed to Phase 15.")
        print("\nCommon bottlenecks:")
        print("  - DB commit >50ms: add indexes, optimize triggers")
        print("  - Outbox relay poll interval too long: reduce to 25ms")
        print("  - WebSocket sever >80ms: optimize connection registry lookup")
        sys.exit(1)
    else:
        print(f"\nPASSED: p99 ({p99:.2f}ms) within threshold ({threshold_ms}ms)")
        print("Gate item 15 (Kill Switch <200ms SLO) is GREEN.")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify <200ms Kill Switch SLO")
    parser.add_argument("--input", required=True, help="Path to kill_switch_results.json")
    parser.add_argument("--threshold-ms", type=int, default=200, help="SLO threshold in ms (default: 200)")
    args = parser.parse_args()
    verify_slo(args.input, args.threshold_ms)
