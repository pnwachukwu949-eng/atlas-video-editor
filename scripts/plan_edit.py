#!/usr/bin/env python3
"""Plan a generic Edit Spec from narration + Style DNA + job profile."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.planner.engine import BeatPlanner
from atlas.engines.style_dna.engine import StyleDNAEngine, load_dna


def main():
    ap = argparse.ArgumentParser(description="Atlas Beat Planner v0.2")
    ap.add_argument("--narration", required=True, help="Path to narration text file")
    ap.add_argument("--duration", type=float, required=True, help="VO duration in seconds")
    ap.add_argument("--dna", default=None, help="Style DNA JSON (optional)")
    ap.add_argument("--profile", default=None, help="Job profile JSON (optional)")
    ap.add_argument("--edit-id", default="edit_auto")
    ap.add_argument("--vo-id", default="vo_main")
    ap.add_argument("--assets", default=None, help="Comma-separated asset_id pool (optional)")
    ap.add_argument("--transcript", default=None, help="Timed transcript JSON from scripts/listen.py")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    text = Path(args.narration).read_text(encoding="utf-8")
    style_defaults = {}
    if args.dna:
        dna = load_dna(args.dna)
        profile = json.loads(Path(args.profile).read_text()) if args.profile else None
        style_defaults = StyleDNAEngine().apply_to_edit_defaults(dna, profile)
    profile = json.loads(Path(args.profile).read_text()) if args.profile else {}
    pool = [a.strip() for a in args.assets.split(",") if a.strip()] if args.assets else []

    timed = None
    if args.transcript:
        tr = json.loads(Path(args.transcript).read_text())
        timed = tr.get("segments") or []
        if not args.duration and tr.get("source", {}).get("duration_seconds"):
            args.duration = float(tr["source"]["duration_seconds"])

    planner = BeatPlanner()
    edit = planner.plan(
        narration_text=text,
        duration_seconds=args.duration,
        style_defaults=style_defaults,
        job_profile=profile,
        edit_id=args.edit_id,
        voiceover_asset_id=args.vo_id,
        asset_pool=pool,
        timed_segments=timed,
    )
    Path(args.out).write_text(json.dumps(edit, indent=2))
    print(json.dumps({
        "edit_id": edit["edit_id"],
        "beat_count": len(edit["beats"]),
        "duration": args.duration,
        "profile_id": edit.get("profile_id"),
        "style_id": edit.get("style_id"),
        "used_timed_segments": edit.get("metadata", {}).get("used_timed_segments"),
        "out": args.out,
    }, indent=2))


if __name__ == "__main__":
    main()
