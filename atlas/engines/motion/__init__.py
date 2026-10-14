"""Atlas Motion Engine — camera-2D presets and story binding."""

from atlas.engines.motion.engine import MotionEngine, build_ffmpeg_zoompan
from atlas.engines.motion.presets import list_presets, get_preset, legacy_type_to_preset_id

__all__ = [
    "MotionEngine",
    "build_ffmpeg_zoompan",
    "list_presets",
    "get_preset",
    "legacy_type_to_preset_id",
]
