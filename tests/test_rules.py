from app.models import CellKpi
from app.rules import evaluate


def kpi(**kw):
    base = dict(
        cell_id="STO-0001-A",
        site="Kista",
        prb_utilization_pct=40,
        dl_throughput_mbps=300,
        drop_call_rate_pct=0.2,
        latency_ms=12,
    )
    base.update(kw)
    return CellKpi(**base)


def test_healthy_cell_no_alerts():
    assert evaluate(kpi()) == []


def test_congestion_is_critical():
    alerts = evaluate(kpi(prb_utilization_pct=95))
    assert [a.rule for a in alerts] == ["prb_congestion"]
    assert alerts[0].severity == "critical"


def test_multiple_rules_fire():
    rules = {a.rule for a in evaluate(kpi(prb_utilization_pct=85, drop_call_rate_pct=3, latency_ms=70))}
    assert rules == {"prb_high", "drop_rate", "high_latency"}
