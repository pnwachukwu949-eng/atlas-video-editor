#!/usr/bin/env python3
"""
Atlas — product entrypoint

  python scripts/atlas.py run      ...   # listen → plan → qc → timeline → render
  python scripts/atlas.py review   ...   # open/build HTML edit review
  python scripts/atlas.py listen   ...   # audio → timed transcript
  python scripts/atlas.py plan     ...   # narration → edit spec
  python scripts/atlas.py revise   ...   # apply revision (locks honored)
  python scripts/atlas.py notes    ...   # plain review notes → revision JSON
  python scripts/atlas.py loop     ...   # notes → revise → timeline → render → review
  python scripts/atlas.py qc       ...   # asset / edit QC

One tool. Editorial job. Not a generator.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, argv: list[str]) -> int:
    cmd = [sys.executable, str(ROOT / "scripts" / script), *argv]
    print("→", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))


def _run_loop(args: argparse.Namespace) -> int:
    """notes → revision → revise → timeline → render → review."""
    out = Path(args.out)
    work = Path(args.workdir) if args.workdir else out.parent / f"{out.stem}_work"
    work.mkdir(parents=True, exist_ok=True)

    edit_path = Path(args.edit)
    notes_path = Path(args.notes)
    rev_req = work / "revision_request.json"
    revised = work / "edit_spec_revised.json"
    timeline = work / "timeline.json"
    report = work / "revision_report.json"
    review = work / "review.html"

    rc = _run("notes_to_revision.py", [
        "--notes", str(notes_path),
        "--out", str(rev_req),
        "--edit-id", edit_path.stem,
    ])
    if rc != 0:
        return rc

    rev_argv = [
        "--edit", str(edit_path),
        "--revision", str(rev_req),
        "--out", str(revised),
        "--report", str(report),
    ]
    if getattr(args, "log", None):
        rev_argv += ["--log", str(args.log)]
    rc = _run("revise.py", rev_argv)
    if rc != 0:
        return rc

    rc = _run("build_timeline.py", ["--edit", str(revised), "--out", str(timeline)])
    if rc != 0:
        return rc

    render_argv = ["--timeline", str(timeline), "--out", str(out)]
    if getattr(args, "audio", None):
        render_argv += ["--audio", str(args.audio)]
    rc = _run("render.py", render_argv)
    if rc != 0:
        return rc

    rc = _run("review_html.py", [
        "--edit", str(revised),
        "--video", str(out),
        "--out", str(review),
    ])
    print("\nLoop done.")
    print("  Revised edit:", revised)
    print("  Video:       ", out)
    print("  Review:      ", review)
    print("  Report:      ", report)
    return rc


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="atlas",
        description="Atlas Video Editor — editorial intelligence for script + VO + assets",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Full pipeline: listen → plan → qc → render")
    p_run.add_argument("--narration", default=None)
    p_run.add_argument("--edit", default=None)
    p_run.add_argument("--audio", default=None)
    p_run.add_argument("--duration", type=float, default=None)
    p_run.add_argument("--dna", default=None)
    p_run.add_argument("--profile", default=None)
    p_run.add_argument("--assets", default=None)
    p_run.add_argument("--out", required=True)
    p_run.add_argument("--qc", action="store_true", default=True)
    p_run.add_argument("--no-qc", action="store_true")
    p_run.add_argument("--max-uses", type=int, default=2)
    p_run.add_argument("--skip-render", action="store_true")
    p_run.add_argument("--edit-id", default="pipeline_edit")
    p_run.add_argument("--workdir", default=None)

    p_rev = sub.add_parser("review", help="Build a browser review page for an edit spec")
    p_rev.add_argument("--edit", required=True, help="Edit Spec JSON")
    p_rev.add_argument("--video", default=None, help="Optional rendered MP4 path (for link)")
    p_rev.add_argument("--out", default=None, help="HTML output (default: beside edit)")

    p_notes = sub.add_parser("notes", help="Plain review notes → revision request JSON")
    p_notes.add_argument("--notes", required=True, help="Notes text file")
    p_notes.add_argument("--edit-id", default=None)
    p_notes.add_argument("--out", required=True)

    p_loop = sub.add_parser("loop", help="notes → revise → timeline → render → review")
    p_loop.add_argument("--edit", required=True, help="Current Edit Spec")
    p_loop.add_argument("--notes", required=True, help="Review notes text file")
    p_loop.add_argument("--out", required=True, help="Output MP4")
    p_loop.add_argument("--audio", default=None)
    p_loop.add_argument("--workdir", default=None)
    p_loop.add_argument("--log", default=None, help="Append-only revision log")

    for name, help_ in [
        ("listen", "Transcribe / time audio"),
        ("plan", "Plan edit from narration"),
        ("revise", "Apply a revision request"),
        ("qc", "QC assets or edit"),
    ]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("args", nargs=argparse.REMAINDER, help="Args passed through")

    args, unknown = ap.parse_known_args()

    if args.cmd == "run":
        argv = ["--out", args.out]
        if args.narration:
            argv += ["--narration", args.narration]
        if args.edit:
            argv += ["--edit", args.edit]
        if args.audio:
            argv += ["--audio", args.audio]
        if args.duration is not None:
            argv += ["--duration", str(args.duration)]
        if args.dna:
            argv += ["--dna", args.dna]
        if args.profile:
            argv += ["--profile", args.profile]
        if args.assets:
            argv += ["--assets", args.assets]
        if not args.no_qc:
            argv += ["--qc", "--max-uses", str(args.max_uses)]
        if args.skip_render:
            argv += ["--skip-render"]
        if args.edit_id:
            argv += ["--edit-id", args.edit_id]
        if args.workdir:
            argv += ["--workdir", args.workdir]
        sys.exit(_run("atlas_pipeline.py", argv))

    if args.cmd == "review":
        sys.exit(_run("review_html.py", [
            "--edit", args.edit,
            *(["--video", args.video] if args.video else []),
            *(["--out", args.out] if args.out else []),
        ]))

    if args.cmd == "notes":
        argv = ["--notes", args.notes, "--out", args.out]
        if args.edit_id:
            argv += ["--edit-id", args.edit_id]
        sys.exit(_run("notes_to_revision.py", argv))

    if args.cmd == "loop":
        sys.exit(_run_loop(args))

    script = {"listen": "listen.py", "plan": "plan_edit.py", "revise": "revise.py", "qc": "qc_assets.py"}[args.cmd]
    passthrough = list(args.args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    sys.exit(_run(script, passthrough + unknown))


if __name__ == "__main__":
    main()
