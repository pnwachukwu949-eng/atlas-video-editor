#!/usr/bin/env python3
"""
Atlas Acquisition Queue v0.1

Tracks visual gaps from Asset Fit until each is filled, dismissed, or still open.
When a still arrives, only the affected beat is updated and re-scored —
not a full redesign of the edit.

Lifecycle:
  fit report → queue (open items)
  fill beat + asset → re-score that beat
  USE → status=filled
  still WEAK/GAP → status=open (updated ask)
  dismiss → status=dismissed
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from atlas.engines.asset_fit.engine import AssetFitEngine


class AcquisitionQueue:
    version = "0.1"

    def __init__(self, fit_engine: Optional[AssetFitEngine] = None):
        self.fit = fit_engine or AssetFitEngine()

    def from_fit_report(
        self,
        fit_report: Dict[str, Any],
        edit_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        items = []
        for req in fit_report.get("acquisition_requests") or []:
            items.append({
                "beat_id": req.get("beat_id"),
                "status": "open",
                "reason": req.get("reason"),
                "need": req.get("need"),
                "ask": req.get("ask"),
                "current_asset": req.get("current_asset"),
                "score": req.get("score"),
                "filled_asset_id": None,
                "filled_at": None,
                "history": [{
                    "at": fit_report.get("timestamp") or self._now(),
                    "event": "opened",
                    "detail": req.get("reason"),
                }],
            })
        return {
            "queue_version": self.version,
            "edit_id": edit_id or fit_report.get("edit_id"),
            "created_at": self._now(),
            "updated_at": self._now(),
            "items": items,
            "summary": self._summary(items),
        }

    def load(self, path: str | Path) -> Dict[str, Any]:
        return json.loads(Path(path).read_text())

    def save(self, queue: Dict[str, Any], path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        queue["updated_at"] = self._now()
        queue["summary"] = self._summary(queue.get("items") or [])
        path.write_text(json.dumps(queue, indent=2))

    def open_items(self, queue: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [i for i in queue.get("items") or [] if i.get("status") == "open"]

    def fill(
        self,
        queue: Dict[str, Any],
        edit_spec: Dict[str, Any],
        beat_id: str,
        asset_id: str,
        registry: Optional[Dict[str, Any]] = None,
        accept: bool = False,
    ) -> Dict[str, Any]:
        edit = copy.deepcopy(edit_spec)
        beat = self._find_beat(edit, beat_id)
        if beat is None:
            raise ValueError(f"Beat not found: {beat_id}")

        visual = beat.setdefault("visual", {})
        visual["asset_id"] = asset_id
        visual["type"] = visual.get("type") or "contextual_photo"
        visual["locked"] = False
        visual["selection"] = {
            "score": None,
            "reason": f"user_fill:{asset_id}",
        }

        fit_report = self.fit.evaluate_edit(edit, registry=registry or {})
        edit = self.fit.apply_to_edit(edit, fit_report)

        beat_result = next(
            (b for b in fit_report.get("beats") or [] if b.get("beat_id") == beat_id),
            None,
        )
        decision = (beat_result or {}).get("decision", "GAP")

        item = self._find_item(queue, beat_id)
        if item is None:
            item = {
                "beat_id": beat_id,
                "status": "open",
                "history": [],
            }
            queue.setdefault("items", []).append(item)

        item["history"] = item.get("history") or []
        item["history"].append({
            "at": self._now(),
            "event": "fill_attempt",
            "asset_id": asset_id,
            "decision": decision,
            "score": (beat_result or {}).get("score"),
        })

        if decision == "USE" or accept:
            item["status"] = "filled"
            item["filled_asset_id"] = asset_id
            item["filled_at"] = self._now()
            item["ask"] = None
            item["score"] = (beat_result or {}).get("score")
            if accept and decision != "USE":
                item["history"].append({
                    "at": self._now(),
                    "event": "accepted_by_user",
                    "note": "Human accepted asset despite fit score",
                })
                vis = beat.setdefault("visual", {})
                vis.setdefault("fit", {})["decision"] = "USE"
                vis["fit"]["reason"] = "user_accepted"
        else:
            item["status"] = "open"
            item["current_asset"] = asset_id
            item["score"] = (beat_result or {}).get("score")
            req = (beat_result or {}).get("acquisition_request")
            if req:
                item["ask"] = req.get("ask")
                item["need"] = req.get("need")
                item["reason"] = req.get("reason")

        queue["updated_at"] = self._now()
        queue["summary"] = self._summary(queue.get("items") or [])

        return {
            "queue": queue,
            "edit_spec": edit,
            "fit_report": fit_report,
            "beat_decision": decision,
            "beat_result": beat_result,
        }

    def dismiss(
        self,
        queue: Dict[str, Any],
        beat_id: str,
        reason: str = "accepted_placeholder",
    ) -> Dict[str, Any]:
        item = self._find_item(queue, beat_id)
        if item is None:
            raise ValueError(f"No queue item for {beat_id}")
        item["status"] = "dismissed"
        item["history"] = item.get("history") or []
        item["history"].append({
            "at": self._now(),
            "event": "dismissed",
            "reason": reason,
        })
        queue["updated_at"] = self._now()
        queue["summary"] = self._summary(queue.get("items") or [])
        return queue

    def rescore_open(
        self,
        queue: Dict[str, Any],
        edit_spec: Dict[str, Any],
        registry: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fit_report = self.fit.evaluate_edit(edit_spec, registry=registry or {})
        edit = self.fit.apply_to_edit(edit_spec, fit_report)
        open_ids = {i["beat_id"] for i in self.open_items(queue)}

        by_beat = {b["beat_id"]: b for b in fit_report.get("beats") or []}
        for item in queue.get("items") or []:
            if item.get("status") != "open":
                continue
            br = by_beat.get(item["beat_id"])
            if not br:
                continue
            if br["decision"] == "USE":
                item["status"] = "filled"
                item["filled_asset_id"] = br.get("asset_id")
                item["filled_at"] = self._now()
                item["ask"] = None
            else:
                req = br.get("acquisition_request") or {}
                item["ask"] = req.get("ask") or item.get("ask")
                item["need"] = req.get("need") or item.get("need")
                item["score"] = br.get("score")
                item["current_asset"] = br.get("asset_id")
            item.setdefault("history", []).append({
                "at": self._now(),
                "event": "rescore",
                "decision": br.get("decision"),
            })

        existing = {i["beat_id"] for i in queue.get("items") or []}
        for req in fit_report.get("acquisition_requests") or []:
            bid = req.get("beat_id")
            if bid and bid not in existing:
                queue.setdefault("items", []).append({
                    "beat_id": bid,
                    "status": "open",
                    "reason": req.get("reason"),
                    "need": req.get("need"),
                    "ask": req.get("ask"),
                    "current_asset": req.get("current_asset"),
                    "score": req.get("score"),
                    "filled_asset_id": None,
                    "history": [{"at": self._now(), "event": "opened_on_rescore"}],
                })

        queue["updated_at"] = self._now()
        queue["summary"] = self._summary(queue.get("items") or [])
        return {
            "queue": queue,
            "edit_spec": edit,
            "fit_report": fit_report,
            "previously_open": sorted(open_ids),
        }

    def human_status(self, queue: Dict[str, Any]) -> str:
        items = queue.get("items") or []
        lines = [
            f"Acquisition queue — {queue.get('edit_id')}",
            f"Open: {queue.get('summary', {}).get('open', 0)}  "
            f"Filled: {queue.get('summary', {}).get('filled', 0)}  "
            f"Dismissed: {queue.get('summary', {}).get('dismissed', 0)}",
            "",
        ]
        for i in items:
            st = i.get("status", "?")
            bid = i.get("beat_id")
            if st == "open":
                lines.append(f"○ {bid} OPEN — {i.get('ask') or i.get('need', {}).get('search_query')}")
            elif st == "filled":
                lines.append(f"● {bid} FILLED — {i.get('filled_asset_id')}")
            else:
                lines.append(f"× {bid} {st.upper()}")
        return "\n".join(lines)

    def _find_beat(self, edit: Dict[str, Any], beat_id: str) -> Optional[Dict]:
        for b in edit.get("beats") or []:
            if b.get("beat_id") == beat_id:
                return b
        return None

    def _find_item(self, queue: Dict[str, Any], beat_id: str) -> Optional[Dict]:
        for i in queue.get("items") or []:
            if i.get("beat_id") == beat_id:
                return i
        return None

    def _summary(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        s = {"open": 0, "filled": 0, "dismissed": 0}
        for i in items:
            st = i.get("status") or "open"
            if st in s:
                s[st] += 1
        return s

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
