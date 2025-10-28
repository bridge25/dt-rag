import io
from typing import Optional
from .base import BaseParser, ParserError

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class CSVParser(BaseParser):
    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def __init__(self) -> None:
        if not PANDAS_AVAILABLE:
            raise ParserError("pandas not installed")

    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        try:
            csv_stream = io.BytesIO(file_content)
            df = pd.read_csv(csv_stream, encoding="utf-8-sig")

            if df.empty:
                raise ParserError("CSV parsing resulted in empty content")

            markdown_table = df.to_markdown(index=False)

            return markdown_table
        except Exception as e:
            raise ParserError(f"CSV parsing failed: {str(e)}")

    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() == "csv"
