from typing import Optional

from .base import BaseParser, ParserError


class TXTParser(BaseParser):
    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        try:
            text = file_content.decode("utf-8", errors="ignore")

            text = text.strip()

            if not text:
                raise ParserError("TXT parsing resulted in empty content")

            return text
        except Exception as e:
            raise ParserError(f"TXT parsing failed: {str(e)}")

    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() == "txt"
