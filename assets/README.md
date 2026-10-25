# MSP Sentinel AI 3.1 visuals

All dashboard images and animations use the real application with the offline
synthetic fixture in `tests/browser_fixture.py`. Tenant names and alerts are fictional.
The Wazuh animation captures actual synthetic API responses from the connector,
including a tenant-scoped success and cross-tenant denial. Tokens are redacted.
Synthetic checks do not establish production-ready tenant isolation.

| File | Content |
|---|---|
| `msp-v3-hero.svg` / `.png` | 3.1 release banner, connector capabilities and verification boundary |
| `msp-v3-architecture.svg` / `.png` | Separate public CTI/demo and private tenant Wazuh paths |
| `msp-sentinel-dashboard.png` | Full synthetic dashboard capture |
| `msp-sentinel-ai-demo.gif` | Situation room, source health, tenants, exposure and real investigation |
| `msp-sentinel-cti-fusion.gif` | Synthetic signals, watchlist, evidence context and source health |
| `msp-sentinel-multi-tenant.gif` | Fictional tenant operations and estimated exposure |
| `msp-sentinel-ai-analyst.gif` | Grounded deterministic briefing and investigation; optional local AI described |
| `msp-sentinel-wazuh.gif` | Authenticated tenant API success, denial and data-boundary walkthrough |

Existing asset filenames are retained so prior README links keep working. SVGs include
accessible titles/descriptions; README image descriptions explain each walkthrough.
GIFs loop, use deliberate reading pauses and contain no flashing effects.

## Rebuild

With Python 3.12+ and Node 20+ available, activate a virtual environment, then run:

```sh
pip install -e . Pillow
npm ci
npx playwright install chromium
npm run render:visuals
```

The renderer owns a temporary loopback fixture server on port 8766. Keep that port
free. `PYTHON` can select a Python executable; `IMAGE_PYTHON` can select a separate
Pillow-enabled executable. `PLAYWRIGHT_BROWSERS_PATH` supports a custom browser cache.
No live feeds, customer credentials or Ollama model are required. Temporary captures
are removed when rendering ends; final media are written here. Python app dependencies
and Pillow must be present in the respective selected environments.

`scripts/render_visuals.cjs` is the source for the vector artwork and browser capture
sequence. `scripts/encode_visuals.py` resizes and encodes the frames using Pillow.
Review the generated images and every GIF frame after changing layout or copy.
