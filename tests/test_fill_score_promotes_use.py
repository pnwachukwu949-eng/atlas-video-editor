"""Fill-domain score must not leave queue open when asset is on timeline."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.asset_fit.queue import AcquisitionQueue


def test_fill_score_promotes_gap_to_use():
    reg = json.loads((ROOT / "assets" / "registry.json").read_text())
    # Prefer a real workspace asset if present
    assets = reg.get("assets") or {}
    aid = "fetched_office_01" if "fetched_office_01" in assets else next(iter(assets))
    edit = {
        "edit_id": "gap_fix",
        "beats": [{
            "beat_id": "B03",
            "narration_summary": "You give it a script, a voiceover, and your assets.",
            "visual": {"type": "pending", "asset_id": None},
        }],
    }
    queue = {"items": [{"beat_id": "B03", "status": "open"}]}
    aq = AcquisitionQueue()
    result = aq.fill(
        copy.deepcopy(queue),
        copy.deepcopy(edit),
        beat_id="B03",
        asset_id=aid,
        registry=reg,
        score=14.4,
    )
    assert result["beat_decision"] == "USE"
    assert result["queue"]["items"][0]["status"] == "filled"
    vis = result["edit_spec"]["beats"][0]["visual"]
    assert vis.get("asset_id") == aid
