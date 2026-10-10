#!/usr/bin/env python3
"""One-command Atlas build: edit spec -> timeline -> render."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.rendering.bridge import build_timeline_from_edit_spec
from atlas.rendering.media_renderer import MediaRenderer


def main():
    ap = argparse.ArgumentParser(description="Atlas one-command build")
    ap.add_argument("--edit", required=True, help="Path to edit spec JSON")
    ap.add_argument("--out", default="renders/output.mp4", help="Output MP4 path")
    ap.add_argument("--timeline-out", default=None, help="Optional timeline JSON path")
    args = ap.parse_args()

    edit = json.loads(Path(args.edit).read_text())
    timeline = build_timeline_from_edit_spec(edit)
    if args.timeline_out:
        Path(args.timeline_out).write_text(json.dumps(timeline, indent=2))

    renderer = MediaRenderer(output_dir=str(Path(args.out).parent), assets_root=str(ROOT / "assets"))
    result = renderer.render(timeline, output_name=Path(args.out).name)
    print(result)


if __name__ == "__main__":
    main()
