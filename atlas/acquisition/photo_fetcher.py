#!/usr/bin/env python3
"""Controlled photo acquisition from free-stock sources with rights checks."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class PhotoFetcher:
    """Fetch contextual photos. Never treats stock as case evidence."""

    def __init__(self, assets_root: str = "assets"):
        self.assets_root = Path(assets_root)
        self.registry_path = self.assets_root / "registry.json"

    def register_local(
        self,
        asset_id: str,
        path: str,
        label: str = "CONTEXTUAL",
        rights: str = "unknown",
        case_specific: bool = False,
    ) -> Dict[str, Any]:
        reg = self._load_registry()
        fp = self.assets_root / path
        entry = {
            "path": path,
            "type": "contextual_photo",
            "label": label,
            "rights": rights,
            "case_specific": case_specific,
            "sha256_prefix": hashlib.sha256(fp.read_bytes()).hexdigest()[:16] if fp.exists() else None,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
        }
        reg.setdefault("assets", {})[asset_id] = entry
        self._save_registry(reg)
        return entry

    def is_banned(self, asset_id: str) -> bool:
        reg = self._load_registry()
        return asset_id in reg.get("banned", {})

    def _load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            return json.loads(self.registry_path.read_text())
        return {"assets": {}, "banned": {}}

    def _save_registry(self, reg: Dict[str, Any]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(reg, indent=2))
