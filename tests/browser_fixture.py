"""Offline browser test server. Never imported by the installed application."""
import json
from datetime import datetime, timedelta, timezone

import httpx

from msp_sentinel.app import app
from msp_sentinel.collectors import wazuh
from msp_sentinel.collectors.demo import signals
from msp_sentinel.config import Settings, settings
from msp_sentinel.services import fusion
from msp_sentinel.services.resilience import CircuitBreaker

settings.ollama_model = None
settings.wazuh_tenants = Settings(_env_file=None, wazuh_tenants={
    tenant: {"indexer_url": "https://synthetic-indexer.test", "username": "reader",
             "password": "synthetic-password", "api_token": f"synthetic-tenant-{tenant}-token-000000000000",
             "agent_ids": [agent]}
    for tenant, agent in [("a", "001"), ("b", "002")]
}).wazuh_tenants


async def synthetic_feed(client):
    return signals()


fusion.COLLECTORS = {"Synthetic fixture": synthetic_feed}
fusion.BREAKERS = {"Synthetic fixture": CircuitBreaker()}
real_collect = wazuh.collect


async def synthetic_collect(tenant, *, limit):
    def upstream(request):
        assert request.method == "POST" and request.url.path == "/wazuh-alerts-*/_search"
        query = json.loads(request.content)
        agents = query["query"]["bool"]["filter"][0]["terms"]["agent.id"]
        assert set(agents) == tenant.agent_ids
        return httpx.Response(200, json={"timed_out": False, "_shards": {"failed": 0}, "hits": {"hits": [{"_source": {
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "agent": {"id": agents[0]},
            "rule": {"id": "5710", "level": 12, "description": f"Private synthetic alert {agents[0]}"},
            "full_log": "PRIVATE RAW LOG",
        }}]}})
    return await real_collect(tenant, limit=limit, transport=httpx.MockTransport(upstream))


wazuh.collect = synthetic_collect
