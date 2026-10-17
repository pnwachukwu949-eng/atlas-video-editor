# Atlas status — 2026-10-17

## Music bed v0.2 — sidechain duck
- Default: music **ducks under speech** (ffmpeg `sidechaincompress`)
- `--no-duck` → flat volume pad
- `--music` / `--soft-bed` / `--music-volume`

## Review package — contact sheet
`--package DIR` includes labeled `asset_contact_sheet.jpg` when available.

## General-job proof (not HOA)
Product profile + `product_snappy_v1` DNA, 28s Atlas product script:

```bash
python scripts/atlas_pipeline.py \
  --narration work/general_demo/product_script.txt \
  --audio work/general_demo/vo.mp3 \
  --dna examples/styles/product_snappy_v1.json \
  --profile examples/profiles/product.json \
  --fill-gaps --qc --post-qc --soft-bed \
  --out renders/atlas_general_product_v1.mp4 \
  --package packages/atlas_general_product_v1
```

Results:
- Plan: 8 beats, style_id `product_snappy_v1`
- Fit → fill: registry USE where possible; remaining GAP left open (no fabricated certainty)
- QC: pass with profile `repeat_cap: 3`
- Package: video + contact sheet + NOTES + QC reports
- Output: `renders/atlas_general_product_v1.mp4` · `packages/atlas_general_product_v1/`

## Full spine
reference → DNA → plan → fit → fill → stagger → motion → ducked music → package → QC

## Expand packed modules
```bash
python scripts/expand_packed_modules.py --out-dir expanded/
```
