from msp_sentinel.services.intelligence import build_exposure, build_graph, build_timeline, build_watchlist, investigate


SIGNALS = [
    {"source": "CISA KEV", "kind": "cve", "title": "CVE-2026-0001 exploited", "severity": "critical", "reference": "https://example.org/CVE-2026-0001", "observed_at": "2026-10-05T12:00:00Z"},
    {"source": "Feodo Tracker", "kind": "c2", "title": "C2 infrastructure observed", "severity": "high", "reference": "https://c2.example.net/item", "observed_at": "2026-10-05T13:00:00Z"},
]
TENANTS = [{"tenant": "Demo Bank", "critical_alerts": 2, "open_incidents": 1}]


def test_exposure_is_explainable_and_bounded():
    row = build_exposure(SIGNALS, TENANTS)[0]
    assert 0 <= row["exposure_score"] <= 100
    assert "validate" in row["basis"].lower()


def test_graph_links_sources_and_tenants():
    graph = build_graph(SIGNALS, TENANTS)
    assert any(n["type"] == "tenant" for n in graph["nodes"])
    assert any(e["relation"] == "feeds" for e in graph["edges"])


def test_timeline_newest_first_and_watchlist_prioritizes():
    assert build_timeline(SIGNALS)[0]["source"] == "Feodo Tracker"
    assert len(build_watchlist(SIGNALS)) == 2


def test_investigate_is_case_insensitive_and_safe_when_empty():
    assert investigate("cve-2026", SIGNALS)["match_count"] == 1
    assert investigate("not-present", SIGNALS)["match_count"] == 0
