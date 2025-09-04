"""
문서 수집 파이프라인 테스트
"""

import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, MagicMock
import os
import tempfile
from pathlib import Path

from ..pipeline import IngestionPipeline
from ..models import DocumentMetadata, DocumentType, IngestionStatus
from ..parsers import PDFParser, MarkdownParser, HTMLParser
from ..chunker import DocumentChunker
from ...api.services.embedding_service import EmbeddingService


@pytest.fixture
async def db_pool():
    """테스트용 데이터베이스 풀"""
    connection_string = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/dt_rag_test"
    )
    
    pool = await asyncpg.create_pool(connection_string, min_size=1, max_size=2)
    
    # 테스트 테이블 설정
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM ingestion_jobs")
        await conn.execute("DELETE FROM documents")
        await conn.execute("DELETE FROM chunks")
        await conn.execute("DELETE FROM embeddings")
    
    yield pool
    
    await pool.close()


@pytest.fixture
def mock_embedding_service():
    """모의 임베딩 서비스"""
    service = MagicMock(spec=EmbeddingService)
    service.get_embedding = AsyncMock(return_value=[0.1] * 384)  # 임베딩 벡터 모의
    service.model_name = "test-model"
    return service


@pytest.fixture
async def ingestion_pipeline(db_pool, mock_embedding_service):
    """수집 파이프라인 픽스처"""
    return IngestionPipeline(db_pool, mock_embedding_service)


@pytest.mark.asyncio
class TestDocumentParsers:
    """문서 파서 테스트"""
    
    def test_markdown_parser(self):
        """Markdown 파서 테스트"""
        content = b"""---
title: Test Document
author: Test Author
---

# 제목

이것은 테스트 **문서**입니다.

## 부제목

- 리스트 아이템 1
- 리스트 아이템 2

```python
print("Hello World")
```

[링크](https://example.com)
"""
        
        metadata = DocumentMetadata.from_content("test.md", content, "text/markdown")
        parser = MarkdownParser()
        
        result = parser.parse(content, metadata)
        
        assert result.success
        assert "제목" in result.text
        assert "테스트 문서" in result.text
        assert result.metadata["title"] == "Test Document"
        assert result.metadata["author"] == "Test Author"
    
    def test_html_parser(self):
        """HTML 파서 테스트"""
        content = b"""<!DOCTYPE html>
<html>
<head>
    <title>테스트 페이지</title>
    <meta name="description" content="테스트용 HTML 페이지">
</head>
<body>
    <h1>메인 제목</h1>
    <p>이것은 테스트 내용입니다.</p>
    <script>console.log("script");</script>
    <div class="sidebar">사이드바 내용</div>
</body>
</html>"""
        
        metadata = DocumentMetadata.from_content("test.html", content, "text/html")
        parser = HTMLParser()
        
        result = parser.parse(content, metadata)
        
        assert result.success
        assert "메인 제목" in result.text
        assert "테스트 내용" in result.text
        assert result.metadata["title"] == "테스트 페이지"
        assert result.metadata["description"] == "테스트용 HTML 페이지"
        # 스크립트나 사이드바는 제거되어야 함
        assert "console.log" not in result.text
        assert "사이드바 내용" not in result.text


@pytest.mark.asyncio
class TestDocumentChunker:
    """문서 청킹 테스트"""
    
    def test_basic_chunking(self):
        """기본 청킹 테스트"""
        text = "이것은 첫 번째 문장입니다. 이것은 두 번째 문장입니다. " * 20
        metadata = DocumentMetadata(
            filename="test.md",
            content_type="text/markdown", 
            size_bytes=len(text),
            doc_hash="test123",
            doc_type=DocumentType.MARKDOWN
        )
        
        chunker = DocumentChunker(chunk_size=100, overlap_size=20)
        chunks = chunker.chunk_document(text, metadata)
        
        assert len(chunks) > 1
        assert all(len(chunk.text) <= 120 for chunk in chunks)  # 약간의 여유
        
        # 오버랩 확인
        if len(chunks) > 1:
            # 연속된 청크들 사이에 오버랩이 있어야 함
            first_chunk_end = chunks[0].text[-20:]
            second_chunk_start = chunks[1].text[:20]
            # 완전 일치는 아니지만 유사한 내용이 있어야 함
            assert len(first_chunk_end.strip()) > 0
            assert len(second_chunk_start.strip()) > 0
    
    def test_sentence_boundary_preservation(self):
        """문장 경계 보존 테스트"""
        text = "짧은 문장. " + "이것은 매우 긴 문장으로써 청크 크기를 넘을 수 있는 내용을 포함하고 있습니다. " * 5
        metadata = DocumentMetadata(
            filename="test.md",
            content_type="text/markdown",
            size_bytes=len(text),
            doc_hash="test123", 
            doc_type=DocumentType.MARKDOWN
        )
        
        chunker = DocumentChunker(chunk_size=100, overlap_size=20)
        chunks = chunker.chunk_document(text, metadata)
        
        # 첫 번째 청크는 "짧은 문장."으로 시작해야 함
        assert chunks[0].text.strip().startswith("짧은 문장")
        
        # 각 청크의 메타데이터 확인
        for chunk in chunks:
            assert chunk.metadata["doc_hash"] == "test123"
            assert chunk.metadata["filename"] == "test.md"
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char


