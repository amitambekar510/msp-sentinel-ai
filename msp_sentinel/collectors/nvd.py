import httpx

from msp_sentinel.config import settings
from msp_sentinel.models import Signal

URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?cvssV3Severity=CRITICAL&resultsPerPage=20"


async def collect(client: httpx.AsyncClient) -> list[Signal]:
    headers = {"apiKey": settings.nvd_api_key} if settings.nvd_api_key else {}
    response = await client.get(URL, headers=headers)
    response.raise_for_status()
    output = []
    for wrapper in response.json().get("vulnerabilities", []):
        cve = wrapper.get("cve", {})
        cve_id = cve.get("id", "CVE")
        descriptions = cve.get("descriptions", [])
        description = next((x.get("value") for x in descriptions if x.get("lang") == "en"), "Critical vulnerability")
        output.append(Signal(source="NVD", kind="vulnerability", title=f"{cve_id} · {description[:110]}", severity="critical", reference=f"https://nvd.nist.gov/vuln/detail/{cve_id}"))
    return output
