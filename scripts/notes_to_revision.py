#!/usr/bin/env python3
"""Plain review notes → structured revision request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.revision_notes.engine import RevisionNotesEngine


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas notes → revision request")
    ap.add_argument("--notes", required=True, help="Path to notes text file")
    ap.add_argument("--edit-id", default=None, help="target_edit id")
    ap.add_argument("--revision-id", default=None)
    ap.add_argument("--by", default="reviewer")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    text = Path(args.notes).read_text(encoding="utf-8")
    req = RevisionNotesEngine().parse(
        text,
        target_edit=args.edit_id,
        revision_id=args.revision_id,
        requested_by=args.by,
    )
    req["instructions"] = [
        i for i in req["instructions"]
        if i.get("action") not in ("note", None)
    ]
    Path(args.out).write_text(json.dumps(req, indent=2))
    print(json.dumps({
        "out": args.out,
        "revision_id": req["revision_id"],
        "instruction_count": len(req["instructions"]),
        "actions": [i.get("action") for i in req["instructions"]],
    }, indent=2))


if __name__ == "__main__":
    main()
