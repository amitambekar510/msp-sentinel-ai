# MSP Sentinel AI 3.1 — implementation and test report

Date: 25 October 2026. Package/API version: 0.3.1.
Feature branch: `feature/msp-sentinel-3.1-wazuh`.

## Implementation

- Added an optional Wazuh indexer read connector, limited to alert search. Upstream
  credentials and URLs come only from operator configuration; no write operations exist.
- Added `GET /api/tenants/{tenant_id}/wazuh` with tenant-bound bearer authentication,
  constant-time token comparison, generic denial responses and no-store cache headers.
- Added configuration checks for unique tokens, nonempty agent assignments, conflicting
  assignments on a canonical indexer origin, manager IDs, HTTPS origins and index paths.
- Added fixed agent/time filters, source projection, bounded alert counts and response
  size, response-scope validation, sanitized failures and explicit incomplete-view metadata.
- Kept Wazuh telemetry separate from public snapshots, exposure, investigation, SSE
  and optional local AI. The public dashboard and offline planner retain their contracts.
- Added custom CA support with mandatory certificate verification; disabled redirects,
  environment proxies and shared credentials/caches in the connector.
- Replaced title-only browser smoke coverage with an offline deterministic suite and
  pinned browser dependencies. CI retains Python 3.12/3.13 and all three browser engines,
  uses read-only repository permissions, explicit timeouts and downloadable evidence.

## Local verification

| Check | Result |
|---|---|
| Python 3.12.14, complete pytest suite | 66 passed; no failures or skips |
| Chromium, Playwright 1.56.1 | 3 passed |
| Firefox, Playwright 1.56.1 | 3 passed |
| WebKit, Playwright 1.56.1 | 3 passed |
| Python compilation | Passed |
| Diff whitespace check | Passed |

The Python tests include a real loopback HTTPS indexer fixture: a configured CA is
accepted and an untrusted certificate fails before an HTTP search is made. Other
synthetic integration cases cover authentication, cross-tenant access denial, 20
concurrent alternating requests, query filters, result normalization, raw-field
omission, redirect refusal, upstream status failures, timeouts, malformed/oversized
responses, partial searches, timestamp scope and alert limits.

Browser tests verify existing dashboard metrics, tenant health, signals, exposure,
watchlist, map, timeline, graph, matching/nonmatching investigation, SSE delivery,
private API scoping, public/private separation and refresh-failure feedback. Every
browser executes the same three tests against the real app with synthetic upstreams.
No live feeds or customer credentials are needed.

The installed FastAPI/Starlette test client emits one upstream deprecation warning
about its HTTPX integration; it does not affect test outcomes. Replacing that test
client transport is outside this release's functional changes.

## CI and merge requirements

The source workflows run `test (3.12)`, `test (3.13)`, `browser (chromium)`,
`browser (firefox)` and `browser (webkit)`. Inspect the pull request's checks for
revision-specific results and links to JUnit, screenshots, reports and failure traces.
The repository had no required branch checks or rulesets at inspection time; all five
jobs are nevertheless required by this release's merge procedure. A merge is allowed
only after every job succeeds on the current PR revision and main has not moved.
The final delivery report records the checked revision, CI run links and merge result.

## Limits and deployment status

This release verifies specific safeguards using synthetic data. It does not verify a
live Wazuh installation, upstream tenant policies, real agent ownership, identity/RBAC,
secret lifecycle, audit logging, deployment boundaries or resistance to hostile
upstream data. **Production-ready tenant isolation has not been established.**
The static API-token boundary does not replace an organizational identity platform.

See [configuration, security assumptions, operational limits and rollback](wazuh-3.1.md).
The connector is disabled by default; enable it only after deployment-specific review.
There are no indexer writes or data migrations. Clearing tenant configuration and
restarting disables private reads; reverting the release PR restores prior code.
