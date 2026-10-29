import os
import sys
from pathlib import Path
from typing import Optional, Set, List, Dict, Any

# Ensure PyAV compatibility with newer versions where metadata_errors was removed
try:
    import av
    _orig_av_open = av.open

    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)

    av.open = _safe_av_open
except Exception:
    pass

from faster_whisper import WhisperModel
from .base import BaseConverter
from .registry import default_registry

SUPPORTED_AUDIO_EXTS: Set[str] = {
    "mp3", "wav", "m4a", "flac", "aac", "ogg", "wma", "opus", "aiff", "amr", "m4b", "mp2"
}

SUPPORTED_VIDEO_EXTS: Set[str] = {
    "mp4", "mkv", "mov", "avi", "webm", "flv", "wmv", "m4v", "ts", "3gp", "mpeg", "mpg"
}

SUPPORTED_MEDIA_EXTS: Set[str] = SUPPORTED_AUDIO_EXTS | SUPPORTED_VIDEO_EXTS


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm string."""
    millis = int((seconds - int(seconds)) * 1000)
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def detect_optimal_device() -> str:
    """Detect if CUDA is available for ctranslate2 / faster-whisper, else CPU."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


class AudioVideoTranscriber:
    """
    Transcribes audio and video files to text using faster_whisper.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: Optional[str] = None,
    ):
        if device == "auto":
            self.device = detect_optimal_device()
        else:
            self.device = device

        if not compute_type:
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type

        self.model_size = model_size
        self._model: Optional[WhisperModel] = None

    def _create_model(self, device: str, compute_type: str) -> WhisperModel:
        return WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
        )

    def _load_model(self) -> WhisperModel:
        if self._model is None:
            print(f"[*] Memuat model Whisper '{self.model_size}' (device: {self.device}, compute: {self.compute_type})...")
            try:
                self._model = self._create_model(self.device, self.compute_type)
            except Exception as e:
                err_msg = str(e).lower()
                if self.device == "cuda" and any(k in err_msg for k in ("cublas", "cuda", "cudnn", "driver")):
                    print(f"[-] CUDA tidak dapat diinisialisasi ({e}). Beralih otomatis ke CPU (int8)...")
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self._model = self._create_model(self.device, self.compute_type)
                else:
                    raise
        return self._model

    def transcribe(
        self,
        source_path: Path,
        target_path: Path,
        language: Optional[str] = None,
        include_timestamps: bool = False,
        print_live: bool = True,
    ) -> bool:
        """
        Transcribe audio or video from source_path and write text to target_path (.txt).
        """
        source_path = Path(source_path)
        target_path = Path(target_path)

        if not source_path.is_file():
            print(f"[!] File sumber tidak ditemukan: {source_path}")
            return False

        try:
            model = self._load_model()
            print(f"[*] Memulai transkripsi: {source_path.name}")

            try:
                segments, info = model.transcribe(
                    str(source_path),
                    language=language,
                    beam_size=5,
                )
                # Test first item to catch generator/CUDA runtime errors early
                seg_iter = iter(segments)
                first_seg = next(seg_iter, None)
            except Exception as e:
                err_msg = str(e).lower()
                if self.device == "cuda" and any(k in err_msg for k in ("cublas", "cuda", "cudnn", "driver")):
                    print(f"[-] CUDA runtime error ({e}). Beralih otomatis ke CPU (int8)...")
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self._model = self._create_model("cpu", "int8")
                    segments, info = self._model.transcribe(
                        str(source_path),
                        language=language,
                        beam_size=5,
                    )
                    seg_iter = iter(segments)
                    first_seg = next(seg_iter, None)
                else:
                    raise

            lang_info = f"{info.language.upper()} ({info.language_probability * 100:.1f}%)" if info.language else "Auto"
            duration_info = f"{info.duration:.1f} detik" if hasattr(info, "duration") and info.duration else "N/A"
            print(f"[*] Bahasa terdeteksi : {lang_info}")
            print(f"[*] Perkiraan durasi : {duration_info}")
            print("-" * 60)

            lines: List[str] = []
            segment_count = 0

            current_seg = first_seg
            while current_seg is not None:
                segment_count += 1
                text = current_seg.text.strip()
                t_start = format_timestamp(current_seg.start)
                t_end = format_timestamp(current_seg.end)

                if include_timestamps:
                    formatted_line = f"[{t_start} -> {t_end}] {text}"
                else:
                    formatted_line = text

                if text:
                    lines.append(formatted_line)

                if print_live and text:
                    print(f"  [{t_start} -> {t_end}] {text}")

                current_seg = next(seg_iter, None)

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            print("-" * 60)
            print(f"[+] Transkripsi selesai! ({segment_count} segmen)")
            print(f"[+] Output tersimpan di: {target_path.resolve()}")
            return True

        except Exception as e:
            print(f"[!] Gagal mentranskripsi {source_path.name}: {e}")
            return False


class WhisperTranscribeConverter(BaseConverter):
    """
    Registry converter allowing 'afeat cvt <audio/video> txt'.
    """

    @property
    def name(self) -> str:
        return "Whisper Audio/Video Transcriber"

    @property
    def supported_inputs(self) -> Set[str]:
        return SUPPORTED_MEDIA_EXTS

    @property
    def supported_outputs(self) -> Set[str]:
        return {"txt"}

    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        transcriber = AudioVideoTranscriber(
            model_size=kwargs.get("model", "base"),
            device=kwargs.get("device", "auto"),
        )
        return transcriber.transcribe(
            source_path=source_path,
            target_path=target_path,
            language=kwargs.get("language"),
            include_timestamps=kwargs.get("include_timestamps", False),
        )


# Register to default_registry so afeat cvt file.mp3 txt also works
default_registry.register(WhisperTranscribeConverter())
