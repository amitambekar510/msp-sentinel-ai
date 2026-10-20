#!/usr/bin/env python3
"""Offline MSP Sentinel deployment planning. No external integrations."""
import argparse
import json
from pathlib import Path

FIELDS = ("siem","tenant_count","telemetry","intelligence","deployment","ai_mode","retention","priority","sector")

def build(data):
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    if any(k not in data for k in FIELDS):
        raise ValueError("Missing required fields")
    if type(data["tenant_count"]) is not int or data["tenant_count"] < 1:
        raise ValueError("tenant_count must be a positive integer")
    for key in ("telemetry","intelligence"):
        if not isinstance(data[key],list) or not all(isinstance(x,str) for x in data[key]):
            raise ValueError(key+" must be a string list")
    for key in ("siem","deployment","ai_mode","retention","priority","sector"):
        if not isinstance(data[key],str) or not data[key].strip():
            raise ValueError(key+" must be nonempty")
    def safe(x):
        return str(x).replace("<","&lt;").replace(">","&gt;").replace("\n"," ").replace("\r"," ")
    lines=["# MSP Sentinel AI 3.0 — Environment Plan","","Offline planning only. No systems accessed.","","## Environment"]
    for key in FIELDS:
        value=", ".join(data[key]) if isinstance(data[key],list) else data[key]
        lines.append("- **"+safe(key)+":** "+safe(value))
    lines+=["","## Rollout checklist","",
      "- [ ] Run local synthetic demo and verify dashboard and source health.",
      "- [ ] Validate external intelligence source terms and data accuracy.",
      "- [ ] Design authenticated SIEM/EDR/ticketing connectors for approved tenants.",
      "- [ ] Implement SSO/RBAC, tenant-specific authorization and isolation testing.",
      "- [ ] Add durable storage, audit logs, secrets management and retention.",
      "- [ ] Test API security, rate limits, TLS, backup and rollback.",
      "- [ ] Obtain documented production security approval.",
      "","## Important limits","",
      "Demo tenant data and exposure scores are synthetic estimates, not evidence of compromise.",
      "See docs/compliance-applicability.md for conditional governance references."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    output=build(json.loads(a.input.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(output,encoding="utf-8")
    print("Wrote",a.output)

if __name__=="__main__":
    main()
