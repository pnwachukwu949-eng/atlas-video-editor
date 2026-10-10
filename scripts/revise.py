#!/usr/bin/env python3
"""
Atlas CLI – Apply a revision request to an Edit Specification.

Usage:
  python scripts/revise.py \\
    --edit examples/hoa_v0.5_edit_spec.json \\
    --revision examples/sample_revision.json \\
    --out examples/hoa_v0.5_revised.json \\
    --log revisions.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from atlas.engines.constraint_revision.engine import ConstraintRevisionEngine, append_revision_log


def main():
    parser = argparse.ArgumentParser(description="Atlas Constraint & Revision Engine CLI")
    parser.add_argument("--edit", required=True, help="Path to Edit Specification JSON")
    parser.add_argument("--revision", required=True, help="Path to Revision Request JSON")
    parser.add_argument("--out", required=True, help="Path to write revised Edit Specification")
    parser.add_argument("--report", help="Optional path to write revision report")
    parser.add_argument("--log", help="Optional append-only revision log JSON")
    args = parser.parse_args()

    with open(args.edit) as f:
        edit_spec = json.load(f)

    with open(args.revision) as f:
        revision_request = json.load(f)

    engine = ConstraintRevisionEngine()
    revised_spec, report = engine.apply_revision(edit_spec, revision_request)

    with open(args.out, "w") as f:
        json.dump(revised_spec, f, indent=2)

    if args.report:
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)

    print(f"Status: {report['status']}")
    print(f"Applied: {len(report['applied'])}")
    print(f"Rejected: {len(report['rejected'])}")
    print(f"Locks respected: {report['locks_respected']}")
    print(f"Revised edit written to: {args.out}")
    if args.report:
        print(f"Report written to: {args.report}")
    if args.log:
        append_revision_log(args.log, report)
        print(f"Revision log appended: {args.log}")

    if report["rejected"]:
        print("\nRejected changes:")
        for r in report["rejected"]:
            print(f"  • {r['element']}: {r['reason']}")


if __name__ == "__main__":
    main()
