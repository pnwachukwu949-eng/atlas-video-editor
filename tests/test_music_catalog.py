"""Music bed catalog resolves profile beds and generates audio."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.acquisition.music_catalog import resolve_bed, list_beds, load_catalog


def test_catalog_has_product_bed():
    beds = {b["id"] for b in list_beds()}
    assert "product_soft_pad" in beds
    assert "explainer_warm_pad" in beds


def test_resolve_product_generates_file():
    r = resolve_bed(profile_id="product", duration=3.0)
    assert r["status"] == "OK"
    assert Path(r["path"]).exists()
    assert Path(r["path"]).stat().st_size > 1000
    assert r["bed_id"] == "product_soft_pad"


def test_resolve_investigative():
    r = resolve_bed(profile_id="investigative", duration=3.0)
    assert r["status"] == "OK"
    assert r["bed_id"] == "investigative_low_drone"
