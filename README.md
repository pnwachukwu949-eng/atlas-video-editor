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
| Edit Specification → Timeline → MP4 | Working |
| Constraint & Revision Engine (locks) | Working |
| Asset registry + bans | Working |
| **Style DNA v0.1** (extract grammar from reference) | **Working** |
| **Job profiles** (explainer / investigative / product / social) | **Working** |
| **Repeat-cap + banned + brightness QC** | **Working** |
| **Asset contact sheet** | **Working** |
| HOA baseline freeze | **v0.24** |
| Style DNA → full auto beat planner | Next |
| UI | Not yet |

---

## Quick start

```bash
# Style DNA from a reference video
python scripts/style_dna.py extract --video path/to/reference.mp4 --out examples/styles/my_dna.json

# Combine DNA + job profile → planning defaults
python scripts/style_dna.py apply \
  --dna examples/styles/my_dna.json \
  --profile examples/profiles/explainer.json

# Asset contact sheet (catch mislabeled files before edit)
python scripts/qc_assets.py contact-sheet --out renders/asset_contact_sheet.jpg

# QC an edit spec (repeat cap ≤2, bans, brightness)
python scripts/qc_assets.py edit --edit examples/hoa_v0.24_edit_spec.json --max-uses 2

# Build / revise / render (existing)
python scripts/revise.py --edit ... --revision ... --out ...
python scripts/build_timeline.py --edit ... --out ...
python scripts/render.py --timeline ... --out ... --audio ...
```

For the single-command path from narration or an existing edit spec to a finished render, use `scripts/atlas_pipeline.py`. It orchestrates the full flow of plan → optional QC → timeline → render without manually chaining each CLI step.

Requires: Python 3.10+, ffmpeg, Pillow.

---

## Job profiles

| Profile | Evidence | Repeat cap | Pacing |
|---------|----------|------------|--------|
| `investigative` | strict | 2 | balanced |
| `explainer` | light | 2 | balanced |
| `product` | off | 3 | dense |
| `social` | off | 2 | dense |

Profiles live in `examples/profiles/`.

---

## Style DNA

Extracts **grammar**, not pixels:

- average / median shot length
- cut density
- preferred transition
- caption posture
- B-roll density / motion hints

Apply with a job profile to get planning defaults for a **new** project.

---

## QC rules (from HOA stress tests)

1. **Repeat cap** — same `asset_id` counted even if darkened under a card  
2. **Banned list** — wrong-geo, watermarks, mislabeled files never reach timeline  
3. **Contact sheet** — labeled grid before use (pagoda-as-bench class failures)  
4. **Brightness** — flag very dark plates under text  

---

## Roadmap

- **Done:** HOA v0.24 freeze, Style DNA v0.1, profiles, QC  
- **Next:** Style DNA → generic beat planner; source-plate tracking under composites  
- **Later:** richer reference analysis; UI; evidence pipeline for strict profiles  

---

## Core principles

1. Story first, effects second  
2. Integrity invisible when possible  
3. Reality default; graphics when reality cannot  
4. Fail closed on evidence (when profile is strict)  
5. Constraint intelligence = professional revisions  
6. Cinematic ≠ more effects  
7. Any job — not one genre  
