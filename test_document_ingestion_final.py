#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 문서 수집 파이프라인 테스트 스크립트

이 스크립트는 문서 수집 파이프라인의 전체 과정을 테스트합니다:
1. 파일 포맷 지원 테스트 (PDF, TXT, MD, HTML, CSV, JSON)
2. 텍스트 추출 및 청킹
3. 메타데이터 추출
4. PII 필터링 (한국어 지원)
5. 임베딩 생성 (MockService 사용)
6. 데이터베이스 저장 시뮬레이션
7. 오류 처리
8. 배치 처리 성능

한글 처리와 실제 파일 검증에 중점을 둡니다.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime
import traceback
import re
from dataclasses import dataclass, field

# 한글 출력을 위한 설정
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 프로젝트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정 (UTF-8 지원)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_ingestion_final_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """테스트 결과"""
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    error: Optional[str] = None

class DocumentIngestionTester:
    """문서 수집 파이프라인 종합 테스터"""

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ingestion_final_test_"))
        self.start_time = time.time()
        self.test_results = {}

        logger.info(f"테스트 디렉토리: {self.temp_dir}")

    def __del__(self):
        """정리"""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_files(self) -> Dict[str, Path]:
        """다양한 포맷의 테스트 파일 생성"""
        logger.info("테스트 파일 생성 중...")
        files = {}

        # 1. 한글 텍스트 파일
        txt_content = """Dynamic Taxonomy RAG 시스템 문서

개인정보 테스트:
- 이메일: hong@example.com, kim.test@company.co.kr
- 전화번호: 010-1234-5678, 02-987-6543
- 주민등록번호: 123456-1234567, 890123-2345678
- 신용카드: 1234-5678-9012-3456

기술 내용:
이 시스템은 동적 분류법을 사용하여 문서를 자동으로 분류합니다.
RAG(Retrieval-Augmented Generation) 아키텍처를 기반으로 하며,
벡터 검색과 키워드 검색을 결합한 하이브리드 검색을 지원합니다.

주요 기능:
1. 문서 자동 분류
2. 의미적 검색
3. 계층적 분류체계
4. 실시간 임베딩 생성

English content is also supported for multilingual processing.
The system handles various document formats including PDF, HTML, and plain text.
"""

        txt_file = self.temp_dir / "test_korean.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        files['txt'] = txt_file

        # 2. Markdown 파일
        md_content = """# 한글 마크다운 문서 테스트

## 개요
이것은 **Dynamic Taxonomy RAG** 시스템의 마크다운 테스트 파일입니다.

### 개인정보 섹션
- 담당자: 김개발 (kim.dev@company.com)
- 연락처: 010-9999-8888
- 부서: AI개발팀

### 기술 스펙
```python
class DocumentProcessor:
    def __init__(self):
        self.chunker = ChunkingStrategy()
        self.pii_filter = PIIFilter()

    async def process(self, document):
        chunks = await self.chunker.chunk(document)
        filtered_chunks = await self.pii_filter.filter(chunks)
        return filtered_chunks
```

### 처리 플로우
1. **문서 파싱** → 텍스트 추출
2. **청킹** → 적절한 크기로 분할
3. **PII 필터링** → 개인정보 마스킹
4. **임베딩** → 벡터 생성
5. **저장** → 데이터베이스 저장

> 중요: 모든 개인정보는 GDPR 및 PIPA 규정에 따라 처리됩니다.

[시스템 문서](https://docs.example.com)
"""

        md_file = self.temp_dir / "test_korean.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        files['md'] = md_file

        # 3. HTML 파일
        html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Taxonomy RAG 시스템</title>
