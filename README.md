# MSP Sentinel AI

**Open-source multi-tenant MSP/MSSP Cyber Situation Room** — a Python-first browser dashboard that fuses public cyber threat intelligence, tenant operational health and optional local AI analysis into one live defensive view.

> Built as an original MSP/SOC-focused project. It is inspired by the resilience and situational-awareness patterns of modern intelligence dashboards, not a clone of any vendor map or reference repository.

## Why this exists

Public threat maps are useful for global context, while MSP teams also need to know **which client needs attention, whether telemetry is healthy, what threat intelligence matters, and whether the upstream feeds themselves are trustworthy right now**. MSP Sentinel AI combines those questions into one operator-oriented interface.

## Highlights

- Multi-tenant MSP/MSSP health view with synthetic demo clients
- Public CTI fusion: CISA KEV, NVD, URLhaus and Feodo Tracker
- Global geospatial threat surface for signals that contain location context
- Concurrent asynchronous collection with retries and circuit breakers
- Explicit source-health states and graceful fallback instead of fake zeroes
- Severity fusion and operational risk scoring
- Optional local Ollama analyst; deterministic grounded brief when no LLM is configured
- FastAPI REST endpoints plus Server-Sent Events stream
- Responsive dark SOC dashboard for modern browsers
- Docker support and Python 3.12+
- GitHub CI for Python 3.12/3.13 and a Chromium/Firefox/WebKit browser matrix

## Quick start

```bash
git clone https://github.com/amitambekar510/msp-sentinel-ai.git
cd msp-sentinel-ai
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -m msp_sentinel.cli
```

Open **http://127.0.0.1:8000**.

You can also run `msp-sentinel --host 0.0.0.0 --port 8000` after installation.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Then open **http://127.0.0.1:8000**.

## API

| Endpoint | Purpose |
|---|---|
| `GET /` | Browser Situation Room |
| `GET /api/health` | Application health |
| `GET /api/snapshot` | Current fused situation snapshot |
| `GET /api/stream` | Live SSE situation stream |

## Optional local AI analyst

The project does not require a cloud LLM. To use a local Ollama model:

```env
MSP_SENTINEL_OLLAMA_URL=http://localhost:11434
MSP_SENTINEL_OLLAMA_MODEL=your-installed-model
```

If the model is unavailable, the dashboard automatically falls back to a deterministic situation brief. The AI prompt is explicitly grounded in the collected snapshot and instructed not to invent facts.

## Intelligence architecture

```text
 CISA KEV ─┐
 NVD ──────┤
 URLhaus ──┼─> async collectors -> retry/circuit breaker -> fusion engine
 Feodo ────┘                                      │
                                                  ├─> risk/severity model
 Synthetic MSP tenant telemetry ──────────────────┤
                                                  ├─> grounded AI brief
                                                  └─> REST / SSE / browser dashboard
```

The collector boundary is intentionally small so additional feeds can be added without changing the dashboard contract. Production users should respect each provider's terms, rate limits and authentication requirements.

## Data integrity and safe degradation

A failed upstream source is marked **degraded**. It is not silently interpreted as “no threats.” When all public sources are unreachable, the application uses clearly labelled synthetic signals so the UI remains demonstrable. Demo tenant records are fictional and must not be confused with customer telemetry.

## Production extension ideas

The repository is designed as a foundation for integrations such as OpenCTI, MISP, Elastic Security, Microsoft Sentinel, CrowdStrike, ticketing systems and tenant-specific asset inventories. Before production use, add authentication/RBAC, persistent storage, secrets management, audit logging, tenant isolation, feed-specific licensing review, rate limiting and organization-specific incident workflows.

## Testing

```bash
pytest -q
python -m compileall -q msp_sentinel
```

GitHub Actions tests Python 3.12 and 3.13. A separate browser workflow starts the application and smoke-tests the dashboard in **Chromium, Firefox and WebKit**, saving screenshots as CI artifacts.

## Security and limitations

This is a defensive situational-awareness project, not a replacement for a SIEM, EDR, SOC analyst or incident-response process. Public-feed indicators can be stale, incomplete, false-positive or context-dependent. Never treat a map marker or public IOC as proof that an organization is compromised. See [SECURITY.md](SECURITY.md).

## Attribution

Architecture research included the public World Intel MCP project and public threat-intelligence dashboards from Kaspersky, Check Point, Radware, Bitdefender, NETSCOUT, FortiGuard, SonicWall, Cisco Talos and Spamhaus. MSP Sentinel AI uses its own implementation and UI and does not redistribute proprietary dashboard data.

## License

MIT © 2026 Amit Ambekar.
