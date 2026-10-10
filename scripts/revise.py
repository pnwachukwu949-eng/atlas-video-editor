#!/usr/bin/env python3
"""Apply a revision request to an Edit Specification under lock constraints."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.engines.constraint_revision.engine import ConstraintRevisionEngine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    edit = json.loads(Path(args.edit).read_text())
    revision = json.loads(Path(args.revision).read_text())
    engine = ConstraintRevisionEngine()
    result = engine.apply(edit, revision)
    Path(args.out).write_text(json.dumps(result["edit_spec"], indent=2))
    print(json.dumps(result.get("report", result), indent=2))


if __name__ == "__main__":
    main()
