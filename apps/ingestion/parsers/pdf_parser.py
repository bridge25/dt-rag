"""
PDF document parser.

@CODE:INGESTION-001
"""
import io
from typing import Optional
from .base import BaseParser, ParserError

try:
    import pymupdf
    import pymupdf4llm

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFParser(BaseParser):
    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    # @CODE:INGESTION-001
    def __init__(self) -> None:
        if not PYMUPDF_AVAILABLE:
            raise ParserError("pymupdf and pymupdf4llm not installed")

    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
            markdown_text: str = pymupdf4llm.to_markdown(doc)

            if not markdown_text or not markdown_text.strip():
                raise ParserError("PDF parsing resulted in empty content")

            return markdown_text
        except Exception as e:
            raise ParserError(f"PDF parsing failed: {str(e)}")

    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() == "pdf"
