#!/usr/bin/env python3
"""
Atlas Asset Fit Engine v0.1

After (or during) planning, evaluate whether the chosen visual is good enough
for each beat. When it isn't, emit an acquisition request the human (or a
fetcher) can act on — without inventing fake evidence or filler B-roll.

Decisions per beat:
  USE       — chosen asset is strong enough
  WEAK      — best available, but below threshold; request better
  GAP       — nothing usable; request a specific visual type
  REJECT    — asset present but wrong for this beat (banned / mismatch)

This is the general-editorial version of the evidence ACQUIRE path:
  "I need X, not whatever looks nice."
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class AssetFitEngine:
    version = "0.3"

    USE_THRESHOLD = 2.0
    WEAK_THRESHOLD = 0.5

    def evaluate_edit(
        self,
        edit_spec: Dict[str, Any],
        registry: Optional[Dict[str, Any]] = None,
        banned_ids: Optional[set] = None,
    ) -> Dict[str, Any]:
        registry = registry or {}
        banned = banned_ids or set((registry.get("banned") or {}).keys())
        assets = registry.get("assets") or {}

        beat_results: List[Dict[str, Any]] = []
        acquisition_requests: List[Dict[str, Any]] = []

        for beat in edit_spec.get("beats") or []:
            result = self._evaluate_beat(beat, assets, banned)
            beat_results.append(result)
            if result.get("acquisition_request"):
                acquisition_requests.append(result["acquisition_request"])

        n = len(beat_results) or 1
        summary = {
            "USE": sum(1 for r in beat_results if r["decision"] == "USE"),
            "WEAK": sum(1 for r in beat_results if r["decision"] == "WEAK"),
            "GAP": sum(1 for r in beat_results if r["decision"] == "GAP"),
            "REJECT": sum(1 for r in beat_results if r["decision"] == "REJECT"),
        }

        return {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "edit_id": edit_spec.get("edit_id"),
            "summary": summary,
            "coverage_ratio": round(summary["USE"] / n, 3),
            "beats": beat_results,
            "acquisition_requests": acquisition_requests,
            "human_brief": self._human_brief(acquisition_requests),
        }

    def apply_to_edit(
        self,
        edit_spec: Dict[str, Any],
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        import copy
        out = copy.deepcopy(edit_spec)
        by_id = {r["beat_id"]: r for r in report.get("beats") or []}
        for beat in out.get("beats") or []:
            r = by_id.get(beat.get("beat_id"))
            if not r:
                continue
            visual = beat.setdefault("visual", {})
            visual["fit"] = {
                "decision": r["decision"],
                "score": r.get("score"),
                "reason": r.get("reason"),
            }
            if r.get("acquisition_request"):
                beat["acquisition"] = r["acquisition_request"]
        out.setdefault("metadata", {})["asset_fit"] = {
            "engine_version": self.version,
            "summary": report.get("summary"),
            "coverage_ratio": report.get("coverage_ratio"),
            "request_count": len(report.get("acquisition_requests") or []),
        }
        return out

    def _evaluate_beat(
        self,
        beat: Dict[str, Any],
        assets: Dict[str, Any],
        banned: set,
    ) -> Dict[str, Any]:
        beat_id = beat.get("beat_id") or "?"
        narration = beat.get("narration_summary") or ""
        visual = beat.get("visual") or {}
        asset_id = visual.get("asset_id")
        selection = visual.get("selection") or {}
        score = selection.get("score")
        if score is None:
            score = self._rough_score(narration, asset_id, assets)

        need = self._visual_need(narration)

        if not asset_id:
            req = self._request(beat_id, narration, need, reason="no_asset_assigned")
            return {
                "beat_id": beat_id,
                "decision": "GAP",
                "score": 0.0,
                "asset_id": None,
                "reason": "No visual assigned",
                "need": need,
                "acquisition_request": req,
            }

        if asset_id in banned:
            req = self._request(beat_id, narration, need, reason="banned_asset", rejected=asset_id)
            return {
                "beat_id": beat_id,
                "decision": "REJECT",
                "score": float(score or 0),
                "asset_id": asset_id,
                "reason": f"Banned asset: {asset_id}",
                "need": need,
                "acquisition_request": req,
            }

        score_f = float(score or 0)
        intention = ((beat.get("intention") or {}).get("job") or "").lower()
        if asset_id and intention:
            entry = assets.get(asset_id) or {}
            blob = " ".join([
                asset_id.replace("_", " "),
                str(entry.get("description") or ""),
                " ".join(entry.get("tags") or []),
            ]).lower()
            intent_tags = {
                "establish": ("hook", "title", "intro", "atlas", "meet"),
                "prove": ("document", "evidence", "court", "tax", "ledger"),
                "release": ("checklist", "advice", "style", "dna"),
                "callback": ("hook", "atlas", "pattern", "same"),
                "illustrate": (),
            }
            prefer = intent_tags.get(intention) or ()
            if prefer and any(t in blob for t in prefer):
                score_f = max(score_f, float(self.USE_THRESHOLD))
            narr_l = (narration or "").lower()
            if "revision" in narr_l and "hook" in blob and "revision" not in blob:
                score_f = min(score_f, float(self.WEAK_THRESHOLD) - 0.1)

        if score_f >= self.USE_THRESHOLD:
            return {
                "beat_id": beat_id,
                "decision": "USE",
                "score": score_f,
                "asset_id": asset_id,
                "reason": selection.get("reason") or "score_above_threshold",
                "need": need,
                "acquisition_request": None,
            }

        if score_f >= self.WEAK_THRESHOLD:
            req = self._request(
                beat_id, narration, need,
                reason="weak_match",
                current=asset_id,
                score=score_f,
            )
            return {
                "beat_id": beat_id,
                "decision": "WEAK",
                "score": score_f,
                "asset_id": asset_id,
                "reason": "Best available is weak for this narration",
                "need": need,
                "acquisition_request": req,
            }

        req = self._request(
            beat_id, narration, need,
            reason="gap_or_rotation_only",
            current=asset_id,
            score=score_f,
        )
        return {
            "beat_id": beat_id,
            "decision": "GAP",
            "score": score_f,
            "asset_id": asset_id,
            "reason": "No meaningful match — rotation/placeholder only",
            "need": need,
            "acquisition_request": req,
        }

    def _visual_need(self, narration: str) -> Dict[str, Any]:
        t = (narration or "").lower()
        tokens = set(re.findall(r"[a-z0-9]+", t))

        kind = "contextual_still"
        query = "relevant illustrative still"
        hints: List[str] = []

        rules = [
            ({"lawn", "mower", "grass", "yard", "landscap"}, "lawn_care", "lawn mower property maintenance"),
            ({"tax", "taxes", "payment", "delinquent"}, "document_tax", "tax record document close-up illustrative"),
            ({"court", "lawsuit", "sue", "litigation", "judge"}, "courthouse", "courthouse exterior US"),
            ({"hoa", "association", "dues", "board"}, "hoa_context", "HOA entrance sign suburban community"),
            ({"community", "neighborhood", "residents", "homes"}, "community", "suburban neighborhood aerial or street"),
            ({"house", "home", "homeowner", "tiny"}, "residence", "single family house exterior US daytime"),
            ({"map", "location", "tennessee", "county"}, "map", "simple location map graphic"),
            ({"document", "filing", "records", "paperwork"}, "document", "clean document stack or filing folder"),
            ({"money", "budget", "percent", "dollar", "spending"}, "data", "simple money or budget graphic"),
            ({"checklist", "check", "advice", "what to"}, "checklist", "clean checklist graphic"),
            ({"script", "voiceover", "assets", "footage"}, "workspace", "creator desk laptop script microphone"),
            ({"plan", "beats", "timeline", "edit", "editor"}, "editing", "video timeline editing software screen"),
            ({"revision", "revisions", "lock", "locked", "change"}, "revision", "before after edit comparison or lock icon graphic"),
            ({"style", "pacing", "reference", "dna"}, "style_ref", "film reference storyboard or pacing waveform"),
            ({"explainers", "product", "investigation", "investigations"}, "multi_genre", "collage: product UI, documentary still, explainer graphic"),
        ]
        for keys, k, q in rules:
            if tokens & keys or any(x in t for x in keys):
                kind = k
                query = q
                hints.append(k)
                break

        return {
            "kind": kind,
            "search_query": query,
            "narration_excerpt": (narration or "")[:120],
            "hints": hints or ["general"],
            "constraints": [
                "Prefer real cleared stock or user photos",
                "Do not fabricate case-specific evidence",
                "Match geography/mood when story is place-specific",
                "Mark illustrative if not authentic to the story",
            ],
        }

    def _request(
        self,
        beat_id: str,
        narration: str,
        need: Dict[str, Any],
        reason: str,
        current: Optional[str] = None,
        rejected: Optional[str] = None,
        score: Optional[float] = None,
    ) -> Dict[str, Any]:
        return {
            "beat_id": beat_id,
            "status": "ACQUIRE",
            "reason": reason,
            "current_asset": current,
            "rejected_asset": rejected,
            "score": score,
            "need": need,
            "ask": (
                f"Beat {beat_id}: need a better visual for "
                f"“{(narration or '')[:80]}…” — "
                f"looking for: {need.get('search_query')} "
                f"(kind={need.get('kind')})."
            ),
        }

    def _rough_score(
        self, narration: str, asset_id: Optional[str], assets: Dict[str, Any]
    ) -> float:
        if not asset_id:
            return 0.0
        entry = assets.get(asset_id) or {}
        blob = " ".join([
            asset_id.replace("_", " "),
            str(entry.get("label") or ""),
            str(entry.get("description") or ""),
            str(entry.get("type") or ""),
            " ".join(entry.get("tags") or []),
        ]).lower()
        words = set(re.findall(r"[a-z0-9]+", (narration or "").lower()))
        words = {w for w in words if len(w) > 2}
        score = float(sum(2 for w in words if w in blob))
        narr = (narration or "").strip().lower()
        if len(words) <= 4 and any(k in narr for k in ("meet", "atlas", "welcome", "intro")):
            if any(k in blob for k in ("hook", "title", "atlas", "intro", "product")):
                score = max(score, float(self.USE_THRESHOLD))
        return score

    def _human_brief(self, requests: List[Dict[str, Any]]) -> str:
        if not requests:
            return "All beats have usable visuals. No acquisition needed."
        lines = ["Asset acquisition brief — replace or add these:", ""]
        for r in requests:
            lines.append(f"• {r.get('ask')}")
            need = r.get("need") or {}
            lines.append(f"  Search: {need.get('search_query')}")
            if r.get("current_asset"):
                lines.append(f"  Current (weak/placeholder): {r['current_asset']}")
            lines.append("")
        return "\n".join(lines)
