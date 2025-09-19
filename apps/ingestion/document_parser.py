"""
Document Parser Module

다양한 문서 포맷을 파싱하는 모듈
- PDF 파서 (PyPDF2, pdfplumber)
- Markdown 파서
- HTML 파서 (BeautifulSoup)
- 텍스트 파일 파서
- CSV 파서
- JSON 파서
- URL 스크래핑 파서
"""

import os
import hashlib
import mimetypes
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, BinaryIO, TextIO
from pathlib import Path
import logging
from datetime import datetime
import asyncio
import aiofiles
import aiohttp
import chardet

# PDF 처리
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# HTML 처리
try:
    from bs4 import BeautifulSoup, NavigableString
    import html2text
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

# CSV/JSON 처리
import json
import csv
from io import StringIO

# Markdown 처리
try:
    import markdown
    from markdown.extensions import codehilite, tables, fenced_code
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

logger = logging.getLogger(__name__)

class ParsedDocument:
    """파싱된 문서를 나타내는 클래스"""

    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        source_type: str,
        encoding: str = "utf-8"
    ):
        self.content = content
        self.metadata = metadata
        self.source_type = source_type
        self.encoding = encoding
        self.processed_at = datetime.utcnow()

    def get_checksum(self) -> str:
        """콘텐츠의 체크섬 생성"""
        return hashlib.sha256(self.content.encode(self.encoding)).hexdigest()

    def get_file_size(self) -> int:
        """콘텐츠 크기 반환 (바이트)"""
        return len(self.content.encode(self.encoding))

