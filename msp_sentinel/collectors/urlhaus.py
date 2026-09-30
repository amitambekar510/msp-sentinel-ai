import httpx

from msp_sentinel.models import Signal

URL = "https://urlhaus.abuse.ch/downloads/json_recent/"


async def collect(client: httpx.AsyncClient) -> list[Signal]:
    response = await client.get(URL)
    response.raise_for_status()
    data = response.json()
    items = data.get("urls", data if isinstance(data, list) else [])
    return [
        Signal(source="URLhaus", kind="malicious-url", title=f'Malicious URL · {x.get("url", "unknown")[:100]}', severity="high", reference="https://urlhaus.abuse.ch/")
        for x in items[:20]
    ]
