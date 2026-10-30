"""Kill Switch <200ms SLO Load Test.

Per the Stage B Verification Suite spec §1.5.
Per ADR-0089 / DEC-0089. Regulator-mandated <200ms SLO.

This script:
1. Opens N WebSocket connections to the server.
2. Triggers the kill switch via API.
3. Measures time from trigger commit to WebSocket disconnect.
4. Reports p50/p95/p99/max latency.

Usage:
  python scripts/kill_switch_load_test.py \
    --target http://localhost:8000 \
    --connections 1000 \
    --triggers 100 \
    --output verify-results/kill_switch_results.json
"""

import argparse
import asyncio
import json
import statistics
import time
import urllib.request
from pathlib import Path

try:
    import websockets
except ImportError:
    websockets = None
    print("WARNING: websockets not installed. Install with: pip install websockets")


class KillSwitchLoadTest:
    """Kill Switch <200ms SLO load test. Per ADR-0089."""

    def __init__(self, target_url: str, num_connections: int, num_triggers: int):
        self.target_url = target_url
        self.ws_url = target_url.replace("http", "ws") + "/ws/kill-switch/"
        self.num_connections = num_connections
        self.num_triggers = num_triggers
        self.connections: dict[str, object] = {}
        self.trigger_times: dict[str, dict] = {}
        self.disconnect_times: dict[str, list[float]] = {}

    async def run_load_test(self):
        """Run the full load test."""
        print(f"Kill Switch <200ms SLO Load Test")
        print(f"  Target: {self.target_url}")
        print(f"  WebSocket: {self.ws_url}")
        print(f"  Connections: {self.num_connections}")
        print(f"  Triggers: {self.num_triggers}")
        print()

        if websockets is None:
            print("ERROR: websockets package not installed.")
            return

        # Phase 1: Open connections
        print(f"Opening {self.num_connections} WebSocket connections...")
        for i in range(self.num_connections):
            player_id = f"player_{i}"
            try:
                ws = await websockets.connect(
                    self.ws_url,
                    extra_headers={"X-Player-ID": player_id},
                    close_timeout=5,
                )
                self.connections[player_id] = ws
                self.disconnect_times[player_id] = []
            except Exception as e:
                print(f"  Failed to connect player_{i}: {e}")
        print(f"  Connected: {len(self.connections)}")

        # Phase 2: Trigger kill switches
        print(f"\nTriggering {self.num_triggers} kill switch events...")
        for i in range(self.num_triggers):
            trigger_id = f"trigger_{i}"

            # Record trigger time (before API call = "commit" time).
            commit_time = time.monotonic() * 1000  # ms

            try:
                # Trigger kill switch via API.
                req = urllib.request.Request(
                    f"{self.target_url}/api/v1/admin/kill-switch/trigger/",
                    method="POST",
                    data=json.dumps({
                        "reason": f"load_test_trigger_{i}",
                        "scope": "global",
                    }).encode(),
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                print(f"  Trigger {i} failed: {e}")
                continue

            self.trigger_times[trigger_id] = {
                "commit_time_ms": commit_time,
                "commit_latency_ms": time.monotonic() * 1000 - commit_time,
            }

            # Wait for disconnects (measure latency).
            await asyncio.sleep(0.3)  # 300ms window for disconnects.

            for player_id, ws in list(self.connections.items()):
                try:
                    # Check if connection is still open.
                    await asyncio.wait_for(ws.recv(), timeout=0.01)
                except asyncio.TimeoutError:
                    pass  # Still open.
                except Exception:
                    # Disconnected!
                    disconnect_time = time.monotonic() * 1000
                    latency = disconnect_time - commit_time
                    self.disconnect_times[player_id].append(latency)

        # Phase 3: Close remaining connections
        print("\nClosing remaining connections...")
        await self.close_all()

    async def close_all(self):
        """Close all WebSocket connections."""
        for player_id, ws in list(self.connections.items()):
            try:
                await ws.close()
            except Exception:
                pass

    def generate_report(self, output_path: str):
        """Generate load test report as JSON."""
        latencies = []
        for player_id, times in self.disconnect_times.items():
            latencies.extend(times)

        if not latencies:
            print("WARNING: No disconnect times recorded!")
            report = {
                "test_config": {
                    "num_connections": self.num_connections,
                    "num_triggers": self.num_triggers,
                },
                "results": {
                    "disconnects_recorded": 0,
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                    "max_ms": 0,
                    "min_ms": 0,
                    "slo_threshold_ms": 200,
                    "slo_met": False,
                },
                "error": "No disconnects recorded — server may not have kill switch endpoint",
            }
        else:
            p50 = statistics.median(latencies)
            p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)

            report = {
                "test_config": {
                    "num_connections": self.num_connections,
                    "num_triggers": self.num_triggers,
                },
                "results": {
                    "disconnects_recorded": len(latencies),
                    "p50_ms": round(p50, 2),
                    "p95_ms": round(p95, 2),
                    "p99_ms": round(p99, 2),
                    "max_ms": round(max_latency, 2),
                    "min_ms": round(min_latency, 2),
                    "slo_threshold_ms": 200,
                    "slo_met": p99 < 200,
                },
                "trigger_latencies": {
                    tid: data["commit_latency_ms"]
                    for tid, data in self.trigger_times.items()
                },
            }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nKill Switch <200ms SLO Load Test Results:")
        print(f"  Connections: {self.num_connections}")
        print(f"  Triggers: {self.num_triggers}")
        print(f"  Disconnects recorded: {report['results']['disconnects_recorded']}")
        print(f"  p50: {report['results']['p50_ms']:.2f}ms")
        print(f"  p95: {report['results']['p95_ms']:.2f}ms")
        print(f"  p99: {report['results']['p99_ms']:.2f}ms")
        print(f"  Max: {report['results']['max_ms']:.2f}ms")
        print(f"  SLO (<200ms): {'PASS' if report['results']['slo_met'] else 'FAIL'}")
        print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kill Switch <200ms SLO Load Test")
    parser.add_argument("--target", default="http://localhost:8000",
                        help="Target server URL (default: http://localhost:8000)")
    parser.add_argument("--connections", type=int, default=1000,
                        help="Number of WebSocket connections (default: 1000)")
    parser.add_argument("--triggers", type=int, default=100,
                        help="Number of kill switch triggers (default: 100)")
    parser.add_argument("--output", default="verify-results/kill_switch_results.json",
                        help="Output file path (default: verify-results/kill_switch_results.json)")
    args = parser.parse_args()

    test = KillSwitchLoadTest(args.target, args.connections, args.triggers)
    asyncio.run(test.run_load_test())
    test.generate_report(args.output)
