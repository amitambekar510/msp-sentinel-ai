import pytest
from scripts.build_deployment_plan import build

@pytest.fixture
def env():
    return {"siem":"ELK","tenant_count":3,"telemetry":["firewall"],"intelligence":["NVD"],"deployment":"demo","ai_mode":"deterministic","retention":"demo only","priority":"source health","sector":"finance"}

def test_build(env):
    result=build(env)
    assert "tenant-specific" in result
    assert "No systems accessed" in result

def test_bad_tenants(env):
    env["tenant_count"]=0
    with pytest.raises(ValueError):
        build(env)

def test_escape(env):
    env["siem"]="<script>"
    assert "<script>" not in build(env)
