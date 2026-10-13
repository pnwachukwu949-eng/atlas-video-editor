# Platform editing research → Atlas

Sources reviewed (2025–2026 practice): YouTube retention workflows, B-roll rules,
J/L-cuts, documentary vs explainer posture, short-form caption culture.

## What platforms reward (and what we adopt)

| Practice | Platform meaning | Atlas response |
|----------|------------------|----------------|
| **VO / A-roll first** | Cut picture to speech, not the reverse | Listen → plan beats on timed segments |
| **B-roll = illustrate or cover** | “Would a picture of this *noun* help?” Decoration is waste | Asset Fit + keyword score; acquisition asks for the *kind* of visual needed |
| **J-cut / L-cut** | Audio leads or trails picture for flow | `picture_lag_seconds` / Style DNA |
| **Pace follows information** | Not “cut every 2s”; hold on payoff, tighten dead air | Shot **intention** (`establish` / `illustrate` / `prove` / `release` / `callback`) |
| **Pattern interrupt with meaning** | Change frame when attention needs a reset, not random zooms | `qc-rhythm` stale-visual warnings; re-engagement points on longer cuts |
| **Captions for mute / phone** | Especially social; keep meaning groups together | Captions on every beat; revision notes can retarget by timestamp |
| **Hook early** | First 15–30s deliver the promise | Opening intention prefers `establish` |
| **Doc vs social** | Doc: invisible cuts, evidence care. Social: denser changes, bold captions | Job **profiles** (`investigative` vs `social` / `product`) |
| **Evidence honesty** | Stock ≠ proof | Provenance + evidence gates; never label illustrative as verified |

## What we refuse

- Constant jump-cuts or zooms for their own sake  
- Filling gaps with unrelated cinematic stock  
- Treating AI-generated B-roll as documentary evidence  
- Rewriting a working edit because a trend video said “cut every 1.5 seconds”

## Commands

```bash
python scripts/atlas.py qc-rhythm --edit edit_spec.json --out rhythm.json
```

Re-engagement points appear when duration ≥ ~45s (1/3 and 2/3 markers).

## Next optional lifts

- Stronger concrete-noun extraction for B-roll scoring  
- Caption safe-area / max-width checks  
- Light SFX “tick” only when profile allows (never over VO)
