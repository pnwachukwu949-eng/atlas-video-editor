# Atlas Video Editor — Architecture

## Vision

Atlas is an AI video editor that understands story, claims, evidence, and constraints.
It does not merely cut on timestamps. It makes editorial decisions and remembers what must not change.

## Core loop

```
SCRIPT + VOICEOVER + ASSETS
        ↓
   ATLAS BRAIN (story, claims, rhythm, visuals)
        ↓
   EDIT SPECIFICATION (beats, locks, captions)
        ↓
   ASSET ENGINE (match, provenance, rights)
        ↓
   EDITOR ENGINE (layout, timing, motion)
        ↓
   RENDERER → ROUGH CUT → HUMAN REVIEW → REVISION
```

## Constraint intelligence

Locked fields cannot change unless the human unlocks them.
Examples: voiceover track, evidence status, approved typography, B10 empty slot.

## Evidence policy

Fail closed. Secondary reporting is not the exhibit.
Decisions: USE_REAL | USE_ILLUSTRATIVE | ACQUIRE | REJECT.

## Stages A–D

- A: Shareable investigative cut
- B: Repeatable editor + revision memory
- C: Style DNA from reference video
- D: Evidence-grade real vs illustration competition

See README for current v0.22 status.
