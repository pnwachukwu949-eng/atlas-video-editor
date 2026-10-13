#!/usr/bin/env python3
"""Editorial rhythm QC — stale visuals, open, re-engagement."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from atlas.engines.rhythm.engine import EditorialRhythmEngine

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    edit = json.loads(Path(args.edit).read_text())
    profile = None
    if args.profile and Path(args.profile).exists():
        profile = json.loads(Path(args.profile).read_text())
    elif edit.get("profile_id"):
        cand = Path("examples/profiles") / f"{edit['profile_id']}.json"
        if cand.exists():
            profile = json.loads(cand.read_text())
    report = EditorialRhythmEngine().evaluate(edit, job_profile=profile)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "passed": report["passed"],
        "warnings": report["warnings"],
        "findings": report["findings"],
        "reengagement_points": report["reengagement_points"],
        "intention_jobs": report["intention_jobs"],
        "out": args.out,
    }, indent=2))

if __name__ == "__main__":
    main()
