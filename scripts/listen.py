#!/usr/bin/env python3
"""
Atlas listen CLI — audio / transcript → timed segments for planning.

  python scripts/listen.py --audio assets/hoa_vo_full.mp3 --narration script.txt --out work/transcript.json
  python scripts/listen.py --transcript work/transcript.json --out work/normalized.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.audio.engine import AudioListenEngine, save_transcript


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas Audio Listen")
    ap.add_argument("--audio", default=None, help="Audio file (mp3/wav)")
    ap.add_argument("--transcript", default=None, help="Existing transcript JSON")
    ap.add_argument("--narration", default=None, help="Plain text narration file")
    ap.add_argument("--duration", type=float, default=None, help="Override duration seconds")
    ap.add_argument("--language", default="en")
    ap.add_argument("--out", required=True, help="Output transcript JSON")
    args = ap.parse_args()

    narration_text = None
    if args.narration:
        narration_text = Path(args.narration).read_text(encoding="utf-8")

    eng = AudioListenEngine()
    result = eng.listen(
        audio_path=args.audio,
        transcript_path=args.transcript,
        narration_text=narration_text,
        duration_seconds=args.duration,
        language=args.language,
    )
    save_transcript(result, args.out)
    bridge = eng.to_narration_and_duration(result)
    print(json.dumps({
        "out": args.out,
        "method": (result.get("source") or {}).get("method"),
        "duration_seconds": bridge["duration_seconds"],
        "segment_count": len(result.get("segments") or []),
        "text_preview": (bridge["narration_text"] or "")[:120],
    }, indent=2))


if __name__ == "__main__":
    main()