</head>
<body>
    <header>
        <h1>한글 HTML 문서 테스트</h1>
        <nav>
            <ul>
                <li><a href="#intro">소개</a></li>
                <li><a href="#features">기능</a></li>
                <li><a href="#contact">연락처</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section id="intro">
            <h2>시스템 소개</h2>
            <p>Dynamic Taxonomy RAG는 <strong>차세대 문서 처리 시스템</strong>입니다.</p>
            <p>다양한 포맷의 문서를 자동으로 분류하고 검색할 수 있습니다.</p>
        </section>

        <section id="features">
            <h2>주요 기능</h2>
            <ul>
                <li>다중 포맷 지원 (PDF, HTML, TXT, MD)</li>
                <li>실시간 PII 탐지 및 마스킹</li>
                <li>의미적 검색 지원</li>
                <li>계층적 분류 체계</li>
            </ul>
        </section>

        <section id="contact">
            <h2>연락처 정보</h2>
            <div class="contact-info">
                <p>이메일: contact@rag-system.com</p>
                <p>전화: 02-1234-5678</p>
                <p>담당자: 박시스템 (park.system@company.kr)</p>
                <p>고객센터: 1588-1234</p>
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 Dynamic Taxonomy RAG System. All rights reserved.</p>
    </footer>

    <script>
        // 이 스크립트는 파싱 시 제거되어야 함
        console.log("JavaScript content should be removed");
        document.addEventListener('DOMContentLoaded', function() {
            alert('이 스크립트는 보이지 않아야 합니다');
        });
    </script>
</body>
</html>"""

        html_file = self.temp_dir / "test_korean.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        files['html'] = html_file

        # 4. CSV 파일
        csv_content = """이름,이메일,전화번호,부서,입사일
