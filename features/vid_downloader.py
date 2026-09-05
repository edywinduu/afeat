import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp


def progress_hook(d: Dict[str, Any]) -> None:
    """Progress display for downloads."""
    if d.get("status") == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        speed = d.get("speed", 0)
        eta = d.get("eta", None)

        def fmt_bytes(s):
            if not s or s <= 0: return "0 B"
            for u in ["B", "KB", "MB", "GB"]:
                if s < 1024: return f"{s:.1f} {u}"
                s /= 1024
            return f"{s:.1f} TB"

        pct = f"{(downloaded / total * 100):.1f}%" if total > 0 else d.get("_percent_str", "")
        msg = f"\r[Downloading] {pct} | {fmt_bytes(downloaded)}/{fmt_bytes(total)} | {fmt_bytes(speed)}/s | ETA: {eta or 'N/A'}s"
        sys.stdout.write(msg.ljust(75))
        sys.stdout.flush()
    elif d.get("status") == "finished":
        sys.stdout.write("\n[Processing] Download complete. Converting/merging media...\n")
        sys.stdout.flush()


class SocialMediaDownloader:
    """Downloader and converter for social media links (YouTube, TikTok, IG, etc.) into CWD."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or Path.cwd()
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def download(
        self,
        url: str,
        is_audio: bool = False,
        media_format: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> bool:
        """Download media directly to target_dir (CWD)."""
        outtmpl = str(self.target_dir / "%(title)s [%(id)s].%(ext)s")

        ydl_opts: Dict[str, Any] = {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "progress_hooks": [progress_hook],
            "windowsfilenames": True,
            "no_warnings": False,
        }

        if is_audio:
            fmt = (media_format or "mp3").lower()
            bitrate = quality if quality and quality.isdigit() else "192"
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": fmt,
                        "preferredquality": bitrate,
                    }
                ],
            })
        else:
            fmt = (media_format or "mp4").lower()
            if quality and quality.isdigit():
                format_selector = (
                    f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
                    f"bestvideo[height<={quality}]+bestaudio/"
                    f"best[height<={quality}]/best"
                )
            else:
                format_selector = (
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                    "bestvideo+bestaudio/"
                    "best"
                )

            ydl_opts.update({
                "format": format_selector,
                "merge_output_format": fmt,
                "postprocessors": [
                    {
                        "key": "FFmpegVideoRemuxer",
                        "preferedformat": fmt,
                    }
                ],
            })

        print(f"[*] Downloading media to: {self.target_dir}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"[+] Download complete: check folder {self.target_dir}")
            return True
        except Exception as e:
            print(f"\n[!] Error downloading media: {e}", file=sys.stderr)
            return False
