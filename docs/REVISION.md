# Atlas Revision Engine — Locked Fields & Fail-Closed Behavior

> The Constraint & Revision Engine (v0.2) enforces editorial locks across revisions. Locked fields reject changes unless explicitly unlocked with reasoning.

## Core principle: fail-closed

When you try to change a locked field without permission, the engine **rejects the change and records it**. You cannot silently override a lock.

```
Locked field + no unlock_required → REJECTED
Locked field + unlock_required=true + unlock_reason → ALLOWED (and logged)
```

This is not a bug; it is by design. Investigative, documentary, and evidence-heavy work depends on this guarantee.

---

## The unlock_required flow

### Lock declaration (in Edit Spec)

Any field in a beat can be locked:

```json
{
  "beat_id": "B3",
  "visual": {
    "asset_id": "photo_123",
    "type": "real",
    "locked": true,
    "lock_reason": "approved by creative director"
  },
  "typography": {
    "primary_text": "Key claim",
    "locked": true,
    "lock_reason": "verified caption"
  }
}
```

Global locks protect the entire edit:

```json
{
  "global_locks": {
    "voiceover": true,
    "overall_duration": false,
    "evidence_policy": true
  }
}
```

### Revision request (attempt without permission)

```json
{
  "revision_id": "rev_001",
  "target_edit": "edit_hoa_v0.5",
  "instructions": [
    {
      "action": "change_visual_asset",
      "beat_id": "B3",
      "element_path": "visual",
      "new_value": "photo_999",
      "unlock_required": false
    }
  ]
}
```

### Engine response: REJECTED

```json
{
  "status": "rejected",
  "applied": [],
  "rejected": [
    {
      "element": "B3.visual",
      "reason": "LOCKED (approved by creative director). Pass unlock_required=true + unlock_reason to change.",
      "suggestion": "Set unlock_required=true and unlock_reason"
    }
  ],
  "locks_respected": 1
}
```

The change is **not applied**. You must ask for permission explicitly.

---

## Unlocking: the second request

When you decide to change a locked field, you must:
1. Set `unlock_required=true`
2. Provide `unlock_reason` explaining why

```json
{
  "revision_id": "rev_002",
  "target_edit": "edit_hoa_v0.5",
  "instructions": [
    {
      "action": "change_visual_asset",
      "beat_id": "B3",
      "element_path": "visual",
      "new_value": "photo_999",
      "unlock_required": true,
      "unlock_reason": "Better shot of the street intersection from new angle"
    }
  ]
}
```

### Engine response: SUCCESS

```json
{
  "status": "success",
  "applied": [
    "B3.visual.asset_id → photo_999"
  ],
  "rejected": [],
  "unlocks": [
    {
      "beat_id": "B3",
      "field": "visual",
      "reason": "Better shot of the street intersection from new angle"
    }
  ],
  "locks_respected": 0
}
```

The change is applied. The unlock is **recorded in the report** and appended to the revision log for audit.

---

## The _gate_lock guard: fail-closed logic

The engine's `_gate_lock()` method checks:

```python
def _gate_lock(container, label, unlock_required, unlock_reason, force):
    if not container.get("locked", False):
        return True, ""                      # Not locked, proceed
    if force:
        return True, ""                      # Force override (emergency only)
    if unlock_required:
        return True, ""                      # Explicit unlock, proceed
    lock_reason = container.get("lock_reason", "locked")
    return False, f"LOCKED ({lock_reason}). Pass unlock_required=true + unlock_reason to change."
```

**Three ways to pass:**
1. **Field is not locked** — proceed normally
2. **unlock_required=true** — proceed and record the unlock
3. **force=true** (request level) — emergency bypass (see below)

All other cases: **REJECTED**.

---

## Emergency bypass: force=true

At the revision request level, you can set `force=true` to bypass all locks:

```json
{
  "revision_id": "rev_emergency",
  "target_edit": "edit_hoa_v0.5",
  "force": true,
  "instructions": [...]
}
```

**Use sparingly.** This should only be used for:
- Emergency corrections (e.g., discovered error in locked narration)
- Final audit overrides (legal sign-off)
- Never for casual editorial changes

The report will not show unlocks when `force=true` is used, but the revision is still logged.

---

## Global voiceover lock: cannot be bypassed

The global voiceover lock is special:

```python
if action in ("change_visual_asset", "change_timing") and global_locks.get("voiceover", True):
    if element_path and "voiceover" in element_path.lower():
        # REJECTED: cannot unlock this way
        rejected.append({
            "reason": "GLOBAL LOCK: voiceover is immutable",
            "suggestion": "Voiceover lock cannot be bypassed without force=true at request level"
        })
```

To change voiceover (rarely needed), you must:
1. Use `force=true` on the entire revision request, **OR**
2. Create a new Edit Spec with different voiceover

This protects investigative work from accidental VO changes that break timing.

---

## Audit trail: append_revision_log

Every revision (success or rejection) is logged:

```python
from atlas.engines.constraint_revision.engine import append_revision_log

report = engine.apply_revision(edit_spec, revision_request)
append_revision_log("revisions.json", report)
```

The log file is **append-only JSON**:

```json
{
  "edit_id": "edit_hoa_v0.5",
  "revision_history": [
    {
      "revision_id": "rev_001",
      "timestamp": "2026-10-10T14:30:00Z",
      "status": "rejected",
      "applied": [],
      "rejected": [...],
      "unlocks": [],
      "locks_respected": 1
    },
    {
      "revision_id": "rev_002",
      "timestamp": "2026-10-10T14:32:00Z",
      "status": "success",
      "applied": ["B3.visual.asset_id → photo_999"],
      "rejected": [],
      "unlocks": [{"beat_id": "B3", "field": "visual", "reason": "..."}],
      "locks_respected": 0
    }
  ]
}
```

