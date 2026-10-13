"""Typography primary_text dual-writes captions.text."""
from atlas.engines.constraint_revision.engine import ConstraintRevisionEngine


def test_caption_sync_on_typography_change():
    edit = {
        "edit_id": "e1",
        "locks": {"voiceover": True},
        "beats": [{
            "beat_id": "B01",
            "start": 0,
            "end": 3,
            "typography": {"primary_text": "Old", "locked": False},
            "captions": {"text": "Old", "locked": False},
            "visual": {"asset_id": "x", "locked": False},
        }],
    }
    revision = {
        "revision_id": "r1",
        "target_edit": "e1",
        "instructions": [{
            "action": "change_typography",
            "beat_id": "B01",
            "new_value": {"primary_text": "New caption line"},
        }],
    }
    result = ConstraintRevisionEngine().apply_revision(edit, revision)
    if isinstance(result, tuple):
        revised, report = result
    elif isinstance(result, dict) and "edit_spec" in result:
        revised = result["edit_spec"]
    else:
        revised = result
    beat = revised["beats"][0]
    primary = (beat.get("typography") or {}).get("primary_text")
    cap = (beat.get("captions") or {}).get("text")
    assert primary == "New caption line"
    assert cap == "New caption line"
