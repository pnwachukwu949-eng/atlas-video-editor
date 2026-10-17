#!/usr/bin/env python3
"""Expand zlib-packed Atlas modules on GitHub back to plain Python source.

Usage:
  python scripts/expand_packed_modules.py
  python scripts/expand_packed_modules.py --out-dir expanded/
"""
from __future__ import annotations
import argparse
import base64
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# modules that may be packed on main
CANDIDATES = [
    "scripts/fill_queue.py",
    "atlas/rendering/bridge.py",
    "atlas/engines/asset_fit/queue.py",
    "atlas/rendering/media_renderer.py",
]


def expand_file(path: Path) -> bytes | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    # single-payload form
    m = re.search(r"_PAYLOAD\s*=\s*\"\"\"(.+?)\"\"\"", text, re.S)
    if m:
        return zlib.decompress(base64.b64decode(m.group(1)))
    # split payload form (media_renderer)
    a = path.parent / "_media_renderer_payload_a.txt"
    b = path.parent / "_media_renderer_payload_b.txt"
    if a.exists() and b.exists() and path.name == "media_renderer.py":
        return zlib.decompress(base64.b64decode(a.read_text().strip() + b.read_text().strip()))
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None, help="Write expanded copies here (default: overwrite in place)")
    args = ap.parse_args()
    out_root = Path(args.out_dir) if args.out_dir else None
    for rel in CANDIDATES:
        p = ROOT / rel
        if not p.exists():
            print("skip missing", rel)
            continue
        data = expand_file(p)
        if not data:
            print("plain (already)", rel)
            continue
        if out_root:
            dest = out_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            dest = p
        dest.write_bytes(data)
        print("expanded", rel, "->", dest, f"({len(data)} bytes)")


if __name__ == "__main__":
    main()
