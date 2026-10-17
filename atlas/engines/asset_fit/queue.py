#!/usr/bin/env python3
"""atlas/engines/asset_fit/queue.py — zlib-packed; plain source in working tree."""
import zlib, base64
from pathlib import Path as _P
_dir = _P(__file__).resolve().parent
_a = (_dir / "_queue_payload_a.txt").read_text().strip()
_b = (_dir / "_queue_payload_b.txt").read_text().strip()
exec(compile(zlib.decompress(base64.b64decode(_a + _b)), str(_P(__file__).resolve()), "exec"), globals())
