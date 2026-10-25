import asyncio
import json
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from msp_sentinel.config import settings
from msp_sentinel.collectors import wazuh
from msp_sentinel.services.ai import brief
from msp_sentinel.services.fusion import snapshot
from msp_sentinel.services.intelligence import investigate

BASE = Path(__file__).parent
app = FastAPI(title="MSP Sentinel AI", version="0.3.1")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
bearer = HTTPBearer(auto_error=False)


@app.middleware("http")
async def private_telemetry_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/tenants/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Vary"] = "Authorization"
    return response


@app.get("/api/tenants/{tenant_id}/wazuh")
async def tenant_wazuh(tenant_id: str, limit: int = Query(50, ge=1, le=100),
                      credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None:
        raise HTTPException(401, "Bearer authentication required", headers={"WWW-Authenticate": "Bearer"})
    tenant = settings.wazuh_tenants.get(tenant_id)
    expected = tenant.api_token.get_secret_value() if tenant else "unconfigured-tenant-deny"
    matches = secrets.compare_digest(credentials.credentials.encode(), expected.encode())
    if tenant is None or not matches:
        raise HTTPException(403, "Tenant access denied")
    try:
        data = await wazuh.collect(tenant, limit=limit)
    except wazuh.WazuhError:
        raise HTTPException(502, "Wazuh source unavailable or invalid") from None
    return {"tenant_id": tenant_id, **data}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "msp-sentinel-ai"}


@app.get("/api/snapshot")
async def api_snapshot():
    data = await snapshot()
    data["brief"] = await brief(data)
    return data


@app.get("/api/exposure")
async def exposure():
    data = await snapshot()
    return {"risk_score": data["risk_score"], "exposure": data["exposure"], "watchlist": data["watchlist"]}


@app.get("/api/investigate/{indicator}")
async def api_investigate(indicator: str):
    data = await snapshot()
    return investigate(indicator, data["signals"])


@app.get("/api/stream")
async def stream():
    async def events():
        while True:
            data = await snapshot()
            data["brief"] = await brief(data)
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(settings.refresh_seconds)

    return StreamingResponse(events(), media_type="text/event-stream")
