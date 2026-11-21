import os
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Gauge, make_asgi_app

from . import __version__
from .models import Alert, CellKpi
from .rules import evaluate

app = FastAPI(
    title="CellPulse",
    version=__version__,
    description="Tiny RAN KPI ingestion + alerting service (demo for CI/CD).",
)

KPI_INGESTED = Counter("cellpulse_kpi_ingested_total", "KPI samples ingested")
ALERTS_RAISED = Counter("cellpulse_alerts_total", "Alerts raised", ["severity"])
PRB_GAUGE = Gauge("cellpulse_prb_utilization_pct", "Latest PRB utilization", ["cell_id"])

_latest: dict[str, CellKpi] = {}
_alerts: dict[str, list[Alert]] = defaultdict(list)

app.mount("/metrics", make_asgi_app())


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/version")
def version():
    # GIT_SHA is injected at image build time by the pipeline -> traceability
    return {"version": __version__, "git_sha": os.getenv("GIT_SHA", "dev")}


@app.post("/kpis", status_code=202)
def ingest(kpi: CellKpi):
    _latest[kpi.cell_id] = kpi
    KPI_INGESTED.inc()
    PRB_GAUGE.labels(kpi.cell_id).set(kpi.prb_utilization_pct)
    alerts = evaluate(kpi)
    for a in alerts:
        _alerts[kpi.cell_id].append(a)
        ALERTS_RAISED.labels(a.severity).inc()
    return {"accepted": True, "alerts": alerts}


@app.get("/cells/{cell_id}")
def get_cell(cell_id: str):
    if cell_id not in _latest:
        raise HTTPException(404, "cell not found")
    return _latest[cell_id]


@app.get("/alerts")
def list_alerts(severity: str | None = None):
    all_alerts = [a for lst in _alerts.values() for a in lst]
    return [a for a in all_alerts if severity is None or a.severity == severity]
