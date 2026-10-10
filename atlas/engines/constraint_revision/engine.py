#!/usr/bin/env python3
"""
Atlas Constraint & Revision Engine v0.2
Enforces locks on an Edit Specification.
Locked fields require unlock_required=true (+ unlock_reason) to change.
"""

from __future__ import annotations
import json
import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ConstraintRevisionEngine:
    def __init__(self):
        self.version = "0.2"

    def apply_revision(
        self,
        edit_spec: Dict[str, Any],
        revision_request: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Apply a revision request to an edit specification.
        Returns (revised_edit_spec, revision_report)

        Fail-closed: locked fields reject unless instruction has
        unlock_required=true (and preferably unlock_reason).
        """
        revised = copy.deepcopy(edit_spec)
        applied: List[str] = []
        rejected: List[Dict[str, str]] = []
        unlocks: List[Dict[str, str]] = []
        locks_respected = 0

        global_locks = revised.get("global_locks", {})
        beats_by_id = {b["beat_id"]: b for b in revised.get("beats", [])}
        force = bool(revision_request.get("force", False))

        for instr in revision_request.get("instructions", []):
            action = instr.get("action")
            beat_id = instr.get("beat_id")
            element_path = instr.get("element_path")
            new_value = instr.get("new_value")
            elements = instr.get("elements", [])
            unlock_required = bool(instr.get("unlock_required", False))
            unlock_reason = instr.get("unlock_reason") or instr.get("reason") or ""

            if action in ("change_visual_asset", "change_timing") and global_locks.get("voiceover", True):
                if element_path and "voiceover" in element_path.lower():
                    rejected.append({
                        "element": element_path or "voiceover",
                        "reason": "GLOBAL LOCK: voiceover is immutable",
                        "suggestion": "Voiceover lock cannot be bypassed without force=true at request level",
                    })
                    locks_respected += 1
                    continue

            if action == "do_not_touch":
                for el in elements:
                    applied.append(f"do_not_touch recorded: {el}")
                continue

            if action == "lock_element":
                target = self._resolve_target(beats_by_id, beat_id, element_path)
                if target is not None:
                    target["locked"] = True
                    if unlock_reason:
                        target["lock_reason"] = unlock_reason
                    applied.append(f"locked {beat_id}.{element_path}")
                else:
                    rejected.append({
                        "element": f"{beat_id}.{element_path}",
                        "reason": "Target element not found",
                    })
                continue

            if action == "unlock_element":
                target = self._resolve_target(beats_by_id, beat_id, element_path)
                if target is not None:
                    target["locked"] = False
                    applied.append(f"unlocked {beat_id}.{element_path}")
                    unlocks.append({
                        "beat_id": beat_id or "",
                        "field": element_path or "",
                        "reason": unlock_reason or "explicit unlock_element",
                    })
                else:
                    rejected.append({
                        "element": f"{beat_id}.{element_path}",
                        "reason": "Target element not found",
                    })
                continue

            if beat_id not in beats_by_id:
                rejected.append({"element": beat_id or "unknown", "reason": "Beat not found"})
                continue

            beat = beats_by_id[beat_id]

            if action == "change_visual_asset":
                visual = beat.setdefault("visual", {})
                ok, msg = self._gate_lock(visual, f"{beat_id}.visual", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.visual", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if visual.get("locked") and unlock_required:
                        visual["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "visual", "reason": unlock_reason})
                    visual["asset_id"] = new_value
                    applied.append(f"{beat_id}.visual.asset_id → {new_value}")

            elif action == "change_layout":
                composition = beat.setdefault("composition", {})
                ok, msg = self._gate_lock(composition, f"{beat_id}.composition", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.composition", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if composition.get("locked") and unlock_required:
                        composition["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "composition", "reason": unlock_reason})
                    composition["layout"] = new_value
                    applied.append(f"{beat_id}.composition.layout → {new_value}")

            elif action == "change_typography":
                typography = beat.setdefault("typography", {})
                ok, msg = self._gate_lock(typography, f"{beat_id}.typography", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.typography", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if typography.get("locked") and unlock_required:
                        typography["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "typography", "reason": unlock_reason})
                    if isinstance(new_value, dict):
                        typography.update(new_value)
                    else:
                        typography["primary_text"] = new_value
                    applied.append(f"{beat_id}.typography updated")

            elif action == "change_caption":
                captions = beat.setdefault("captions", {})
                ok, msg = self._gate_lock(captions, f"{beat_id}.captions", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.captions", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if captions.get("locked") and unlock_required:
                        captions["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "captions", "reason": unlock_reason})
                    captions["text"] = new_value if isinstance(new_value, str) else (new_value or {}).get("text", "")
                    applied.append(f"{beat_id}.captions updated")

            elif action == "change_motion":
                motion = beat.setdefault("motion", {})
                ok, msg = self._gate_lock(motion, f"{beat_id}.motion", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.motion", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if motion.get("locked") and unlock_required:
                        motion["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "motion", "reason": unlock_reason})
                    motion["type"] = new_value
                    applied.append(f"{beat_id}.motion → {new_value}")

            elif action == "change_timing":
                timing = beat.setdefault("timing", {})
                ok, msg = self._gate_lock(timing, f"{beat_id}.timing", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.timing", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if timing.get("locked") and unlock_required:
                        timing["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "timing", "reason": unlock_reason})
                    if isinstance(new_value, dict):
                        timing.update(new_value)
                        if "start" in new_value:
                            beat["start"] = new_value["start"]
                        if "end" in new_value:
                            beat["end"] = new_value["end"]
                    applied.append(f"{beat_id}.timing updated")

            elif action == "change_evidence_status":
                evidence = beat.setdefault("evidence_status", {})
                if isinstance(evidence, str):
                    beat["evidence_status"] = {"status": evidence, "locked": False}
                    evidence = beat["evidence_status"]
                ok, msg = self._gate_lock(evidence if isinstance(evidence, dict) else {},
                                         f"{beat_id}.evidence_status", unlock_required, unlock_reason, force)
                if not ok:
                    rejected.append({"element": f"{beat_id}.evidence_status", "reason": msg,
                                    "suggestion": "Set unlock_required=true and unlock_reason"})
                    locks_respected += 1
                else:
                    if isinstance(evidence, dict) and evidence.get("locked") and unlock_required:
                        evidence["locked"] = False
                        unlocks.append({"beat_id": beat_id, "field": "evidence_status", "reason": unlock_reason})
                    if isinstance(new_value, dict):
                        if isinstance(evidence, dict):
                            evidence.update(new_value)
                        else:
                            beat["evidence_status"] = new_value
                    else:
                        if isinstance(evidence, dict):
                            evidence["status"] = new_value
                        else:
                            beat["evidence_status"] = {"status": new_value}
                    applied.append(f"{beat_id}.evidence_status updated")

            else:
                rejected.append({
                    "element": f"{beat_id}.{action}",
                    "reason": f"Unknown action: {action}",
                })

        status = "success"
        if rejected and applied:
            status = "partial_success"
        elif rejected and not applied:
            status = "rejected"

        report = {
            "revision_id": revision_request.get("revision_id"),
            "target_edit": revision_request.get("target_edit") or revised.get("edit_id"),
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "applied": applied,
            "rejected": rejected,
            "unlocks": unlocks,
            "locks_respected": locks_respected,
        }
        return revised, report

    def _gate_lock(
        self,
        container: Dict[str, Any],
        label: str,
        unlock_required: bool,
        unlock_reason: str,
        force: bool,
    ) -> Tuple[bool, str]:
        """Return (allowed, reason_if_not)."""
        if not container.get("locked", False):
            return True, ""
        if force:
            return True, ""
        if unlock_required:
            return True, ""
        lock_reason = container.get("lock_reason", "locked")
        return False, f"LOCKED ({lock_reason}). Pass unlock_required=true + unlock_reason to change."

    def _resolve_target(self, beats_by_id, beat_id, element_path):
        if not beat_id or beat_id not in beats_by_id:
            return None
        beat = beats_by_id[beat_id]
        if not element_path:
            return beat
        parts = element_path.split(".")
        node = beat
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                if isinstance(node, dict):
                    node[part] = node.get(part) or {}
                    if not isinstance(node[part], dict):
                        return None
                    node = node[part]
                else:
                    return None
        return node if isinstance(node, dict) else None


def append_revision_log(log_path: str, entry: Dict[str, Any]) -> None:
    """Append one revision result to an append-only JSON log file."""
    path = Path(log_path)
    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = {"edit_id": entry.get("target_edit"), "revision_history": []}
    data.setdefault("revision_history", []).append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
