"""
Markdown 문서 파서
frontmatter 지원
"""

import re
import yaml
from typing import Dict, Any, Optional

from .base_parser import BaseParser
from ..models import ParseResult, DocumentMetadata


class MarkdownParser(BaseParser):
    """Markdown 파서 (frontmatter 지원)"""
    
    def parse(self, content: bytes, metadata: DocumentMetadata) -> ParseResult:
        """Markdown 문서 파싱"""
        try:
            # UTF-8 디코딩
            text = content.decode('utf-8')
            
            # frontmatter와 본문 분리
            frontmatter, main_content = self._parse_frontmatter(text)
            
            # 메타데이터 추출
            extracted_metadata = self._extract_metadata(content, metadata.filename)
            if frontmatter:
                extracted_metadata.update(frontmatter)
            
            # Markdown 구조 분석
            headers = self._extract_headers(main_content)
            if headers:
                extracted_metadata["headers"] = headers
            
            # 텍스트 정리
            cleaned_text = self._clean_markdown_text(main_content)
            
            if not cleaned_text.strip():
                return ParseResult(
                    text="",
                    metadata=extracted_metadata,
                    success=False,
                    error_message="Markdown에서 콘텐츠를 추출할 수 없습니다"
                )
            
            return ParseResult(
                text=cleaned_text,
                metadata=extracted_metadata,
                success=True
            )
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Markdown 인코딩 오류 ({metadata.filename}): {e}")
            return ParseResult(
                text="",
                metadata=self._extract_metadata(content, metadata.filename),
                success=False,
                error_message=f"인코딩 오류: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Markdown 파싱 오류 ({metadata.filename}): {e}")
            return ParseResult(
                text="",
                metadata=self._extract_metadata(content, metadata.filename),
                success=False,
                error_message=f"Markdown 파싱 실패: {str(e)}"
            )
    
    def _parse_frontmatter(self, text: str) -> tuple[Optional[Dict[str, Any]], str]:
        """frontmatter 파싱"""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, text, re.DOTALL)
        
        if not match:
            return None, text
        
        try:
            frontmatter_text = match.group(1)
            frontmatter = yaml.safe_load(frontmatter_text)
            main_content = text[match.end():]
            return frontmatter, main_content
        except yaml.YAMLError:
            # frontmatter 파싱 실패 시 전체를 본문으로 처리
            return None, text
    
    def _extract_headers(self, text: str) -> list[Dict[str, Any]]:
        """헤더 추출"""
        headers = []
        pattern = r'^(#{1,6})\s+(.+)$'
        
        for match in re.finditer(pattern, text, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append({
                "level": level,
                "title": title,
                "position": match.start()
            })
        
        return headers
    
    def _clean_markdown_text(self, text: str) -> str:
        """Markdown 마크업 제거 및 텍스트 정리"""
        # 코드 블록 제거
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`\n]+`', '', text)
        
        # 링크 ([text](url) -> text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # 이미지 제거
        text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)
        
        # 강조 표시 제거 (**bold**, *italic*)
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*\n]+)\*', r'\1', text)
        
        # 헤더 마크 제거
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 리스트 마크 제거
        text = re.sub(r'^\s*[-\*\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 인용 마크 제거
        text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
        
        return self._clean_text(text)