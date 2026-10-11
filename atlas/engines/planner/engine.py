#!/usr/bin/env python3
"""
Atlas Beat Planner v0.2

Turns narration text + duration + Style DNA + job profile into a generic
Edit Specification. Genre-agnostic: no HOA-shaped assumptions.
Supports opening vs body shot pacing when Style DNA provides it.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class BeatPlanner:
    version = "0.2"

    def plan(
        self,
        narration_text: str,
        duration_seconds: float,
        style_defaults: Optional[Dict[str, Any]] = None,
        job_profile: Optional[Dict[str, Any]] = None,
        edit_id: str = "edit_auto",
        voiceover_asset_id: str = "vo_main",
        asset_pool: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build an Edit Spec from narration.

        Segments are split on sentence boundaries, then merged/split to
        approximate Style DNA target shot length.
        """
        style_defaults = style_defaults or {}
        job_profile = job_profile or {}
        asset_pool = asset_pool or []

        target = float(style_defaults.get("target_avg_shot_seconds") or 4.0)
        target = max(1.5, min(target, 20.0))
        transition = style_defaults.get("preferred_transition", "hard_cut")
        motion = style_defaults.get("motion_default", "slow_push")
        caption_style = style_defaults.get("caption_style") or {"position": "bottom", "max_lines": 2}
        evidence_strict = job_profile.get("evidence_strictness", "off")
        vo_locked = True

        sentences = self._split_sentences(narration_text)
        if not sentences:
            sentences = [narration_text.strip() or "Narration"]

        weights = [max(1, len(s)) for s in sentences]
        total_w = sum(weights)
        raw = []
        t = 0.0
        for s, w in zip(sentences, weights):
            dur = duration_seconds * (w / total_w)
            raw.append({"text": s, "start": t, "end": t + dur})
            t += dur
        if raw:
            raw[-1]["end"] = duration_seconds

        beats_src = self._fit_to_target_shot(raw, target)
        beats_src = self._apply_opening_body_pacing(
            beats_src,
            duration_seconds,
            style_defaults.get("opening_shot_seconds"),
            style_defaults.get("body_avg_shot_seconds"),
        )

        beats: List[Dict[str, Any]] = []
        for i, seg in enumerate(beats_src):
            beat_id = f"B{i+1:02d}"
            text = seg["text"].strip()
            caption = self._caption_line(text, caption_style.get("max_lines", 2))
            asset_id = asset_pool[i % len(asset_pool)] if asset_pool else None

            beat: Dict[str, Any] = {
                "beat_id": beat_id,
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "narration_summary": text[:160],
                "visual": {
                    "asset_id": asset_id,
                    "type": "contextual_photo" if asset_id else "placeholder",
                    "label": "",
                    "locked": False,
                },
                "typography": {
                    "primary_text": caption,
                    "secondary_text": "",
                    "locked": False,
                },
                "captions": {
                    "text": caption,
                    "locked": False,
                },
                "composition": {
                    "layout": "full_frame",
                    "locked": False,
                },
                "motion": {
                    "type": motion if motion != "static" else "none",
                    "locked": False,
                },
                "timing": {
                    "transition_in": transition,
                    "locked": False,
                },
            }
            if evidence_strict in ("light", "strict"):
                beat["evidence_status"] = {
                    "status": "unspecified",
                    "locked": evidence_strict == "strict",
                }
            beats.append(beat)

        edit_spec = {
            "edit_id": edit_id,
            "version": "0.2-planner",
            "profile_id": job_profile.get("profile_id"),
            "style_id": style_defaults.get("style_id"),
            "source_voiceover": {
                "asset_id": voiceover_asset_id,
                "duration_seconds": duration_seconds,
                "locked": vo_locked,
            },
            "global_locks": {
                "voiceover": vo_locked,
                "overall_duration": False,
                "evidence_policy": evidence_strict == "strict",
            },
            "beats": beats,
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "planner_version": self.version,
                "target_avg_shot_seconds": target,
                "sentence_count": len(sentences),
                "beat_count": len(beats),
                "notes": "Generic plan from narration + Style DNA + job profile",
            },
        }
        return edit_spec

    def _apply_opening_body_pacing(
        self,
        segments: List[Dict[str, Any]],
        total_duration: float,
        opening_shot: Any,
        body_avg: Any,
    ) -> List[Dict[str, Any]]:
        """Bias first segment toward Style DNA opening length; rescale the rest."""
        if not segments or total_duration <= 0:
            return segments
        try:
            open_t = float(opening_shot) if opening_shot is not None else None
        except (TypeError, ValueError):
            open_t = None
        if open_t is None or open_t <= 0:
            return segments

        open_t = max(0.4, min(open_t, total_duration * 0.4))
        rest = total_duration - open_t
        if len(segments) == 1:
            segments[0]["start"] = 0.0
            segments[0]["end"] = total_duration
            return segments

        first = dict(segments[0])
        first["start"] = 0.0
        first["end"] = open_t
        others = segments[1:]
        weights = [max(0.05, o["end"] - o["start"]) for o in others]
        wsum = sum(weights) or 1.0
        t = open_t
        out = [first]
        for o, w in zip(others, weights):
            dur = rest * (w / wsum)
            out.append({"text": o["text"], "start": t, "end": t + dur})
            t += dur
        if out:
            out[-1]["end"] = total_duration
        return out

    def _split_sentences(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]

    def _fit_to_target_shot(
        self, segments: List[Dict[str, Any]], target: float
    ) -> List[Dict[str, Any]]:
        if not segments:
            return []
        merged: List[Dict[str, Any]] = []
        buf_text: List[str] = []
        buf_start = segments[0]["start"]
        buf_end = segments[0]["end"]

        def flush():
            nonlocal buf_text, buf_start, buf_end
            if not buf_text:
                return
            merged.append({
                "text": " ".join(buf_text),
                "start": buf_start,
                "end": buf_end,
            })
            buf_text = []

        for seg in segments:
            dur = seg["end"] - seg["start"]
            if not buf_text:
                buf_start = seg["start"]
                buf_end = seg["end"]
                buf_text = [seg["text"]]
                continue
            cur = buf_end - buf_start
            if cur + dur <= target * 1.35:
                buf_text.append(seg["text"])
                buf_end = seg["end"]
            else:
                flush()
                buf_start = seg["start"]
                buf_end = seg["end"]
                buf_text = [seg["text"]]
        flush()
        return merged

    def _caption_line(self, text: str, max_lines: int = 2) -> str:
        words = text.split()
        if len(words) <= 8:
            return text
        line = " ".join(words[:12])
        if len(words) > 12:
            line += "…"
        return line
