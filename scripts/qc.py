#!/usr/bin/env python3
"""Post-render QC checks for Atlas outputs."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def probe(path: str) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    return json.loads(r.stdout) if r.returncode == 0 else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--edit", default=None)
    args = ap.parse_args()

    checks = []
    p = Path(args.video)
    checks.append({"name": "file_exists", "passed": p.exists()})

    info = probe(args.video) if p.exists() else {}
    streams = info.get("streams", [])
    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0) or 0)
    checks.append({"name": "has_duration", "passed": duration > 0, "value": duration})

    if streams:
        w = streams[0].get("width")
        h = streams[0].get("height")
        checks.append({"name": "resolution_1080p", "passed": w == 1920 and h == 1080, "value": f"{w}x{h}"})

    if args.edit and Path(args.edit).exists():
        edit = json.loads(Path(args.edit).read_text())
        expected = edit.get("source_voiceover", {}).get("duration_seconds")
        if expected:
            checks.append({
                "name": "duration_matches_vo",
                "passed": abs(duration - expected) < 1.0,
                "value": f"video={duration:.1f} vo={expected}",
            })

    all_ok = all(c["passed"] for c in checks)
    print(json.dumps({"all_passed": all_ok, "checks": checks}, indent=2))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
