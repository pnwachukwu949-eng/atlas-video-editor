#!/usr/bin/env python3
"""
Atlas Publish Readiness v0.1

One score before you ship — not a vanity metric.
Combines asset fit coverage, QC, acquisition queue, and basic lock posture.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PublishReadiness:
    version = "0.1"

    def evaluate(
        self,
        *,
        fit_report: Optional[Dict[str, Any]] = None,
        qc_report: Optional[Dict[str, Any]] = None,
        queue: Optional[Dict[str, Any]] = None,
        edit_spec: Optional[Dict[str, Any]] = None,
        rhythm_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []
        score = 100.0

        if fit_report:
            cov = float(fit_report.get("coverage_ratio") or 0)
            summary = fit_report.get("summary") or {}
            gap = int(summary.get("GAP") or 0)
            weak = int(summary.get("WEAK") or 0)
            checks.append({
                "id": "fit_coverage",
                "ok": cov >= 0.7,
                "detail": f"coverage={cov:.0%} USE={summary.get('USE')} WEAK={weak} GAP={gap}",
            })
            score -= (1.0 - cov) * 40
            score -= min(15, weak * 3)
            score -= min(25, gap * 5)
        else:
            checks.append({"id": "fit_coverage", "ok": None, "detail": "not_run"})

        if qc_report is not None:
            passed = bool(qc_report.get("passed"))
            checks.append({
                "id": "qc",
                "ok": passed,
                "detail": "passed" if passed else "failed",
            })
            if not passed:
                score -= 30
        else:
            checks.append({"id": "qc", "ok": None, "detail": "not_run"})

        if queue is not None:
            open_n = int((queue.get("summary") or {}).get("open") or 0)
            checks.append({
                "id": "acquisition_queue",
                "ok": open_n == 0,
                "detail": f"open={open_n}",
            })
            score -= min(25, open_n * 5)
        else:
            checks.append({"id": "acquisition_queue", "ok": None, "detail": "not_run"})

        if edit_spec is not None:
            vo_locked = bool(
                (edit_spec.get("global_locks") or {}).get("voiceover")
                or (edit_spec.get("source_voiceover") or {}).get("locked")
            )
            checks.append({
                "id": "voiceover_locked",
                "ok": vo_locked,
                "detail": "locked" if vo_locked else "unlocked",
            })
            if not vo_locked:
                score -= 5

        if rhythm_report is not None:
            stale = sum(1 for f in (rhythm_report.get("findings") or []) if f.get("code") == "stale_visual")
            warns = len(rhythm_report.get("warnings") or [])
            checks.append({
                "id": "rhythm",
                "ok": stale == 0 and warns == 0,
                "detail": f"stale={stale} warnings={warns}",
            })
            score -= min(15, stale * 4 + warns * 2)
        else:
            checks.append({"id": "rhythm", "ok": None, "detail": "not_run"})

        score = max(0, min(100, round(score)))
        if score >= 80:
            level = "green"
            label = "Ready for private review"
        elif score >= 55:
            level = "yellow"
            label = "Ship only with known gaps documented"
        else:
            level = "red"
            label = "Not ready — close gaps / QC first"

        return {
            "engine_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "level": level,
            "label": label,
            "checks": checks,
            "edit_id": (edit_spec or {}).get("edit_id") or (fit_report or {}).get("edit_id"),
        }
