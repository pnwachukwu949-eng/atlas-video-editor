# Copilot handoff tasks (Atlas)

Source of truth is the **local working tree**. Do not rewrite engines listed in `docs/ENGINE_MANIFEST.json`. Prefer minimal patches + tests.

## Done locally (15 pytest passed)

- tests/test_revision_notes.py
- tests/test_rhythm_captions.py
- tests/test_planner_diversity.py
- tests/test_revise_caption_sync.py
- docs/CLI.md

## Optional remaining

1. Remove `return True` from tests/test_style_dna_qc_v0_1.py to clear PytestReturnNotNoneWarning
2. Confirm pytest on CI if added later

## Do NOT

- Rewrite planner / fit / constraint / style_dna / evidence engines
- Soften evidence fail-closed rules
- Add API keys
- HOA-hardcode core
- Claim B10 evidence cleared
