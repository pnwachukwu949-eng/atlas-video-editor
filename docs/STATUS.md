# Atlas status — 2026-10-17

## Domain-aware fill + PhotoFetcher
- Shared module: `atlas/acquisition/domains.py`
- Local registry fill prefers product cards for editor/timeline queries
- PhotoFetcher refuses residential stock for software queries
- Fill diversify: escalating use penalty → 8 unique assets on product demo

## Fill score ↔ timeline
Bug: domain fill assigned an asset but fit re-GAP'd it (`filled: false` while visual on timeline).

Fix:
- `AcquisitionQueue.fill(..., score=)` keeps fill-side domain score
- GAP/WEAK + score ≥ 3.0 → promote **USE** and queue `filled`
- `fill_queue.py` passes `chosen_score`

Proven: product pipeline **8/8 USE**, readiness **100**, open queue **0**.

## Music bed catalog v0.1
- `atlas/acquisition/music_catalog.py`
- Profile beds: product_soft_pad, explainer_warm_pad, investigative_low_drone
- CLI: `--music-bed product` / `--bed-id product_soft_pad`
- Same sidechain duck under VO
- Drop licensed files in `assets/music/` + catalog `path` for publish

## Product proof
`renders/atlas_product_fill_v5.mp4` — 8/8 USE, soft pad + duck, post-QC pass

Tests: fill score promote, music catalog, domain, diversify — green.