class DocumentParser(ABC):
    """문서 파서 추상 기본 클래스"""

    @abstractmethod
    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        """파싱 가능 여부 확인"""
        pass

    @abstractmethod
    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        """문서 파싱 실행"""
        pass

    def _detect_encoding(self, content: bytes) -> str:
        """인코딩 감지"""
        try:
            result = chardet.detect(content)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)

            # 신뢰도가 낮으면 UTF-8 사용
            if confidence < 0.7:
                encoding = 'utf-8'

            return encoding
        except Exception:
            return 'utf-8'

    def _get_mime_type(self, file_path: Union[str, Path]) -> str:
        """MIME 타입 추출"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

class TextParser(DocumentParser):
    """일반 텍스트 파일 파서"""

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.suffix.lower() in ['.txt', '.text'] or path.name.lower().endswith('.txt')
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            async with aiofiles.open(path, 'rb') as f:
                content_bytes = await f.read()
        else:
            content_bytes = source.read()
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode('utf-8')

        # 인코딩 감지 및 텍스트 변환
        encoding = self._detect_encoding(content_bytes)
        try:
            content = content_bytes.decode(encoding)
        except UnicodeDecodeError:
            content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'utf-8'

        metadata = {
            'parser': 'TextParser',
            'encoding': encoding,
            'original_filename': str(source) if isinstance(source, (str, Path)) else 'unknown',
            'mime_type': self._get_mime_type(source) if isinstance(source, (str, Path)) else 'text/plain'
        }

        return ParsedDocument(
            content=content.strip(),
            metadata=metadata,
            source_type='text',
            encoding=encoding
        )

class PDFParser(DocumentParser):
    """PDF 파일 파서"""

    def __init__(self, prefer_pdfplumber: bool = True):
        self.prefer_pdfplumber = prefer_pdfplumber
        if not PDF_AVAILABLE:
            raise ImportError("PDF 파싱을 위해 PyPDF2와 pdfplumber 설치가 필요합니다: pip install PyPDF2 pdfplumber")

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, (str, Path)):
            return Path(source).suffix.lower() == '.pdf'
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            async with aiofiles.open(path, 'rb') as f:
                content_bytes = await f.read()
        else:
            content_bytes = source.read()

        # pdfplumber 우선 시도
        content = ""
        metadata = {'parser': 'PDFParser'}

        if self.prefer_pdfplumber:
            try:
                content = await self._parse_with_pdfplumber(content_bytes)
                metadata['extraction_method'] = 'pdfplumber'
            except Exception as e:
                logger.warning(f"pdfplumber 파싱 실패, PyPDF2로 대체: {e}")
                content = await self._parse_with_pypdf2(content_bytes)
                metadata['extraction_method'] = 'PyPDF2'
        else:
            try:
                content = await self._parse_with_pypdf2(content_bytes)
                metadata['extraction_method'] = 'PyPDF2'
            except Exception as e:
                logger.warning(f"PyPDF2 파싱 실패, pdfplumber로 대체: {e}")
                content = await self._parse_with_pdfplumber(content_bytes)
                metadata['extraction_method'] = 'pdfplumber'

        metadata.update({
            'original_filename': str(source) if isinstance(source, (str, Path)) else 'unknown.pdf',
            'mime_type': 'application/pdf',
            'text_length': len(content)
        })

        return ParsedDocument(
            content=content.strip(),
            metadata=metadata,
            source_type='pdf'
        )

    async def _parse_with_pdfplumber(self, content_bytes: bytes) -> str:
        """pdfplumber를 사용한 PDF 파싱"""
        from io import BytesIO

        text_parts = []
        with pdfplumber.open(BytesIO(content_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num} ---\n{text}\n")
                except Exception as e:
                    logger.warning(f"페이지 {page_num} 추출 실패: {e}")

        return "\n".join(text_parts)

    async def _parse_with_pypdf2(self, content_bytes: bytes) -> str:
        """PyPDF2를 사용한 PDF 파싱"""
        from io import BytesIO

        text_parts = []
        reader = PyPDF2.PdfReader(BytesIO(content_bytes))

        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num} ---\n{text}\n")
            except Exception as e:
                logger.warning(f"페이지 {page_num} 추출 실패: {e}")

        return "\n".join(text_parts)

class HTMLParser(DocumentParser):
    """HTML 파일 파서"""

    def __init__(self, preserve_formatting: bool = False):
        self.preserve_formatting = preserve_formatting
        if not HTML_AVAILABLE:
            raise ImportError("HTML 파싱을 위해 beautifulsoup4와 html2text 설치가 필요합니다: pip install beautifulsoup4 html2text")

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.suffix.lower() in ['.html', '.htm']
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            async with aiofiles.open(path, 'rb') as f:
                content_bytes = await f.read()
        else:
            content_bytes = source.read()
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode('utf-8')

        # 인코딩 감지
        encoding = self._detect_encoding(content_bytes)
        try:
            html_content = content_bytes.decode(encoding)
        except UnicodeDecodeError:
            html_content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'utf-8'

        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(html_content, 'html.parser')

        # 메타데이터 추출
        title = soup.find('title')
        title_text = title.get_text() if title else None

        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content') if meta_description else None

        # 텍스트 추출
        if self.preserve_formatting:
            # html2text 사용하여 마크다운 스타일로 변환
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            content = h.handle(html_content)
        else:
            # 스크립트/스타일 태그 제거
            for script in soup(["script", "style"]):
                script.decompose()

            # 텍스트만 추출
            content = soup.get_text()
            # 여러 줄바꿈을 하나로 정리
            lines = (line.strip() for line in content.splitlines())
            content = '\n'.join(line for line in lines if line)

        metadata = {
            'parser': 'HTMLParser',
            'encoding': encoding,
            'title': title_text,
            'description': description,
            'preserve_formatting': self.preserve_formatting,
            'original_filename': str(source) if isinstance(source, (str, Path)) else 'unknown.html',
            'mime_type': 'text/html'
        }

        return ParsedDocument(
            content=content.strip(),
            metadata=metadata,
            source_type='html',
            encoding=encoding
        )

class MarkdownParser(DocumentParser):
    """Markdown 파일 파서"""

    def __init__(self, render_to_html: bool = False):
        self.render_to_html = render_to_html
        if render_to_html and not MARKDOWN_AVAILABLE:
            raise ImportError("Markdown 렌더링을 위해 markdown 설치가 필요합니다: pip install markdown")

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.suffix.lower() in ['.md', '.markdown']
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            async with aiofiles.open(path, 'rb') as f:
                content_bytes = await f.read()
        else:
            content_bytes = source.read()
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode('utf-8')

        # 인코딩 감지
        encoding = self._detect_encoding(content_bytes)
        try:
            md_content = content_bytes.decode(encoding)
        except UnicodeDecodeError:
            md_content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'utf-8'

        # 메타데이터 추출 (첫 번째 헤딩을 제목으로)
        lines = md_content.split('\n')
        title = None
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # 내용 처리
        if self.render_to_html:
            # HTML로 렌더링
            md = markdown.Markdown(extensions=['codehilite', 'tables', 'fenced_code'])
            content = md.convert(md_content)
        else:
            # 마크다운 그대로 유지
            content = md_content

        metadata = {
            'parser': 'MarkdownParser',
            'encoding': encoding,
            'title': title,
            'render_to_html': self.render_to_html,
            'original_filename': str(source) if isinstance(source, (str, Path)) else 'unknown.md',
            'mime_type': 'text/markdown'
        }

        return ParsedDocument(
            content=content.strip(),
            metadata=metadata,
            source_type='markdown',
            encoding=encoding
        )

class CSVParser(DocumentParser):
    """CSV 파일 파서"""

    def __init__(self, max_rows: int = 10000, include_headers: bool = True):
        self.max_rows = max_rows
        self.include_headers = include_headers

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, (str, Path)):
            return Path(source).suffix.lower() == '.csv'
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            async with aiofiles.open(path, 'rb') as f:
                content_bytes = await f.read()
        else:
            content_bytes = source.read()
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode('utf-8')

        # 인코딩 감지
        encoding = self._detect_encoding(content_bytes)
        try:
            csv_content = content_bytes.decode(encoding)
        except UnicodeDecodeError:
            csv_content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'utf-8'

        # CSV 파싱
        csv_reader = csv.DictReader(StringIO(csv_content))

        rows = []
        headers = csv_reader.fieldnames or []

        for i, row in enumerate(csv_reader):
            if i >= self.max_rows:
                break
            rows.append(row)

        # 텍스트 형태로 변환
        content_parts = []

        if self.include_headers and headers:
            content_parts.append("Headers: " + ", ".join(headers))
            content_parts.append("")

        for i, row in enumerate(rows):
            row_text = f"Row {i+1}:"
            for key, value in row.items():
                if value:
                    row_text += f"\n  {key}: {value}"
            content_parts.append(row_text)
            content_parts.append("")

        metadata = {
            'parser': 'CSVParser',
            'encoding': encoding,
            'headers': headers,
            'total_rows': len(rows),
            'max_rows_limit': self.max_rows,
            'original_filename': str(source) if isinstance(source, (str, Path)) else 'unknown.csv',
            'mime_type': 'text/csv'
        }

        return ParsedDocument(
            content="\n".join(content_parts).strip(),
            metadata=metadata,
            source_type='csv',
            encoding=encoding
        )

class JSONParser(DocumentParser):
    """JSON 파일 파서"""

    def __init__(self, flatten_nested: bool = True, max_depth: int = 10):
        self.flatten_nested = flatten_nested
        self.max_depth = max_depth

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, (str, Path)):
            return Path(source).suffix.lower() == '.json'
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            async with aiofiles.open(path, 'rb') as f:
                content_bytes = await f.read()
        else:
            content_bytes = source.read()
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode('utf-8')

        # 인코딩 감지
        encoding = self._detect_encoding(content_bytes)
        try:
            json_content = content_bytes.decode(encoding)
        except UnicodeDecodeError:
            json_content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'utf-8'

        # JSON 파싱
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {e}")

        # 텍스트 형태로 변환
        if self.flatten_nested:
            content = self._flatten_json_to_text(data)
        else:
            content = json.dumps(data, indent=2, ensure_ascii=False)

        metadata = {
            'parser': 'JSONParser',
            'encoding': encoding,
            'data_type': type(data).__name__,
            'flatten_nested': self.flatten_nested,
            'original_filename': str(source) if isinstance(source, (str, Path)) else 'unknown.json',
            'mime_type': 'application/json'
        }

        return ParsedDocument(
            content=content.strip(),
            metadata=metadata,
            source_type='json',
            encoding=encoding
        )

    def _flatten_json_to_text(self, data: Any, prefix: str = "", depth: int = 0) -> str:
        """JSON 데이터를 평면적인 텍스트로 변환"""
        if depth > self.max_depth:
            return f"{prefix}: [Max depth reached]"

        parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                parts.append(self._flatten_json_to_text(value, new_prefix, depth + 1))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}[{i}]" if prefix else f"[{i}]"
                parts.append(self._flatten_json_to_text(item, new_prefix, depth + 1))
        else:
            return f"{prefix}: {str(data)}"

        return "\n".join(parts)

class URLParser(DocumentParser):
    """URL 스크래핑 파서"""

    def __init__(self, timeout: int = 30, max_size: int = 10 * 1024 * 1024):  # 10MB
        self.timeout = timeout
        self.max_size = max_size

    def can_parse(self, source: Union[str, Path, BinaryIO]) -> bool:
        if isinstance(source, str):
            return source.startswith(('http://', 'https://'))
        return False

    async def parse(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        if not isinstance(source, str):
            raise ValueError("URL 파서는 문자열 URL만 처리할 수 있습니다")

        url = source

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP 오류: {response.status}")

                content_type = response.headers.get('content-type', '').lower()
                content_length = response.headers.get('content-length')

                if content_length and int(content_length) > self.max_size:
                    raise ValueError(f"콘텐츠 크기가 너무 큽니다: {content_length} bytes")

                content_bytes = await response.read()

                if len(content_bytes) > self.max_size:
                    raise ValueError(f"다운로드된 콘텐츠 크기가 너무 큽니다: {len(content_bytes)} bytes")

        # Content-Type에 따라 적절한 파서 선택
        if 'text/html' in content_type:
            parser = HTMLParser()
            encoding = self._detect_encoding(content_bytes)
            html_content = content_bytes.decode(encoding, errors='replace')

            soup = BeautifulSoup(html_content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()

            content = soup.get_text()
            lines = (line.strip() for line in content.splitlines())
            content = '\n'.join(line for line in lines if line)

            title = soup.find('title')
            title_text = title.get_text() if title else None

        elif 'application/json' in content_type:
            encoding = self._detect_encoding(content_bytes)
            json_content = content_bytes.decode(encoding, errors='replace')
            data = json.loads(json_content)
            content = json.dumps(data, indent=2, ensure_ascii=False)
            title_text = None

        else:
            # 일반 텍스트로 처리
            encoding = self._detect_encoding(content_bytes)
            content = content_bytes.decode(encoding, errors='replace')
            title_text = None

        metadata = {
            'parser': 'URLParser',
            'url': url,
            'content_type': content_type,
            'content_length': len(content_bytes),
            'title': title_text,
            'original_filename': url.split('/')[-1] or 'webpage',
            'mime_type': content_type.split(';')[0]
        }

        return ParsedDocument(
            content=content.strip(),
            metadata=metadata,
            source_type='url'
        )

class DocumentParserFactory:
    """문서 파서 팩토리"""

    def __init__(self):
        self.parsers: List[DocumentParser] = []
        self._register_default_parsers()

    def _register_default_parsers(self):
        """기본 파서들 등록"""
        # 우선순위 순으로 등록
        try:
            self.parsers.append(PDFParser())
        except ImportError:
            logger.warning("PDF 파서를 사용할 수 없습니다. PyPDF2와 pdfplumber를 설치하세요.")

        try:
            self.parsers.append(HTMLParser())
        except ImportError:
            logger.warning("HTML 파서를 사용할 수 없습니다. beautifulsoup4를 설치하세요.")

        try:
            self.parsers.append(MarkdownParser())
        except ImportError:
            logger.warning("Markdown HTML 렌더링을 사용할 수 없습니다. markdown 패키지를 설치하세요.")
            # 기본 마크다운 파서는 여전히 사용 가능
            self.parsers.append(MarkdownParser(render_to_html=False))

        self.parsers.extend([
            CSVParser(),
            JSONParser(),
            URLParser(),
            TextParser()  # 마지막에 추가 (가장 일반적)
        ])

    def register_parser(self, parser: DocumentParser, priority: int = -1):
        """커스텀 파서 등록"""
        if priority == -1:
            self.parsers.append(parser)
        else:
            self.parsers.insert(priority, parser)

    def get_parser(self, source: Union[str, Path, BinaryIO]) -> Optional[DocumentParser]:
        """소스에 적합한 파서 찾기"""
        for parser in self.parsers:
            if parser.can_parse(source):
                return parser
        return None

    async def parse_document(self, source: Union[str, Path, BinaryIO]) -> ParsedDocument:
        """문서 파싱 실행"""
        parser = self.get_parser(source)
        if not parser:
            raise ValueError(f"지원되지 않는 문서 타입: {source}")

        try:
            return await parser.parse(source)
        except Exception as e:
            logger.error(f"문서 파싱 실패 ({parser.__class__.__name__}): {e}")
            raise

    def get_supported_extensions(self) -> List[str]:
        """지원되는 파일 확장자 목록"""
        extensions = []
        test_sources = [
            Path("test.txt"),
            Path("test.pdf"),
            Path("test.html"),
            Path("test.md"),
            Path("test.csv"),
            Path("test.json"),
            "https://example.com"
        ]

        for source in test_sources:
            for parser in self.parsers:
                if parser.can_parse(source):
                    if isinstance(source, Path):
                        extensions.append(source.suffix)
                    elif isinstance(source, str) and source.startswith('http'):
                        extensions.append('URL')
                    break

        return list(set(extensions))

# 싱글톤 팩토리 인스턴스
_parser_factory = None

def get_parser_factory() -> DocumentParserFactory:
    """문서 파서 팩토리 싱글톤 인스턴스 반환"""
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = DocumentParserFactory()
    return _parser_factory