# Atlas status — 2026-10-17

## Music bed v0.2 — sidechain duck
- Default: music **ducks under speech** (ffmpeg `sidechaincompress`)
- `--no-duck` → flat volume pad (v0.1 behavior)
- `--music` / `--soft-bed` / `--music-volume` unchanged

```bash
python scripts/atlas_pipeline.py \
  --narration script.txt --audio vo.mp3 \
  --music bed.mp3 --music-volume 0.15 \
  --out renders/out.mp4 --package packages/out_v1

# demo without a track:
python scripts/atlas_pipeline.py ... --soft-bed --music-volume 0.18
```

Proof: `renders/atlas_duck_bed.mp4` · `packages/atlas_duck_bed/`

## Full spine
reference → DNA → plan → fit → fill → stagger → motion → **ducked music** → package → QC
