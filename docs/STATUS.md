# Atlas status — 2026-10-17

## Music bed v0.2 — sidechain duck
- Default: music **ducks under speech** (ffmpeg `sidechaincompress`)
- `--no-duck` → flat volume pad
- `--music` / `--soft-bed` / `--music-volume`

## Domain-aware fill v0.2
Registry scoring uses semantic domains (`software` vs `place` vs `nature`):
- Software/editor queries → product cards / workspace stills
- Place queries → residential / neighborhood stills
- Mismatch penalty so product narration does not land on suburban B-roll
- Generic query fallback no longer forces `suburban neighborhood` for product/explainer profiles

Proof: `renders/atlas_general_product_v2.mp4` — 8/8 beats product cards (0 residential).
Tests: `tests/test_fill_domain_score.py` (3 passed).

## General-job proof (not HOA)
Product profile + `product_snappy_v1` DNA → plan → fit → fill → QC → soft-bed → package.

## Full spine
reference → DNA → plan → fit → fill → stagger → motion → ducked music → package → QC
