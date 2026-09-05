import sys
import subprocess
from pathlib import Path
from typing import Set, Optional, Any

from .base import BaseConverter
from .registry import default_registry


class AudioConverter(BaseConverter):
    """Converter for audio formats using FFmpeg."""

    @property
    def name(self) -> str:
        return "Audio Converter"

    @property
    def supported_inputs(self) -> Set[str]:
        return {"mp3", "wav", "m4a", "aac", "flac", "opus", "ogg", "wma"}

    @property
    def supported_outputs(self) -> Set[str]:
        return {"mp3", "m4a", "wav", "flac", "opus", "ogg", "aac"}

    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        """Convert audio file using FFmpeg."""
        try:
            target_ext = target_path.suffix.lower().lstrip(".")
            target_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = ["ffmpeg", "-y", "-i", str(source_path)]

            # Codec and bitrate configurations
            if target_ext == "mp3":
                bitrate = f"{quality}k" if quality and quality > 32 else "192k"
                cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
            elif target_ext in ["m4a", "aac"]:
                bitrate = f"{quality}k" if quality and quality > 32 else "192k"
                cmd.extend(["-c:a", "aac", "-b:a", bitrate])
            elif target_ext == "flac":
                cmd.extend(["-c:a", "flac"])
            elif target_ext == "wav":
                cmd.extend(["-c:a", "pcm_s16le"])
            elif target_ext == "ogg":
                cmd.extend(["-c:a", "libvorbis"])
            elif target_ext == "opus":
                cmd.extend(["-c:a", "libopus", "-b:a", "128k"])

            cmd.append(str(target_path))

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                print(f"[!] FFmpeg error converting {source_path.name}: {result.stderr[-200:]}", file=sys.stderr)
                return False

            return True
        except Exception as e:
            print(f"[!] Error converting audio {source_path.name}: {e}", file=sys.stderr)
            return False


# Register default instance
default_registry.register(AudioConverter())
