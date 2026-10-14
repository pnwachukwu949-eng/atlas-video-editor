#!/usr/bin/env python3
"""Motion Engine v0.1 — presets, resolution, clamping, ffmpeg compile."""

from __future__ import annotations

from atlas.engines.motion import (
    MotionEngine,
    build_ffmpeg_zoompan,
    get_preset,
    legacy_type_to_preset_id,
    list_presets,
)


def test_preset_catalog_has_five_kb_family():
    ids = list_presets()
    for required in (
        "kb_static",
        "kb_slow_push",
        "kb_pull_back",
        "kb_pan_right",
        "kb_pan_left",
        "kb_subtle_hold",
    ):
        assert required in ids
        p = get_preset(required)
        assert p is not None
        assert "params" in p
        assert p["family"] == "camera_2d"


def test_legacy_type_mapping():
    assert legacy_type_to_preset_id("slow_push") == "kb_slow_push"
    assert legacy_type_to_preset_id("none") == "kb_static"
    assert legacy_type_to_preset_id("pan_left") == "kb_pan_left"
    assert legacy_type_to_preset_id("hold") == "kb_static"


def test_resolve_intention_prove_is_subtle():
    eng = MotionEngine()
    spec = eng.for_intention("prove", style_motion_default="slow_push")
    assert spec["preset_id"] == "kb_subtle_hold"
    assert spec["params"]["zoom_end"] <= 1.05


def test_resolve_intention_release_is_static():
    eng = MotionEngine()
    spec = eng.for_intention("release")
    assert spec["preset_id"] == "kb_static"
    assert abs(spec["params"]["zoom_end"] - spec["params"]["zoom_start"]) < 0.001


def test_anti_repeat_changes_neighbor():
    eng = MotionEngine()
    a = eng.for_intention("illustrate", style_motion_default="slow_push", prev_preset_id=None)
    b = eng.for_intention(
        "illustrate",
        style_motion_default="slow_push",
        prev_preset_id=a["preset_id"],
    )
    assert a["preset_id"] != b["preset_id"] or a["preset_id"] in ("kb_static", "kb_subtle_hold")


def test_unknown_preset_falls_back_safely():
    eng = MotionEngine()
    spec = eng.resolve(motion_field={"preset_id": "does_not_exist", "type": "slow_push"})
    assert spec["preset_id"] in list_presets()
    assert "params" in spec


def test_clamp_blocks_extreme_zoom():
    eng = MotionEngine()
    spec = eng.resolve(
        motion_field={
            "preset_id": "kb_slow_push",
            "params": {"zoom_end": 2.5, "pan_x": 9.0},
        }
    )
    assert spec["params"]["zoom_end"] <= 1.12
    assert abs(spec["params"]["pan_x"]) <= 1.0


def test_build_ffmpeg_static_is_simple_crop():
    filt = build_ffmpeg_zoompan(
        {"zoom_start": 1.0, "zoom_end": 1.0, "pan_x": 0.0, "pan_y": 0.0},
        1920,
        1080,
        3.0,
    )
    assert "zoompan" not in filt
    assert "crop=1920:1080" in filt


def test_build_ffmpeg_push_uses_zoompan():
    filt = build_ffmpeg_zoompan(
        {"zoom_start": 1.0, "zoom_end": 1.06, "pan_x": 0.0, "pan_y": 0.0, "intensity": 0.35},
        1920,
        1080,
        3.0,
    )
    assert "zoompan" in filt
    assert "1920x1080" in filt


def test_old_type_string_still_resolves():
    eng = MotionEngine()
    spec = eng.resolve(motion_field={"type": "pan_right", "locked": False})
    assert spec["preset_id"] == "kb_pan_right"
    assert spec["type"] == "pan_right"
