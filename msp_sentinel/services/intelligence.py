from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse


def _indicator(signal: dict) -> str:
    ref = signal.get("reference") or ""
    host = urlparse(ref).hostname
    return host or signal.get("title", "unknown")


def build_exposure(signals: list[dict], tenants: list[dict]) -> list[dict]:
    """Create explainable demo exposure estimates without claiming real compromise."""
    severity = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    weighted = sum(severity.get(s.get("severity", "info"), 1) for s in signals[:40])
    rows = []
    for index, tenant in enumerate(tenants):
        coverage = max(55, 96 - index * 7)
        exposure = min(100, weighted + tenant.get("critical_alerts", 0) * 8 + tenant.get("open_incidents", 0) * 4)
        confidence = min(95, 45 + len(signals) // 2 + (10 if coverage > 80 else 0))
        rows.append({
            "tenant": tenant["tenant"],
            "exposure_score": exposure,
            "confidence": confidence,
            "detection_coverage": coverage,
            "status": "priority" if exposure >= 70 else "watch" if exposure >= 40 else "normal",
            "basis": "Public CTI + synthetic tenant telemetry; validate against client SIEM/EDR.",
        })
    return rows


def build_timeline(signals: list[dict]) -> list[dict]:
    ordered = sorted(signals, key=lambda s: s.get("observed_at", ""), reverse=True)
    return [{
        "time": s.get("observed_at"),
        "source": s.get("source"),
        "severity": s.get("severity"),
        "event": s.get("title"),
        "kind": s.get("kind"),
    } for s in ordered[:20]]


def build_graph(signals: list[dict], tenants: list[dict]) -> dict:
    nodes = [{"id": "fusion", "label": "CTI Fusion", "type": "engine"}]
    edges = []
    for source in sorted({s.get("source", "unknown") for s in signals}):
        sid = "source:" + source
        nodes.append({"id": sid, "label": source, "type": "source"})
        edges.append({"from": sid, "to": "fusion", "relation": "feeds"})
    for tenant in tenants:
        tid = "tenant:" + tenant["tenant"]
        nodes.append({"id": tid, "label": tenant["tenant"], "type": "tenant"})
        edges.append({"from": "fusion", "to": tid, "relation": "context"})
    for i, signal in enumerate(signals[:8]):
        iid = f"indicator:{i}"
        nodes.append({"id": iid, "label": _indicator(signal), "type": "indicator", "severity": signal.get("severity")})
        edges.append({"from": "source:" + signal.get("source", "unknown"), "to": iid, "relation": signal.get("kind", "observed")})
    return {"nodes": nodes, "edges": edges}


def build_watchlist(signals: list[dict]) -> list[dict]:
    counts = Counter(s.get("source", "unknown") for s in signals)
    result = []
    for signal in signals:
        if signal.get("severity") not in {"critical", "high"}:
            continue
        result.append({
            "indicator": _indicator(signal),
            "source": signal.get("source"),
            "severity": signal.get("severity"),
            "reason": signal.get("title"),
            "source_volume": counts[signal.get("source", "unknown")],
            "reference": signal.get("reference"),
        })
        if len(result) == 12:
            break
    return result


def investigate(indicator: str, signals: list[dict]) -> dict:
    needle = indicator.casefold().strip()
    matches = [s for s in signals if needle and needle in str(s).casefold()]
    severities = Counter(s.get("severity", "info") for s in matches)
    return {
        "query": indicator,
        "matches": matches[:20],
        "match_count": len(matches),
        "severity_summary": dict(severities),
        "assessment": "Context found; corroborate with tenant SIEM/EDR before response." if matches else "No match in the current in-memory intelligence snapshot.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
