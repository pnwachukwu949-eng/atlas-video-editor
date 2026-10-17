# Atlas brand voice

## Locked default: `atlas_default`

This is **the same voice** used on the rain explainer (`assets/explainer_rain_vo.mp3`).

- Synthesis: Grok Voice API with **voice parameter omitted** (platform default).
- Catalog: `assets/voices/catalog.json`
- Aliases `atlas_calm`, `atlas_product`, `atlas_investigative` all resolve to `atlas_default`.
- Do not change the default to a different Grok voice id unless the user explicitly requests it.

## Pipeline

```bash
python scripts/atlas_pipeline.py \
  --narration examples/samples/explainer_rain_narration.txt \
  --speak \
  --voice atlas_default \
  --dna examples/styles/explainer_calm_v1.json \
  --profile examples/profiles/explainer.json \
  --fill-gaps --fill-max 8 \
  --music-bed explainer \
  --out renders/out.mp4 --qc --post-qc
```

If `--audio` is provided, it wins (your recording). `--speak` only runs when audio is missing.

## Fallbacks

When Grok Voice is not available in the runtime, `atlas.acquisition.speak` may use edge_tts/gTTS as a **dev fallback**. Those will not sound identical. Prefer pre-rendered VO or a session that can call Grok Voice for publish-quality brand audio.
