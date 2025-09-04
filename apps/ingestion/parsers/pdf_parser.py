"""
PDF 문서 파서
PyMuPDF 사용
"""

import fitz  # PyMuPDF
from typing import Dict, Any

from .base_parser import BaseParser
from ..models import ParseResult, DocumentMetadata


class PDFParser(BaseParser):
    """PDF 파서 (PyMuPDF 기반)"""
    
    def parse(self, content: bytes, metadata: DocumentMetadata) -> ParseResult:
        """PDF 문서 파싱"""
        try:
            # PDF 문서 열기
            doc = fitz.open(stream=content, filetype="pdf")
            
            # 모든 페이지에서 텍스트 추출
            text_parts = []
            extracted_metadata = {}
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            
            # 전체 텍스트 결합
            full_text = "\n".join(text_parts)
            full_text = self._clean_text(full_text)
            
            # PDF 메타데이터 추출
            pdf_metadata = doc.metadata
            extracted_metadata.update({
                "title": pdf_metadata.get("title", ""),
                "author": pdf_metadata.get("author", ""),
                "creator": pdf_metadata.get("creator", ""),
                "producer": pdf_metadata.get("producer", ""),
                "creation_date": pdf_metadata.get("creationDate", ""),
                "modification_date": pdf_metadata.get("modDate", ""),
                "page_count": len(doc),
                "parser": "PDFParser"
            })
            
            doc.close()
            
            if not full_text.strip():
                return ParseResult(
                    text="",
                    metadata=extracted_metadata,
                    success=False,
                    error_message="PDF에서 텍스트를 추출할 수 없습니다"
                )
            
            return ParseResult(
                text=full_text,
                metadata=extracted_metadata,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"PDF 파싱 오류 ({metadata.filename}): {e}")
            return ParseResult(
                text="",
                metadata=self._extract_metadata(content, metadata.filename),
                success=False,
                error_message=f"PDF 파싱 실패: {str(e)}"
            )