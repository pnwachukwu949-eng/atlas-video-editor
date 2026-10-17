# GitHub sync note (2026-10-17)

## Pushed to main
- scripts/render.py — sidechain music duck, soft-bed, VO mux
- docs/STATUS.md, docs/CLI.md, docs/ENGINE_MANIFEST.json
- tests/test_video_stagger.py, tests/test_fill_registry_video.py

## Still local-first (working tree is source of truth)
These are newer on the sandbox than GitHub; push next session or via desktop:
- scripts/atlas_pipeline.py — --package, --music, --fill-gaps, --soft-bed
- scripts/fill_queue.py — registry video preference before download
- atlas/rendering/bridge.py — video in-point stagger
- atlas/rendering/media_renderer.py — video loop + -ss in-points
- atlas/engines/asset_fit/queue.py — fill sets contextual_video type from registry

Repo: https://github.com/pnwachukwu949-eng/atlas-video-editor
