"""
문서 파서 기본 클래스
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from ..models import ParseResult, DocumentMetadata

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """문서 파서 기본 클래스"""
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    def parse(self, content: bytes, metadata: DocumentMetadata) -> ParseResult:
        """문서 파싱"""
        pass
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 연속된 공백 제거
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _extract_metadata(self, content: bytes, filename: str) -> Dict[str, Any]:
        """기본 메타데이터 추출"""
        return {
            "filename": filename,
            "size_bytes": len(content),
            "parser": self.__class__.__name__
        }