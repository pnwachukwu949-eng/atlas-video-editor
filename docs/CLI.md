# Atlas CLI

Entry point: `python scripts/atlas.py <command>`

## run — full editorial pipeline

```bash
python scripts/atlas.py run \
  --narration script.txt \
  --audio voice.mp3 \
  --dna examples/styles/product_snappy_v1.json \
  --profile examples/profiles/product.json \
  --assets asset_a,asset_b \
  --out renders/out.mp4 \
  --fill-gaps --package packages/out_v1
```

Optional:
- `--music path` — bed under VO (sidechain duck by default)
- `--music-volume 0.12` — bed gain
- `--soft-bed` — quiet generated bed if no music file
- `--no-duck` — flat bed volume (no sidechain)
- `--reference path/to/cut.mp4` — extract Style DNA, then plan
- `--fill-gaps` — auto-fill GAP queue from registry/catalog
- `--package DIR` — export review package after render
- `--post-qc` / `--no-post-qc`

## package — export review folder

```bash
python scripts/atlas.py package \
  --edit work/edit_spec.json \
  --video renders/out.mp4 \
  --out packages/cut_v1
```

## fill — close acquisition gaps

```bash
python scripts/atlas.py fill \
  --edit work/edit_spec.json \
  --queue work/acquisition_queue.json \
  --out-edit work/edit_filled.json \
  --out-queue work/queue_filled.json \
  --accept-weak
```

## notes → revise loop

```bash
# After editing packages/cut_v1/NOTES.txt:
python scripts/review_loop.py apply \
  --package packages/cut_v1 \
  --audio voice.mp3 \
  --out renders/out_v2.mp4 \
  --post-qc
```

Also: `listen`, `plan`, `revise`, `fit`, `queue`, `ready`, `qc-render`, `qc-provenance`, `qc-rhythm`, `review`.
