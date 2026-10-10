#!/usr/bin/env python3
"""Extract or apply Atlas Style DNA."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.style_dna.engine import StyleDNAEngine, save_dna, load_dna


def main():
    ap = argparse.ArgumentParser(description="Atlas Style DNA v0.1")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="Extract grammar from a reference video")
    ex.add_argument("--video", required=True)
    ex.add_argument("--out", required=True)
    ex.add_argument("--style-id", default=None)
    ex.add_argument("--threshold", type=float, default=0.35)

    ap_apply = sub.add_parser("apply", help="Merge Style DNA + job profile into planning defaults")
    ap_apply.add_argument("--dna", required=True)
    ap_apply.add_argument("--profile", default=None)
    ap_apply.add_argument("--out", default=None)

    args = ap.parse_args()
    engine = StyleDNAEngine()

    if args.cmd == "extract":
        dna = engine.extract_from_video(args.video, style_id=args.style_id, scene_threshold=args.threshold)
        save_dna(dna, args.out)
        print(json.dumps(dna, indent=2))
        print(f"\nWritten: {args.out}")
    elif args.cmd == "apply":
        dna = load_dna(args.dna)
        profile = json.loads(Path(args.profile).read_text()) if args.profile else None
        defaults = engine.apply_to_edit_defaults(dna, profile)
        if args.out:
            Path(args.out).write_text(json.dumps(defaults, indent=2))
        print(json.dumps(defaults, indent=2))


if __name__ == "__main__":
    main()
