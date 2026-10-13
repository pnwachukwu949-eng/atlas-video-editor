"""Planner consecutive still avoidance + hook preference."""
from atlas.engines.planner.engine import BeatPlanner


def test_no_consecutive_identical():
    pool = ["a_house", "b_house", "c_house"]
    defaults = {
        "target_avg_shot_seconds": 3.0,
        "picture_lag_seconds": 0.1,
        "motion_default": "slow_push",
        "preferred_transition": "hard_cut",
        "caption_style": {},
    }
    profile = {"profile_id": "product", "caption_max_chars": 75}
    narr = "One. Two. Three. Four. Five. Six."
    edit = BeatPlanner().plan(
        narration_text=narr,
        duration_seconds=18,
        style_defaults=defaults,
        job_profile=profile,
        edit_id="div",
        asset_pool=pool,
    )
    ids = [b["visual"]["asset_id"] for b in edit["beats"]]
    consec = sum(1 for i in range(1, len(ids)) if ids[i] == ids[i - 1])
    assert consec == 0, ids


def test_meet_atlas_prefers_hook_when_scored():
    from atlas.engines.planner.engine import BeatPlanner
    bp = BeatPlanner()
    reg = {
        "assets": {
            "product_hook_card": {
                "label": "ATLAS hook",
                "tags": ["atlas", "meet", "hook", "title"],
                "description": "Meet Atlas intro title",
            },
            "plain_house": {
                "label": "suburban house",
                "tags": ["house"],
                "description": "house exterior",
            },
        }
    }
    s_hook = bp._score_asset("Meet Atlas.", "product_hook_card", reg, [])
    s_house = bp._score_asset("Meet Atlas.", "plain_house", reg, [])
    assert s_hook > s_house
