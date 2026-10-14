#!/usr/bin/env python3
"""
Atlas Motion Engine v0.1

Resolves named Ken-Burns presets into a Motion Spec the renderer can apply.
Story binding: intention → preferred preset (still editorial, not decoration).
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from atlas.engines.motion.presets import (
    PRESETS,
    get_preset,
    legacy_type_to_preset_id,
    list_presets,
)


class MotionEngine:
    version = "0.1"

    INTENTION_PRESET = {
        "establish": "kb_slow_push",
        "illustrate": None,
        "prove": "kb_subtle_hold",
        "release": "kb_static",
        "callback": "kb_slow_push",
        "hold": "kb_static",
    }

    REPEAT_CYCLE = [
        "kb_slow_push",
        "kb_pan_right",
        "kb_pan_left",
        "kb_pull_back",
    ]

    def resolve(
        self,
        *,
        motion_field: Optional[Dict[str, Any]] = None,
        legacy_type: Optional[str] = None,
        intention: Optional[str] = None,
        style_motion_default: Optional[str] = None,
        intensity_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        field = dict(motion_field or {})
        locked = bool(field.get("locked"))

        preset_id = field.get("preset_id")
        if not preset_id or preset_id not in PRESETS:
            intent = (intention or "").lower()
            preferred = self.INTENTION_PRESET.get(intent)
            if preferred:
                preset_id = preferred
            else:
                raw = (
                    field.get("type")
                    or legacy_type
                    or style_motion_default
                    or "slow_push"
                )
                preset_id = legacy_type_to_preset_id(str(raw))

        spec = get_preset(preset_id) or get_preset("kb_slow_push")
        assert spec is not None
        params = copy.deepcopy(spec["params"])

        intensity = params.get("intensity", 0.35)
        if intensity_override is not None:
            intensity = max(0.0, min(1.0, float(intensity_override)))
            params["intensity"] = intensity
            params = self._scale_params_by_intensity(params, intensity, spec["params"])

        user_params = field.get("params") or {}
        if isinstance(user_params, dict):
            for k, v in user_params.items():
                if k in params and isinstance(v, (int, float)):
                    params[k] = float(v)
        params = self._clamp_params(params)

        return {
            "preset_id": preset_id,
            "type": self._legacy_type_for(preset_id, field.get("type")),
            "family": "camera_2d",
            "params": params,
            "locked": locked,
            "engine_version": self.version,
        }

    def for_intention(
        self,
        intention: str,
        style_motion_default: str = "slow_push",
        prev_preset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        intent = (intention or "illustrate").lower()
        preferred = self.INTENTION_PRESET.get(intent)
        if preferred:
            preset_id = preferred
        else:
            preset_id = legacy_type_to_preset_id(style_motion_default)

        if (
            prev_preset_id
            and preset_id == prev_preset_id
            and preset_id not in ("kb_static", "kb_subtle_hold")
        ):
            preset_id = self._next_in_cycle(prev_preset_id)

        return self.resolve(
            motion_field={"preset_id": preset_id},
            intention=intent,
            style_motion_default=style_motion_default,
        )

    def _next_in_cycle(self, current: str) -> str:
        cycle = self.REPEAT_CYCLE
        if current not in cycle:
            return cycle[0]
        return cycle[(cycle.index(current) + 1) % len(cycle)]

    def _legacy_type_for(self, preset_id: str, existing: Any) -> str:
        mapping = {
            "kb_static": "none",
            "kb_slow_push": "slow_push",
            "kb_pull_back": "pull_back",
            "kb_pan_right": "pan_right",
            "kb_pan_left": "pan_left",
            "kb_subtle_hold": "none",
        }
        if existing in ("slow_push", "pan_right", "pan_left", "none", "static", "hold", "pull_back"):
            return mapping.get(preset_id, str(existing))
        return mapping.get(preset_id, "slow_push")

    def _scale_params_by_intensity(
        self,
        params: Dict[str, Any],
        intensity: float,
        base: Dict[str, Any],
    ) -> Dict[str, Any]:
        out = dict(params)
        base_zs = float(base.get("zoom_start", 1.0))
        base_ze = float(base.get("zoom_end", 1.0))
        base_intensity = float(base.get("intensity") or 0.35) or 0.35
        factor = intensity / base_intensity if base_intensity else 1.0
        delta = (base_ze - base_zs) * factor
        out["zoom_start"] = base_zs
        out["zoom_end"] = base_zs + delta
        out["pan_x"] = float(base.get("pan_x", 0.0)) * factor
        out["pan_y"] = float(base.get("pan_y", 0.0)) * factor
        out["intensity"] = intensity
        return out

    def _clamp_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(params)
        zs = float(out.get("zoom_start", 1.0))
        ze = float(out.get("zoom_end", 1.0))
        zs = max(1.0, min(1.12, zs))
        ze = max(1.0, min(1.12, ze))
        out["zoom_start"] = round(zs, 4)
        out["zoom_end"] = round(ze, 4)
        out["pan_x"] = round(max(-1.0, min(1.0, float(out.get("pan_x", 0.0)))), 4)
        out["pan_y"] = round(max(-1.0, min(1.0, float(out.get("pan_y", 0.0)))), 4)
        ease = str(out.get("ease") or "ease_in_out")
        if ease not in ("linear", "ease_in", "ease_out", "ease_in_out"):
            ease = "ease_in_out"
        out["ease"] = ease
        out["intensity"] = round(max(0.0, min(1.0, float(out.get("intensity", 0.35)))), 3)
        return out


def build_ffmpeg_zoompan(
    params: Dict[str, Any],
    width: int,
    height: int,
    seg_duration: float,
    fps: float = 30.0,
) -> str:
    zs = float(params.get("zoom_start", 1.0))
    ze = float(params.get("zoom_end", 1.0))
    pan_x = float(params.get("pan_x", 0.0))
    pan_y = float(params.get("pan_y", 0.0))
    frames = max(8, int(float(seg_duration) * float(fps)))

    if abs(ze - zs) < 0.001 and abs(pan_x) < 0.001 and abs(pan_y) < 0.001:
        return (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
        )

    z_expr = f"{zs}+({ze}-{zs})*on/{frames}"
    max_shift = 28
    x_shift = f"({pan_x})*{max_shift}*on/{frames}"
    y_shift = f"({pan_y})*{max_shift}*on/{frames}"
    x = f"iw/2-(iw/zoom/2)-({x_shift})"
    y = f"ih/2-(ih/zoom/2)-({y_shift})"

    return (
        f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
        f"crop={width * 2}:{height * 2},"
        f"zoompan=z='{z_expr}':x='{x}':y='{y}':d=1:s={width}x{height}:fps={int(fps)}"
    )
