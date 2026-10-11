# Atlas as a product

Atlas is an **editorial engine**, not a generation studio.

## One entrypoint

```bash
python scripts/atlas.py run \
  --narration script.txt \
  --audio voiceover.mp3 \
  --dna examples/styles/product_snappy_v1.json \
  --profile examples/profiles/product.json \
  --out renders/out.mp4

python scripts/atlas.py review \
  --edit path/to/edit_spec.json \
  --video renders/out.mp4
```

| Command | Job |
|---------|-----|
| `run` | Listen → plan → QC → timeline → render |
| `review` | Browser page: beats, visuals, evidence, lag |
| `listen` | Audio → timed transcript (Whisper when installed) |
| `plan` | Narration → Edit Spec |
| `revise` | Patch with locks / fail-closed |
| `qc` | Repeat cap, bans, brightness |

## Product rules

1. **Stage before commit** — Edit Spec is the craft surface; render is the commit.
2. **Locks are sacred** — revision never silently unlocks VO or approved beats.
3. **Evidence is optional by profile** — strict for investigative, off for product explainers.
4. **Not a generator** — Atlas directs assets you provide (or clear stock), it does not replace ArtCraft-style model studios.

## vs ArtCraft

ArtCraft stages a shot for **generation**.  
Atlas stages a beat for **editing**.

Same craft discipline. Different job.
