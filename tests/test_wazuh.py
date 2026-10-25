"""Synthetic Wazuh wire contracts and adversarial tenant boundary checks."""
import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import msp_sentinel.app as app_module
from msp_sentinel.collectors import wazuh
from msp_sentinel.config import Settings

TOKEN_A = "synthetic-tenant-a-token-000000000000"
TOKEN_B = "synthetic-tenant-b-token-000000000000"


def config(agent="001", token=TOKEN_A, **overrides):
    return {"indexer_url": "https://indexer.example.test:9200", "username": "reader",
            "password": "synthetic-password", "api_token": token, "agent_ids": [agent], **overrides}


def payload(agent="001", level=12):
    return {"timed_out": False, "_shards": {"failed": 0}, "hits": {"hits": [{"_source": {
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "agent": {"id": agent, "name": "not exported"},
        "rule": {"id": "5710", "level": level, "description": "Synthetic SSH alert"},
        "full_log": "PRIVATE RAW LOG MUST NOT BE EXPORTED",
    }}]}}


def run_collect(handler, tenant=None, limit=50):
    return asyncio.run(wazuh.collect(tenant or wazuh.WazuhTenant(**config()), limit=limit,
                                    transport=httpx.MockTransport(handler)))


@pytest.mark.parametrize("level,severity", [(0,"info"),(3,"info"),(4,"low"),(6,"low"),
    (7,"medium"),(11,"medium"),(12,"high"),(14,"high"),(15,"critical"),(16,"critical")])
def test_wire_contract_and_normalization(level, severity):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.path == "/wazuh-alerts-*/_search"
        assert request.url.params["allow_partial_search_results"] == "false"
        assert request.headers["Authorization"].startswith("Basic ")
        query = json.loads(request.content)
        assert query["query"]["bool"]["filter"][0] == {"terms": {"agent.id": ["001"]}}
        assert "range" in query["query"]["bool"]["filter"][1]
        assert query["size"] == 50
        assert query["track_total_hits"] is False
        assert "full_log" not in query["_source"]
        return httpx.Response(200, json=payload(level=level))
    result = run_collect(handler)
    assert len(calls) == 1
    assert result["alerts"][0]["severity"] == severity
    assert result["returned"] == 1 and result["read_only"]
    assert "PRIVATE" not in json.dumps(result) and "not exported" not in json.dumps(result)


@pytest.mark.parametrize("status", [301,302,307,308,401,403,404,429,500,503])
def test_upstream_status_and_redirects_fail_closed(status):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"Location": "https://other.example/steal"},
                              text="sensitive upstream body")
    with pytest.raises(wazuh.WazuhError):
        run_collect(handler)
    assert len(calls) == 1


def test_timeout_fails_closed():
    def handler(request):
        raise httpx.ReadTimeout("secret upstream details", request=request)
    with pytest.raises(wazuh.WazuhError):
        run_collect(handler)


@pytest.mark.parametrize("case", ["other_tenant", "missing_agent", "malformed", "partial",
    "timeout", "invalid_level", "oversized", "too_many", "old", "no_timezone", "future"])
def test_invalid_or_unscoped_upstream_response_is_rejected(case):
    data = payload()
    source = data["hits"]["hits"][0]["_source"]
    if case == "other_tenant": source["agent"]["id"] = "002"
    if case == "missing_agent": del source["agent"]
    if case == "partial": data["_shards"]["failed"] = 1
    if case == "timeout": data["timed_out"] = True
    if case == "invalid_level": source["rule"]["level"] = 99
    if case == "too_many": data["hits"]["hits"] *= 51
    if case == "old": source["timestamp"] = "2000-01-01T00:00:00Z"
    if case == "no_timezone": source["timestamp"] = "2026-01-01T00:00:00"
    if case == "future": source["timestamp"] = "2099-01-01T00:00:00Z"
    def handler(request):
        if case == "malformed": return httpx.Response(200, text="not json")
        if case == "oversized": return httpx.Response(200, content=b"x" * 1_000_001)
        return httpx.Response(200, json=data)
    with pytest.raises(wazuh.WazuhError):
        run_collect(handler)


def test_empty_is_valid_and_limits_are_explicit():
    data = payload()
    data["hits"]["hits"] = []
    assert run_collect(lambda r: httpx.Response(200, json=data))["alerts"] == []
    result = run_collect(lambda r: httpx.Response(200, json=payload()), limit=1)
    assert result["at_limit"] and result["limit"] == 1
    for limit in (0, 101):
        with pytest.raises(ValueError): run_collect(lambda r: None, limit=limit)


@pytest.mark.parametrize("changes", [
    {"indexer_url": "http://indexer.test"}, {"indexer_url": "https://user:pass@indexer.test"},
    {"indexer_url": "https://indexer.test/path"}, {"indexer_url": "https://indexer.test?x=y"},
    {"indexer_url": "https://indexer.test#fragment"}, {"indexer_url": "https://indexer.test:bad"},
    {"index_pattern": "*"}, {"index_pattern": "wazuh-alerts-*/_delete_by_query"},
    {"index_pattern": "wazuh-alerts-*,private"}, {"agent_ids": []}, {"agent_ids": ["*"]},
    {"agent_ids": ["000"]}, {"agent_ids": ["0000"]}, {"api_token": "short"}, {"password": ""},
])
def test_unsafe_configuration_is_rejected(changes):
    with pytest.raises(ValidationError): wazuh.WazuhTenant(**config(**changes))


