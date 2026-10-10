#!/usr/bin/env python3
"""
Atlas Asset / Edit QC Engine v0.1

Genre-agnostic checks learned from HOA stress tests:
- Repeat cap (same source image counts even when darkened under a card)
- Contact sheet of registry assets before timeline use
- Brightness / contrast risk for text-over-photo
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AssetQCEngine:
    version = "0.1"

    def __init__(self, assets_root: str = "assets"):
        self.assets_root = Path(assets_root)
        self.registry_path = self.assets_root / "registry.json"

    def load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            return json.loads(self.registry_path.read_text())
        return {"assets": {}, "banned": {}}

    def check_repeat_cap(
        self,
        edit_spec_or_timeline: Dict[str, Any],
        max_uses: int = 2,
        count_darkened_as_repeat: bool = True,
    ) -> Dict[str, Any]:
        """
        Count asset_id uses across beats/clips.
        Darkened card plates that reuse the same source still count if the
        asset_id is the same (identity = registry id, not visual treatment).
        """
        counts: Counter = Counter()
        source = edit_spec_or_timeline

        if "beats" in source:
            for beat in source.get("beats", []):
                aid = (beat.get("visual") or {}).get("asset_id")
                if aid:
                    counts[aid] += 1
        elif "tracks" in source:
            for clip in source.get("tracks", {}).get("video", []):
                aid = clip.get("asset_id")
                if aid:
                    counts[aid] += 1

        violations = [
            {"asset_id": aid, "uses": n, "max_uses": max_uses}
            for aid, n in sorted(counts.items(), key=lambda x: -x[1])
            if n > max_uses
        ]
        return {
            "check": "repeat_cap",
            "max_uses": max_uses,
            "counts": dict(counts),
            "violations": violations,
            "passed": len(violations) == 0,
            "count_darkened_as_repeat": count_darkened_as_repeat,
        }

    def check_banned_in_timeline(
        self, edit_spec_or_timeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        reg = self.load_registry()
        banned = set(reg.get("banned", {}).keys())
        used = []
        if "beats" in edit_spec_or_timeline:
            used = [
                (b.get("visual") or {}).get("asset_id")
                for b in edit_spec_or_timeline.get("beats", [])
            ]
        else:
            used = [
                c.get("asset_id")
                for c in edit_spec_or_timeline.get("tracks", {}).get("video", [])
            ]
        hits = sorted({a for a in used if a and a in banned})
        return {
            "check": "banned_assets",
            "hits": hits,
            "passed": len(hits) == 0,
        }

    def check_brightness(
        self,
        asset_ids: Optional[List[str]] = None,
        dark_threshold: float = 45.0,
    ) -> Dict[str, Any]:
        """
        Flag stills whose mean luminance is very low (text-over-photo risk).
        Requires Pillow. Skips missing files.
        """
        try:
            from PIL import Image
            import statistics
        except ImportError:
            return {"check": "brightness", "passed": True, "skipped": "Pillow not available"}

        reg = self.load_registry()
        assets = reg.get("assets", {})
        ids = asset_ids or list(assets.keys())
        flags = []
        samples = []

        for aid in ids:
            entry = assets.get(aid)
            if not entry:
                continue
            path = self.assets_root / entry.get("path", "")
            if not path.exists() or path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            try:
                im = Image.open(path).convert("L")
                im.thumbnail((320, 180))
                pixels = list(im.getdata())
                mean_y = statistics.mean(pixels) if pixels else 128
                samples.append({"asset_id": aid, "mean_luminance": round(mean_y, 1)})
                if mean_y < dark_threshold:
                    flags.append({
                        "asset_id": aid,
                        "mean_luminance": round(mean_y, 1),
                        "threshold": dark_threshold,
                        "risk": "low_contrast_for_text_overlay",
                    })
            except Exception as e:
                flags.append({"asset_id": aid, "error": str(e)})

        return {
            "check": "brightness",
            "dark_threshold": dark_threshold,
            "flags": flags,
            "samples": samples,
            "passed": len([f for f in flags if "error" not in f]) == 0,
        }

    def render_contact_sheet(
        self,
        out_path: str,
        columns: int = 4,
        thumb: int = 240,
        only_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Labeled contact sheet of registry stills — catches mislabeled assets
        (e.g. 'bench' that was actually a pagoda) before they hit the timeline.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return {"ok": False, "error": "Pillow required"}

        reg = self.load_registry()
        assets = reg.get("assets", {})
        banned = reg.get("banned", {})
        ids = only_ids or sorted(assets.keys())

        font = None
        for fp in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ):
            if Path(fp).exists():
                font = ImageFont.truetype(fp, 14)
                break
        if font is None:
            font = ImageFont.load_default()

        cells: List[Tuple[str, Optional[Image.Image], bool]] = []
        for aid in ids:
            entry = assets.get(aid, {})
            path = self.assets_root / entry.get("path", "")
            is_banned = aid in banned
            im = None
            if path.exists() and path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                try:
                    im = Image.open(path).convert("RGB")
                    im.thumbnail((thumb, thumb))
                except Exception:
                    im = None
            cells.append((aid, im, is_banned))

        if not cells:
            return {"ok": False, "error": "no assets"}

        pad = 8
        label_h = 36
        cell_w = thumb + pad * 2
        cell_h = thumb + label_h + pad * 2
        cols = min(columns, len(cells))
        rows = (len(cells) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (30, 30, 34))
        draw = ImageDraw.Draw(sheet)

        for i, (aid, im, is_banned) in enumerate(cells):
            r, c = divmod(i, cols)
            x, y = c * cell_w + pad, r * cell_h + pad
            if im is not None:
                sheet.paste(im, (x, y))
            else:
                draw.rectangle([x, y, x + thumb, y + thumb], fill=(50, 50, 55))
                draw.text((x + 8, y + thumb // 2), "no preview", fill=(160, 160, 160), font=font)
            label = aid[:28] + ("…" if len(aid) > 28 else "")
            color = (220, 80, 80) if is_banned else (220, 220, 220)
            if is_banned:
                label = f"[BAN] {label}"
            draw.text((x, y + thumb + 4), label, fill=color, font=font)

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out, quality=90)
        return {
            "ok": True,
            "path": str(out),
            "assets_shown": len(cells),
            "banned_marked": sum(1 for _, _, b in cells if b),
        }

    def run_edit_qc(
        self,
        edit_spec: Dict[str, Any],
        max_uses: int = 2,
    ) -> Dict[str, Any]:
        """Full pre-render QC bundle for an edit spec."""
        used_ids = [
            (b.get("visual") or {}).get("asset_id")
            for b in edit_spec.get("beats", [])
            if (b.get("visual") or {}).get("asset_id")
        ]
        report = {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repeat_cap": self.check_repeat_cap(edit_spec, max_uses=max_uses),
            "banned": self.check_banned_in_timeline(edit_spec),
            "brightness": self.check_brightness(asset_ids=list(set(used_ids))),
        }
        report["passed"] = all(
            report[k].get("passed", True)
            for k in ("repeat_cap", "banned")
        )
        return report
