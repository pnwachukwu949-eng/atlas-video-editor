#!/usr/bin/env python3
"""Provenance QC for assets used in an edit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.provenance.engine import ProvenanceEngine


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas provenance QC")
    ap.add_argument("--edit", required=True)
    ap.add_argument("--registry", default="assets/registry.json")
    ap.add_argument("--profile", default=None, help="Profile JSON (evidence_strictness)")
    ap.add_argument("--strictness", default=None, help="off|light|strict override")
    ap.add_argument("--out", default=None)
    ap.add_argument("--fail-closed", action="store_true")
    args = ap.parse_args()

    edit = json.loads(Path(args.edit).read_text())
    reg = json.loads(Path(args.registry).read_text()) if Path(args.registry).exists() else {"assets": {}}
    strictness = args.strictness or "off"
    if args.profile and Path(args.profile).exists():
        strictness = args.strictness or json.loads(Path(args.profile).read_text()).get(
            "evidence_strictness", "off"
        )
    if args.strictness is None and args.profile is None:
        strictness = "off"

    report = ProvenanceEngine().evaluate_edit(
        edit, reg, evidence_strictness=strictness
    )
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "passed": report["passed"],
        "strictness": report["evidence_strictness"],
        "assets_checked": report["assets_checked"],
        "errors": report["errors"][:10],
        "warnings": report["warnings"][:10],
        "out": args.out,
    }, indent=2))
    if args.fail_closed and not report["passed"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
