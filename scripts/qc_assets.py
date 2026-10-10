#!/usr/bin/env python3
"""Asset contact sheet + edit-level QC (repeat cap, bans, brightness)."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.qc.engine import AssetQCEngine


def main():
    ap = argparse.ArgumentParser(description="Atlas Asset / Edit QC")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cs = sub.add_parser("contact-sheet", help="Labeled contact sheet of registry assets")
    cs.add_argument("--out", default="renders/asset_contact_sheet.jpg")
    cs.add_argument("--assets-root", default="assets")

    ed = sub.add_parser("edit", help="QC an edit spec (repeat cap, bans, brightness)")
    ed.add_argument("--edit", required=True)
    ed.add_argument("--max-uses", type=int, default=2)
    ed.add_argument("--out", default=None)
    ed.add_argument("--assets-root", default="assets")

    args = ap.parse_args()
    qc = AssetQCEngine(assets_root=args.assets_root)

    if args.cmd == "contact-sheet":
        result = qc.render_contact_sheet(args.out)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("ok") else 1)

    if args.cmd == "edit":
        edit = json.loads(Path(args.edit).read_text())
        report = qc.run_edit_qc(edit, max_uses=args.max_uses)
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        sys.exit(0 if report.get("passed") else 1)


if __name__ == "__main__":
    main()
