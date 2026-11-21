"""Continuously sends realistic KPI samples to CellPulse so metrics keep moving.

Usage:
    python scripts/simulate_traffic.py                      # 8 cells, 1 sample/cell every 2s, runs until Ctrl+C
    python scripts/simulate_traffic.py --cells 15 --interval 1 --duration 120
    python scripts/simulate_traffic.py --url http://localhost:8080 --seed 42

Each cell does a random walk around a base load, with occasional congestion
spikes and call-drop bursts, so you get a mix of healthy samples and alerts.
Uses only the standard library (no extra pip install).
"""

import argparse
import json
import random
import time
import urllib.error
import urllib.request

SITES = ["Stockholm-Kista", "Stockholm-Solna", "Gothenburg-Centrum", "Malmo-Hamnen", "Uppsala-Norra"]


class Cell:
    def __init__(self, idx: int):
        self.cell_id = f"STO-{idx:04d}-{random.choice('ABC')}"
        self.site = random.choice(SITES)
        self.base_load = random.uniform(35, 75)  # typical PRB utilisation
        self.load = self.base_load
        self.spike_left = 0  # samples remaining in a congestion spike

    def sample(self) -> dict:
        # random walk pulled back towards the base load
        self.load += random.gauss(0, 4) + (self.base_load - self.load) * 0.15
        if self.spike_left == 0 and random.random() < 0.04:  # ~4% chance a spike begins
            self.spike_left = random.randint(2, 5)
        if self.spike_left:
            self.spike_left -= 1
            self.load = random.uniform(88, 99)
        prb = max(2.0, min(99.5, self.load))

        congested = prb > 85
        return {
            "cell_id": self.cell_id,
            "site": self.site,
            "prb_utilization_pct": round(prb, 1),
            # throughput per cell rises with load, then flattens/drops when congested
            "dl_throughput_mbps": round(
                max(5, prb * 4 - (prb - 85) * 15 * congested + random.gauss(0, 15)), 1
            ),
            "drop_call_rate_pct": round(max(0, random.gauss(0.4 + 2.5 * congested, 0.4)), 2),
            "latency_ms": round(max(5, random.gauss(14 + 45 * congested, 5)), 1),
        }


def post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{url}/kpis", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--cells", type=int, default=8)
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between rounds")
    ap.add_argument("--duration", type=float, default=0, help="stop after N seconds (0 = run forever)")
    ap.add_argument("--seed", type=int, default=None, help="fixed seed for reproducible runs")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    cells = [Cell(i + 1) for i in range(args.cells)]
    url = args.url.rstrip("/")
    sent = alerts = errors = 0
    start = time.time()
    print(f"Sending KPIs for {len(cells)} cells to {url} every {args.interval}s (Ctrl+C to stop)")

    try:
        while not args.duration or time.time() - start < args.duration:
            for cell in cells:
                kpi = cell.sample()
                try:
                    result = post(url, kpi)
                    sent += 1
                    for a in result["alerts"]:
                        alerts += 1
                        print(f"  ALERT [{a['severity']:8}] {a['cell_id']}: {a['message']}")
                except (urllib.error.URLError, TimeoutError) as exc:
                    errors += 1
                    print(f"  ! could not reach {url}: {exc}")
            print(f"[{time.strftime('%H:%M:%S')}] sent={sent} alerts={alerts} errors={errors}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    print(f"\nDone. sent={sent} alerts={alerts} errors={errors}")


if __name__ == "__main__":
    main()
