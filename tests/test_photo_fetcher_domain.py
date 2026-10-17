"""PhotoFetcher domain-aware search — refuse residential for software queries."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.acquisition.photo_fetcher import PhotoFetcher
from atlas.acquisition.domains import is_software_query, domain_mismatch_penalty


def test_software_query_returns_no_suburban_hits():
    f = PhotoFetcher(assets_root=str(ROOT / "assets"))
    hits = f.search("video timeline editing software screen")
    for h in hits:
        terms = " ".join(h.get("query_terms") or []).lower()
        assert "suburban" not in terms or "software" in terms
    assert hits == []


def test_place_query_still_returns_catalog():
    f = PhotoFetcher(assets_root=str(ROOT / "assets"))
    hits = f.search("suburban neighborhood houses")
    assert len(hits) >= 1
    assert hits[0]["match_score"] > 0


def test_acquire_software_fails_closed():
    f = PhotoFetcher(assets_root=str(ROOT / "assets"))
    r = f.search_and_acquire("editor timeline software screen workspace")
    assert r["status"] == "NOT_FOUND"
    assert "refusing residential" in r.get("reason", "").lower() or "domain" in r.get("reason", "").lower()


def test_domain_helpers():
    assert is_software_query("atlas video editor timeline")
    assert domain_mismatch_penalty(
        "video editing software", "suburban neighborhood houses"
    ) < 0
