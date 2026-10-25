# MSP Sentinel AI 3.1: Wazuh connector

Package/API version: `0.3.1`. The existing public CTI dashboard, offline planner,
REST endpoints, SSE stream, optional local AI and synthetic tenants remain available.

## Implemented boundary

`GET /api/tenants/{tenant_id}/wazuh?limit=50` requires an `Authorization: Bearer`
token assigned to that exact tenant. Configuration is empty by default, so no Wazuh
requests occur until an operator provisions a tenant. Missing authentication returns
401; invalid tokens, wrong-tenant tokens and unknown tenants return the same 403.
All tenant responses, including errors, carry `Cache-Control: no-store` and
`Vary: Authorization`. Tokens are never accepted in URLs, cookies or browser storage.

The connector reads the Wazuh **indexer**, not the Wazuh manager API. Wazuh documents
alert queries using [`POST /wazuh-alerts*/_search`](https://documentation.wazuh.com/current/user-manual/indexer-api/use-case.html).
This POST is a read-only search; the connector has no ingest, document-write,
index-management, agent-management or active-response operations. HTTP verbs alone
cannot enforce least privilege: provision an upstream account restricted to search
and the assigned alert indices/documents. Never use the indexer administrator account.

Each request uses an operator-owned index pattern and explicit `agent.id` allowlist,
a fixed last-24-hour timestamp range, source-field projection and at most 100 alerts.
No client-supplied URL, agent list or search DSL is accepted. Every returned source is
validated again against the agent assignment and time window. Partial searches,
malformed data, out-of-scope agents and upstream failures reject the entire response
with a sanitized 502. There is no synthetic fallback for private telemetry.

Results contain `agent_id`, `rule_id`, title, Wazuh level, normalized severity and
observation time. Raw logs, agent names, arbitrary fields and upstream totals are not
returned. Levels 0–3 map to info, 4–6 low, 7–11 medium, 12–14 high and 15–16 critical.
The response reports `returned`, `limit`, `window_hours` and `at_limit`. This is a
bounded recent-alert view, **not** a complete export, inventory, incident count or
continuous ingestion service; `at_limit` only means the cap was reached.

## Operator configuration

Set `MSP_SENTINEL_WAZUH_TENANTS` to a JSON object in the process environment or a
protected `.env` file. A synthetic example is below; replace these fictional values
only in your own secret store. Do not commit real tokens or credentials.

```json
{
  "demo-a": {
    "indexer_url": "https://indexer.example.test:9200",
    "username": "tenant-a-search-reader",
    "password": "synthetic-example-password",
    "api_token": "synthetic-example-token-replace-before-use",
    "agent_ids": ["001", "003"],
    "index_pattern": "wazuh-alerts-*",
    "ca_file": "/absolute/path/to/trusted-indexer-ca.pem"
  }
}
```

For `.env`, store compact JSON on one line after `MSP_SENTINEL_WAZUH_TENANTS=`.
Use independent random bearer tokens of at least 32 characters (for example generated
with Python's `secrets.token_urlsafe(32)`). These API tokens are independent of upstream
indexer credentials. Give each caller only its assigned tenant token. Configuration
changes and token rotation require an application restart.

Only HTTPS origins are accepted. `ca_file` is optional for a publicly trusted
certificate and required when your private indexer CA is not in the default trust
store. Certificate verification is always enabled. Redirects and environment proxies
are disabled; credentials are bound to a new client per request. Connect/read/write/pool
timeouts are 12 seconds each, responses are capped at 1 MB of decoded data, and there
are no shared telemetry caches or automatic retries.

Configuration rejects empty agent assignments, manager ID zero, unsafe index paths,
duplicate API tokens and agents assigned to two tenants on the same canonical indexer
origin. Host aliases pointing to the same physical cluster are not automatically
detected: operators must use a single canonical origin for each cluster and review
assignments whenever agents are re-enrolled or moved.

## Verified safeguards and remaining limits

Synthetic tests verify API authorization, concurrent tenant request separation, query
scope, response scope checks, field projection, error sanitization, redirect refusal,
timeouts, limits and separation from public snapshot/exposure/investigation/stream/AI.
A real local HTTPS fixture verifies trusted-CA acceptance, untrusted-certificate denial
and the HTTP search contract. Browser fixtures exercise the same application and real
connector with synthetic upstream responses; they are imported only by the test runner.

These checks **do not establish production-ready tenant isolation**. No live customer
Wazuh deployment, upstream DLS/RBAC policy, agent ownership or hostile deployment has
been assessed. An indexer can mislabel an alert's agent ID or include unrelated data in
a description; application checks cannot prove the truth of upstream fields. A shared
indexer credential may still read other tenants directly if its upstream policy permits
it. Configure upstream document-level access control or separate tenant indices and
credentials, then verify denial tests against the actual deployment.

Before admitting customer telemetry, verify identity integration, authorization,
secret rotation, TLS termination for the API, network restrictions, logging redaction,
audit trails, rate limits, retention and an independent security assessment. Static
bearer tokens here are a limited API safeguard, not an identity/RBAC platform. Private
telemetry is deliberately absent from the existing public dashboard and optional AI.
Elastic, Microsoft Sentinel and Splunk adapters are outside this release's scope.

## Verification and rollback

```sh
pip install -e '.[dev]'
python -m compileall -q msp_sentinel
pytest -q --junitxml=test-results/python.xml
npm ci
npx playwright install --with-deps chromium firefox webkit
npm run test:browser
```

The browser runner starts an offline fixture on loopback port 8765. It requires that
port to be free. CI runs Python 3.12/3.13 and separate Chromium/Firefox/WebKit jobs,
with JUnit results, screenshots, HTML reports and failure traces as artifacts. Tests
must not be skipped to merge. Check every job for the exact current PR revision;
repeat verification after any change or update from main.

Disable private reads by clearing `MSP_SENTINEL_WAZUH_TENANTS` and restarting. Revoke
upstream credentials and API tokens if compromised. Reverting the release PR restores
the prior application; no indexer data migrations or write-side rollback are required.
