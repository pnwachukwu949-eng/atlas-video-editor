#!/usr/bin/env python3
"""
Atlas Revision Notes → Revision Request

Turns human review notes into a structured revision request
the Constraint engine can apply fail-closed.

Supported line forms (one change per line):

  B03: asset=pexels_house_106399
  B05: caption=Check your governing documents
  B07: secondary=Alleged · illustrative
  B02: lag=0.35
  B04: motion=slow_push
  B06: layout=full_frame
  unlock B10.visual: reason=approved new still after QC
  do_not_touch: voiceover, B01.visual

Blank lines and lines starting with # are ignored.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class RevisionNotesEngine:
    version = "0.1"

    _beat = re.compile(r"^(B\d{1,3})\s*:\s*(.+)$", re.I)
    _unlock = re.compile(
        r"^unlock\s+([A-Za-z0-9_.]+)\s*:\s*(?:reason\s*=\s*)?(.+)$", re.I
    )
    _do_not = re.compile(r"^do_not_touch\s*:\s*(.+)$", re.I)

    def parse(
        self,
        notes_text: str,
        *,
        target_edit: Optional[str] = None,
        revision_id: Optional[str] = None,
        requested_by: str = "reviewer",
    ) -> Dict[str, Any]:
        instructions: List[Dict[str, Any]] = []
        unlocks: Dict[str, str] = {}
        raw_lines: List[str] = []

        for line in (notes_text or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw_lines.append(line)

            m = self._do_not.match(line)
            if m:
                elements = [e.strip() for e in m.group(1).split(",") if e.strip()]
                instructions.append({"action": "do_not_touch", "elements": elements})
                continue

            m = self._unlock.match(line)
            if m:
                unlocks[m.group(1).strip()] = m.group(2).strip()
                continue

            m = self._beat.match(line)
            if not m:
                instructions.append({"action": "note", "reason": line})
                continue

            beat_id = m.group(1).upper()
            body = m.group(2).strip()
            instructions.extend(self._parse_beat_body(beat_id, body, unlocks))

        rid = revision_id or f"rev_notes_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        return {
            "revision_id": rid,
            "target_edit": target_edit,
            "requested_by": requested_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instructions": instructions,
            "notes": "\n".join(raw_lines),
            "metadata": {
                "parser": "RevisionNotesEngine",
                "parser_version": self.version,
            },
        }

    def _parse_beat_body(
        self, beat_id: str, body: str, unlocks: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        parts = [p.strip() for p in re.split(r"\s*;\s*", body) if p.strip()]
        for part in parts:
            if "=" not in part:
                out.append(self._caption_instr(beat_id, part, unlocks))
                continue
            key, val = part.split("=", 1)
            key = key.strip().lower()
            val = val.strip().strip('"').strip("'")
            if key in ("asset", "visual", "asset_id"):
                out.append(self._with_unlock({
                    "action": "change_visual_asset",
                    "beat_id": beat_id,
                    "new_value": val,
                }, f"{beat_id}.visual", unlocks))
            elif key in ("caption", "text", "primary", "primary_text"):
                out.append(self._caption_instr(beat_id, val, unlocks))
            elif key in ("secondary", "secondary_text"):
                out.append(self._with_unlock({
                    "action": "change_typography",
                    "beat_id": beat_id,
                    "new_value": {"secondary_text": val},
                }, f"{beat_id}.typography", unlocks))
            elif key in ("lag", "picture_lag", "picture_lag_seconds"):
                try:
                    lag = float(val)
                except ValueError:
                    continue
                out.append({
                    "action": "change_timing",
                    "beat_id": beat_id,
                    "new_value": {"picture_lag_seconds": lag},
                })
            elif key == "motion":
                out.append(self._with_unlock({
                    "action": "change_motion",
                    "beat_id": beat_id,
                    "new_value": val,
                }, f"{beat_id}.motion", unlocks))
            elif key == "layout":
                out.append(self._with_unlock({
                    "action": "change_layout",
                    "beat_id": beat_id,
                    "new_value": val,
                }, f"{beat_id}.composition", unlocks))
            elif key in ("evidence", "evidence_status"):
                out.append(self._with_unlock({
                    "action": "change_evidence_status",
                    "beat_id": beat_id,
                    "new_value": val,
                }, f"{beat_id}.evidence_status", unlocks))
            else:
                out.append({
                    "action": "note",
                    "beat_id": beat_id,
                    "reason": f"unrecognized key '{key}' = {val}",
                })
        return out

    def _caption_instr(
        self, beat_id: str, text: str, unlocks: Dict[str, str]
    ) -> Dict[str, Any]:
        return self._with_unlock({
            "action": "change_typography",
            "beat_id": beat_id,
            "new_value": {"primary_text": text},
        }, f"{beat_id}.typography", unlocks)

    def _with_unlock(
        self, instr: Dict[str, Any], path: str, unlocks: Dict[str, str]
    ) -> Dict[str, Any]:
        reason = unlocks.get(path) or unlocks.get(path.split(".")[0])
        if reason:
            instr["unlock_required"] = True
            instr["unlock_reason"] = reason
        return instr
