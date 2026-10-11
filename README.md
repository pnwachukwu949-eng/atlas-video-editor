# Atlas Video Editor

**AI video editor with editorial intelligence, constraint memory, and style DNA.**

> Give Atlas a script + voiceover + visual assets (+ optional reference video),  
> and it produces a structured, context-aware edit for **any assigned job** —  
> then accepts controlled revisions without destroying what you already approved.

HOA / investigative cuts were a **stress test**, not the product ceiling.

---

## Status

| Capability | Status |
|------------|--------|
| **Product CLI** `scripts/atlas.py` | **Working** |
| **HTML edit review** | **Working** |
| Edit Spec → Timeline → MP4 | Working |
| Constraint & Revision (locks, fail-closed) | Working |
| Style DNA + job profiles | Working |
| Whisper listen → timed beats | Working |
| J-cut / L-cut picture lag | Working |
| Asset registry + QC (repeat / ban / brightness) | Working |
| HOA baseline freeze | **v0.24** |
| Desktop app shell | Not the focus |

---

## Quick start

```bash
# One command: listen → plan → QC → render
python scripts/atlas.py run \
  --narration script.txt \
  --audio voiceover.mp3 \
  --dna examples/styles/product_snappy_v1.json \
  --profile examples/profiles/product.json \
  --out renders/out.mp4

# Review the edit in a browser
python scripts/atlas.py review \
  --edit path/to/edit_spec.json \
  --video renders/out.mp4
```

See [docs/PRODUCT.md](docs/PRODUCT.md) and [docs/CRAFT.md](docs/CRAFT.md).

### Lower-level tools

```bash
# Style DNA from a reference video
python scripts/style_dna.py extract --video path/to/reference.mp4 --out examples/styles/my_dna.json

# Combine DNA + job profile → planning defaults
python scripts/style_dna.py apply \
  --dna examples/styles/my_dna.json \
  --profile examples/profiles/explainer.json
```

Requires: Python 3.10+, ffmpeg, Pillow. Optional: `faster-whisper` for real speech timing.

---

## Job profiles

| Profile | Evidence | Repeat cap | Pacing | Default picture lag |
|---------|----------|------------|--------|---------------------|
| `investigative` | strict | 2 | balanced | 0.3s (J-cut feel) |
| `explainer` | light | 2 | balanced | 0.25s |
| `product` | off | 3 | dense | 0.2s |
| `social` | off | 2 | dense | 0.15s |

Profiles live in `examples/profiles/`.

---

## Style DNA

Extracts **grammar**, not pixels: shot length, cut density, transitions, caption posture, motion hints. Apply with a job profile for a **new** project.

---

## Core principles

1. Story first, effects second  
2. Integrity invisible when possible  
3. Reality default; graphics when reality cannot  
4. Fail closed on evidence (when profile is strict)  
5. Constraint intelligence = professional revisions  
6. Cinematic ≠ more effects  
7. Any job — not one genre  
8. Stage the edit, then commit the render  
