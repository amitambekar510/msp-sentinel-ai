from fastapi.testclient import TestClient
from msp_sentinel.app import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard():
    r = client.get("/")
    assert r.status_code == 200
    assert "MSP Sentinel" in r.text
    assert "IOC / INTELLIGENCE INVESTIGATOR" in r.text


def test_investigation_endpoint_handles_unknown_indicator():
    r = client.get("/api/investigate/definitely-not-present")
    assert r.status_code == 200
    assert "match_count" in r.json()


def test_exposure_endpoint_contract():
    r = client.get("/api/exposure")
    assert r.status_code == 200
    body = r.json()
    assert "exposure" in body
    assert "watchlist" in body
