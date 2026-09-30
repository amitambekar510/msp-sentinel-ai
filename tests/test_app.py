from fastapi.testclient import TestClient
from msp_sentinel.app import app
client=TestClient(app)
def test_health():
 r=client.get("/api/health");assert r.status_code==200;assert r.json()["status"]=="ok"
def test_dashboard():
 r=client.get("/");assert r.status_code==200;assert "MSP Sentinel" in r.text