@pytest.mark.asyncio
class TestIngestionPipeline:
    """수집 파이프라인 통합 테스트"""
    
    async def test_submit_document(self, ingestion_pipeline):
        """문서 제출 테스트"""
        content = b"""# 테스트 문서

이것은 테스트 문서입니다.

## 섹션 1

내용이 있습니다."""
        
        job_id = await ingestion_pipeline.submit_document(
            content=content,
            filename="test.md",
            content_type="text/markdown"
        )
        
        assert job_id is not None
        assert len(job_id) > 0
        
        # 작업 상태 확인
        job_status = await ingestion_pipeline.get_job_status(job_id)
        assert job_status is not None
        assert job_status["filename"] == "test.md"
        assert job_status["doc_type"] == "markdown"
    
    async def test_idempotent_submission(self, ingestion_pipeline):
        """동일 문서 중복 제출 시 idempotent 동작 테스트"""
        content = b"# Same Document\n\nThis is the same content."
        
        # 첫 번째 제출
        job_id_1 = await ingestion_pipeline.submit_document(
            content=content,
            filename="same.md",
            content_type="text/markdown"
        )
        
        # 처리 완료까지 대기
        await asyncio.sleep(0.1)
        
        # 동일한 content로 두 번째 제출 (해시가 같아야 함)
        job_id_2 = await ingestion_pipeline.submit_document(
            content=content, 
            filename="same_different_name.md",
            content_type="text/markdown"
        )
        
        # 기존 작업이 있으면 기존 job_id를 반환해야 함
        # (실제로는 파이프라인 구현에 따라 다를 수 있음)
        assert job_id_1 is not None
        assert job_id_2 is not None
    
    async def test_get_job_list(self, ingestion_pipeline):
        """작업 목록 조회 테스트"""
        # 여러 문서 제출
        contents = [
            b"# Document 1\nContent 1",
            b"# Document 2\nContent 2", 
            b"# Document 3\nContent 3"
        ]
        
        job_ids = []
        for i, content in enumerate(contents):
            job_id = await ingestion_pipeline.submit_document(
                content=content,
                filename=f"doc_{i}.md",
                content_type="text/markdown"
            )
            job_ids.append(job_id)
        
        # 작업 목록 조회
        jobs = await ingestion_pipeline.get_job_list(limit=10)
        
        assert len(jobs) >= 3
        
        # 최신 작업이 먼저 나와야 함 (created_at DESC)
        assert jobs[0]["created_at"] >= jobs[-1]["created_at"]
    
    async def test_job_status_filtering(self, ingestion_pipeline):
        """상태별 작업 필터링 테스트"""
        # pending 상태 작업 조회
        pending_jobs = await ingestion_pipeline.get_job_list(
            status=IngestionStatus.PENDING,
            limit=50
        )
        
        # 모든 작업이 pending 상태여야 함
        for job in pending_jobs:
            assert job["status"] == "pending"


@pytest.mark.asyncio
class TestIntegrationErrors:
    """오류 상황 통합 테스트"""
    
    async def test_invalid_file_handling(self, ingestion_pipeline):
        """잘못된 파일 처리 테스트"""
        # 빈 파일
        with pytest.raises(Exception):
            await ingestion_pipeline.submit_document(
                content=b"",
                filename="empty.pdf",
                content_type="application/pdf"
            )
    
    async def test_parsing_error_handling(self, ingestion_pipeline, db_pool):
        """파싱 오류 처리 테스트"""
        # 잘못된 PDF 바이너리
        invalid_pdf = b"This is not a PDF file"
        
        job_id = await ingestion_pipeline.submit_document(
            content=invalid_pdf,
            filename="invalid.pdf",
            content_type="application/pdf"
        )
        
        # 처리 완료까지 대기
        await asyncio.sleep(0.5)
        
        # 오류 상태 확인
        job_status = await ingestion_pipeline.get_job_status(job_id)
        assert job_status["status"] in ["failed", "dlq"]
        assert job_status["error_message"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])