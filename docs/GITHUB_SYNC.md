# GitHub sync (2026-10-17)

## On main (complete for current spine)
| Path | Form |
|------|------|
| `scripts/render.py` | plain — sidechain duck, soft-bed |
| `scripts/atlas_pipeline.py` | plain — `--music` `--soft-bed` `--package` `--fill-gaps` `--post-qc` |
| `scripts/fill_queue.py` | zlib-packed (expands at import) |
| `atlas/rendering/bridge.py` | zlib-packed |
| `atlas/engines/asset_fit/queue.py` | zlib-packed |
| `atlas/rendering/media_renderer.py` | split zlib payload (`_media_renderer_payload_a/b.txt`) |
| docs + tests | STATUS, CLI, ENGINE_MANIFEST, stagger/fill tests |

## Expand packed modules to plain source
```bash
python scripts/expand_packed_modules.py --out-dir expanded/
# or overwrite in place:
python scripts/expand_packed_modules.py
```

Working tree under Grok remains the readable source of truth.

Repo: https://github.com/pnwachukwu949-eng/atlas-video-editor
