import sys
from pathlib import Path
from typing import Set, Optional, Any
from PIL import Image
import pillow_heif

from .base import BaseConverter
from .registry import default_registry

# Register HEIF opener with Pillow so .heic / .heif files are natively opened
pillow_heif.register_heif_opener()


class ImageConverter(BaseConverter):
    """Converter for modern and standard image formats."""

    @property
    def name(self) -> str:
        return "Image Converter"

    @property
    def supported_inputs(self) -> Set[str]:
        return {
            "jpg", "jpeg", "png", "webp", "heic", "heif",
            "bmp", "tiff", "tif", "gif", "ico"
        }

    @property
    def supported_outputs(self) -> Set[str]:
        return {
            "webp", "jpg", "jpeg", "png", "bmp", "tiff", "ico", "pdf"
        }

    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        """Convert and compress an image to target format."""
        try:
            target_ext = target_path.suffix.lower().lstrip(".")
            q = quality if quality is not None and 1 <= quality <= 100 else 85

            target_path.parent.mkdir(parents=True, exist_ok=True)

            with Image.open(source_path) as img:
                # Convert palette images to RGBA/RGB
                if img.mode == "P":
                    img = img.convert("RGBA" if "transparency" in img.info else "RGB")

                # Handle transparency when converting to JPEG or BMP which do not support alpha
                if target_ext in ["jpg", "jpeg", "bmp"]:
                    if img.mode in ("RGBA", "LA"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        alpha = img.split()[-1]
                        background.paste(img, mask=alpha)
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")

                # Handle ICO format (requires resizing if too large)
                if target_ext == "ico":
                    if img.size[0] > 256 or img.size[1] > 256:
                        img = img.resize((256, 256), Image.Resampling.LANCZOS)
                    img.save(target_path, format="ICO")
                    return True

                # Save options based on format
                if target_ext in ["jpg", "jpeg"]:
                    img.save(target_path, format="JPEG", quality=q, optimize=True)
                elif target_ext == "webp":
                    img.save(target_path, format="WEBP", quality=q, method=6)
                elif target_ext == "png":
                    img.save(target_path, format="PNG", optimize=True)
                elif target_ext == "pdf":
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(target_path, format="PDF")
                else:
                    img.save(target_path, quality=q)

            return True
        except Exception as e:
            print(f"[!] Error converting {source_path.name} to {target_path.suffix}: {e}", file=sys.stderr)
            return False


# Register default instance
default_registry.register(ImageConverter())
