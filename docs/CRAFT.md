# Atlas Craft Principles

Inspired by tools like **ArtCraft** (compose intentionally, then commit) — adapted for **editorial** work, not generation.

## Stage before you commit

ArtCraft stages a shot in 2D/3D before a model generates pixels.

Atlas stages a **beat** (timing, visual, caption, evidence status, locks) before ffmpeg renders frames.

```
Intent → Edit Spec (crafted, locked) → Timeline → Render
```

Not:

```
Prompt → hope → re-roll
```

## Audio and picture need not cut together

**J-cut feel** (`picture_lag_seconds` > 0):
Narration of the next idea starts while the previous picture still holds briefly. The ear leads; the eye follows.

**L-cut feel** (`picture_lag_seconds` < 0):
The next picture arrives slightly before the narration boundary. The eye leads; the ear follows.

Set globally via Style DNA / profile, or per beat:

```json
"timing": {
  "picture_lag_seconds": 0.25,
  "transition_in": "hard_cut"
}
```

The bridge shifts video clip windows relative to narration windows, then stitches so the picture track stays continuous (no black flash gaps).

## What we deliberately do *not* copy from ArtCraft

| ArtCraft | Atlas |
|----------|--------|
| Multi-model AI generation studio | Not a generator |
| 3D prop / character posing | Not required for editorial cuts |
| Credit-based model catalog | Asset provenance + rights instead |
| Prompt-first creation | Script + VO + assets first |

## Shared spirit

- **Control over chance** — editorial decisions are explicit in the Edit Spec
- **Reviewable craft** — locks, revision log, QC, evidence gates
- **Human direction** — “change only this” without redesigning the whole film

Atlas remains an **editor/director engine**. ArtCraft remains a **crafting/generation studio**. They solve different jobs; the craft mindset is compatible.
