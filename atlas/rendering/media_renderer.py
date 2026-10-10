#!/usr/bin/env python3
"""Atlas Media Renderer — stills/video to MP4 with typography, captions, VO."""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


class MediaRenderer:
    def __init__(self, output_dir: str = "renders", assets_root: str = "assets"):
        self.output_dir = Path(output_dir)
        self.assets_root = Path(assets_root)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        p = self.assets_root / "registry.json"
        if p.exists():
            return json.loads(p.read_text())
        return {"assets": {}, "banned": {}}

    def _resolve_asset(self, asset_id: Optional[str]) -> Optional[Path]:
        if not asset_id:
            return None
        if asset_id in self.registry.get("banned", {}):
            return None
        entry = self.registry.get("assets", {}).get(asset_id)
        if not entry:
            return None
        path = self.assets_root / entry["path"]
        return path if path.exists() else None

    def _escape(self, text: str) -> str:
        text = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")
        text = text.replace("%", " pct")
        return text

    def _drawtext_lines(self, lines: List[str], fontsize: int, y0: int) -> List[str]:
        filters = []
        for i, line in enumerate(lines):
            if not line:
                continue
            esc = self._escape(line)
            y = y0 + i * (fontsize + 14)
            filters.append(
                f"drawtext=fontfile={FONT}:text='{esc}':fontsize={fontsize}:fontcolor=white:"
                f"x=40:y={y}:box=1:boxcolor=black@0.6:boxborderw=12"
            )
        return filters

    def render(self, timeline: Dict[str, Any], output_name: str = "output.mp4") -> str:
        video_clips = timeline.get("tracks", {}).get("video", [])
        caption_clips = timeline.get("tracks", {}).get("captions", [])
        overlay_clips = timeline.get("tracks", {}).get("overlays", [])
        captions_by_beat = {c["beat_id"]: c for c in caption_clips if c.get("beat_id")}
        overlays_by_beat: Dict[str, List] = {}
        for o in overlay_clips:
            overlays_by_beat.setdefault(o.get("beat_id", ""), []).append(o)

        with tempfile.TemporaryDirectory(prefix="atlas_render_") as tmp:
            tmp_path = Path(tmp)
            segments = []
            for i, clip in enumerate(video_clips):
                beat_id = clip.get("beat_id", f"seg_{i}")
                dur = max(0.1, float(clip["end"]) - float(clip["start"]))
                asset_path = self._resolve_asset(clip.get("asset_id"))
                seg = tmp_path / f"seg_{i:03d}.mp4"

                filters: List[str] = []
                if asset_path and asset_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    # Still with gentle scale
                    vf = [
                        f"scale=1920:1080:force_original_aspect_ratio=increase",
                        "crop=1920:1080",
                        f"fps=30",
                    ]
                    # Typography overlays
                    typs = [o for o in overlays_by_beat.get(beat_id, []) if o.get("type") == "typography"]
                    for o in typs:
                        lines = [o.get("content") or ""]
                        if o.get("secondary"):
                            lines.append(o["secondary"])
                        vf.extend(self._drawtext_lines(lines, 36, 40))
                    # Bottom caption
                    cap = captions_by_beat.get(beat_id)
                    if cap and cap.get("text"):
                        esc = self._escape(cap["text"])
                        vf.append(
                            f"drawtext=fontfile={FONT}:text='{esc}':fontsize=36:fontcolor=white:"
                            f"x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.55:boxborderw=14"
                        )
                    # Soft fade
                    fade_d = min(0.4, dur / 4)
                    vf.append(f"fade=t=in:st=0:d={fade_d}")
                    vf.append(f"fade=t=out:st={max(0, dur - fade_d)}:d={fade_d}")

                    cmd = [
                        "ffmpeg", "-y", "-loop", "1", "-i", str(asset_path),
                        "-vf", ",".join(vf),
                        "-t", str(dur), "-r", "30", "-pix_fmt", "yuv420p",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                        str(seg),
                    ]
                else:
                    # Color placeholder
                    cmd = [
                        "ffmpeg", "-y",
                        "-f", "lavfi", "-i", f"color=c=0x1a1a1a:s=1920x1080:d={dur}:r=30",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        str(seg),
                    ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"ffmpeg failed on {beat_id}: {result.stderr[-500:]}")
                segments.append(seg)

            # Concat
            concat_list = tmp_path / "list.txt"
            concat_list.write_text("".join(f"file '{s}'\n" for s in segments))
            silent = self.output_dir / output_name.replace(".mp4", "_silent.mp4")
            if silent.name == output_name:
                silent = self.output_dir / f"_{output_name}"
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c", "copy", str(silent),
            ], check=True, capture_output=True)

            # Mux VO if available
            out = self.output_dir / output_name
            vo_path = self.assets_root / "hoa_vo_full_narration.mp3"
            if not vo_path.exists():
                # try path from timeline audio
                for a in timeline.get("tracks", {}).get("audio", []):
                    cand = self.assets_root / f"{a.get('asset_id', '')}.mp3"
                    if cand.exists():
                        vo_path = cand
                        break
            if vo_path.exists():
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(silent), "-i", str(vo_path),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
                    "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(out),
                ], check=True, capture_output=True)
            else:
                silent.rename(out)

            return str(out)
