import sys
import subprocess
from pathlib import Path
from typing import Set, Optional, Any

from .base import BaseConverter
from .registry import default_registry


class VideoConverter(BaseConverter):
    """Converter for video files, GIF generation, and audio extraction."""

    @property
    def name(self) -> str:
        return "Video Converter"

    @property
    def supported_inputs(self) -> Set[str]:
        return {"mp4", "mkv", "mov", "avi", "webm", "flv", "wmv", "m4v", "ts"}

    @property
    def supported_outputs(self) -> Set[str]:
        return {
            "mp4", "mkv", "webm", "mov", "avi",  # Video to Video
            "gif",                               # Video to GIF animation
            "mp3", "wav", "m4a", "flac", "ogg"   # Video to Audio extraction
        }

    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        """Convert video, create GIF, or extract audio using FFmpeg."""
        try:
            target_ext = target_path.suffix.lower().lstrip(".")
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Case 1: Video to animated GIF
            if target_ext == "gif":
                # High-quality 2-pass GIF generation using palettegen & paletteuse
                filter_complex = "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
                cmd = [
                    "ffmpeg", "-y", "-i", str(source_path),
                    "-vf", filter_complex,
                    str(target_path)
                ]

            # Case 2: Video to Audio Extraction
            elif target_ext in ["mp3", "wav", "m4a", "flac", "ogg"]:
                cmd = ["ffmpeg", "-y", "-i", str(source_path), "-vn"]
                if target_ext == "mp3":
                    bitrate = f"{quality}k" if quality and quality > 32 else "192k"
                    cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
                elif target_ext in ["m4a"]:
                    cmd.extend(["-c:a", "aac", "-b:a", "192k"])
                elif target_ext == "flac":
                    cmd.extend(["-c:a", "flac"])
                elif target_ext == "wav":
                    cmd.extend(["-c:a", "pcm_s16le"])
                cmd.append(str(target_path))

            # Case 3: Video to Video Container / Transcode
            else:
                cmd = ["ffmpeg", "-y", "-i", str(source_path)]
                if target_ext == "mp4":
                    cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-preset", "fast"])
                elif target_ext == "webm":
                    cmd.extend(["-c:v", "libvpx-vp9", "-c:a", "libopus"])
                elif target_ext == "mkv":
                    cmd.extend(["-c:v", "copy", "-c:a", "copy"])

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
            print(f"[!] Error converting video {source_path.name}: {e}", file=sys.stderr)
            return False


# Register default instance
default_registry.register(VideoConverter())
