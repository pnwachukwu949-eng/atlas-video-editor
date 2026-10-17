import importlib.util
from pathlib import Path

def _load():
    path = Path("scripts/fill_queue.py")
    spec = importlib.util.spec_from_file_location("fill_queue", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_registry_prefers_video_for_place_query():
    mod = _load()
    reg = {
        "assets": {
            "still_a": {"path": "contextual/x.jpg", "type": "contextual_photo", "description": "checklist card"},
            "vid_a": {"path": "video/mixkit_residential_4332.mp4", "type": "contextual_video", "description": "residential neighborhood suburban"},
        },
        "banned": {},
    }
    pick = mod._pick_from_registry("suburban neighborhood houses", reg, min_score=1.0)
    assert pick is not None
    assert pick[0] == "vid_a"

def test_banned_not_picked():
    mod = _load()
    reg = {
        "assets": {
            "vid_a": {"path": "video/mixkit_residential_4332.mp4", "type": "contextual_video", "description": "residential neighborhood"},
        },
        "banned": {"vid_a": "test ban"},
    }
    pick = mod._pick_from_registry("suburban neighborhood", reg, min_score=1.0)
    assert pick is None
