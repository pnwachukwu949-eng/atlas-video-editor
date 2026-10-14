#!/usr/bin/env python3
"""
Atlas Editorial Rhythm v0.1

Platform-informed checks (YouTube / explainer / doc practice):
- B-roll must illustrate a concrete idea or vary the frame — decoration is waste
- Consecutive identical assets = stale visual (pattern fatigue)
- Long edits benefit from planned re-engagement points (~1/3 and ~2/3)
- Opening beats should establish stakes/value quickly

Does not force jump-cuts-every-2s. Pace follows intention + information, not fashion.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EditorialRhythmEngine:
    version = "0.3"

    def evaluate(self, edit_spec: Dict[str, Any], job_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        beats = edit_spec.get("beats") or []
        duration = 0.0
        vo = edit_spec.get("source_voiceover") or {}
        if vo.get("duration_seconds"):
            duration = float(vo["duration_seconds"])
        elif beats:
            duration = float(beats[-1].get("end") or 0)

        findings: List[Dict[str, Any]] = []
        warnings: List[str] = []

        prev_asset = None
        stale_run = 0
        for b in beats:
            aid = (b.get("visual") or {}).get("asset_id")
            if aid and aid == prev_asset:
                stale_run += 1
                if stale_run >= 1:
                    findings.append({
                        "code": "stale_visual",
                        "severity": "warning",
                        "beat_id": b.get("beat_id"),
                        "detail": f"Same asset as previous beat: {aid}",
                    })
                    warnings.append(f"{b.get('beat_id')}: consecutive same asset ({aid})")
            else:
                stale_run = 0
            prev_asset = aid

        if beats and duration >= 5:
            first = beats[0]
            aid = (first.get("visual") or {}).get("asset_id")
            job = (first.get("intention") or {}).get("job")
            if not aid:
                findings.append({
                    "code": "weak_open",
                    "severity": "warning",
                    "beat_id": first.get("beat_id"),
                    "detail": "Opening beat has no visual — hook needs a picture",
                })
            if job and job not in ("establish", "prove", "illustrate"):
                findings.append({
                    "code": "open_intention",
                    "severity": "info",
                    "beat_id": first.get("beat_id"),
                    "detail": f"Opening intention is {job}; establish is preferred",
                })

        reengage = []
        if duration >= 45 and beats:
            targets = [duration / 3.0, 2.0 * duration / 3.0]
            for t in targets:
                nearest = min(
                    beats,
                    key=lambda b: abs(((float(b.get("start", 0)) + float(b.get("end", 0))) / 2) - t),
                )
                reengage.append({
                    "target_seconds": round(t, 2),
                    "nearest_beat": nearest.get("beat_id"),
                    "beat_start": nearest.get("start"),
                    "suggestion": "Consider a visual change, new claim, or caption emphasis here (re-engagement)",
                })

        profile = job_profile or {}
        pid = (profile.get("profile_id") or edit_spec.get("profile_id") or "").lower()
        if pid == "social":
            max_chars, max_lines = 55, 2
        elif pid == "product":
            max_chars, max_lines = 75, 2
        elif pid in ("investigative", "explainer"):
            max_chars, max_lines = 90, 2
        else:
            max_chars, max_lines = 80, 2
        if profile.get("caption_max_chars") is not None:
            max_chars = int(profile["caption_max_chars"])
        if profile.get("caption_max_lines") is not None:
            max_lines = int(profile["caption_max_lines"])

        for b in beats:
            cap = (b.get("captions") or {}).get("text") or (b.get("typography") or {}).get("primary_text") or ""
            cap = cap.strip()
            n = len(cap)
            lines = [ln for ln in cap.split("\n") if ln.strip()] if "\n" in cap else (
                [cap] if cap else []
            )
            approx_lines = max(len(lines), 1 if not cap else (1 + n // 42))
            if n == 0:
                findings.append({
                    "code": "caption_missing",
                    "severity": "info",
                    "beat_id": b.get("beat_id"),
                    "detail": "No caption text",
                })
            elif n > max_chars:
                findings.append({
                    "code": "caption_long",
                    "severity": "warning",
                    "beat_id": b.get("beat_id"),
                    "detail": f"Caption {n} chars > {max_chars} ({pid or 'default'}); prefer split beat or shorter line",
                })
                warnings.append(f"{b.get('beat_id')}: caption long ({n}>{max_chars})")
            if approx_lines > max_lines and n > 0:
                findings.append({
                    "code": "caption_lines",
                    "severity": "warning",
                    "beat_id": b.get("beat_id"),
                    "detail": f"~{approx_lines} lines > max {max_lines} for profile {pid or 'default'}",
                })
                warnings.append(f"{b.get('beat_id')}: too many caption lines (~{approx_lines})")

        jobs = [(b.get("intention") or {}).get("job") for b in beats]
        jobs_set = {j for j in jobs if j}
        if len(beats) >= 5 and len(jobs_set) <= 1:
            warnings.append("All beats share one intention — vary establish/illustrate/prove/release")

        return {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "edit_id": edit_spec.get("edit_id"),
            "duration_seconds": duration,
            "findings": findings,
            "warnings": warnings,
            "reengagement_points": reengage,
            "intention_jobs": jobs,
            "caption_limits": {
                "profile_id": (job_profile or {}).get("profile_id") or edit_spec.get("profile_id"),
                "max_chars": max_chars,
                "max_lines": max_lines,
            },
            "passed": not any(f.get("severity") == "error" for f in findings),
        }
