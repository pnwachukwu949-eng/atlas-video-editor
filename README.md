# Atlas Video Editor

**AI video editor with editorial intelligence and constraint memory.**

> Give Atlas a script + voiceover + visual assets,  
> and it produces a structured, context-aware edit that can be reviewed and revised  
> without destroying what the human has already approved.

---

## Status (v0.22)

| Capability | Status |
|------------|--------|
| Edit Specification (structured beats) | Working |
| Constraint & Revision Engine (locks) | Working |
| Timeline generation | Working |
| Asset registry + provenance bans | Working |
| Typography overlays (including `$`) | Working |
| Burned-in captions | Working |
| Media Renderer (MP4 + VO mux) | Working |
| Evidence lock (B10 fail-closed) | Working |
| VO-synced beat timing | Working |
| Photo acquisition (basic) | Working |
| Pre-render QC script | Working |
| Full HOA cut (shareable Stage A) | `hoa_v0.22` |

---

## Quick Start

```bash
# One-command build from edit spec
python scripts/atlas_build.py --edit examples/hoa_v0.22_edit_spec.json --out renders/hoa_v0.22.mp4

# Or step by step:
python scripts/revise.py --edit examples/hoa_v0.22_edit_spec.json --revision examples/sample_revision.json --out examples/revised.json
python scripts/build_timeline.py --edit examples/hoa_v0.22_edit_spec.json --out examples/hoa_v0.22_timeline.json
python scripts/render.py --timeline examples/hoa_v0.22_timeline.json --out renders/output.mp4
python scripts/qc.py --video renders/output.mp4 --edit examples/hoa_v0.22_edit_spec.json
```

Requires: Python 3.10+, ffmpeg, Pillow (for generated cards).

---

## Project Structure

```
atlas-video-editor/
├── atlas/
│   ├── core/schemas/           # Edit Spec, Revision, Timeline JSON schemas
│   ├── engines/constraint_revision/
│   ├── acquisition/            # Photo fetcher
│   └── rendering/              # Timeline bridge + Media Renderer
├── assets/
│   ├── registry.json           # Asset paths, rights, bans
│   └── contextual/             # Local stills (not all committed; large)
├── examples/                   # Edit specs + timelines (v0.5 → v0.22)
├── renders/                    # Output MP4s (gitignored)
├── scripts/                    # CLI tools
├── docs/architecture.md
└── tests/
```

---

## Core Principles

1. Story first, effects second  
2. Integrity must be invisible when possible  
3. Reality is the default; graphics explain what reality cannot  
4. Fail closed on evidence  
5. Constraint intelligence = creative intelligence  
6. Cinematic ≠ more effects  
7. Visuals follow narration semantic timing  
8. Banned assets stay banned (wrong geo, watermarks, mislabeled files)

---

## Roadmap (A → D)

- **A** Shareable HOA cut with VO sync and honest evidence treatment  
- **B** Repeatable editor CLI + revision memory  
- **C** Style DNA from reference video  
- **D** Evidence-grade asset pipeline (real exhibit vs illustration)

---

## License / note

Prototype for product development. Contextual photos may require their own licenses for redistribution.