def test_registry_rejects_shared_tokens_and_overlapping_assignments():
    for second in (config("002"), config("001", TOKEN_B, indexer_url="https://INDEXER.example.test:9200/")):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, wazuh_tenants={"a": config(), "b": second})
    with pytest.raises(ValidationError):
        Settings(_env_file=None, wazuh_tenants={"../a": config()})
    assert "synthetic-password" not in repr(wazuh.WazuhTenant(**config()))


@pytest.fixture
def tenant_api(monkeypatch):
    registry = Settings(_env_file=None, wazuh_tenants={"a": config(), "b": config("002", TOKEN_B)})
    monkeypatch.setattr(app_module, "settings", registry)
    calls = []
    real_collect = wazuh.collect
    async def fake_collect(tenant, *, limit):
        calls.append(tenant)
        return await real_collect(tenant, limit=limit, transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json=payload(next(iter(tenant.agent_ids))))))
    monkeypatch.setattr(app_module.wazuh, "collect", fake_collect)
    # Keep a reference to the real connector for the synthetic upstream.
    return registry, calls


def test_tenant_authorization_denies_before_upstream(tenant_api):
    _, calls = tenant_api
    with TestClient(app_module.app) as client:
        for tenant, token, status in [("a", None, 401), ("a", TOKEN_B, 403),
            ("b", TOKEN_A, 403), ("unknown", TOKEN_A, 403), ("a", "wrong", 403)]:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = client.get(f"/api/tenants/{tenant}/wazuh", headers=headers)
            assert response.status_code == status
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["vary"] == "Authorization"
        assert calls == []
        assert client.post("/api/tenants/a/wazuh", headers={"Authorization": f"Bearer {TOKEN_A}"}).status_code == 405
        for limit in (0, 101):
            assert client.get(f"/api/tenants/a/wazuh?limit={limit}", headers={"Authorization": f"Bearer {TOKEN_A}"}).status_code == 422
        assert calls == []


def test_interleaved_and_concurrent_requests_stay_scoped(tenant_api):
    async def requests():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_module.app), base_url="http://test") as client:
            results = await asyncio.gather(*[
                client.get(f"/api/tenants/{tenant}/wazuh", headers={"Authorization": f"Bearer {token}"})
                for tenant, token in [("a", TOKEN_A), ("b", TOKEN_B)] * 10
            ])
            for i, response in enumerate(results):
                assert response.status_code == 200
                data = response.json()
                assert data["tenant_id"] == ("a" if i % 2 == 0 else "b")
                assert data["alerts"][0]["agent_id"] == ("001" if i % 2 == 0 else "002")
                assert "password" not in response.text and "api_token" not in response.text
    asyncio.run(requests())


def test_upstream_failure_is_sanitized_without_demo_fallback(tenant_api, monkeypatch):
    async def fail(*args, **kwargs):
        raise wazuh.WazuhError("sensitive credentials and upstream logs")
    monkeypatch.setattr(wazuh, "collect", fail)
    with TestClient(app_module.app) as client:
        response = client.get("/api/tenants/a/wazuh", headers={"Authorization": f"Bearer {TOKEN_A}"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Wazuh source unavailable or invalid"}
    assert response.headers["cache-control"] == "no-store"


def test_public_routes_stream_and_ai_never_collect_tenant_telemetry(tenant_api, monkeypatch):
    from msp_sentinel.services import fusion
    from msp_sentinel.services.resilience import CircuitBreaker
    from msp_sentinel.models import Signal
    _, calls = tenant_api
    async def synthetic(client):
        return [Signal(source="Synthetic", kind="test", title="public test")]
    monkeypatch.setattr(fusion, "COLLECTORS", {"Synthetic": synthetic})
    monkeypatch.setattr(fusion, "BREAKERS", {"Synthetic": CircuitBreaker()})
    async def check_brief(data):
        assert "Wazuh" not in json.dumps(data)
        return "synthetic brief"
    monkeypatch.setattr(app_module, "brief", check_brief)
    with TestClient(app_module.app) as client:
        for path in ("/api/snapshot", "/api/exposure", "/api/investigate/001", "/api/health", "/"):
            response = client.get(path)
            assert response.status_code == 200
            assert "Synthetic SSH alert" not in response.text
            assert TOKEN_A not in response.text and "synthetic-password" not in response.text
    async def check_stream():
        response = await app_module.stream()
        try:
            event = await anext(response.body_iterator)
            assert "Wazuh" not in event and "Synthetic SSH alert" not in event
        finally:
            await response.body_iterator.aclose()
    asyncio.run(check_stream())
    assert calls == []


@pytest.fixture
def https_indexer(tmp_path):
    """Real local HTTPS server to verify certificate trust and the HTTP wire contract."""
    import ssl
    import subprocess
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(key), "-out", str(cert), "-days", "1", "-subj", "/CN=localhost",
        "-addext", "subjectAltName=IP:127.0.0.1"], check=True, capture_output=True)
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            query = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, self.headers["Authorization"], query))
            body = json.dumps(payload()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://127.0.0.1:{server.server_port}", str(cert), calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_https_indexer_custom_ca_and_untrusted_certificate(https_indexer):
    url, cert, calls = https_indexer
    tenant = wazuh.WazuhTenant(**config(indexer_url=url, ca_file=cert))
    result = asyncio.run(wazuh.collect(tenant))
    assert result["alerts"][0]["agent_id"] == "001"
    assert calls[0][0] == "/wazuh-alerts-*/_search?allow_partial_search_results=false"
    assert calls[0][1].startswith("Basic ")
    assert calls[0][2]["query"]["bool"]["filter"][0] == {"terms": {"agent.id": ["001"]}}
    untrusted = wazuh.WazuhTenant(**config(indexer_url=url))
    with pytest.raises(wazuh.WazuhError):
        asyncio.run(wazuh.collect(untrusted))
    assert len(calls) == 1
