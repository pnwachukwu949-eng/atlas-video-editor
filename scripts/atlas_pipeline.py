#!/usr/bin/env python3
"""
Atlas full pipeline — any job, not HOA-specific.

Paths:
  A) Narration (+ audio listen) → plan → fit → fill → QC → timeline → render → package
  B) Existing edit spec → timeline → render → optional QC
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
    ap = argparse.ArgumentParser(description="Atlas pipeline: plan → fit → render → package")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--narration", help="Narration text file (triggers planning)")
    src.add_argument("--edit", help="Existing Edit Spec JSON (skip planning)")

    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--dna", default=None)
    ap.add_argument("--reference", default=None, help="Reference video for Style DNA extract")
    ap.add_argument("--style-id", default=None)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--assets", default=None)
    ap.add_argument("--edit-id", default="pipeline_edit")
    ap.add_argument("--vo-id", default="vo_main")

    ap.add_argument("--out", required=True)
    ap.add_argument("--audio", default=None)
    ap.add_argument("--music", default=None, help="Music bed under VO")
    ap.add_argument("--music-volume", type=float, default=0.12)
    ap.add_argument("--soft-bed", action="store_true", help="Quiet generated bed if no --music")
    ap.add_argument("--no-duck", action="store_true", help="Flat music volume (no sidechain)")
    ap.add_argument("--workdir", default=None)

    ap.add_argument("--qc", action="store_true")
    ap.add_argument("--fit", action="store_true", default=True)
    ap.add_argument("--no-fit", action="store_true")
    ap.add_argument("--fill-gaps", action="store_true")
    ap.add_argument("--fill-max", type=int, default=5)
    ap.add_argument("--fill-accept-weak", action="store_true")
    ap.add_argument("--post-qc", action="store_true")
    ap.add_argument("--post-qc-fail", action="store_true")
    ap.add_argument("--package", default=None, help="Export review package directory after render")
    ap.add_argument("--max-uses", type=int, default=2)
    ap.add_argument("--contact-sheet", default=None)
    ap.add_argument("--skip-render", action="store_true")

    args = ap.parse_args()
    do_fit = bool(args.fit) and not bool(args.no_fit)

    out = Path(args.out)
    work = Path(args.workdir) if args.workdir else out.parent / f"{out.stem}_work"
    work.mkdir(parents=True, exist_ok=True)

    edit_path = Path(args.edit) if args.edit else work / "edit_spec.json"
    timeline_path = work / "timeline.json"
    qc_path = work / "qc_report.json"
    fit_path = work / "fit_report.json"
    queue_path = work / "acquisition_queue.json"
    brief_path = work / "acquisition_brief.txt"
    readiness_path = work / "readiness.json"
    post_qc_path = work / "post_render_qc.json"

    duration = args.duration
    transcript_path = None
    dna_path = args.dna

    if args.reference:
        dna_out = work / "reference_dna.json"
        cmd = [
            sys.executable, str(ROOT / "scripts/style_dna.py"),
            "--video", str(args.reference),
            "--out", str(dna_out),
        ]
        if args.style_id:
            cmd += ["--style-id", args.style_id]
        run(cmd, "Extract Style DNA from reference")
        dna_path = str(dna_out)

    if args.narration and args.audio:
        transcript_path = work / "transcript.json"
        run([
            sys.executable, str(ROOT / "scripts/listen.py"),
            "--audio", str(args.audio),
            "--narration", str(args.narration),
            "--out", str(transcript_path),
        ], "Listen (audio → timed segments)")
        listened = json.loads(transcript_path.read_text())
        probed = float((listened.get("source") or {}).get("duration_seconds") or 0)
        if duration is None:
            duration = probed
        if not duration or duration <= 0:
            print("Listen could not determine duration; pass --duration", file=sys.stderr)
            sys.exit(1)
        print(f"  listened duration: {duration:.3f}s  segments: {len(listened.get('segments') or [])}")

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
        if transcript_path is not None:
            plan_cmd += ["--transcript", str(transcript_path)]
        if dna_path:
            plan_cmd += ["--dna", str(dna_path)]
        if args.profile:
            plan_cmd += ["--profile", str(args.profile)]
        if args.assets:
            plan_cmd += ["--assets", args.assets]
        run(plan_cmd, "Plan edit from narration")
    else:
        print(f"→ Using existing edit: {edit_path}")

    if do_fit:
        run([
            sys.executable, str(ROOT / "scripts/asset_fit.py"),
            "--edit", str(edit_path),
            "--out", str(fit_path),
            "--brief", str(brief_path),
            "--write-edit", str(edit_path),
        ], "Asset fit (USE / WEAK / GAP)")
        run([
            sys.executable, str(ROOT / "scripts/asset_queue.py"),
            "init", "--fit", str(fit_path), "--out", str(queue_path),
        ], "Acquisition queue init")
        if args.fill_gaps:
            fill_cmd = [
                sys.executable, str(ROOT / "scripts/fill_queue.py"),
                "--edit", str(edit_path),
                "--queue", str(queue_path),
                "--out-edit", str(edit_path),
                "--out-queue", str(queue_path),
                "--max", str(args.fill_max),
            ]
            if args.fill_accept_weak:
                fill_cmd.append("--accept-weak")
            run(fill_cmd, "Fill acquisition gaps")
            run([
                sys.executable, str(ROOT / "scripts/asset_fit.py"),
                "--edit", str(edit_path),
                "--out", str(fit_path),
                "--brief", str(brief_path),
                "--write-edit", str(edit_path),
            ], "Re-fit after fill")
        try:
            run([
                sys.executable, str(ROOT / "scripts/ready.py"),
                "--fit", str(fit_path),
                "--queue", str(queue_path),
                "--edit", str(edit_path),
                "--out", str(readiness_path),
            ], "Readiness")
        except SystemExit:
            pass

    if args.contact_sheet:
        run([
            sys.executable, str(ROOT / "scripts/qc_assets.py"),
            "contact-sheet", "--out", str(args.contact_sheet),
        ], "Asset contact sheet")

    if args.qc:
        run([
            sys.executable, str(ROOT / "scripts/qc_assets.py"),
            "edit", "--edit", str(edit_path),
            "--max-uses", str(args.max_uses),
            "--out", str(qc_path),
        ], "Edit QC (repeat cap + bans)")
        report = json.loads(qc_path.read_text())
        if not report.get("passed", True):
            print("QC FAILED — not rendering. See", qc_path, file=sys.stderr)
            sys.exit(2)

    run([
        sys.executable, str(ROOT / "scripts/build_timeline.py"),
        "--edit", str(edit_path),
        "--out", str(timeline_path),
    ], "Build timeline")

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
    if args.music:
        render_cmd += ["--music", str(args.music)]
    if args.music_volume is not None:
        render_cmd += ["--music-volume", str(args.music_volume)]
    if args.soft_bed:
        render_cmd.append("--soft-bed")
    if args.no_duck:
        render_cmd.append("--no-duck")
    run(render_cmd, "Render MP4")

    if args.post_qc or args.post_qc_fail:
        pq = [
            sys.executable, str(ROOT / "scripts/qc_render.py"),
            "--video", str(out),
            "--edit", str(edit_path),
            "--out", str(post_qc_path),
        ]
        if not args.audio:
            pq.append("--no-audio-required")
        if args.post_qc_fail:
            pq.append("--fail-closed")
        run(pq, "Post-render QC")

    if args.package:
        pkg_cmd = [
            sys.executable, str(ROOT / "scripts/review_package.py"),
            "--edit", str(edit_path),
            "--video", str(out),
            "--out", str(args.package),
        ]
        if do_fit and readiness_path.exists():
            pkg_cmd += ["--readiness", str(readiness_path)]
        if do_fit and queue_path.exists():
            pkg_cmd += ["--queue", str(queue_path)]
        if args.qc and qc_path.exists():
            pkg_cmd += ["--qc", str(qc_path)]
        if post_qc_path.exists():
            pkg_cmd += ["--post-qc", str(post_qc_path)]
        run(pkg_cmd, "Export review package")

    print("\nDone.")
    print("  Edit:    ", edit_path)
    print("  Timeline:", timeline_path)
    print("  Video:   ", out)
    if args.qc:
        print("  QC:      ", qc_path)
    if do_fit:
        print("  Fit:     ", fit_path)
        print("  Queue:   ", queue_path)
        print("  Ready:   ", readiness_path)
    if args.post_qc or args.post_qc_fail:
        print("  PostQC:  ", post_qc_path)
    if args.package:
        print("  Package: ", args.package)


if __name__ == "__main__":
    main()
