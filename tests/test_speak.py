"""Atlas speak synthesizes narration to audio."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from atlas.acquisition.speak import synthesize, resolve_voice_id

def test_resolve_voice_from_profile():
    assert resolve_voice_id(profile_id="explainer") == "atlas_calm"
    assert resolve_voice_id(profile_id="product") == "atlas_product"

def test_synthesize_short():
    out = ROOT / "renders" / "_speak_test.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    r = synthesize("Rain starts as water vapor from the ocean.", out, voice_id="atlas_calm")
    assert r["status"] == "OK", r
    assert out.exists() and out.stat().st_size > 500
