import sys
from pathlib import Path
from typing import Set, Optional, Any
import markdown
import pypdf

try:
    import anydoc
    HAS_ANYDOC = True
except ImportError:
    HAS_ANYDOC = False

from .base import BaseConverter
from .registry import default_registry

ANYDOC_FORMATS = {
    "doc", "docx", "docm",
    "ppt", "pptx", "pptm",
    "xls", "xlsx", "xlsm", "xlsb",
    "odt", "ods", "odp",
    "rtf", "epub", "csv", "tsv", "pdf",
}


class DocumentConverter(BaseConverter):
    """
    Universal Document Converter powered by Firecrawl AnyDoc engine
    with PyPDF and Python-Markdown fallbacks.
    """

    @property
    def name(self) -> str:
        return "Document Converter (AnyDoc Engine)"

    @property
    def supported_inputs(self) -> Set[str]:
        return {
            "doc", "docx", "docm",
            "ppt", "pptx", "pptm",
            "xls", "xlsx", "xlsm", "xlsb",
            "odt", "ods", "odp",
            "rtf", "epub", "csv", "tsv",
            "pdf", "md", "txt",
        }

    @property
    def supported_outputs(self) -> Set[str]:
        return {"md", "html", "txt"}

    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        """Convert document using AnyDoc engine with fallback."""
        try:
            src_ext = source_path.suffix.lower().lstrip(".")
            target_ext = target_path.suffix.lower().lstrip(".")
            target_path.parent.mkdir(parents=True, exist_ok=True)

            md_content: Optional[str] = None

            # Step 1: Extract/convert document into Markdown representation
            if HAS_ANYDOC and src_ext in ANYDOC_FORMATS:
                try:
                    md_content = anydoc.to_markdown(str(source_path))
                except Exception as anydoc_err:
                    # If AnyDoc encounters an unsupported sub-variant or corrupted stream, fallback below
                    md_content = None

            # Fallback for PDF if AnyDoc didn't produce content
            if md_content is None and src_ext == "pdf":
                reader = pypdf.PdfReader(str(source_path))
                extracted = []
                for i, page in enumerate(reader.pages):
                    page_text = (page.extract_text() or "").strip()
                    if len(reader.pages) > 1:
                        extracted.append(f"## Page {i+1}\n\n{page_text}")
                    else:
                        extracted.append(page_text)
                md_content = "\n\n---\n\n".join(extracted)

            # Fallback for plain text or markdown source
            if md_content is None and src_ext in ["txt", "md"]:
                md_content = source_path.read_text(encoding="utf-8")

            if md_content is None:
                print(f"[!] Could not extract content from {source_path.name}", file=sys.stderr)
                return False

            # Step 2: Write out to target format
            if target_ext == "md":
                target_path.write_text(md_content, encoding="utf-8")
                return True

            elif target_ext == "html":
                html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
                full_html = (
                    f"<!DOCTYPE html>\n<html>\n"
                    f"<head><meta charset='utf-8'><title>{source_path.stem}</title>\n"
                    f"<style>body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; "
                    f"max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333; }} "
                    f"table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }} "
                    f"th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }} "
                    f"th {{ background-color: #f2f2f2; }}</style>\n"
                    f"</head>\n<body>\n{html_body}\n</body>\n</html>"
                )
                target_path.write_text(full_html, encoding="utf-8")
                return True

            elif target_ext == "txt":
                target_path.write_text(md_content, encoding="utf-8")
                return True

            return False
        except Exception as e:
            print(f"[!] Error converting document {source_path.name}: {e}", file=sys.stderr)
            return False


# Register default instance
default_registry.register(DocumentConverter())
