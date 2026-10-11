#!/usr/bin/env python3
"""
Atlas Style DNA Engine v0.2

Extracts editing *grammar* from a reference video (or accepts a manual DNA),
then applies that grammar as defaults when planning beats for a new job.

This is not a visual clone of the reference.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class StyleDNAEngine:
    version = "0.2"

    def extract_from_video(
        self,
        video_path: str,
        style_id: Optional[str] = None,
        scene_threshold: float = 0.35,
    ) -> Dict[str, Any]:
        """
        Estimate shot length / cut density via ffmpeg scene detection.
        Falls back to duration-based defaults if scene detection yields nothing.
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Reference video not found: {video_path}")

        duration = self._probe_duration(path)
        cut_times = self._scene_cuts(path, scene_threshold)
        boundaries = [0.0] + cut_times + ([duration] if duration else [])
        boundaries = sorted(set(round(t, 3) for t in boundaries if t is not None))
        shots = []
        for i in range(len(boundaries) - 1):
            length = boundaries[i + 1] - boundaries[i]
            if length > 0.05:
                shots.append(length)

        if not shots and duration:
            shots = [duration]
            method_note = "ffprobe_scene (no cuts detected; single-shot fallback)"
        else:
            method_note = "ffprobe_scene"

        avg = sum(shots) / len(shots) if shots else 3.0
        median = sorted(shots)[len(shots) // 2] if shots else avg
        cuts_per_min = (len(shots) / (duration / 60.0)) if duration and duration > 0 else 0.0

        short = sum(1 for s in shots if s < 2.0)
        medium = sum(1 for s in shots if 2.0 <= s < 5.0)
        long = sum(1 for s in shots if s >= 5.0)
        n = max(1, len(shots))
        hist = {
            "short_pct": round(100.0 * short / n, 1),
            "medium_pct": round(100.0 * medium / n, 1),
            "long_pct": round(100.0 * long / n, 1),
        }

        opening_shot = round(shots[0], 2) if shots else None
        body = shots[1:] if len(shots) > 1 else shots
        body_avg = round(sum(body) / len(body), 2) if body else round(avg, 2)

        if avg < 2.0:
            broll, pacing_motion = "high", "mixed"
        elif avg < 4.5:
            broll, pacing_motion = "medium", "slow_push"
        else:
            broll, pacing_motion = "low", "static"

        style_id = style_id or f"style_{path.stem}"

        return {
            "style_id": style_id,
            "version": self.version,
            "source": {
                "reference_path": str(path),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "method": "ffprobe_scene",
                "duration_seconds": duration,
                "shot_count": len(shots),
                "notes": method_note,
            },
            "grammar": {
                "avg_shot_seconds": round(avg, 2),
                "median_shot_seconds": round(median, 2),
                "cut_density_per_minute": round(cuts_per_min, 2),
                "shot_length_histogram": hist,
                "opening_shot_seconds": opening_shot,
                "body_avg_shot_seconds": body_avg,
                "preferred_transition": "hard_cut",
                "caption_style": {
                    "position": "bottom",
                    "max_lines": 2,
                    "emphasis": "key_nouns",
                },
                "broll_density": broll,
                "hold_on_key_claims": avg >= 3.0,
                "motion": pacing_motion,
                "visual_mode_changes": "moderate" if cuts_per_min > 8 else "rare",
            },
            "notes": "Grammar only — do not clone reference footage or graphics.",
        }

    def apply_to_edit_defaults(
        self,
        style_dna: Dict[str, Any],
        job_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Produce planning defaults for a new edit from Style DNA (+ optional job profile)."""
        g = style_dna.get("grammar", {})
        profile = job_profile or {}
        target_shot = g.get("avg_shot_seconds", 3.5)

        pacing = profile.get("pacing", "balanced")
        if pacing == "dense":
            target_shot = max(1.5, target_shot * 0.75)
        elif pacing == "relaxed":
            target_shot = target_shot * 1.25

        return {
            "style_id": style_dna.get("style_id"),
            "profile_id": profile.get("profile_id"),
            "target_avg_shot_seconds": round(target_shot, 2),
            "opening_shot_seconds": g.get("opening_shot_seconds"),
            "body_avg_shot_seconds": g.get("body_avg_shot_seconds"),
            "shot_length_histogram": g.get("shot_length_histogram"),
            "preferred_transition": g.get("preferred_transition", "hard_cut"),
            "caption_style": g.get("caption_style", {"position": "bottom", "max_lines": 2}),
            "broll_density": g.get("broll_density", "medium"),
            "motion_default": g.get("motion", "slow_push"),
            "hold_on_key_claims": g.get("hold_on_key_claims", True),
            "visual_mode_changes": g.get("visual_mode_changes", "rare"),
            "repeat_cap": profile.get("repeat_cap", 2),
            "evidence_strictness": profile.get("evidence_strictness", "off"),
            "prefer_real_footage": profile.get("prefer_real_footage", True),
        }

    def _probe_duration(self, path: Path) -> float:
        r = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(r.stdout.strip())
        except (ValueError, AttributeError):
            return 0.0

    def _scene_cuts(self, path: Path, threshold: float) -> List[float]:
        """Return timestamps where scene score exceeds threshold."""
        r = subprocess.run(
            [
                "ffmpeg", "-i", str(path),
                "-filter:v", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null", "-",
            ],
            capture_output=True,
            text=True,
        )
        times: List[float] = []
        for line in (r.stderr or "").splitlines():
            if "pts_time:" in line:
                try:
                    part = line.split("pts_time:")[1].split()[0]
                    times.append(float(part))
                except (IndexError, ValueError):
                    continue
        return times


def save_dna(dna: Dict[str, Any], out_path: str) -> None:
    Path(out_path).write_text(json.dumps(dna, indent=2))


def load_dna(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())
