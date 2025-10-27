from typing import Dict, Type
from .base import BaseParser, ParserError
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .html_parser import HTMLParser
from .csv_parser import CSVParser
from .txt_parser import TXTParser
from .markdown_parser import MarkdownParser


class ParserFactory:
    _parsers: Dict[str, Type[BaseParser]] = {
        "pdf": PDFParser,
        "docx": DOCXParser,
        "html": HTMLParser,
        "csv": CSVParser,
        "txt": TXTParser,
        "md": MarkdownParser,
        "markdown": MarkdownParser,
    }

    @classmethod
    def get_parser(cls, file_format: str) -> BaseParser:
        file_format_lower = file_format.lower()

        parser_class = cls._parsers.get(file_format_lower)

        if not parser_class:
            supported_formats = ", ".join(cls._parsers.keys())
            raise ParserError(
                f"Unsupported file format: {file_format}. "
                f"Supported formats: {supported_formats}"
            )

        try:
            return parser_class()
        except Exception as e:
            raise ParserError(
                f"Failed to initialize parser for {file_format}: {str(e)}"
            )

    @classmethod
    def supports_format(cls, file_format: str) -> bool:
        return file_format.lower() in cls._parsers

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        return list(cls._parsers.keys())
