"""
HTML 문서 파서  
BeautifulSoup 사용
"""

from bs4 import BeautifulSoup, Comment
from typing import Dict, Any

from .base_parser import BaseParser
from ..models import ParseResult, DocumentMetadata


class HTMLParser(BaseParser):
    """HTML 파서 (BeautifulSoup 기반)"""
    
    def parse(self, content: bytes, metadata: DocumentMetadata) -> ParseResult:
        """HTML 문서 파싱"""
        try:
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(content, 'html.parser')
            
            # 메타데이터 추출
            extracted_metadata = self._extract_html_metadata(soup)
            extracted_metadata.update(self._extract_metadata(content, metadata.filename))
            
            # 불필요한 요소 제거
            self._remove_unwanted_elements(soup)
            
            # 텍스트 추출
            text = soup.get_text(separator=' ', strip=True)
            text = self._clean_text(text)
            
            if not text.strip():
                return ParseResult(
                    text="",
                    metadata=extracted_metadata,
                    success=False,
                    error_message="HTML에서 콘텐츠를 추출할 수 없습니다"
                )
            
            return ParseResult(
                text=text,
                metadata=extracted_metadata,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"HTML 파싱 오류 ({metadata.filename}): {e}")
            return ParseResult(
                text="",
                metadata=self._extract_metadata(content, metadata.filename),
                success=False,
                error_message=f"HTML 파싱 실패: {str(e)}"
            )
    
    def _extract_html_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """HTML 메타데이터 추출"""
        metadata = {"parser": "HTMLParser"}
        
        # 제목
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # 메타 태그들
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            
            if name and content:
                # 주요 메타데이터만 추출
                if name in ['description', 'keywords', 'author', 'viewport']:
                    metadata[name] = content
                elif name.startswith('og:'):  # Open Graph
                    metadata[name] = content
        
        # 헤더 구조 추출
        headers = []
        for level in range(1, 7):
            header_tags = soup.find_all(f'h{level}')
            for tag in header_tags:
                headers.append({
                    "level": level,
                    "text": tag.get_text().strip()
                })
        
        if headers:
            metadata["headers"] = headers
        
        return metadata
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """불필요한 HTML 요소 제거"""
        # 제거할 태그들
        unwanted_tags = [
            'script', 'style', 'nav', 'footer', 'aside',
            'advertisement', 'ads', 'sidebar'
        ]
        
        for tag_name in unwanted_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 주석 제거
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # 클래스명으로 제거
        unwanted_classes = [
            'navigation', 'nav', 'sidebar', 'advertisement', 'ads',
            'footer', 'header', 'menu', 'social', 'share'
        ]
        
        for class_name in unwanted_classes:
            for tag in soup.find_all(class_=class_name):
                tag.decompose()