from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["critical", "high", "medium", "low", "info"]


class Signal(BaseModel):
    source: str
    kind: str
    title: str
    severity: Severity = "info"
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    reference: str | None = None
    observed_at: datetime = Field(default_factory=datetime.utcnow)


class TenantHealth(BaseModel):
    tenant: str
    assets: int
    log_sources: int
    open_incidents: int
    critical_alerts: int
    ingest_latency_seconds: int
    health: Literal["healthy", "degraded", "critical"]
