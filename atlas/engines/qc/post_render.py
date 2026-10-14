#!/usr/bin/env python3
"""
Atlas Post-Render QC v0.1

Deterministic checks on the finished MP4 — not creative judgment.

  - file exists and is non-empty
  - ffprobe: duration, width, height, fps, has audio
  - duration vs edit / voiceover tolerance
  - blackdetect (ffmpeg) for near-black flashes / holds
  - optional audio stream presence when VO was expected

Never claim pass unless these checks actually ran and passed.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class PostRenderQC:
    version = "0.1"

    def __init__(
        self,
        duration_tolerance_seconds: float = 0.75,
        black_min_duration: float = 0.08,
        black_threshold: float = 0.12,
        black_pixel_ratio: float = 0.98,
        max_black_events: int = 0,
    ):
        self.duration_tolerance = duration_tolerance_seconds
        self.black_min_duration = black_min_duration
        self.black_threshold = black_threshold
        self.black_pixel_ratio = black_pixel_ratio
        self.max_black_events = max_black_events

    def evaluate(
        self,
        video_path: str | Path,
        *,
        expected_duration: Optional[float] = None,
        expect_audio: bool = True,
        min_width: int = 1280,
        min_height: int = 720,
    ) -> Dict[str, Any]:
        path = Path(video_path)
        checks: List[Dict[str, Any]] = []
        errors: List[str] = []
        warnings: List[str] = []

        if not path.exists():
            return self._fail(path, [{"id": "file_exists", "ok": False, "detail": "missing"}], ["file missing"])
        size = path.stat().st_size
        ok_file = size > 1000
        checks.append({"id": "file_exists", "ok": ok_file, "detail": f"bytes={size}"})
        if not ok_file:
            errors.append("video file empty or tiny")

        probe = self._ffprobe(path)
        if probe.get("error"):
            checks.append({"id": "ffprobe", "ok": False, "detail": probe["error"]})
            errors.append(f"ffprobe: {probe['error']}")
            return self._result(path, checks, errors, warnings, probe)

        dur = float(probe.get("duration") or 0)
        w = int(probe.get("width") or 0)
        h = int(probe.get("height") or 0)
        fps = probe.get("fps")
        has_audio = bool(probe.get("has_audio"))

        checks.append({"id": "duration", "ok": dur > 0.05, "detail": f"{dur:.3f}s"})
        if dur <= 0.05:
            errors.append("duration too short")

        res_ok = w >= min_width and h >= min_height
        checks.append({"id": "resolution", "ok": res_ok, "detail": f"{w}x{h}"})
        if not res_ok:
            warnings.append(f"resolution {w}x{h} below {min_width}x{min_height}")

        checks.append({"id": "fps", "ok": fps is not None and float(fps) > 1, "detail": str(fps)})
        checks.append({"id": "has_audio", "ok": (has_audio if expect_audio else True), "detail": str(has_audio)})
        if expect_audio and not has_audio:
            errors.append("expected audio stream missing")

        if expected_duration is not None and expected_duration > 0:
            delta = abs(dur - float(expected_duration))
            ok_dur = delta <= self.duration_tolerance
            checks.append({
                "id": "duration_match",
                "ok": ok_dur,
                "detail": f"video={dur:.3f}s expected={expected_duration:.3f}s delta={delta:.3f}s tol={self.duration_tolerance}",
            })
            if not ok_dur:
                errors.append("duration mismatch vs edit/VO")
        else:
            checks.append({"id": "duration_match", "ok": None, "detail": "no expected_duration"})

        black = self._blackdetect(path)
        events = black.get("events") or []
        checks.append({
            "id": "blackdetect",
            "ok": len(events) <= self.max_black_events if black.get("ran") else None,
            "detail": {
                "ran": black.get("ran"),
                "event_count": len(events),
                "events": events[:20],
                "error": black.get("error"),
            },
        })
        if black.get("ran") and len(events) > self.max_black_events:
            errors.append(f"blackdetect found {len(events)} event(s)")
        if black.get("error"):
            warnings.append(f"blackdetect: {black['error']}")

        return self._result(path, checks, errors, warnings, probe)

    def _result(
        self,
        path: Path,
        checks: List[Dict[str, Any]],
        errors: List[str],
        warnings: List[str],
        probe: Dict[str, Any],
    ) -> Dict[str, Any]:
        hard = [c for c in checks if c.get("ok") is False]
        passed = len(hard) == 0 and len(errors) == 0
        return {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "video": str(path),
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "checks": checks,
            "probe": {
                "duration": probe.get("duration"),
                "width": probe.get("width"),
                "height": probe.get("height"),
                "fps": probe.get("fps"),
                "has_audio": probe.get("has_audio"),
            },
        }

    def _fail(self, path: Path, checks: List, errors: List) -> Dict[str, Any]:
        return {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "video": str(path),
            "passed": False,
            "errors": errors,
            "warnings": [],
            "checks": checks,
            "probe": {},
        }

    def _ffprobe(self, path: Path) -> Dict[str, Any]:
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(path),
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                return {"error": (r.stderr or r.stdout or "ffprobe failed")[:300]}
            data = json.loads(r.stdout or "{}")
            fmt = data.get("format") or {}
            duration = float(fmt.get("duration") or 0)
            width = height = None
            fps = None
            has_audio = False
            for s in data.get("streams") or []:
                if s.get("codec_type") == "video" and width is None:
                    width = int(s.get("width") or 0)
                    height = int(s.get("height") or 0)
                    fr = s.get("r_frame_rate") or s.get("avg_frame_rate") or ""
                    if fr and "/" in fr:
                        a, b = fr.split("/", 1)
                        try:
                            fps = round(float(a) / float(b), 3) if float(b) else None
                        except ValueError:
                            fps = None
                if s.get("codec_type") == "audio":
                    has_audio = True
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "has_audio": has_audio,
            }
        except FileNotFoundError:
            return {"error": "ffprobe not found"}
        except Exception as e:
            return {"error": str(e)[:300]}

    def _blackdetect(self, path: Path) -> Dict[str, Any]:
        try:
            filt = (
                f"blackdetect=d={self.black_min_duration}:"
                f"pix_th={self.black_threshold}:pic_th={self.black_pixel_ratio}"
            )
            cmd = [
                "ffmpeg", "-hide_banner", "-i", str(path),
                "-vf", filt, "-an", "-f", "null", "-",
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            text = (r.stderr or "") + (r.stdout or "")
            events = []
            for m in re.finditer(
                r"black_start:(?P<start>[0-9.]+)\s+black_end:(?P<end>[0-9.]+)\s+black_duration:(?P<dur>[0-9.]+)",
                text,
            ):
                events.append({
                    "start": float(m.group("start")),
                    "end": float(m.group("end")),
                    "duration": float(m.group("dur")),
                })
            return {"ran": True, "events": events, "error": None}
        except FileNotFoundError:
            return {"ran": False, "events": [], "error": "ffmpeg not found"}
        except subprocess.TimeoutExpired:
            return {"ran": False, "events": [], "error": "blackdetect timeout"}
        except Exception as e:
            return {"ran": False, "events": [], "error": str(e)[:200]}
