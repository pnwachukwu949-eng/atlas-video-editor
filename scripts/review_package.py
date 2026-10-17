#!/usr/bin/env python3
"""
Export a review package for human feedback.

  python scripts/review_package.py \
    --edit work/edit_spec.json \
    --video renders/out.mp4 \
    --out packages/review_v1 \
    --readiness work/readiness.json \
    --queue work/acquisition_queue.json \
    --qc work/qc_report.json

Creates:
  package/
    video.mp4          (copy or symlink of render)
    edit_spec.json
    review.html
    NOTES.txt          (template for human notes)
    readiness.json     (optional)
    acquisition_queue.json (optional)
    qc_report.json     (optional)
    asset_contact_sheet.jpg (optional — mislabel guard)
    README.txt
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


NOTES_TEMPLATE = """# Atlas review notes
# One change per line. Lines starting with # are ignored.
#
# Examples:
#   B01: caption=Clearer opening line
#   B02: motion=pan_left
#   unlock B02.motion: reason=want opposite pan for variety
#   at 0:05: caption=Mapped from timestamp
#   do_not_touch: voiceover, B01.motion
#
# After notes, run:
#   python scripts/review_loop.py apply --package <this folder> --audio <vo.mp3> --out renders/next.mp4

"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas review package exporter")
    ap.add_argument("--edit", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True, help="Package directory")
    ap.add_argument("--readiness", default=None)
    ap.add_argument("--queue", default=None)
    ap.add_argument("--qc", default=None)
    ap.add_argument("--post-qc", default=None)
    ap.add_argument("--dna", default=None)
    ap.add_argument("--contact-sheet", default=None,
                    help="Labeled registry contact sheet (mislabel guard)")
    args = ap.parse_args()

    pkg = Path(args.out)
    pkg.mkdir(parents=True, exist_ok=True)

    edit_src = Path(args.edit)
    video_src = Path(args.video)
    if not edit_src.exists():
        sys.exit(f"Edit not found: {edit_src}")
    if not video_src.exists():
        sys.exit(f"Video not found: {video_src}")

    shutil.copy2(edit_src, pkg / "edit_spec.json")
    dest_video = pkg / "video.mp4"
    if video_src.resolve() != dest_video.resolve():
        shutil.copy2(video_src, dest_video)

    for label, path in (
        ("readiness.json", args.readiness),
        ("acquisition_queue.json", args.queue),
        ("qc_report.json", args.qc),
        ("post_render_qc.json", args.post_qc),
        ("reference_dna.json", args.dna),
        ("asset_contact_sheet.jpg", args.contact_sheet),
    ):
        if path and Path(path).exists():
            shutil.copy2(path, pkg / label)

    html_out = pkg / "review.html"
    cmd = [
        sys.executable, str(ROOT / "scripts/review_html.py"),
        "--edit", str(pkg / "edit_spec.json"),
        "--video", "video.mp4",
        "--out", str(html_out),
    ]
    if (pkg / "readiness.json").exists():
        cmd += ["--readiness", str(pkg / "readiness.json")]
    if (pkg / "acquisition_queue.json").exists():
        cmd += ["--queue", str(pkg / "acquisition_queue.json")]
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit("review_html failed")

    notes_path = pkg / "NOTES.txt"
    if not notes_path.exists():
        notes_path.write_text(NOTES_TEMPLATE)

    edit = json.loads((pkg / "edit_spec.json").read_text())
    beats = edit.get("beats") or []
    readme = f"""Atlas Review Package
====================
edit_id: {edit.get('edit_id')}
beats:   {len(beats)}
style:   {edit.get('style_id')}
video:   video.mp4
review:  review.html
sheet:   asset_contact_sheet.jpg (if included)

How to give feedback
--------------------
1. Watch video.mp4 (or open review.html).
2. Edit NOTES.txt with one change per line.
3. Hand the package back (or run review_loop apply).

Example NOTES.txt lines:
  B01: caption=Stronger hook line
  unlock B02.motion: reason=variety
  B02: motion=pan_left
  do_not_touch: voiceover
"""
    (pkg / "README.txt").write_text(readme)

    manifest = {
        "package_version": "0.2",
        "edit_id": edit.get("edit_id"),
        "beat_count": len(beats),
        "style_id": edit.get("style_id"),
        "files": sorted(p.name for p in pkg.iterdir() if p.is_file()),
    }
    (pkg / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"package": str(pkg), **manifest}, indent=2))


if __name__ == "__main__":
    main()
