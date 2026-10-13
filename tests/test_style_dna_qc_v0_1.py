#!/usr/bin/env python3
"""Deterministic tests for Style DNA + Asset QC v0.1."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.style_dna.engine import StyleDNAEngine
from atlas.engines.qc.engine import AssetQCEngine


def test_style_dna_apply():
    engine = StyleDNAEngine()
    dna = {
        "style_id": "test",
        "version": "0.1",
        "grammar": {
            "avg_shot_seconds": 4.0,
            "preferred_transition": "hard_cut",
            "broll_density": "medium",
            "motion": "slow_push",
            "hold_on_key_claims": True,
            "caption_style": {"position": "bottom", "max_lines": 2},
        },
    }
    profile = json.loads((ROOT / "examples/profiles/product.json").read_text())
    defaults = engine.apply_to_edit_defaults(dna, profile)
    assert defaults["style_id"] == "test"
    assert defaults["preferred_transition"] == "hard_cut"
    assert defaults["repeat_cap"] == 3  # product profile
    assert defaults["evidence_strictness"] == "off"
    # dense pacing shortens target shot
    assert defaults["target_avg_shot_seconds"] < 4.0


def test_repeat_cap():
    qc = AssetQCEngine(assets_root=str(ROOT / "assets"))
    edit = {
        "beats": [
            {"beat_id": "A", "visual": {"asset_id": "x"}},
            {"beat_id": "B", "visual": {"asset_id": "x"}},
            {"beat_id": "C", "visual": {"asset_id": "x"}},
            {"beat_id": "D", "visual": {"asset_id": "y"}},
        ]
    }
    r = qc.check_repeat_cap(edit, max_uses=2)
    assert r["passed"] is False
    v0 = r["violations"][0]
    assert v0.get("asset_id") == "x" or "x" in (v0.get("asset_ids") or []) or str(v0.get("plate", "")).endswith("x")
    assert r["violations"][0]["uses"] == 3


def test_banned():
    qc = AssetQCEngine(assets_root=str(ROOT / "assets"))
    reg = qc.load_registry()
    banned_ids = list(reg.get("banned", {}).keys())
    if not banned_ids:
        return  # skip if empty registry
    edit = {"beats": [{"beat_id": "A", "visual": {"asset_id": banned_ids[0]}}]}
    r = qc.check_banned_in_timeline(edit)
    assert r["passed"] is False
    assert banned_ids[0] in r["hits"]


def test_contact_sheet():
    qc = AssetQCEngine(assets_root=str(ROOT / "assets"))
    out = ROOT / "renders" / "test_contact_sheet.jpg"
    result = qc.render_contact_sheet(str(out))
    assert result.get("ok") is True
    assert out.exists()


if __name__ == "__main__":
    checks = [
        ("style_dna_apply", test_style_dna_apply),
        ("repeat_cap", test_repeat_cap),
        ("banned", test_banned),
        ("contact_sheet", test_contact_sheet),
    ]
    results = []
    for name, fn in checks:
        try:
            fn()
            results.append({"name": name, "passed": True})
        except Exception as e:
            results.append({"name": name, "passed": False, "error": str(e)})
    all_ok = all(r["passed"] for r in results)
    report = {"suite": "style_dna_qc_v0_1", "all_passed": all_ok, "checks": results}
    print(json.dumps(report, indent=2))
    (ROOT / "tests" / "style_dna_qc_v0_1_report.json").write_text(json.dumps(report, indent=2))
    sys.exit(0 if all_ok else 1)
