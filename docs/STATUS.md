# Atlas status — 2026-10-14

## Three-genre proof (same pipeline)

| Demo | Profile | DNA | Avg shot | Result |
|------|---------|-----|----------|--------|
| Product | product | product_snappy_v1 | ~3.5s | `atlas_demo_v10.mp4` · 94 green |
| Explainer | explainer | explainer_calm_v1 | ~5.0s | `atlas_explainer_v1.mp4` · 88 green |
| **Social** | social | social_snappy_v1 | **~2.3s** | `atlas_social_v1.mp4` · **94 green** |

Only DNA + profile + asset pool change. Core engines stay genre-agnostic.

## Social v1 specifics
- 14s · 6 beats · USE 6 / GAP 0 · Post-QC PASS
- Centered captions · dense cuts · motion alternation
- DNA: `examples/styles/social_snappy_v1.json`
- Narration: `examples/samples/social_hook_narration.txt`

## Already solid
- Pillow text overlays (no drawtext dependency)
- Contact sheet on `--qc`
- Neighbor-aware motion variety
- Style DNA → timeline metadata (align, motion, lag)
