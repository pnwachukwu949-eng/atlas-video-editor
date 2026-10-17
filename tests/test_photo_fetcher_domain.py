"""PhotoFetcher domain-aware search — workspace for software, place for place."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.acquisition.photo_fetcher import PhotoFetcher
from atlas.acquisition.domains import is_software_query, domain_mismatch_penalty


def test_software_query_returns_workspace_not_suburban():
    f = PhotoFetcher(assets_root=str(ROOT / "assets"))
    hits = f.search("video timeline editing software screen workspace")
    assert hits, "expected workspace catalog hits for software query"
    for h in hits:
        terms = " ".join(h.get("query_terms") or []).lower()
        assert "suburban" not in terms
        assert any(t in terms for t in ("laptop", "desk", "workspace", "office", "computer", "editor"))


def test_place_query_still_returns_catalog():
    f = PhotoFetcher(assets_root=str(ROOT / "assets"))
    hits = f.search("suburban neighborhood houses")
    assert len(hits) >= 1
    assert hits[0]["match_score"] > 0
    assert "suburban" in " ".join(hits[0].get("query_terms") or []).lower() or "house" in hits[0]["title"].lower()


def test_software_does_not_prefer_residential():
    f = PhotoFetcher(assets_root=str(ROOT / "assets"))
    hits = f.search("editor timeline software screen")
    for h in hits:
        blob = " ".join(h.get("query_terms") or []) + " " + h.get("title", "")
        assert "suburban" not in blob.lower()


def test_domain_helpers():
    assert is_software_query("atlas video editor timeline")
    assert domain_mismatch_penalty(
        "video editing software", "suburban neighborhood houses"
    ) < 0