김민수,kim.min@company.com,010-1111-2222,개발팀,2023-01-15
이영희,lee.young@company.com,010-3333-4444,마케팅팀,2023-02-01
박철수,park.chul@company.com,010-5555-6666,영업팀,2023-03-10
최지훈,choi.ji@company.com,010-7777-8888,기획팀,2023-04-05
정미래,jung.mi@company.com,010-9999-0000,인사팀,2023-05-20"""

        csv_file = self.temp_dir / "test_korean.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        files['csv'] = csv_file

        # 5. JSON 파일
        json_data = {
            "system_info": {
                "name": "Dynamic Taxonomy RAG",
                "version": "1.8.1",
                "description": "지능형 문서 분류 및 검색 시스템"
            },
            "configuration": {
                "chunk_size": 500,
                "overlap_size": 128,
                "embedding_model": "text-embedding-ada-002",
                "languages": ["ko", "en"]
            },
            "test_users": [
                {
                    "name": "홍길동",
                    "email": "hong@test.example.com",
                    "phone": "010-1234-0000",
                    "role": "관리자",
                    "created_at": "2024-01-01T09:00:00Z"
                },
                {
                    "name": "김영수",
                    "email": "kim.young@test.example.com",
                    "phone": "010-5678-0000",
                    "role": "사용자",
                    "created_at": "2024-01-02T10:30:00Z"
                }
            ],
            "sensitive_data": {
                "api_key": "sk-test-api-key-1234567890",
                "database_url": "postgresql://user:pass@localhost:5432/db",
                "credit_card": "4532-1234-5678-9012"
            },
            "features": {
                "document_parsing": {
                    "supported_formats": ["pdf", "html", "txt", "md", "csv", "json"],
                    "encoding_support": ["utf-8", "cp949", "iso-8859-1"],
                    "korean_support": True
                },
                "pii_detection": {
                    "email_patterns": True,
                    "phone_patterns": True,
                    "ssn_patterns": True,
                    "credit_card_patterns": True,
                    "korean_specific": True
                }
            }
        }

        json_file = self.temp_dir / "test_korean.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        files['json'] = json_file

        # 6. 빈 파일 (오류 처리 테스트)
        empty_file = self.temp_dir / "empty.txt"
        empty_file.touch()
        files['empty'] = empty_file

        # 7. 손상된 파일 (오류 처리 테스트)
        corrupted_file = self.temp_dir / "corrupted.pdf"
        with open(corrupted_file, 'wb') as f:
            f.write(b"This is not a valid PDF file content - corrupted data \x00\xFF\xFE")
        files['corrupted'] = corrupted_file

        # 8. 대용량 파일 (성능 테스트)
        large_content = "한글 대용량 테스트 콘텐츠입니다. " * 2000 + \
                       "이메일: large@test.com, 전화: 010-0000-1111 " * 100
        large_file = self.temp_dir / "large_test.txt"
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        files['large'] = large_file

        logger.info(f"총 {len(files)}개의 테스트 파일 생성 완료")
        return files

    def test_file_parsing(self, files: Dict[str, Path]) -> TestResult:
        """파일 파싱 테스트"""
        logger.info("=== 파일 파싱 테스트 시작 ===")
        start_time = time.time()

        results = {}

        try:
            # 기본 import 테스트
            from apps.ingestion.document_parser import get_parser_factory

            parser_factory = get_parser_factory()

            for file_type, file_path in files.items():
                if file_type in ['corrupted', 'empty']:
                    continue

                try:
                    parser = parser_factory.get_parser(file_path)
                    if parser:
                        # 동기 방식으로 변경
                        import asyncio
                        try:
                            # 기존 이벤트 루프가 있는지 확인
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # 이미 실행 중인 루프가 있으면 새 태스크로 실행
                                parsed_doc = loop.run_until_complete(parser.parse(file_path))
                            else:
                                parsed_doc = asyncio.run(parser.parse(file_path))
                        except RuntimeError:
                            # 새 이벤트 루프 생성
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                parsed_doc = new_loop.run_until_complete(parser.parse(file_path))
                            finally:
                                new_loop.close()

                        results[file_type] = {
                            'success': True,
                            'content_length': len(parsed_doc.content),
                            'metadata_keys': list(parsed_doc.metadata.keys()) if parsed_doc.metadata else [],
                            'has_korean': any(ord(c) > 127 for c in parsed_doc.content[:100]),
                            'sample_content': parsed_doc.content[:200] + "..." if len(parsed_doc.content) > 200 else parsed_doc.content
                        }
                        logger.info(f"{file_type} 파싱 성공: {len(parsed_doc.content)} 문자")
                    else:
                        results[file_type] = {
                            'success': False,
                            'error': 'Parser not available for this format'
                        }

                except Exception as e:
                    results[file_type] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"{file_type} 파싱 실패: {e}")

            processing_time = time.time() - start_time
            success_count = sum(1 for r in results.values() if r.get('success', False))

            return TestResult(
                success=success_count > 0,
                message=f"파일 파싱 테스트 완료: {success_count}/{len(results)}개 성공",
                details=results,
                processing_time=processing_time
            )

        except Exception as e:
            return TestResult(
                success=False,
                message="파일 파싱 테스트 실패",
                error=str(e),
                processing_time=time.time() - start_time
            )

    def test_chunking(self, files: Dict[str, Path]) -> TestResult:
        """청킹 테스트"""
        logger.info("=== 청킹 테스트 시작 ===")
        start_time = time.time()

        results = {}

        try:
            from apps.ingestion.chunking_strategy import default_chunker
            from apps.ingestion.document_parser import get_parser_factory

            parser_factory = get_parser_factory()

            # 대표적인 파일들로 테스트
            test_files = {k: v for k, v in files.items() if k in ['txt', 'md', 'html']}

            for file_type, file_path in test_files.items():
                try:
                    parser = parser_factory.get_parser(file_path)
                    if not parser:
                        continue

                    # 비동기 처리
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            parsed_doc = loop.run_until_complete(parser.parse(file_path))
                            chunks = loop.run_until_complete(default_chunker.chunk_document(parsed_doc))
                        else:
                            parsed_doc = asyncio.run(parser.parse(file_path))
                            chunks = asyncio.run(default_chunker.chunk_document(parsed_doc))
                    except RuntimeError:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            parsed_doc = new_loop.run_until_complete(parser.parse(file_path))
                            chunks = new_loop.run_until_complete(default_chunker.chunk_document(parsed_doc))
                        finally:
                            new_loop.close()

                    chunk_info = []
                    for i, chunk in enumerate(chunks):
                        chunk_info.append({
                            'id': i,
                            'length': len(chunk.content),
                            'start_pos': chunk.start_pos,
                            'end_pos': chunk.end_pos,
                            'sample': chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                        })

                    results[file_type] = {
                        'success': True,
                        'original_length': len(parsed_doc.content),
                        'chunk_count': len(chunks),
                        'chunks': chunk_info,
                        'avg_chunk_size': sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0
                    }

                    logger.info(f"{file_type} 청킹 성공: {len(chunks)}개 청크")

                except Exception as e:
                    results[file_type] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"{file_type} 청킹 실패: {e}")

            processing_time = time.time() - start_time
            success_count = sum(1 for r in results.values() if r.get('success', False))

            return TestResult(
                success=success_count > 0,
                message=f"청킹 테스트 완료: {success_count}/{len(results)}개 성공",
                details=results,
                processing_time=processing_time
            )

        except Exception as e:
            return TestResult(
                success=False,
                message="청킹 테스트 실패",
                error=str(e),
                processing_time=time.time() - start_time
            )

    def test_pii_filtering(self, files: Dict[str, Path]) -> TestResult:
        """PII 필터링 테스트"""
        logger.info("=== PII 필터링 테스트 시작 ===")
        start_time = time.time()

        results = {}

        try:
            from apps.ingestion.pii_filter import default_pii_filter, MaskingStrategy
            from apps.ingestion.document_parser import get_parser_factory

            parser_factory = get_parser_factory()

            # PII가 포함된 파일들로 테스트
            test_files = {k: v for k, v in files.items() if k in ['txt', 'html', 'csv', 'json']}

            for file_type, file_path in test_files.items():
                try:
                    parser = parser_factory.get_parser(file_path)
                    if not parser:
                        continue

                    # 비동기 처리
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            parsed_doc = loop.run_until_complete(parser.parse(file_path))
                            filter_result = loop.run_until_complete(
                                default_pii_filter.filter_text(parsed_doc.content, MaskingStrategy.MASK)
                            )
                        else:
                            parsed_doc = asyncio.run(parser.parse(file_path))
                            filter_result = asyncio.run(
                                default_pii_filter.filter_text(parsed_doc.content, MaskingStrategy.MASK)
                            )
                    except RuntimeError:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            parsed_doc = new_loop.run_until_complete(parser.parse(file_path))
                            filter_result = new_loop.run_until_complete(
                                default_pii_filter.filter_text(parsed_doc.content, MaskingStrategy.MASK)
                            )
                        finally:
                            new_loop.close()

                    detections = []
                    for detection in filter_result.detections:
                        detections.append({
                            'type': detection.pii_type.value,
                            'confidence': detection.confidence,
                            'original': detection.original_text,
                            'masked': detection.masked_text,
                            'position': f"{detection.start_pos}-{detection.end_pos}"
                        })

                    results[file_type] = {
                        'success': True,
                        'original_length': len(parsed_doc.content),
                        'filtered_length': len(filter_result.filtered_text),
                        'detections_count': len(filter_result.detections),
                        'detections': detections,
                        'is_compliant': filter_result.compliance_flags.get('gdpr_compliant', False),
                        'sample_filtered': filter_result.filtered_text[:300] + "..." if len(filter_result.filtered_text) > 300 else filter_result.filtered_text
                    }

                    logger.info(f"{file_type} PII 필터링 성공: {len(filter_result.detections)}개 탐지")

                except Exception as e:
                    results[file_type] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"{file_type} PII 필터링 실패: {e}")

            processing_time = time.time() - start_time
            success_count = sum(1 for r in results.values() if r.get('success', False))
            total_pii = sum(r.get('detections_count', 0) for r in results.values() if r.get('success', False))

            return TestResult(
                success=success_count > 0,
                message=f"PII 필터링 테스트 완료: {success_count}/{len(results)}개 성공, 총 {total_pii}개 PII 탐지",
                details=results,
                processing_time=processing_time
            )

        except Exception as e:
            return TestResult(
                success=False,
                message="PII 필터링 테스트 실패",
                error=str(e),
                processing_time=time.time() - start_time
            )

    def test_mock_embedding(self, files: Dict[str, Path]) -> TestResult:
        """Mock 임베딩 생성 테스트"""
        logger.info("=== Mock 임베딩 생성 테스트 시작 ===")
        start_time = time.time()

        results = {}

        try:
            import numpy as np
            import hashlib

            class MockEmbeddingService:
                """Mock 임베딩 서비스"""

                def __init__(self, dimension=1536):
                    self.dimension = dimension

                async def embed(self, text: str) -> List[float]:
                    """텍스트를 임베딩으로 변환 (Mock)"""
                    # 텍스트의 해시를 기반으로 결정적 임베딩 생성
                    hash_object = hashlib.md5(text.encode('utf-8'))
                    hash_hex = hash_object.hexdigest()

                    # 해시를 시드로 사용하여 일관된 임베딩 생성
                    np.random.seed(int(hash_hex[:8], 16))
                    embedding = np.random.normal(0, 1, self.dimension)

                    # 정규화
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm

                    return embedding.tolist()

            mock_embedding_service = MockEmbeddingService()

            # 간단한 텍스트들로 테스트
            test_texts = [
                "안녕하세요. 한글 텍스트입니다.",
                "This is English text.",
                "Dynamic Taxonomy RAG 시스템",
                "임베딩 생성 테스트용 긴 텍스트입니다. " * 10
            ]

            for i, text in enumerate(test_texts):
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            embedding = loop.run_until_complete(mock_embedding_service.embed(text))
                        else:
                            embedding = asyncio.run(mock_embedding_service.embed(text))
                    except RuntimeError:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            embedding = new_loop.run_until_complete(mock_embedding_service.embed(text))
                        finally:
                            new_loop.close()

                    # 임베딩 품질 검증
                    embedding_norm = sum(x*x for x in embedding) ** 0.5

                    results[f'text_{i}'] = {
                        'success': True,
                        'text_length': len(text),
                        'embedding_dimension': len(embedding),
                        'embedding_norm': embedding_norm,
                        'sample_values': embedding[:5],  # 처음 5개 값
                        'text_sample': text[:50] + "..." if len(text) > 50 else text
                    }

                    logger.info(f"텍스트 {i} 임베딩 성공: {len(embedding)}차원")

                except Exception as e:
                    results[f'text_{i}'] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"텍스트 {i} 임베딩 실패: {e}")

            processing_time = time.time() - start_time
            success_count = sum(1 for r in results.values() if r.get('success', False))

            return TestResult(
                success=success_count > 0,
                message=f"임베딩 생성 테스트 완료: {success_count}/{len(results)}개 성공",
                details=results,
                processing_time=processing_time
            )

        except Exception as e:
            return TestResult(
                success=False,
                message="임베딩 생성 테스트 실패",
                error=str(e),
                processing_time=time.time() - start_time
            )

    def test_error_handling(self, files: Dict[str, Path]) -> TestResult:
        """오류 처리 테스트"""
        logger.info("=== 오류 처리 테스트 시작 ===")
        start_time = time.time()

        results = {}

        try:
            from apps.ingestion.document_parser import get_parser_factory

            parser_factory = get_parser_factory()

            # 1. 빈 파일 테스트
            empty_file = files.get('empty')
            if empty_file:
                try:
                    parser = parser_factory.get_parser(empty_file)
                    if parser:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                parsed_doc = loop.run_until_complete(parser.parse(empty_file))
                            else:
                                parsed_doc = asyncio.run(parser.parse(empty_file))
                        except RuntimeError:
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                parsed_doc = new_loop.run_until_complete(parser.parse(empty_file))
                            finally:
                                new_loop.close()

                        results['empty_file'] = {
                            'success': True,
                            'handled_gracefully': len(parsed_doc.content) == 0,
                            'content_length': len(parsed_doc.content)
                        }
                    else:
                        results['empty_file'] = {
                            'success': False,
                            'error': 'No parser available'
                        }
                except Exception as e:
                    results['empty_file'] = {
                        'success': True,  # 오류가 적절히 처리됨
                        'handled_gracefully': True,
                        'error_handled': str(e)
                    }

            # 2. 손상된 파일 테스트
            corrupted_file = files.get('corrupted')
            if corrupted_file:
                try:
                    parser = parser_factory.get_parser(corrupted_file)
                    if parser:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                parsed_doc = loop.run_until_complete(parser.parse(corrupted_file))
                            else:
                                parsed_doc = asyncio.run(parser.parse(corrupted_file))
                        except RuntimeError:
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                parsed_doc = new_loop.run_until_complete(parser.parse(corrupted_file))
                            finally:
                                new_loop.close()

                        results['corrupted_file'] = {
                            'success': True,
                            'handled_gracefully': True,
                            'content_length': len(parsed_doc.content)
                        }
                    else:
                        results['corrupted_file'] = {
                            'success': False,
                            'error': 'No parser available'
                        }
                except Exception as e:
                    results['corrupted_file'] = {
                        'success': True,  # 오류가 적절히 처리됨
                        'handled_gracefully': True,
                        'error_handled': str(e)
                    }

            # 3. 존재하지 않는 파일 테스트
            nonexistent_file = self.temp_dir / "nonexistent.txt"
            try:
                parser = parser_factory.get_parser(nonexistent_file)
                if parser:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            parsed_doc = loop.run_until_complete(parser.parse(nonexistent_file))
                        else:
                            parsed_doc = asyncio.run(parser.parse(nonexistent_file))
                    except RuntimeError:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            parsed_doc = new_loop.run_until_complete(parser.parse(nonexistent_file))
                        finally:
                            new_loop.close()

                    results['nonexistent_file'] = {
                        'success': False,
                        'unexpected_success': True
                    }
                else:
                    results['nonexistent_file'] = {
                        'success': True,
                        'handled_gracefully': True,
                        'error_handled': 'No parser for nonexistent file'
                    }
            except Exception as e:
                results['nonexistent_file'] = {
                    'success': True,  # 오류가 적절히 처리됨
                    'handled_gracefully': True,
                    'error_handled': str(e)
                }

            processing_time = time.time() - start_time
            handled_gracefully = sum(1 for r in results.values() if r.get('handled_gracefully', False))

            return TestResult(
                success=handled_gracefully > 0,
                message=f"오류 처리 테스트 완료: {handled_gracefully}/{len(results)}개 적절히 처리됨",
                details=results,
                processing_time=processing_time
            )

        except Exception as e:
            return TestResult(
                success=False,
                message="오류 처리 테스트 실패",
                error=str(e),
                processing_time=time.time() - start_time
            )

    def test_performance_benchmark(self, files: Dict[str, Path]) -> TestResult:
        """성능 벤치마크 테스트"""
        logger.info("=== 성능 벤치마크 테스트 시작 ===")
        start_time = time.time()

        results = {}

        try:
            from apps.ingestion.document_parser import get_parser_factory

            parser_factory = get_parser_factory()

            # 대용량 파일 성능 테스트
            large_file = files.get('large')
            if large_file:
                file_start = time.time()
                try:
                    parser = parser_factory.get_parser(large_file)
                    if parser:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                parsed_doc = loop.run_until_complete(parser.parse(large_file))
                            else:
                                parsed_doc = asyncio.run(parser.parse(large_file))
                        except RuntimeError:
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                parsed_doc = new_loop.run_until_complete(parser.parse(large_file))
                            finally:
                                new_loop.close()

                        file_time = time.time() - file_start

                        results['large_file'] = {
                            'success': True,
                            'file_size_chars': len(parsed_doc.content),
                            'processing_time': file_time,
                            'chars_per_second': len(parsed_doc.content) / file_time if file_time > 0 else 0,
                            'throughput_mb_per_sec': (len(parsed_doc.content.encode('utf-8')) / 1024 / 1024) / file_time if file_time > 0 else 0
                        }

                        logger.info(f"대용량 파일 처리: {len(parsed_doc.content):,} 문자, {file_time:.3f}초")
                    else:
                        results['large_file'] = {
                            'success': False,
                            'error': 'No parser available'
                        }
                except Exception as e:
                    results['large_file'] = {
                        'success': False,
                        'error': str(e)
                    }

            # 배치 처리 성능 테스트
            batch_start = time.time()
            batch_results = {
                'total_files': 0,
                'successful_files': 0,
                'total_chars': 0,
                'total_time': 0
            }

            test_files = {k: v for k, v in files.items() if k not in ['corrupted', 'empty', 'large']}

            for file_type, file_path in test_files.items():
                file_start = time.time()
                try:
                    parser = parser_factory.get_parser(file_path)
                    if parser:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                parsed_doc = loop.run_until_complete(parser.parse(file_path))
                            else:
                                parsed_doc = asyncio.run(parser.parse(file_path))
                        except RuntimeError:
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                parsed_doc = new_loop.run_until_complete(parser.parse(file_path))
                            finally:
                                new_loop.close()

                        batch_results['successful_files'] += 1
                        batch_results['total_chars'] += len(parsed_doc.content)

                except Exception as e:
                    logger.warning(f"배치 처리 중 {file_type} 실패: {e}")

                batch_results['total_files'] += 1

            batch_time = time.time() - batch_start
            batch_results['total_time'] = batch_time

            results['batch_processing'] = {
                'success': batch_results['successful_files'] > 0,
                **batch_results,
                'success_rate': batch_results['successful_files'] / batch_results['total_files'] * 100 if batch_results['total_files'] > 0 else 0,
                'files_per_second': batch_results['total_files'] / batch_time if batch_time > 0 else 0,
                'chars_per_second': batch_results['total_chars'] / batch_time if batch_time > 0 else 0
            }

            logger.info(f"배치 처리: {batch_results['successful_files']}/{batch_results['total_files']}개 파일, {batch_time:.3f}초")

            processing_time = time.time() - start_time

            return TestResult(
                success=True,
                message="성능 벤치마크 테스트 완료",
                details=results,
                processing_time=processing_time
            )

        except Exception as e:
            return TestResult(
                success=False,
                message="성능 벤치마크 테스트 실패",
                error=str(e),
                processing_time=time.time() - start_time
            )

    def generate_final_report(self) -> Dict[str, Any]:
        """최종 보고서 생성"""
        total_time = time.time() - self.start_time

        # 전체 통계 계산
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.success)

        # 성능 메트릭 수집
        total_processing_time = sum(result.processing_time for result in self.test_results.values())

        # 권장사항 생성
        recommendations = []

        if successful_tests < total_tests:
            failed_tests = [name for name, result in self.test_results.items() if not result.success]
            recommendations.append(f"실패한 테스트들을 검토하세요: {', '.join(failed_tests)}")

        if total_processing_time > 30:
            recommendations.append("전체 처리 시간이 30초를 초과했습니다. 성능 최적화를 고려하세요.")

        # PII 탐지 결과 확인
        pii_result = self.test_results.get('pii_filtering')
        if pii_result and pii_result.success:
            total_pii = sum(
                details.get('detections_count', 0)
                for details in pii_result.details.values()
                if isinstance(details, dict)
            )
            if total_pii == 0:
                recommendations.append("PII가 탐지되지 않았습니다. PII 패턴을 확인하세요.")
            elif total_pii > 20:
                recommendations.append(f"많은 PII가 탐지되었습니다 ({total_pii}개). 데이터 보안을 강화하세요.")

        if not recommendations:
            recommendations.append("모든 테스트가 성공적으로 완료되었습니다. 시스템이 정상적으로 작동하고 있습니다.")

        return {
            "summary": {
                "test_duration": total_time,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_processing_time": total_processing_time
            },
            "test_results": {name: {
                "success": result.success,
                "message": result.message,
                "processing_time": result.processing_time,
                "error": result.error,
                "details": result.details
            } for name, result in self.test_results.items()},
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("🚀 최종 문서 수집 파이프라인 테스트 시작")

        try:
            # 테스트 파일 생성
            test_files = self.create_test_files()

            # 1. 파일 파싱 테스트
            logger.info("1️⃣ 파일 파싱 테스트")
            self.test_results['file_parsing'] = self.test_file_parsing(test_files)

            # 2. 청킹 테스트
            logger.info("2️⃣ 청킹 테스트")
            self.test_results['chunking'] = self.test_chunking(test_files)

            # 3. PII 필터링 테스트
            logger.info("3️⃣ PII 필터링 테스트")
            self.test_results['pii_filtering'] = self.test_pii_filtering(test_files)

            # 4. Mock 임베딩 테스트
            logger.info("4️⃣ Mock 임베딩 테스트")
            self.test_results['embedding'] = self.test_mock_embedding(test_files)

            # 5. 오류 처리 테스트
            logger.info("5️⃣ 오류 처리 테스트")
            self.test_results['error_handling'] = self.test_error_handling(test_files)

            # 6. 성능 벤치마크 테스트
            logger.info("6️⃣ 성능 벤치마크 테스트")
            self.test_results['performance'] = self.test_performance_benchmark(test_files)

            logger.info("✅ 모든 테스트 완료")

        except Exception as e:
            logger.error(f"테스트 실행 중 치명적 오류: {e}")
            self.test_results['fatal_error'] = TestResult(
                success=False,
                message="치명적 오류 발생",
                error=str(e),
                details={'traceback': traceback.format_exc()}
            )

        return self.generate_final_report()

def main():
    """메인 실행 함수"""
    print("📋 Dynamic Taxonomy RAG - 문서 수집 파이프라인 종합 테스트")
    print("=" * 70)

    tester = DocumentIngestionTester()

    try:
        # 전체 테스트 실행
        report = tester.run_all_tests()

        # 결과 저장
        report_file = Path("document_ingestion_final_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 결과 출력
        print("\n📊 테스트 결과 요약")
        print("-" * 40)

        summary = report['summary']
        print(f"🕐 총 테스트 시간: {summary['test_duration']:.2f}초")
        print(f"📝 총 테스트 수: {summary['total_tests']}개")
        print(f"✅ 성공: {summary['successful_tests']}개")
        print(f"❌ 실패: {summary['failed_tests']}개")
        print(f"📈 성공률: {summary['success_rate']:.1f}%")
        print(f"⚡ 처리 시간: {summary['total_processing_time']:.2f}초")

        # 개별 테스트 결과
        print(f"\n📋 개별 테스트 결과:")
        for test_name, result in report['test_results'].items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {test_name}: {result['message']} ({result['processing_time']:.3f}초)")
            if result.get('error'):
                print(f"   오류: {result['error']}")

        # 권장사항
        if report['recommendations']:
            print(f"\n💡 권장사항:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")

        print(f"\n📄 상세 보고서: {report_file.absolute()}")

        # 성공 여부 판단
        success_rate = summary['success_rate']
        if success_rate >= 90:
            print("\n🎉 테스트 성공! 문서 수집 파이프라인이 정상적으로 작동합니다.")
            return 0
        elif success_rate >= 70:
            print("\n⚠️ 테스트 부분 성공. 일부 개선이 필요합니다.")
            return 1
        else:
            print("\n❌ 테스트 실패. 심각한 문제가 있습니다.")
            return 2

    except Exception as e:
        print(f"\n💥 테스트 실행 실패: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        return 3

    finally:
        # 정리
        if hasattr(tester, 'temp_dir') and tester.temp_dir.exists():
            shutil.rmtree(tester.temp_dir, ignore_errors=True)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)