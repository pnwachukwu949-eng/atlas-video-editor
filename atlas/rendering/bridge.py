#!/usr/bin/env python3
"""Atlas Render Bridge — Edit Spec to Timeline."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


class RenderBridge:
    def __init__(self, frame_rate: float = 30.0, width: int = 1920, height: int = 1080):
        self.frame_rate = frame_rate
        self.width = width
        self.height = height
        self.version = "0.1"

    def build_timeline(self, edit_spec: Dict[str, Any]) -> Dict[str, Any]:
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

        for beat in edit_spec.get("beats", []):
            beat_id = beat["beat_id"]
            start, end = beat["start"], beat["end"]
            visual = beat.get("visual", {})
            composition = beat.get("composition", {})
            motion = beat.get("motion", {})
            typography = beat.get("typography", {})
            evidence = beat.get("evidence_status", {})
            captions = beat.get("captions", {})

            video_clips.append({
                "start": start,
                "end": end,
                "asset_id": visual.get("asset_id"),
                "type": visual.get("type", "unknown"),
                "label": visual.get("label", ""),
                "motion": motion.get("type"),
                "layout": composition.get("layout"),
                "locked": visual.get("locked", False),
                "beat_id": beat_id,
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
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_version": edit_spec.get("version"),
            },
        }


def build_timeline_from_edit_spec(edit_spec: Dict[str, Any]) -> Dict[str, Any]:
    """CLI helper used by scripts/build_timeline.py and scripts/atlas_build.py."""
    return RenderBridge().build_timeline(edit_spec)
