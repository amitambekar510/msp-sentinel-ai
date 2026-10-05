import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from msp_sentinel.config import settings
from msp_sentinel.services.ai import brief
from msp_sentinel.services.fusion import snapshot
from msp_sentinel.services.intelligence import investigate

BASE = Path(__file__).parent
app = FastAPI(title="MSP Sentinel AI", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


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
