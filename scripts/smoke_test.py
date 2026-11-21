"""Post-deploy smoke test: python scripts/smoke_test.py http://host:port [expected_git_sha]
Exits non-zero on failure so the pipeline job (and rollback) reacts."""

import json
import sys
import time
import urllib.request


def call(url, data=None):
    req = urllib.request.Request(
        url, data=json.dumps(data).encode() if data else None, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def main(base, sha=None):
    for _ in range(20):  # wait for rollout
        try:
            if call(f"{base}/healthz")["status"] == "ok":
                break
        except Exception:
            time.sleep(2)
    else:
        sys.exit("FAIL: service never became healthy")
    if sha and call(f"{base}/version")["git_sha"] != sha:
        sys.exit("FAIL: running version does not match the commit being deployed")
    out = call(
        f"{base}/kpis",
        dict(
            cell_id="SMOKE-001",
            site="ci",
            prb_utilization_pct=95,
            dl_throughput_mbps=1,
            drop_call_rate_pct=0,
            latency_ms=1,
        ),
    )
    assert out["alerts"], "expected congestion alert"
    print("smoke test OK")


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"), sys.argv[2] if len(sys.argv) > 2 else None)
