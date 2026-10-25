# Security Policy

MSP Sentinel AI is a defensive situational-awareness project.

- Never place customer credentials, private indicators or production tenant data in issues.
- Store secrets in environment variables, not source control.
- Public intelligence is context, not proof of compromise.
- Report a suspected vulnerability privately to the maintainer before public disclosure.
- The demo tenant records are synthetic.

Supported branch: `main`.

## Wazuh 3.1 boundary

The optional private Wazuh API uses per-tenant bearer tokens and explicit agent
assignments. It is separate from public CTI routes, SSE and AI. Synthetic tests
verify specific safeguards; they do not certify production tenant isolation.
See [the verified boundary and deployment limitations](docs/wazuh-3.1.md).
