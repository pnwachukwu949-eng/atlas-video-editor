#!/usr/bin/env python3
"""Render a timeline JSON to MP4."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.rendering.media_renderer import MediaRenderer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", default=str(ROOT / "assets"))
    args = ap.parse_args()

    timeline = json.loads(Path(args.timeline).read_text())
    out_path = Path(args.out)
    renderer = MediaRenderer(output_dir=str(out_path.parent), assets_root=args.assets)
    result = renderer.render(timeline, output_name=out_path.name)
    print(result)


if __name__ == "__main__":
    main()
