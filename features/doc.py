import sys
from pathlib import Path
from typing import Set, Optional, Any
import markdown
import pypdf

from .base import BaseConverter
from .registry import default_registry


class DocumentConverter(BaseConverter):
    """Converter for documents (Markdown, TXT, PDF)."""

    @property
    def name(self) -> str:
        return "Document Converter"

    @property
    def supported_inputs(self) -> Set[str]:
        return {"md", "txt", "pdf"}

    @property
    def supported_outputs(self) -> Set[str]:
        return {"html", "txt", "pdf"}

    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        """Convert documents."""
        try:
            src_ext = source_path.suffix.lower().lstrip(".")
            target_ext = target_path.suffix.lower().lstrip(".")
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Markdown to HTML
            if src_ext == "md" and target_ext == "html":
                text = source_path.read_text(encoding="utf-8")
                html_body = markdown.markdown(text, extensions=["tables", "fenced_code"])
                full_html = f"<!DOCTYPE html>\n<html>\n<head><meta charset='utf-8'><title>{source_path.stem}</title></head>\n<body>\n{html_body}\n</body>\n</html>"
                target_path.write_text(full_html, encoding="utf-8")
                return True

            # PDF to TXT
            elif src_ext == "pdf" and target_ext == "txt":
                reader = pypdf.PdfReader(str(source_path))
                extracted_text = []
                for i, page in enumerate(reader.pages):
                    extracted_text.append(f"--- Page {i+1} ---\n" + (page.extract_text() or ""))
                target_path.write_text("\n\n".join(extracted_text), encoding="utf-8")
                return True

            # TXT to Markdown or Plain Copy
            elif src_ext in ["txt", "md"] and target_ext in ["txt", "md"]:
                content = source_path.read_text(encoding="utf-8")
                target_path.write_text(content, encoding="utf-8")
                return True

            return False
        except Exception as e:
            print(f"[!] Error converting document {source_path.name}: {e}", file=sys.stderr)
            return False


# Register default instance
default_registry.register(DocumentConverter())
