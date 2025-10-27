from typing import Optional
from .base import BaseParser, ParserError

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class HTMLParser(BaseParser):
    def __init__(self):
        if not BS4_AVAILABLE:
            raise ParserError("beautifulsoup4 not installed")

    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        try:
            html_text = file_content.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html_text, "lxml")

            for script_or_style in soup(["script", "style", "meta", "link"]):
                script_or_style.decompose()

            text = soup.get_text(separator="\n", strip=True)

            lines = [line.strip() for line in text.split("\n") if line.strip()]

            if not lines:
                raise ParserError("HTML parsing resulted in empty content")

            return "\n".join(lines)
        except Exception as e:
            raise ParserError(f"HTML parsing failed: {str(e)}")

    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() == "html"
