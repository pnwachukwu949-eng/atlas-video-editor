# Atlas status — 2026-10-17

## Domain-aware fill + PhotoFetcher
- Shared module: `atlas/acquisition/domains.py` (`software` / `place` / `nature`)
- Local registry fill prefers product cards for editor/timeline queries
- PhotoFetcher **refuses residential stock** for software queries (`NOT_FOUND`)
- Place queries still return neighborhood catalog hits

Tests: `tests/test_fill_domain_score.py` + `tests/test_photo_fetcher_domain.py` (7 passed)

## General product proof
`renders/atlas_general_product_v2.mp4` — 8/8 product cards, 0 residential

## Full spine
reference → DNA → plan → fit → fill → stagger → motion → ducked music → package → QC
