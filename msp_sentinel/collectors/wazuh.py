"""Bounded, read-only Wazuh indexer searches; never part of public CTI fusion."""

import json
import ssl
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class WazuhTenant(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    indexer_url: str
    username: str = Field(min_length=1)
    password: SecretStr
    api_token: SecretStr
    ca_file: str | None = None
    agent_ids: frozenset[Annotated[str, Field(pattern=r"^[0-9]{3,8}$")]] = Field(min_length=1, max_length=1000)
    index_pattern: str = Field(default="wazuh-alerts-*", pattern=r"^wazuh-alerts-[a-z0-9*._-]+$")

    @field_validator("indexer_url")
    @classmethod
    def validate_url(cls, value):
        url = urlsplit(value)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.path not in ("", "/") or url.query or url.fragment):
            raise ValueError("indexer_url must be an HTTPS origin without credentials or a path")
        port = url.port  # Validate the port before making requests.
        return f"https://{url.hostname.lower() if ':' not in url.hostname else '[' + url.hostname.lower() + ']'}:{port or 443}"

    @field_validator("password", "api_token")
    @classmethod
    def validate_secret(cls, value, info):
        if len(value.get_secret_value()) < (32 if info.field_name == "api_token" else 1):
            raise ValueError("secret is too short")
        return value

    @field_validator("agent_ids")
    @classmethod
    def exclude_manager(cls, value):
        if any(int(agent) == 0 for agent in value):
            raise ValueError("manager agent IDs cannot be assigned to a tenant")
        return value


class WazuhError(Exception):
    """Upstream failure. Its body and credentials must never reach API clients."""


class AlertSource(BaseModel):
    class Agent(BaseModel):
        id: str

    class Rule(BaseModel):
        id: str
        level: int = Field(strict=True, ge=0, le=16)
        description: str = Field(max_length=2000)

    agent: Agent
    rule: Rule
    timestamp: datetime


async def collect(tenant: WazuhTenant, *, limit: int = 50,
                  transport: httpx.AsyncBaseTransport | None = None) -> dict:
    """Use only POST _search (a read operation), with a fixed operator-owned scope."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)
    query = {
        "size": limit,
        "track_total_hits": False,
        "_source": ["timestamp", "agent.id", "rule.id", "rule.level", "rule.description"],
        "sort": [{"timestamp": "desc"}],
        "query": {"bool": {"filter": [
            {"terms": {"agent.id": sorted(tenant.agent_ids)}},
            {"range": {"timestamp": {"gte": start.isoformat(), "lte": now.isoformat()}}},
        ]}},
    }
    try:
        # Dedicated client: no shared auth/cookies, redirects, proxies, retries or caches.
        async with httpx.AsyncClient(
            auth=httpx.BasicAuth(tenant.username, tenant.password.get_secret_value()),
            timeout=httpx.Timeout(12), follow_redirects=False, trust_env=False,
            transport=transport, verify=ssl.create_default_context(cafile=tenant.ca_file),
        ) as client:
            async with client.stream("POST", f"{tenant.indexer_url}/{tenant.index_pattern}/_search",
                                     params={"allow_partial_search_results": "false"}, json=query) as response:
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 1_000_000:
                        raise WazuhError()
        data = json.loads(body)
        if data.get("timed_out") is not False or data["_shards"]["failed"] != 0:
            raise WazuhError()
        hits = data["hits"]["hits"]
        if not isinstance(hits, list) or len(hits) > limit:
            raise WazuhError()
        alerts = []
        for hit in hits:
            source = AlertSource.model_validate(hit["_source"])
            # Recheck upstream results; never silently drop a scope violation.
            if (source.agent.id not in tenant.agent_ids or source.timestamp.tzinfo is None
                    or not start <= source.timestamp <= now):
                raise WazuhError()
            level = source.rule.level
            alerts.append({
                "agent_id": source.agent.id, "rule_id": source.rule.id,
                "title": source.rule.description, "level": level,
                "severity": "critical" if level >= 15 else "high" if level >= 12 else
                            "medium" if level >= 7 else "low" if level >= 4 else "info",
                "observed_at": source.timestamp.isoformat(),
            })
        return {"source": "Wazuh indexer", "read_only": True, "window_hours": 24,
                "limit": limit, "at_limit": len(alerts) == limit,
                "alerts": alerts, "returned": len(alerts)}
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        raise WazuhError() from exc
