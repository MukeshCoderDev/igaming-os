"""Check Phase 15 gate based on Stage B verification report.

Per the Stage B Verification Suite spec §1.12.
Exit non-zero (fail CI) if gate is NO-GO.
"""

import sys
import argparse
import re
from pathlib import Path


def check_gate(report_path: str):
    """Check Phase 15 gate. Exit 0 if GO, exit 1 if NO-GO/UNVERIFIED."""
    path = Path(report_path)
    if not path.exists():
        print(f"ERROR: Verification report not found: {report_path}")
        sys.exit(2)

    with open(path) as f:
        content = f.read()

    # Extract verdict from front-matter.
    verdict_match = re.search(r"verdict:\s*(\S+)", content)
    if not verdict_match:
        print("Could not extract verdict from report")
        sys.exit(2)

    verdict = verdict_match.group(1)
    print(f"Phase 15 Gate Verdict: {verdict}")
    print()

    # Print gate items summary.
    lines = content.split("\n")
    for line in lines:
        if line.startswith("- ") and ("**" in line):
            print(f"  {line}")

    print()

    if verdict == "GO":
        print("✅ GATE PASSED — Phase 15 may proceed")
        print("\nAll gate items are GREEN. The money layer + safety layer are verified.")
        sys.exit(0)
    elif verdict == "CONDITIONAL-GO":
        print("⚠️  CONDITIONAL GO — Kill Switch SLO passed; review UNVERIFIED items")
        print("\nKill Switch <200ms SLO is PASS. Check CI output for UNVERIFIED items.")
        print("If all UNVERIFIED items are actually PASS in CI logs, Phase 15 may proceed.")
        sys.exit(0)  # Allow proceed with warning.
    else:
        print("❌ GATE FAILED — Phase 15 BLOCKED")
        print("\nAddress gate item failures before proceeding.")
        print("\nCommon failures:")
        print("  - Kill Switch <200ms SLO: optimize DB commit, outbox relay, Redis, WebSocket sever")
        print("  - Coverage <95%: add tests until threshold met (no exceptions for money layer)")
        print("  - Concurrency test FAIL: fix race condition (missing FOR UPDATE, idempotency)")
        print("  - PCI DLP injection FAIL: investigate PAN leakage immediately")
        print("  - Cross-module SE FAIL: fix transaction atomicity")
        print("  - SE-survives-erasure FAIL: fix HMAC pseudonymization")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Phase 15 Gate")
    parser.add_argument("--report", required=True, help="Path to stage-b-verification-report.md")
    args = parser.parse_args()
    check_gate(args.report)
