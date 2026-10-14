# Atlas status — 2026-10-14

## Latest demo: v6
- Video: `renders/atlas_demo_v6.mp4`
- Readiness **88 green** · Fit **USE 8 / GAP 0** · Post-QC **PASS**
- Product explainer (28s) end-to-end: plan → fit → queue → rhythm → readiness → QC → render → post-QC

## Tests
`python -m pytest tests/ -q` → **15 passed** (local)

## GitHub sync (main)
On remote: tests, CLI docs, rhythm engine, readiness, provenance engine, QC scripts.
Still pushing in batches: asset_fit engine/queue, post_render, planner 0.8.

## Product identity
General editorial engine (profiles + Style DNA + constraints). HOA was a test project, not the product limit.
Evidence fail-closed stays strict for investigative profiles only.
