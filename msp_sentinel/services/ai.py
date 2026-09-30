import httpx

from msp_sentinel.config import settings


async def brief(snapshot: dict) -> str:
    if settings.ollama_model:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "stream": False,
                        "prompt": "You are an MSP SOC analyst. Summarize this grounded snapshot, do not invent facts:\n" + str(snapshot)[:10000],
                    },
                )
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception:
            pass
    critical = snapshot.get("counts", {}).get("critical", 0)
    high = snapshot.get("counts", {}).get("high", 0)
    degraded = sum(1 for t in snapshot.get("tenants", []) if t.get("health") != "healthy")
    return f"Situation brief: {critical} critical and {high} high signals are visible. {degraded} demo tenant(s) require operational attention. Validate source health and correlate indicators before escalation."
