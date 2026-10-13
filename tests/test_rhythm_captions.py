"""Profile caption limits via EditorialRhythmEngine."""
from atlas.engines.rhythm.engine import EditorialRhythmEngine


def _edit(caption: str, profile_id: str = "product"):
    return {
        "edit_id": "cap",
        "profile_id": profile_id,
        "source_voiceover": {"duration_seconds": 5},
        "beats": [{
            "beat_id": "B01",
            "start": 0,
            "end": 5,
            "captions": {"text": caption},
            "intention": {"job": "establish"},
            "visual": {"asset_id": "x"},
        }],
    }


def test_social_flags_long():
    profile = {"profile_id": "social", "caption_max_chars": 55, "caption_max_lines": 2}
    long = "x" * 70
    r = EditorialRhythmEngine().evaluate(_edit(long, "social"), job_profile=profile)
    codes = [f["code"] for f in r["findings"]]
    assert "caption_long" in codes
    assert r["caption_limits"]["max_chars"] == 55


def test_product_allows_70():
    profile = {"profile_id": "product", "caption_max_chars": 75, "caption_max_lines": 2}
    r = EditorialRhythmEngine().evaluate(_edit("x" * 70, "product"), job_profile=profile)
    assert "caption_long" not in [f["code"] for f in r["findings"]]


def test_investigative_allows_85():
    profile = {"profile_id": "investigative", "caption_max_chars": 90, "caption_max_lines": 2}
    r = EditorialRhythmEngine().evaluate(_edit("x" * 85, "investigative"), job_profile=profile)
    assert "caption_long" not in [f["code"] for f in r["findings"]]
