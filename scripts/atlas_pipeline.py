#!/usr/bin/env python3
"""
Atlas full pipeline — any job, not HOA-specific.

Paths:
  A) Narration (+ optional audio listen) → plan → timeline → render → optional QC
  B) Existing edit spec → timeline → render → optional QC

Examples:
  python scripts/atlas_pipeline.py \\
    --narration examples/samples/product_explainer_narration.txt \\
    --audio assets/vo.mp3 \\
    --dna examples/styles/product_snappy_v1.json \\
    --profile examples/profiles/product.json \\
    --out renders/product_pipeline.mp4

  python scripts/atlas_pipeline.py \\
    --edit examples/hoa_v0.24_edit_spec.json \\
    --audio assets/hoa_vo_full_narration.mp3 \\
    --out renders/hoa_from_edit.mp4 \\
    --qc --max-uses 2
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run(cmd: list, step: str) -> None:
    print(f"→ {step}")
    print(" ", " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print(f"FAILED: {step}", file=sys.stderr)
        sys.exit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas pipeline: plan → timeline → render → QC")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--narration", help="Narration text file (triggers planning)")
    src.add_argument("--edit", help="Existing Edit Spec JSON (skip planning)")

    ap.add_argument("--duration", type=float, default=None, help="VO seconds (optional if --audio can be probed)")
    ap.add_argument("--dna", default=None, help="Style DNA JSON")
    ap.add_argument("--profile", default=None, help="Job profile JSON")
    ap.add_argument("--assets", default=None, help="Comma-separated asset_id pool for planner")
    ap.add_argument("--edit-id", default="pipeline_edit")
    ap.add_argument("--vo-id", default="vo_main")

    ap.add_argument("--out", required=True, help="Output MP4 path")
    ap.add_argument("--audio", default=None, help="Voiceover audio (probes duration; muxed on render)")
    ap.add_argument("--workdir", default=None, help="Directory for intermediate JSON (default: beside --out)")

    ap.add_argument("--qc", action="store_true", help="Run edit QC (repeat cap + bans) before render")
    ap.add_argument("--max-uses", type=int, default=2, help="Repeat-cap threshold for --qc")
    ap.add_argument("--contact-sheet", default=None, help="Optional contact sheet output path")
    ap.add_argument("--skip-render", action="store_true", help="Stop after plan/timeline (debug)")

    args = ap.parse_args()

    out = Path(args.out)
    work = Path(args.workdir) if args.workdir else out.parent / f"{out.stem}_work"
    work.mkdir(parents=True, exist_ok=True)

    edit_path = Path(args.edit) if args.edit else work / "edit_spec.json"
    timeline_path = work / "timeline.json"
    qc_path = work / "qc_report.json"

    duration = args.duration
    if args.narration and duration is None and args.audio:
        transcript_path = work / "transcript.json"
        listen_cmd = [
            sys.executable, str(ROOT / "scripts/listen.py"),
            "--audio", str(args.audio),
            "--narration", str(args.narration),
            "--out", str(transcript_path),
        ]
        run(listen_cmd, "Listen (audio → timed segments)")
        listened = json.loads(transcript_path.read_text())
        duration = float((listened.get("source") or {}).get("duration_seconds") or 0)
        if duration <= 0:
            print("Listen could not determine duration; pass --duration", file=sys.stderr)
            sys.exit(1)
        print(f"  listened duration: {duration:.3f}s")

    if args.narration:
        if duration is None:
            ap.error("--duration is required with --narration (or pass --audio to probe it)")
        plan_cmd = [
            sys.executable, str(ROOT / "scripts/plan_edit.py"),
            "--narration", str(args.narration),
            "--duration", str(duration),
            "--edit-id", args.edit_id,
            "--vo-id", args.vo_id,
            "--out", str(edit_path),
        ]
        if args.dna:
            plan_cmd += ["--dna", str(args.dna)]
        if args.profile:
            plan_cmd += ["--profile", str(args.profile)]
        if args.assets:
            plan_cmd += ["--assets", args.assets]
        run(plan_cmd, "Plan edit from narration")
    else:
        print(f"→ Using existing edit: {edit_path}")

    if args.contact_sheet:
        run(
            [
                sys.executable, str(ROOT / "scripts/qc_assets.py"),
                "contact-sheet", "--out", str(args.contact_sheet),
            ],
            "Asset contact sheet",
        )

    if args.qc:
        run(
            [
                sys.executable, str(ROOT / "scripts/qc_assets.py"),
                "edit",
                "--edit", str(edit_path),
                "--max-uses", str(args.max_uses),
                "--out", str(qc_path),
            ],
            "Edit QC (repeat cap + bans)",
        )
        report = json.loads(qc_path.read_text())
        if not report.get("passed", True):
            print("QC FAILED — not rendering. See", qc_path, file=sys.stderr)
            print(json.dumps(report.get("repeat_cap", {}), indent=2))
            print(json.dumps(report.get("banned", {}), indent=2))
            sys.exit(2)

    run(
        [
            sys.executable, str(ROOT / "scripts/build_timeline.py"),
            "--edit", str(edit_path),
            "--out", str(timeline_path),
        ],
        "Build timeline",
    )

    if args.skip_render:
        print("Skip render. Edit:", edit_path, "Timeline:", timeline_path)
        return

    render_cmd = [
        sys.executable, str(ROOT / "scripts/render.py"),
        "--timeline", str(timeline_path),
        "--out", str(out),
    ]
    if args.audio:
        render_cmd += ["--audio", str(args.audio)]
    run(render_cmd, "Render MP4")

    print("\nDone.")
    print("  Edit:    ", edit_path)
    print("  Timeline:", timeline_path)
    print("  Video:   ", out)
    if args.qc:
        print("  QC:      ", qc_path)


if __name__ == "__main__":
    main()
