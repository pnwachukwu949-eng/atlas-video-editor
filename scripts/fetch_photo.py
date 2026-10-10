#!/usr/bin/env python3
"""CLI for registering local contextual photos into the asset registry."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.acquisition.photo_fetcher import PhotoFetcher


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="Asset id")
    ap.add_argument("--path", required=True, help="Path relative to assets/")
    ap.add_argument("--label", default="CONTEXTUAL · not case-specific")
    ap.add_argument("--rights", default="user-supplied")
    args = ap.parse_args()

    fetcher = PhotoFetcher(assets_root=str(ROOT / "assets"))
    if fetcher.is_banned(args.id):
        print(f"REFUSED: {args.id} is banned")
        sys.exit(1)
    entry = fetcher.register_local(args.id, args.path, label=args.label, rights=args.rights)
    print(entry)


if __name__ == "__main__":
    main()
