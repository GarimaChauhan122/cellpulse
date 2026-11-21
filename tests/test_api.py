from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
GOOD = dict(
    cell_id="STO-0002-B",
    site="Kista",
    prb_utilization_pct=92,
    dl_throughput_mbps=120,
    drop_call_rate_pct=0.5,
    latency_ms=20,
)


def test_health():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_ingest_and_alert_flow():
    r = client.post("/kpis", json=GOOD)
    assert r.status_code == 202
    assert r.json()["alerts"][0]["severity"] == "critical"
    assert client.get("/cells/STO-0002-B").status_code == 200
    assert any(a["cell_id"] == "STO-0002-B" for a in client.get("/alerts?severity=critical").json())


def test_validation_rejects_bad_payload():
    assert client.post("/kpis", json={**GOOD, "prb_utilization_pct": 140}).status_code == 422


def test_unknown_cell_404():
    assert client.get("/cells/nope").status_code == 404


def test_metrics_exposed():
    client.post("/kpis", json=GOOD)
    assert "cellpulse_kpi_ingested_total" in client.get("/metrics/").text
