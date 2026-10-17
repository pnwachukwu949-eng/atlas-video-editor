"""Domain-aware registry scoring for fill_queue."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import fill_queue as fq  # scripts/fill_queue.py


def _reg():
    return json.loads((ROOT / "assets" / "registry.json").read_text())


def test_software_query_prefers_product_card_not_residential():
    reg = _reg()
    pick = fq._pick_from_registry(
        "video timeline editing software screen", reg, min_score=3.0
    )
    assert pick is not None
    aid, score = pick
    assert "product" in aid or "timeline" in aid or "script" in aid or "style" in aid
    assert "residential" not in aid
    assert "suburb" not in aid
    assert score >= 8.0


def test_place_query_still_prefers_residential():
    reg = _reg()
    pick = fq._pick_from_registry(
        "suburban neighborhood houses", reg, min_score=3.0
    )
    assert pick is not None
    aid, _ = pick
    blob = aid.lower()
    assert any(x in blob for x in ("suburb", "house", "residential", "aerial", "pexels", "street"))


def test_software_query_penalizes_place_video():
    reg = _reg()
    banned = reg.get("banned") or {}
    assets = reg.get("assets") or {}
    for aid, entry in assets.items():
        if not isinstance(entry, dict):
            continue
        path = str(entry.get("path") or "").lower()
        if "residential" in aid.lower() or "suburb" in path or "mixkit" in path:
            soft = fq._score_registry_asset(
                "video timeline editing software screen", aid, entry, banned
            )
            place = fq._score_registry_asset(
                "suburban neighborhood houses", aid, entry, banned
            )
            assert place > soft or soft < 5.0
            break
