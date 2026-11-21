"""Threshold rules - kept separate so they are trivial to unit test."""

from .models import Alert, CellKpi

RULES = [
    # (rule name, predicate, severity, message template)
    (
        "prb_congestion",
        lambda k: k.prb_utilization_pct >= 90,
        "critical",
        "PRB utilization {k.prb_utilization_pct:.0f}% - cell congested",
    ),
    (
        "prb_high",
        lambda k: 80 <= k.prb_utilization_pct < 90,
        "warning",
        "PRB utilization {k.prb_utilization_pct:.0f}% - nearing congestion",
    ),
    (
        "drop_rate",
        lambda k: k.drop_call_rate_pct >= 2.0,
        "critical",
        "Drop call rate {k.drop_call_rate_pct:.2f}% above 2% threshold",
    ),
    (
        "high_latency",
        lambda k: k.latency_ms >= 50,
        "warning",
        "Latency {k.latency_ms:.0f} ms above 50 ms target",
    ),
]


def evaluate(kpi: CellKpi) -> list[Alert]:
    return [
        Alert(cell_id=kpi.cell_id, severity=sev, rule=name, message=tmpl.format(k=kpi))
        for name, pred, sev, tmpl in RULES
        if pred(kpi)
    ]
