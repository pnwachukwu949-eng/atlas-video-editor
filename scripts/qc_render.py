#!/usr/bin/env python3
"""Post-render QC CLI for Atlas MP4 outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.qc.post_render import PostRenderQC


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas post-render QC")
    ap.add_argument("--video", required=True)
    ap.add_argument("--expected-duration", type=float, default=None)
    ap.add_argument("--edit", default=None, help="Edit spec — use VO duration as expected")
    ap.add_argument("--no-audio-required", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--fail-closed", action="store_true", help="Exit 2 if not passed")
    args = ap.parse_args()

    expected = args.expected_duration
    if expected is None and args.edit:
        edit = json.loads(Path(args.edit).read_text())
        vo = edit.get("source_voiceover") or {}
        if vo.get("duration_seconds") is not None:
            expected = float(vo["duration_seconds"])
        else:
            beats = edit.get("beats") or []
            if beats:
                expected = float(beats[-1].get("end") or 0)

    report = PostRenderQC().evaluate(
        args.video,
        expected_duration=expected,
        expect_audio=not args.no_audio_required,
    )
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "passed": report["passed"],
        "errors": report["errors"],
        "warnings": report["warnings"],
        "probe": report["probe"],
        "check_ids": [(c["id"], c["ok"]) for c in report["checks"]],
        "out": args.out,
    }, indent=2))
    if args.fail_closed and not report["passed"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
