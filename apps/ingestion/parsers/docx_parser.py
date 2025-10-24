import io
from typing import Optional

from .base import BaseParser, ParserError

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DOCXParser(BaseParser):
    def __init__(self):
        if not DOCX_AVAILABLE:
            raise ParserError("python-docx not installed")

    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        try:
            docx_stream = io.BytesIO(file_content)
            document = Document(docx_stream)

            paragraphs = []
            for paragraph in document.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)

            if not paragraphs:
                raise ParserError("DOCX parsing resulted in empty content")

            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ParserError(f"DOCX parsing failed: {str(e)}")

    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() == "docx"