Each entry includes:
- `revision_id` — unique identifier for this change request
- `timestamp` — when applied
- `status` — success | partial_success | rejected
- `applied` — list of successful changes
- `rejected` — list of blocked changes (with reasons)
- `unlocks` — list of fields unlocked (with rationale)
- `locks_respected` — count of locks that prevented changes

**Immutable history.** Once logged, earlier revisions cannot be rewritten. This creates a defensible audit trail.

---

## CLI usage: scripts/revise.py

```bash
python scripts/revise.py \
  --edit examples/hoa_v0.5_edit_spec.json \
  --revision examples/sample_revision.json \
  --out examples/hoa_v0.5_revised.json \
  --report revision_report.json \
  --log revisions.json
```

- `--edit`: Edit Spec to revise
- `--revision`: Revision Request JSON
- `--out`: Path to write revised Edit Spec
- `--report`: (Optional) Write revision report
- `--log`: (Optional) Append to revision log

Output shows:
```
Status: success
Applied: 1
Rejected: 0
Locks respected: 0
Revised edit written to: examples/hoa_v0.5_revised.json
Report written to: revision_report.json
Revision log appended: revisions.json
```

---

## Profiles & lock defaults

Job profiles (in `examples/profiles/`) set initial lock patterns:

- **investigative.json** — most fields locked by default; evidence_status always locked
- **explainer.json** — looser; typography and captions unlocked; evidence off
- **product.json** — minimal locks; motion and timing free; evidence off
- **social.json** — very loose; short holds and frequent cuts

The Beat Planner uses profile defaults when generating an initial Edit Spec. For example, the investigative profile locks evidence status from the start; the planner honors that.

Revision behavior is the same for all profiles: locks require explicit `unlock_required=true` to change.

---

## Complete example: revision workflow

### Step 1: Generate initial Edit Spec

```bash
python scripts/plan_edit.py \
  --narration "Narration text..." \
  --duration 180.0 \
  --profile examples/profiles/investigative.json \
  --style examples/style_hoa_v0.22.json \
  --out edit_spec_v1.json
```

Output: `edit_spec_v1.json` with all evidence_status locked (investigative profile default).

### Step 2: Review and try to change a locked field

Revision request attempts to change a caption (locked by profile):

```json
{
  "revision_id": "rev_001",
  "target_edit": "edit_spec_v1",
  "instructions": [
    {
      "action": "change_caption",
      "beat_id": "B2",
      "element_path": "captions",
      "new_value": "Updated caption",
      "unlock_required": false
    }
  ]
}
```

Apply:

```bash
python scripts/revise.py \
  --edit edit_spec_v1.json \
  --revision revision_001.json \
  --out edit_spec_v1_rev1.json \
  --log revisions.json
```

Result:

```
Status: rejected
Applied: 0
Rejected: 1
Locks respected: 1
```

Report shows:
```json
{
  "rejected": [
    {
      "element": "B2.captions",
      "reason": "LOCKED (investigative profile default). Pass unlock_required=true + unlock_reason to change.",
      "suggestion": "Set unlock_required=true and unlock_reason"
    }
  ]
}
```

### Step 3: Unlock with reasoning

New revision request with permission:

```json
{
  "revision_id": "rev_002",
  "target_edit": "edit_spec_v1",
  "instructions": [
    {
      "action": "change_caption",
      "beat_id": "B2",
      "element_path": "captions",
      "new_value": "Updated caption",
      "unlock_required": true,
      "unlock_reason": "Grammar correction; meaning unchanged"
    }
  ]
}
```

Apply:

```bash
python scripts/revise.py \
  --edit edit_spec_v1.json \
  --revision revision_002.json \
  --out edit_spec_v1_rev2.json \
  --log revisions.json
```

Result:

```
Status: success
Applied: 1
Rejected: 0
Locks respected: 0
Revised edit written to: edit_spec_v1_rev2.json
Revision log appended: revisions.json
```

Revision log now shows both attempts:

```json
{
  "revision_history": [
    {
      "revision_id": "rev_001",
      "timestamp": "...",
      "status": "rejected",
      "applied": [],
      "rejected": [{"element": "B2.captions", "reason": "LOCKED..."}],
      "unlocks": [],
      "locks_respected": 1
    },
    {
      "revision_id": "rev_002",
      "timestamp": "...",
      "status": "success",
      "applied": ["B2.captions updated"],
      "rejected": [],
      "unlocks": [
        {
          "beat_id": "B2",
          "field": "captions",
          "reason": "Grammar correction; meaning unchanged"
        }
      ],
      "locks_respected": 0
    }
  ]
}
```

**Auditable history:** Anyone reviewing the log sees that the caption was locked, a grammar change was requested, and approval was granted with a clear reason. No silent changes.

---

## Summary

- **Locks are by default.** Profiles set which fields are locked in the initial Edit Spec.
- **Revisions must ask permission.** `unlock_required=true` + `unlock_reason` is required to change locked fields.
- **Fail-closed.** Locked fields reject silently unless explicitly unlocked. No accidental overwrites.
- **Audit trail.** Every revision (success and rejection) is appended to the log. Immutable history.
- **Emergency bypass.** `force=true` exists but should only be used for emergencies (legal sign-off, discovered errors).
- **Voiceover is sacred.** Global voiceover lock requires `force=true` to change; normal unlock path is blocked.

Use this pattern for any project—investigative, explainer, product, social—that needs controlled revisions and an audit trail.
