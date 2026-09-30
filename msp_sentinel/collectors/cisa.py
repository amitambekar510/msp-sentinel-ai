import httpx

from msp_sentinel.models import Signal

URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


async def collect(client: httpx.AsyncClient) -> list[Signal]:
    response = await client.get(URL)
    response.raise_for_status()
    data = response.json()
    output = []
    for item in data.get("vulnerabilities", [])[:25]:
        output.append(Signal(
            source="CISA KEV",
            kind="known-exploited-vulnerability",
            title=f'{item.get("cveID", "CVE")} · {item.get("vulnerabilityName", "Known exploited vulnerability")}',
            severity="critical",
            reference=f'https://nvd.nist.gov/vuln/detail/{item.get("cveID")}' if item.get("cveID") else URL,
        ))
    return output
