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
- `--soft-bed` — catalog/generated pad if no music file
- `--music-bed product|explainer|investigative` — profile bed from `assets/music/catalog.json`
- `--bed-id product_soft_pad` — force a specific catalog bed
- `--no-duck` — flat bed volume (no sidechain)

- `--reference path/to/cut.mp4` — extract Style DNA, then plan
- `--fill-gaps` — domain-aware fill (registry → stock → re-score; diversify repeats)
- `--fill-max 8` — max open GAPs to fill in one pass
- `--package DIR` — export review package after render
- `--post-qc` / `--no-post-qc`

### Product recipe (copy-paste)

```bash
python scripts/atlas_pipeline.py \
  --narration examples/samples/product_explainer_narration.txt \
  --audio assets/product_vo.mp3 \
  --duration 27 \
  --dna examples/styles/product_snappy_v1.json \
  --profile examples/profiles/product.json \
  --fill-gaps --fill-max 8 \
  --music-bed product --music-volume 0.11 \
  --package work/product_fill_package \
  --out renders/atlas_product_fill.mp4 \
  --qc --post-qc
```

What this does:
1. Plan beats from narration + Style DNA + product profile
2. Open acquisition queue for every GAP
3. Fill with domain-matched assets (no residential on software beats)
4. Escalate repeat penalty so one card does not monopolize the cut
5. Promote fill-score matches to USE (timeline and report agree)
6. Mux VO + soft product pad with sidechain duck
7. QC + review package

Proven: readiness 100, 8/8 USE, post-QC pass (`atlas_product_fill_v5.mp4`).

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
