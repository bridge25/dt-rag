"""
Base parser interface for document processing.

@CODE:INGESTION-001
"""
from abc import ABC, abstractmethod
from typing import Optional


class ParserError(Exception):
    pass


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def supports_format(self, file_format: str) -> bool:
        pass
