#!/usr/bin/env python3
"""
Atlas Render Bridge v0.2

Converts an Edit Specification into a renderer-ready Timeline.
Supports picture lag (J-cut / L-cut feel) so audio and picture
need not share identical cut points — intentional craft, not generator flash.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


class RenderBridge:
    def __init__(self, frame_rate: float = 30.0, width: int = 1920, height: int = 1080):
        self.frame_rate = frame_rate
        self.width = width
        self.height = height
        self.version = "0.2"

    def build_timeline(self, edit_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an Edit Specification into a Timeline that a renderer can consume."""
        video_clips: List[Dict] = []
        caption_clips: List[Dict] = []
        overlay_clips: List[Dict] = []
        locks_honored: List[str] = []

        duration = edit_spec.get("source_voiceover", {}).get("duration_seconds", 0.0)

        audio_clips = []
        vo = edit_spec.get("source_voiceover", {})
        if vo.get("asset_id"):
            audio_clips.append({
                "start": 0.0,
                "end": duration,
                "asset_id": vo["asset_id"],
                "type": "voiceover",
                "locked": vo.get("locked", True),
            })
            if vo.get("locked", True):
                locks_honored.append("voiceover")

        style_av = edit_spec.get("style_av") or {}
        default_picture_lag = float(style_av.get("picture_lag_seconds") or 0.0)
        # picture_lag > 0 → J-cut feel (hear new line, old picture holds briefly)
        # picture_lag < 0 → L-cut feel (new picture arrives slightly before the line)

        for beat in edit_spec.get("beats", []):
            beat_id = beat["beat_id"]
            start = float(beat["start"])
            end = float(beat["end"])

            visual = beat.get("visual", {})
            composition = beat.get("composition", {})
            motion = beat.get("motion", {})
            typography = beat.get("typography", {})
            evidence = beat.get("evidence_status", {})
            captions = beat.get("captions", {})
            timing = beat.get("timing") or {}

            lag = timing.get("picture_lag_seconds")
            if lag is None:
                lag = default_picture_lag
            try:
                lag = float(lag)
            except (TypeError, ValueError):
                lag = 0.0

            v_start = start + lag
            v_end = end + lag
            v_start = max(0.0, v_start)
            v_end = min(duration, max(v_start + 0.05, v_end)) if duration else max(v_start + 0.05, v_end)

            video_clips.append({
                "start": round(v_start, 3),
                "end": round(v_end, 3),
                "asset_id": visual.get("asset_id"),
                "type": visual.get("type", "unknown"),
                "label": visual.get("label", ""),
                "motion": motion.get("type"),
                "layout": composition.get("layout"),
                "locked": visual.get("locked", False),
                "beat_id": beat_id,
                "picture_lag_seconds": lag,
                "narration_start": start,
                "narration_end": end,
            })
            if visual.get("locked"):
                locks_honored.append(f"{beat_id}.visual")

            if typography.get("primary_text"):
                overlay_clips.append({
                    "start": start,
                    "end": end,
                    "content": typography.get("primary_text"),
                    "secondary": typography.get("secondary_text"),
                    "type": "typography",
                    "locked": typography.get("locked", False),
                    "beat_id": beat_id,
                })
                if typography.get("locked"):
                    locks_honored.append(f"{beat_id}.typography")

            if evidence.get("status") in ("allegation", "locked_unavailable", "illustrative"):
                overlay_clips.append({
                    "start": start,
                    "end": end,
                    "content": evidence.get("status"),
                    "type": "evidence_marker",
                    "locked": evidence.get("locked", True),
                    "beat_id": beat_id,
                })
                if evidence.get("locked", True):
                    locks_honored.append(f"{beat_id}.evidence_status")

            if captions.get("text"):
                caption_clips.append({
                    "start": start,
                    "end": end,
                    "text": captions["text"],
                    "locked": captions.get("locked", False),
                    "beat_id": beat_id,
                })

        video_clips = self._stitch_video(video_clips, duration)

        return {
            "timeline_id": f"tl_{edit_spec.get('edit_id', 'unknown')}",
            "source_edit": edit_spec.get("edit_id"),
            "duration_seconds": duration,
            "frame_rate": self.frame_rate,
            "resolution": {"width": self.width, "height": self.height},
            "tracks": {
                "video": video_clips,
                "audio": audio_clips,
                "captions": caption_clips,
                "overlays": overlay_clips,
            },
            "locks_honored": sorted(list(set(locks_honored))),
            "metadata": {
                "bridge_version": self.version,
                "supports_av_offset": True,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_version": edit_spec.get("version"),
                "notes": "Renderer-ready timeline with optional J/L picture lag.",
            },
        }

    def _stitch_video(self, clips: List[Dict], duration: float) -> List[Dict]:
        """Make picture continuous after J/L lag shifts; avoid black flash gaps."""
        if not clips:
            return clips
        clips = sorted(clips, key=lambda c: c["start"])
        clips[0]["start"] = 0.0
        for i in range(len(clips) - 1):
            a, b = clips[i], clips[i + 1]
            if a["end"] < b["start"]:
                a["end"] = b["start"]
            elif a["end"] > b["start"]:
                a["end"] = b["start"]
        if duration and clips:
            clips[-1]["end"] = max(clips[-1]["end"], duration)
        return clips


def build_from_file(edit_path: str, out_path: str) -> Dict[str, Any]:
    with open(edit_path) as f:
        edit_spec = json.load(f)
    bridge = RenderBridge()
    timeline = bridge.build_timeline(edit_spec)
    with open(out_path, "w") as f:
        json.dump(timeline, f, indent=2)
    return timeline


def build_timeline_from_edit_spec(edit_spec: Dict[str, Any]) -> Dict[str, Any]:
    """CLI helper used by scripts/build_timeline.py and scripts/atlas_build.py."""
    return RenderBridge().build_timeline(edit_spec)
