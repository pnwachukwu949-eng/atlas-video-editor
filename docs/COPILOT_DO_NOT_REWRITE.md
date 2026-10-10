# For Copilot / collaborators — DO NOT REWRITE

Atlas already has these modules. **Extend them; do not create parallel copies.**

## Exists (authoritative paths)

| Capability | Path |
|------------|------|
| Constraint + unlock_required + fail-closed | `atlas/engines/constraint_revision/engine.py` (v0.2) |
| Append-only revision log | `append_revision_log()` in same file; `scripts/revise.py --log` |
| Style DNA extract/apply | `atlas/engines/style_dna/engine.py` + `scripts/style_dna.py` |
| Job profiles | `examples/profiles/{investigative,explainer,product,social}.json` |
| Beat planner | `atlas/engines/planner/engine.py` + `scripts/plan_edit.py` |
| Asset QC (repeat/ban/contact/brightness) | `atlas/engines/qc/engine.py` + `scripts/qc_assets.py` |
| Non-HOA demo | `examples/samples/product_explainer_*` → `renders/product_explainer_v0.1.mp4` |
| HOA baseline (frozen) | v0.24 |

## Forbidden

- `atlas/acquisition/style_extractor.py` (use `engines/style_dna`)
- `atlas/core/profiles.py` or `atlas/config/profiles/` (use `examples/profiles/`)
- Greenfield rewrite of constraint_revision

## Safe help

1. Read existing engines and document behavior
2. Push any missing engine file **verbatim** from the working tree
3. One small extension PR on existing code only
