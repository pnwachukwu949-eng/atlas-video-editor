#!/usr/bin/env python3
"""Atlas Constraint & Revision Engine v0.1 — enforces locks on an Edit Specification."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


class ConstraintRevisionEngine:
    def __init__(self):
        self.version = "0.1"

    def apply(self, edit_spec: Dict[str, Any], revision_request: Dict[str, Any]) -> Dict[str, Any]:
        """CLI-friendly wrapper returning {edit_spec, report}."""
        revised, report = self.apply_revision(edit_spec, revision_request)
        return {"edit_spec": revised, "report": report}

    def apply_revision(
        self, edit_spec: Dict[str, Any], revision_request: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        revised = copy.deepcopy(edit_spec)
        applied: List[str] = []
        rejected: List[Dict[str, str]] = []
        locks_respected = 0

        global_locks = revised.get("global_locks", {})
        beats_by_id = {b["beat_id"]: b for b in revised.get("beats", [])}

        for instr in revision_request.get("instructions", []):
            action = instr.get("action")
            beat_id = instr.get("beat_id")
            element_path = instr.get("element_path")
            new_value = instr.get("new_value")
            elements = instr.get("elements", [])

            if action in ("change_visual_asset", "change_timing") and global_locks.get("voiceover", True):
                if element_path and "voiceover" in element_path.lower():
                    rejected.append({"element": element_path or "voiceover", "reason": "GLOBAL LOCK: voiceover is immutable"})
                    locks_respected += 1
                    continue

            if action == "do_not_touch":
                for el in elements:
                    applied.append(f"do_not_touch recorded: {el}")
                continue

            if action in ("lock_element", "unlock_element"):
                target = self._resolve_target(beats_by_id, beat_id, element_path)
                if target is not None:
                    target["locked"] = action == "lock_element"
                    applied.append(f"{action} {beat_id}.{element_path}")
                else:
                    rejected.append({"element": f"{beat_id}.{element_path}", "reason": "Target not found"})
                continue

            if beat_id not in beats_by_id:
                rejected.append({"element": beat_id or "unknown", "reason": "Beat not found"})
                continue

            beat = beats_by_id[beat_id]

            if action == "change_visual_asset":
                visual = beat.setdefault("visual", {})
                if visual.get("locked", False):
                    rejected.append({"element": f"{beat_id}.visual", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    visual["asset_id"] = new_value
                    applied.append(f"{beat_id}.visual.asset_id → {new_value}")

            elif action == "change_layout":
                composition = beat.setdefault("composition", {})
                if composition.get("locked", False):
                    rejected.append({"element": f"{beat_id}.composition", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    composition["layout"] = new_value
                    applied.append(f"{beat_id}.composition.layout → {new_value}")

            elif action == "change_typography":
                typography = beat.setdefault("typography", {})
                if typography.get("locked", False):
                    rejected.append({"element": f"{beat_id}.typography", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    if isinstance(new_value, dict):
                        typography.update(new_value)
                    else:
                        typography["primary_text"] = new_value
                    applied.append(f"{beat_id}.typography updated")

            elif action == "change_timing":
                timing = beat.setdefault("timing", {})
                if timing.get("locked", False):
                    rejected.append({"element": f"{beat_id}.timing", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    if isinstance(new_value, dict):
                        timing.update(new_value)
                    applied.append(f"{beat_id}.timing updated")

            elif action == "change_motion":
                motion = beat.setdefault("motion", {})
                if motion.get("locked", False):
                    rejected.append({"element": f"{beat_id}.motion", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    motion["type"] = new_value
                    applied.append(f"{beat_id}.motion.type → {new_value}")

            elif action == "change_caption":
                captions = beat.setdefault("captions", {})
                if captions.get("locked", False):
                    rejected.append({"element": f"{beat_id}.captions", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    captions["text"] = new_value
                    applied.append(f"{beat_id}.captions.text updated")

            elif action == "change_evidence_status":
                evidence = beat.setdefault("evidence_status", {})
                if evidence.get("locked", True):
                    rejected.append({"element": f"{beat_id}.evidence_status", "reason": "LOCKED"})
                    locks_respected += 1
                else:
                    evidence["status"] = new_value
                    applied.append(f"{beat_id}.evidence_status → {new_value}")

            else:
                rejected.append({"element": f"{beat_id}.{action}", "reason": f"Unknown action: {action}"})

        if not rejected and applied:
            status = "success"
        elif applied and rejected:
            status = "partial_success"
        else:
            status = "rejected"

        report = {
            "revision_id": revision_request.get("revision_id"),
            "target_edit": revision_request.get("target_edit"),
            "status": status,
            "applied": applied,
            "rejected": rejected,
            "locks_respected": locks_respected,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_version": self.version,
        }
        revised.setdefault("metadata", {})["last_revised_at"] = report["timestamp"]
        return revised, report

    def _resolve_target(self, beats_by_id: Dict, beat_id: str, element_path: str):
        if not beat_id or beat_id not in beats_by_id or not element_path:
            return None
        current = beats_by_id[beat_id]
        for part in element_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current if isinstance(current, dict) else None
