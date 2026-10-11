#!/usr/bin/env python3
"""
Build a self-contained HTML review of an Atlas Edit Spec.

  python scripts/atlas.py review --edit path/to/edit_spec.json --video path/to/out.mp4
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s))


def build_html(edit: dict, video_path: str | None) -> str:
    beats = edit.get("beats") or []
    meta = edit.get("metadata") or {}
    vo = edit.get("source_voiceover") or {}
    locks = edit.get("global_locks") or {}
    style_av = edit.get("style_av") or {}

    rows = []
    for b in beats:
        visual = b.get("visual") or {}
        cap = (b.get("captions") or {}).get("text") or (b.get("typography") or {}).get("primary_text") or ""
        ev = b.get("evidence_status") or {}
        timing = b.get("timing") or {}
        lag = timing.get("picture_lag_seconds", style_av.get("picture_lag_seconds", ""))
        rows.append(f"""
        <tr>
          <td class="id">{esc(b.get('beat_id'))}</td>
          <td class="t">{esc(round(float(b.get('start', 0)), 2))}–{esc(round(float(b.get('end', 0)), 2))}s</td>
          <td class="narr">{esc((b.get('narration_summary') or '')[:120])}</td>
          <td class="vis">{esc(visual.get('asset_id') or visual.get('type') or '—')}</td>
          <td class="cap">{esc(cap[:80])}</td>
          <td class="ev">{esc(ev.get('status') or '—')}</td>
          <td class="lag">{esc(lag if lag != '' else '0')}</td>
        </tr>""")

    video_block = ""
    if video_path:
        video_block = f"""
        <section class="video">
          <h2>Render</h2>
          <p class="path">{esc(video_path)}</p>
          <video controls src="{esc(Path(video_path).name)}" style="max-width:100%;background:#000"></video>
          <p class="hint">If the player is empty, open the MP4 from the path above (browser may block file:// media).</p>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Atlas Review — {esc(edit.get('edit_id', 'edit'))}</title>
  <style>
    :root {{
      --bg: #0f1115;
      --panel: #171a21;
      --text: #e8eaed;
      --muted: #9aa0a6;
      --accent: #7aa2ff;
      --line: #2a2f3a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 24px;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.45;
    }}
    h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
    h2 {{ font-size: 1.05rem; margin: 28px 0 12px; color: var(--accent); }}
    .sub {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
    .card {{
      background: var(--panel); border: 1px solid var(--line);
      border-radius: 10px; padding: 12px 14px;
    }}
    .card .k {{ color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: .04em; }}
    .card .v {{ font-size: 1.05rem; margin-top: 4px; word-break: break-word; }}
    table {{
      width: 100%; border-collapse: collapse; font-size: 0.88rem;
      background: var(--panel); border-radius: 10px; overflow: hidden;
      border: 1px solid var(--line);
    }}
    th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: none; }}
    .id {{ font-family: ui-monospace, monospace; color: var(--accent); white-space: nowrap; }}
    .t {{ white-space: nowrap; color: var(--muted); }}
    .hint {{ color: var(--muted); font-size: 0.85rem; }}
    .path {{ font-family: ui-monospace, monospace; font-size: 0.85rem; color: var(--muted); }}
    footer {{ margin-top: 32px; color: var(--muted); font-size: 0.8rem; }}
  </style>
</head>
<body>
  <h1>Atlas Edit Review</h1>
  <p class="sub">{esc(edit.get('edit_id', 'edit'))} · profile {esc(edit.get('profile_id') or '—')} · style {esc(edit.get('style_id') or '—')}</p>

  <div class="grid">
    <div class="card"><div class="k">Beats</div><div class="v">{len(beats)}</div></div>
    <div class="card"><div class="k">Duration</div><div class="v">{esc(vo.get('duration_seconds') or meta.get('duration') or '—')}s</div></div>
    <div class="card"><div class="k">Timed segments</div><div class="v">{esc(meta.get('used_timed_segments'))}</div></div>
    <div class="card"><div class="k">VO locked</div><div class="v">{esc(locks.get('voiceover', vo.get('locked')))}</div></div>
    <div class="card"><div class="k">Picture lag</div><div class="v">{esc(style_av.get('picture_lag_seconds', 0))}s</div></div>
    <div class="card"><div class="k">Planner</div><div class="v">{esc(meta.get('planner_version') or '—')}</div></div>
  </div>

  {video_block}

  <h2>Beats</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Time</th><th>Narration</th><th>Visual</th><th>Caption</th><th>Evidence</th><th>Lag</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>

  <footer>
    Atlas Video Editor — review surface. Stage the edit, then commit a render.
    Locks and evidence status are visible here so craft stays intentional.
  </footer>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Atlas HTML edit review")
    ap.add_argument("--edit", required=True)
    ap.add_argument("--video", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    edit_path = Path(args.edit)
    edit = json.loads(edit_path.read_text())
    out = Path(args.out) if args.out else edit_path.with_suffix(".review.html")
    out.write_text(build_html(edit, args.video), encoding="utf-8")
    print(json.dumps({"out": str(out), "beats": len(edit.get("beats") or []), "edit_id": edit.get("edit_id")}, indent=2))


if __name__ == "__main__":
    main()
