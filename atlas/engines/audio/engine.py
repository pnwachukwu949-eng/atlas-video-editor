#!/usr/bin/env python3
"""
Atlas Audio / Listen Engine v0.1

Atlas "listens" by turning speech into timed text the planner can use.

Paths:
  1. External timed transcript JSON (preferred when available)
  2. Plain narration text + duration → proportional segment estimates
  3. Optional Whisper (openai-whisper or faster-whisper) if installed

Listening is for *structure and timing*, not for claiming facts from tone alone.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class AudioListenEngine:
    version = "0.1"

    def listen(
        self,
        audio_path: Optional[str] = None,
        transcript_path: Optional[str] = None,
        narration_text: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Produce a timed transcript structure.

        Priority:
          transcript_path JSON → Whisper on audio → narration_text + duration
        """
        if transcript_path:
            return self.load_transcript(transcript_path)

        if audio_path and Path(audio_path).exists():
            dur = duration_seconds or self.probe_duration(audio_path)
            whispered = self._try_whisper(audio_path, language=language)
            if whispered is not None:
                whispered["source"] = {
                    "method": whispered.get("source", {}).get("method", "whisper"),
                    "audio_path": str(audio_path),
                    "duration_seconds": dur,
                    "listened_at": datetime.now(timezone.utc).isoformat(),
                }
                return whispered

            return {
                "version": self.version,
                "language": language,
                "full_text": (narration_text or "").strip(),
                "segments": self._segments_from_text(narration_text or "", dur or 0.0),
                "source": {
                    "method": "audio_probe_only",
                    "audio_path": str(audio_path),
                    "duration_seconds": dur,
                    "listened_at": datetime.now(timezone.utc).isoformat(),
                    "notes": "Whisper not installed; used narration_text timing if provided",
                },
            }

        if narration_text is not None:
            dur = float(duration_seconds or 0.0)
            return {
                "version": self.version,
                "language": language,
                "full_text": narration_text.strip(),
                "segments": self._segments_from_text(narration_text, dur),
                "source": {
                    "method": "text_proportional",
                    "duration_seconds": dur,
                    "listened_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        raise ValueError("Provide audio_path, transcript_path, or narration_text")

    def load_transcript(self, path: str) -> Dict[str, Any]:
        data = json.loads(Path(path).read_text())
        if "segments" not in data and "full_text" in data:
            dur = float(data.get("duration_seconds") or data.get("source", {}).get("duration_seconds") or 0)
            data["segments"] = self._segments_from_text(data["full_text"], dur)
        data.setdefault("version", self.version)
        return data

    def probe_duration(self, audio_path: str) -> float:
        r = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(r.stdout.strip())
        except (ValueError, AttributeError):
            return 0.0

    def to_narration_and_duration(self, listened: Dict[str, Any]) -> Dict[str, Any]:
        """Bridge into BeatPlanner.plan inputs."""
        text = listened.get("full_text") or " ".join(
            s.get("text", "") for s in listened.get("segments", [])
        )
        dur = (
            listened.get("source", {}).get("duration_seconds")
            or (listened.get("segments") or [{}])[-1].get("end")
            or 0.0
        )
        return {
            "narration_text": text.strip(),
            "duration_seconds": float(dur or 0.0),
            "segments": listened.get("segments", []),
        }

    def _segments_from_text(self, text: str, duration: float) -> List[Dict[str, Any]]:
        text = (text or "").strip()
        if not text:
            return []
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
        if not parts:
            parts = [text]
        weights = [max(1, len(p)) for p in parts]
        total = sum(weights)
        t = 0.0
        segs = []
        for p, w in zip(parts, weights):
            dur = (duration * w / total) if duration and total else 0.0
            segs.append({
                "start": round(t, 3),
                "end": round(t + dur, 3),
                "text": p,
            })
            t += dur
        if segs and duration:
            segs[-1]["end"] = round(duration, 3)
        return segs

    def _try_whisper(self, audio_path: str, language: str = "en") -> Optional[Dict[str, Any]]:
        try:
            from faster_whisper import WhisperModel  # type: ignore

            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments_iter, info = model.transcribe(audio_path, language=language)
            segments = []
            texts = []
            for s in segments_iter:
                segments.append({
                    "start": round(float(s.start), 3),
                    "end": round(float(s.end), 3),
                    "text": s.text.strip(),
                })
                texts.append(s.text.strip())
            return {
                "version": self.version,
                "language": getattr(info, "language", language),
                "full_text": " ".join(texts).strip(),
                "segments": segments,
                "source": {"method": "faster_whisper"},
            }
        except Exception:
            pass

        try:
            import whisper  # type: ignore

            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language=language)
            segments = []
            for s in result.get("segments") or []:
                segments.append({
                    "start": round(float(s.get("start", 0)), 3),
                    "end": round(float(s.get("end", 0)), 3),
                    "text": (s.get("text") or "").strip(),
                })
            return {
                "version": self.version,
                "language": result.get("language", language),
                "full_text": (result.get("text") or "").strip(),
                "segments": segments,
                "source": {"method": "openai_whisper"},
            }
        except Exception:
            return None


def save_transcript(data: Dict[str, Any], out_path: str) -> None:
    Path(out_path).write_text(json.dumps(data, indent=2))
