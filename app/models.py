from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CellKpi(BaseModel):
    """A single KPI sample reported by a radio cell (e.g. a 5G NR gNodeB cell)."""

    cell_id: str = Field(..., min_length=3, examples=["STO-0001-A"])
    site: str = Field(..., examples=["Stockholm-Kista"])
    prb_utilization_pct: float = Field(..., ge=0, le=100)
    dl_throughput_mbps: float = Field(..., ge=0)
    drop_call_rate_pct: float = Field(..., ge=0, le=100)
    latency_ms: float = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    cell_id: str
    severity: str  # "warning" | "critical"
    rule: str
    message: str
