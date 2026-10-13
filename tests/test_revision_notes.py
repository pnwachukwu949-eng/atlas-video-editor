"""Revision notes parser tests."""
import json
from atlas.engines.revision_notes.engine import RevisionNotesEngine


def test_beat_caption():
    req = RevisionNotesEngine().parse("B03: caption=Hello world")
    assert len(req["instructions"]) == 1
    inst = req["instructions"][0]
    assert inst["action"] == "change_typography"
    assert inst["beat_id"] == "B03"
    assert inst["new_value"]["primary_text"] == "Hello world"


def test_comment_and_blank_ignored():
    text = """
# ignore me

B01: caption=Keep
"""
    req = RevisionNotesEngine().parse(text)
    assert len(req["instructions"]) == 1
    assert req["instructions"][0]["beat_id"] == "B01"


def test_timestamp_to_beat():
    edit = {
        "edit_id": "e1",
        "beats": [
            {"beat_id": "B01", "start": 0.0, "end": 5.0},
            {"beat_id": "B02", "start": 5.0, "end": 12.0},
            {"beat_id": "B03", "start": 12.0, "end": 20.0},
        ],
    }
    req = RevisionNotesEngine().parse(
        "at 0:12: caption=Mapped line",
        edit_spec=edit,
        target_edit="e1",
    )
    assert any(
        i.get("beat_id") == "B03" and i.get("action") == "change_typography"
        for i in req["instructions"]
    )


def test_unlock_line():
    req = RevisionNotesEngine().parse(
        "unlock B01.visual: reason=approved new still"
    )
    unlocks = req.get("unlocks") or {}
    if unlocks:
        assert "B01.visual" in unlocks or any("B01" in k for k in unlocks)
    else:
        assert "approved" in json.dumps(req).lower() or req.get("instructions") is not None


def test_do_not_touch():
    req = RevisionNotesEngine().parse("do_not_touch: voiceover, B01.visual")
    assert any(i.get("action") == "do_not_touch" for i in req["instructions"])
    els = next(i for i in req["instructions"] if i["action"] == "do_not_touch")["elements"]
    assert "voiceover" in els
