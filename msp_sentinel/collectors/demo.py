from msp_sentinel.models import Signal, TenantHealth


def tenants() -> list[TenantHealth]:
    return [
        TenantHealth(tenant="Northstar Bank (Demo)", assets=428, log_sources=67, open_incidents=4, critical_alerts=1, ingest_latency_seconds=34, health="healthy"),
        TenantHealth(tenant="BluePeak Securities (Demo)", assets=211, log_sources=39, open_incidents=8, critical_alerts=3, ingest_latency_seconds=91, health="degraded"),
        TenantHealth(tenant="Harbor Health (Demo)", assets=319, log_sources=52, open_incidents=2, critical_alerts=0, ingest_latency_seconds=23, health="healthy"),
    ]


def signals() -> list[Signal]:
    return [
        Signal(source="Demo Fusion", kind="c2", title="C2 infrastructure activity cluster", severity="critical", country="DE", latitude=50.11, longitude=8.68),
        Signal(source="Demo Fusion", kind="ransomware", title="Ransomware precursor behavior", severity="high", country="IN", latitude=19.07, longitude=72.87),
        Signal(source="Demo Fusion", kind="phishing", title="Credential phishing campaign", severity="medium", country="US", latitude=37.77, longitude=-122.42),
    ]
