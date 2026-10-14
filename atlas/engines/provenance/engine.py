#!/usr/bin/env python3
"""
Atlas Provenance Engine v0.1

Normalize and validate asset provenance without blocking ordinary product edits.

Fields (optional on registry entries, recommended):
  source_url      — where the file came from
  license         — e.g. CC-BY-2.0, Pexels, user_supplied, unknown
  attribution     — required text when license demands it
  rights          — short rights posture (user_supplied, cleared_stock, restricted, unknown)
  case_specific   — bool: claims to depict this story's real places/people/docs
  media_class     — photo | stock | illustration | graphic | ai_generated | evidence
  attribution_required — bool override

Profiles:
  evidence_strictness off    → soft warnings only
  light                  → warn on missing rights for used assets
  strict                 → fail if case_specific/evidence without source+license path
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


class ProvenanceEngine:
    version = "0.1"

    MEDIA_CLASSES = {
        "photo", "stock", "illustration", "graphic",
        "ai_generated", "evidence", "unknown",
    }

    def normalize_entry(self, asset_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        e = dict(entry or {})
        rights = (e.get("rights") or e.get("license") or "unknown")
        if isinstance(rights, str):
            rights = rights.strip() or "unknown"
        media = (e.get("media_class") or e.get("type") or "unknown")
        if media in ("contextual_photo", "photo"):
            media = "photo"
        elif media in ("card", "text_card", "graphic_card"):
            media = "graphic"
        elif media not in self.MEDIA_CLASSES:
            media = "unknown"
        license_ = e.get("license") or (
            "user_supplied" if rights == "user_supplied" else rights
        )
        return {
            "asset_id": asset_id,
            "source_url": e.get("source_url") or e.get("url") or None,
            "license": license_,
            "attribution": e.get("attribution") or e.get("credit") or None,
            "rights": rights,
            "case_specific": bool(e.get("case_specific")),
            "media_class": media,
            "attribution_required": bool(
                e.get("attribution_required")
                or (isinstance(license_, str) and "BY" in license_.upper())
            ),
            "path": e.get("path"),
            "label": e.get("label"),
        }

    def evaluate_edit(
        self,
        edit_spec: Dict[str, Any],
        registry: Dict[str, Any],
        *,
        evidence_strictness: str = "off",
    ) -> Dict[str, Any]:
        assets = registry.get("assets") or {}
        used_ids: List[str] = []
        for beat in edit_spec.get("beats") or []:
            aid = (beat.get("visual") or {}).get("asset_id")
            if aid:
                used_ids.append(aid)

        findings: List[Dict[str, Any]] = []
        for aid in used_ids:
            raw = assets.get(aid) or {}
            norm = self.normalize_entry(aid, raw)
            issues = self._issues(norm, evidence_strictness)
            findings.append({
                "asset_id": aid,
                "provenance": norm,
                "issues": issues,
                "ok": len(issues) == 0,
            })

        errors = []
        warnings = []
        for f in findings:
            for iss in f["issues"]:
                if iss["severity"] == "error":
                    errors.append(f"{f['asset_id']}: {iss['code']} — {iss['detail']}")
                else:
                    warnings.append(f"{f['asset_id']}: {iss['code']} — {iss['detail']}")

        strict = evidence_strictness == "strict"
        passed = len(errors) == 0 if strict else True  # light/off: never hard-fail provenance

        return {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence_strictness": evidence_strictness,
            "passed": passed,
            "assets_checked": len(findings),
            "findings": findings,
            "errors": errors,
            "warnings": warnings,
        }

    def _issues(self, norm: Dict[str, Any], strictness: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        rights = (norm.get("rights") or "unknown").lower()
        license_ = str(norm.get("license") or "unknown")
        media = norm.get("media_class") or "unknown"

        if rights in ("unknown", "") and strictness in ("light", "strict"):
            issues.append({
                "code": "missing_rights",
                "severity": "warning" if strictness == "light" else "error",
                "detail": "No rights posture on registry entry",
            })

        if media == "ai_generated":
            issues.append({
                "code": "ai_generated_label",
                "severity": "warning",
                "detail": "Must not be presented as verified evidence",
            })

        if norm.get("case_specific") or media == "evidence":
            if not norm.get("source_url") and strictness == "strict":
                issues.append({
                    "code": "case_specific_no_source",
                    "severity": "error",
                    "detail": "Case-specific/evidence asset needs source_url",
                })
            if license_.lower() in ("unknown", "") and strictness == "strict":
                issues.append({
                    "code": "case_specific_no_license",
                    "severity": "error",
                    "detail": "Case-specific/evidence asset needs license",
                })

        if norm.get("attribution_required") and not norm.get("attribution"):
            sev = "error" if strictness == "strict" else "warning"
            if strictness != "off":
                issues.append({
                    "code": "attribution_missing",
                    "severity": sev,
                    "detail": "License requires attribution text",
                })

        return issues
