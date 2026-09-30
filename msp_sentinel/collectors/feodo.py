import csv
import io

import httpx

from msp_sentinel.models import Signal

URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.csv"


async def collect(client: httpx.AsyncClient) -> list[Signal]:
    response = await client.get(URL)
    response.raise_for_status()
    rows = csv.reader(io.StringIO(response.text))
    output = []
    for row in rows:
        if not row or row[0].startswith("#"):
            continue
        output.append(Signal(source="Feodo Tracker", kind="c2", title=f"Botnet C2 · {row[1] if len(row) > 1 else row[0]}", severity="critical", reference="https://feodotracker.abuse.ch/"))
        if len(output) >= 20:
            break
    return output
