import asyncio

import httpx

from msp_sentinel.collectors import cisa, feodo, nvd, urlhaus
from msp_sentinel.collectors.demo import signals as demo_signals
from msp_sentinel.collectors.demo import tenants
from msp_sentinel.config import settings
from msp_sentinel.services.resilience import CircuitBreaker, retry
from msp_sentinel.services.intelligence import build_exposure, build_graph, build_timeline, build_watchlist

COLLECTORS = {"CISA KEV": cisa.collect, "NVD": nvd.collect, "URLhaus": urlhaus.collect, "Feodo Tracker": feodo.collect}
BREAKERS = {name: CircuitBreaker() for name in COLLECTORS}


async def snapshot() -> dict:
    health = {}
    gathered = []
    async with httpx.AsyncClient(timeout=settings.http_timeout, follow_redirects=True, headers={"User-Agent": "MSP-Sentinel-AI/0.1"}) as client:
        async def one(name, fn):
            try:
                rows = await BREAKERS[name].run(lambda: retry(lambda: fn(client)))
                health[name] = {"status": "online", "signals": len(rows)}
                return rows
            except Exception as exc:
                health[name] = {"status": "degraded", "signals": 0, "error": type(exc).__name__}
                return []

        batches = await asyncio.gather(*(one(name, fn) for name, fn in COLLECTORS.items()))
        for batch in batches:
            gathered.extend(batch)

    if not gathered:
        gathered = demo_signals()
        health["Demo Fusion"] = {"status": "fallback", "signals": len(gathered)}

    severity_weight = {"critical": 20, "high": 10, "medium": 5, "low": 2, "info": 1}
    score = min(100, sum(severity_weight[s.severity] for s in gathered[:20]))
    counts = {level: sum(1 for s in gathered if s.severity == level) for level in severity_weight}
    signal_rows = [s.model_dump(mode="json") for s in gathered[:80]]
    tenant_rows = [t.model_dump() for t in tenants()]
    return {
        "schema_version": "2.0",
        "risk_score": score,
        "counts": counts,
        "signals": signal_rows,
        "tenants": tenant_rows,
        "exposure": build_exposure(signal_rows, tenant_rows),
        "timeline": build_timeline(signal_rows),
        "graph": build_graph(signal_rows, tenant_rows),
        "watchlist": build_watchlist(signal_rows),
        "sources": health,
    }
