#!/usr/bin/env python3
"""
Atlas Motion Presets v0.1 — Ken-Burns / camera-2D recipes only.

Named, versioned presets. Not a full keyframe system.
All movement is 2D simulation via zoom/pan on stills.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

PRESETS: Dict[str, Dict[str, Any]] = {
    "kb_static": {
        "preset_id": "kb_static",
        "version": "1",
        "family": "camera_2d",
        "label": "Static hold",
        "description": "No camera move — reading / legal / release beats",
        "legacy_types": ["none", "static", "hold"],
        "params": {
            "zoom_start": 1.0,
            "zoom_end": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "ease": "linear",
            "intensity": 0.0,
        },
    },
    "kb_slow_push": {
        "preset_id": "kb_slow_push",
        "version": "1",
        "family": "camera_2d",
        "label": "Slow push-in",
        "description": "Gentle centered zoom — establish / product hook",
        "legacy_types": ["slow_push"],
        "params": {
            "zoom_start": 1.0,
            "zoom_end": 1.06,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "ease": "ease_in_out",
            "intensity": 0.35,
        },
    },
    "kb_pull_back": {
        "preset_id": "kb_pull_back",
        "version": "1",
        "family": "camera_2d",
        "label": "Pull back",
        "description": "Gentle zoom-out — reveal / context",
        "legacy_types": ["pull_back"],
        "params": {
            "zoom_start": 1.06,
            "zoom_end": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "ease": "ease_in_out",
            "intensity": 0.35,
        },
    },
    "kb_pan_right": {
        "preset_id": "kb_pan_right",
        "version": "1",
        "family": "camera_2d",
        "label": "Pan right",
        "description": "Slight horizontal drift with micro-zoom",
        "legacy_types": ["pan_right"],
        "params": {
            "zoom_start": 1.0,
            "zoom_end": 1.04,
            "pan_x": 0.35,
            "pan_y": 0.0,
            "ease": "ease_in_out",
            "intensity": 0.3,
        },
    },
    "kb_pan_left": {
        "preset_id": "kb_pan_left",
        "version": "1",
        "family": "camera_2d",
        "label": "Pan left",
        "description": "Slight horizontal drift (opposite) with micro-zoom",
        "legacy_types": ["pan_left"],
        "params": {
            "zoom_start": 1.0,
            "zoom_end": 1.04,
            "pan_x": -0.35,
            "pan_y": 0.0,
            "ease": "ease_in_out",
            "intensity": 0.3,
        },
    },
    "kb_subtle_hold": {
        "preset_id": "kb_subtle_hold",
        "version": "1",
        "family": "camera_2d",
        "label": "Subtle hold",
        "description": "Near-static micro-zoom — prove / emphasis without distraction",
        "legacy_types": [],
        "params": {
            "zoom_start": 1.0,
            "zoom_end": 1.02,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "ease": "ease_out",
            "intensity": 0.15,
        },
    },
}


def list_presets() -> List[str]:
    return sorted(PRESETS.keys())


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    return PRESETS.get(preset_id)


def legacy_type_to_preset_id(legacy: str) -> str:
    t = (legacy or "").strip().lower()
    if not t:
        return "kb_slow_push"
    for pid, spec in PRESETS.items():
        if t in (spec.get("legacy_types") or []):
            return pid
    aliases = {
        "push": "kb_slow_push",
        "push_in": "kb_slow_push",
        "zoom_in": "kb_slow_push",
        "zoom_out": "kb_pull_back",
        "pull": "kb_pull_back",
    }
    return aliases.get(t, "kb_slow_push")
