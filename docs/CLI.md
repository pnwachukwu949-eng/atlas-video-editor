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
- `--speak` — synthesize VO from narration when `--audio` is omitted
- `--voice atlas_calm|atlas_product|atlas_investigative` — brand voice for `--speak`

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

### Speak-only explainer (no recorded VO)

```bash
python scripts/atlas_pipeline.py \
  --narration examples/samples/explainer_rain_narration.txt \
  --speak --voice atlas_calm \
  --dna examples/styles/explainer_calm_v1.json \
  --profile examples/profiles/explainer.json \
  --fill-gaps --fill-max 6 \
  --music-bed explainer --music-volume 0.10 \
  --out renders/atlas_explainer_speak.mp4 \
  --qc --post-qc
```

Atlas voices live in `assets/voices/catalog.json`. Your own recording always wins when you pass `--audio`.

Also: `listen`, `plan`, `revise`, `fit`, `queue`, `ready`, `qc-render`, `speak`.
