from fastapi.testclient import TestClient
import msp_sentinel.app as app_module

client = TestClient(app_module.app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard():
    r = client.get("/")
    assert r.status_code == 200
    assert "MSP Sentinel" in r.text
    assert "IOC / INTELLIGENCE INVESTIGATOR" in r.text


async def fake_snapshot():
    return {
        "risk_score": 42,
        "signals": [{"source": "test", "kind": "ioc", "title": "example IOC", "severity": "high", "reference": None}],
        "exposure": [{"tenant": "Demo", "exposure_score": 42}],
        "watchlist": [],
    }


def test_investigation_endpoint_handles_unknown_indicator(monkeypatch):
    monkeypatch.setattr(app_module, "snapshot", fake_snapshot)
    r = client.get("/api/investigate/definitely-not-present")
    assert r.status_code == 200
    assert r.json()["match_count"] == 0


def test_exposure_endpoint_contract(monkeypatch):
    monkeypatch.setattr(app_module, "snapshot", fake_snapshot)
    r = client.get("/api/exposure")
    assert r.status_code == 200
    body = r.json()
    assert "exposure" in body
    assert "watchlist" in body
