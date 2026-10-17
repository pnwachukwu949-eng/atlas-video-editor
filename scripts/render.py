#!/usr/bin/env python3
"""
Atlas CLI – Render a Timeline into a real MP4.

Usage:
  python scripts/render.py \
    --timeline examples/timeline.json \
    --out renders/out.mp4 \
    --audio assets/vo.mp3

  # Optional music bed under VO (ducked):
  python scripts/render.py \
    --timeline examples/timeline.json \
    --out renders/out.mp4 \
    --audio assets/vo.mp3 \
    --music assets/music/bed.mp3 \
    --music-volume 0.12
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from atlas.rendering.media_renderer import MediaRenderer


def _probe_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float((r.stdout or "").strip() or 0)
    except ValueError:
        return 0.0


def mux_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    music_path: Path | None = None,
    music_volume: float = 0.12,
    duck: bool = True,
) -> Path:
    """
    Mux voiceover (+ optional music bed) into video.

    Music sits under VO. When duck=True (default), sidechain compression
    pulls the bed down while speech is present, then releases in gaps —
    closer to a real editor mix than a flat volume pad.
    """
    tmp = output_path.with_suffix(".tmp.mp4")
    music_volume = max(0.0, min(1.0, float(music_volume)))

    if music_path and music_path.exists() and music_volume > 0.001:
        # Inputs: 0=video, 1=VO, 2=music
        if duck:
            # VO drives sidechain → music ducks under speech → mix
            filter_complex = (
                f"[2:a]volume={music_volume:.4f},aloop=loop=-1:size=2e+09[mg];"
                f"[1:a]asplit=2[vo][sc];"
                f"[mg][sc]sidechaincompress=threshold=0.025:ratio=8:attack=40:release=400:level_sc=1[ducked];"
                f"[vo][ducked]amix=inputs=2:duration=first:dropout_transition=0[aout]"
            )
        else:
            filter_complex = (
                f"[2:a]volume={music_volume:.4f},aloop=loop=-1:size=2e+09[mg];"
                f"[1:a][mg]amix=inputs=2:duration=first:dropout_transition=0[aout]"
            )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-i", str(music_path),
            "-filter_complex", filter_complex,
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest",
            str(tmp),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            str(tmp),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Audio mux failed: {result.stderr[-600:]}")
    tmp.replace(output_path)
    return output_path


def make_soft_bed(duration: float, out_path: Path) -> Path:
    """
    Generate a soft pink-noise bed (no external music file required for demos).
    Always marked illustrative / non-commercial placeholder tone.
    """
    duration = max(1.0, float(duration))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Quiet low pink noise — under VO at default music_volume it is barely audible warmth
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anoisesrc=d={duration:.3f}:c=pink:r=44100:a=0.15",
        "-af", "lowpass=f=280,highpass=f=40,volume=0.35",
        "-c:a", "aac", "-b:a", "96k",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"soft bed failed: {r.stderr[-300:]}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Atlas Media Renderer – Timeline → MP4")
    parser.add_argument("--timeline", required=True, help="Path to Timeline JSON")
    parser.add_argument("--out", required=True, help="Output MP4 path")
    parser.add_argument("--audio", default=None, help="Optional MP3/WAV voiceover to mux")
    parser.add_argument("--music", default=None, help="Optional music bed under VO")
    parser.add_argument(
        "--music-volume",
        type=float,
        default=0.12,
        help="Music bed gain 0–1 (default 0.12). VO stays primary.",
    )
    parser.add_argument(
        "--soft-bed",
        action="store_true",
        help="Generate a quiet pink-noise bed if --music is not provided",
    )
    parser.add_argument(
        "--no-duck",
        action="store_true",
        help="Disable sidechain ducking (flat music volume under VO)",
    )
    args = parser.parse_args()

    with open(args.timeline) as f:
        timeline = json.load(f)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    renderer = MediaRenderer(output_dir=str(out_path.parent), assets_root="assets")

    music_path = Path(args.music) if args.music else None
    soft_tmp = None

    if args.audio:
        silent_path = out_path.with_name(out_path.stem + "_silent.mp4")
        renderer.render(timeline, output_name=silent_path.name)

        if args.soft_bed and not (music_path and music_path.exists()):
            dur = float(timeline.get("duration_seconds") or 0) or _probe_duration(Path(args.audio))
            soft_tmp = out_path.with_name(out_path.stem + "_softbed.m4a")
            make_soft_bed(dur, soft_tmp)
            music_path = soft_tmp

        final = mux_audio(
            silent_path,
            Path(args.audio),
            out_path,
            music_path=music_path if music_path and music_path.exists() else None,
            music_volume=args.music_volume,
            duck=not bool(getattr(args, "no_duck", False)),
        )
        silent_path.unlink(missing_ok=True)
        if soft_tmp:
            soft_tmp.unlink(missing_ok=True)
        print(f"Rendered:     {final}  (with voiceover"
              f"{' + music bed' if music_path else ''})")
    else:
        result = renderer.render(timeline, output_name=out_path.name)
        print(f"Rendered:     {result}")

    print(f"Timeline ID:  {timeline.get('timeline_id')}")
    print(f"Duration:     {timeline.get('duration_seconds')}s")
    print(f"Video clips:  {len(timeline.get('tracks', {}).get('video', []))}")
    print(f"Locks honored:{len(timeline.get('locks_honored', []))}")
    print()
    print("Renderer: real images + optional --audio / --music bed")


if __name__ == "__main__":
    main()
