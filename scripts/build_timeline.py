#!/usr/bin/env python3
"""Build a timeline JSON from an Edit Specification."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.rendering.bridge import build_timeline_from_edit_spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    edit = json.loads(Path(args.edit).read_text())
    timeline = build_timeline_from_edit_spec(edit)
    Path(args.out).write_text(json.dumps(timeline, indent=2))

    print(f"Timeline ID:      {timeline.get('timeline_id', 'n/a')}")
    print(f"Duration:         {timeline.get('duration_seconds', 0)}s")
    tracks = timeline.get("tracks", {})
    print(f"Video clips:      {len(tracks.get('video', []))}")
    print(f"Audio clips:      {len(tracks.get('audio', []))}")
    print(f"Caption clips:    {len(tracks.get('captions', []))}")
    print(f"Overlay clips:    {len(tracks.get('overlays', []))}")
    locks = timeline.get("locks_honored", [])
    print(f"Locks honored:    {len(locks)}")
    print(f"Written to:       {args.out}")
    for lock in locks[:20]:
        print(f"  • {lock}")


if __name__ == "__main__":
    main()
