"""
문서 수집 파이프라인 오케스트레이터
idempotent 작업과 DLQ 지원
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4
import asyncpg
from pathlib import Path

from .models import DocumentMetadata, IngestionJob, IngestionStatus, DocumentType
from .parsers import PDFParser, MarkdownParser, HTMLParser, BaseParser
from .chunker import DocumentChunker
from ..api.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """문서 수집 파이프라인"""
    
    def __init__(self, db_pool: asyncpg.Pool, embedding_service: EmbeddingService):
        self.db_pool = db_pool
        self.embedding_service = embedding_service
        self.chunker = DocumentChunker()
        self.logger = logger
        
        # 파서 매핑
        self.parsers: Dict[DocumentType, BaseParser] = {
            DocumentType.PDF: PDFParser(),
            DocumentType.MARKDOWN: MarkdownParser(),
            DocumentType.HTML: HTMLParser()
        }
        
        # 재시도 설정
        self.max_retries = 3
        self.dlq_threshold = 5  # DLQ로 이동할 재시도 임계값
    
    async def submit_document(self, content: bytes, filename: str, 
                            content_type: str, **metadata_kwargs) -> str:
        """문서 수집 작업 제출"""
        try:
            # 메타데이터 생성
            doc_metadata = DocumentMetadata.from_content(
                filename, content, content_type, **metadata_kwargs
            )
            
            # 중복 검사 (idempotent)
            existing_job = await self._check_existing_job(doc_metadata.doc_hash)
            if existing_job:
                self.logger.info(f"기존 작업 발견: {existing_job['job_id']} (상태: {existing_job['status']})")
                return existing_job['job_id']
            
            # 새 작업 생성
            job_id = str(uuid4())
            job = IngestionJob(
                job_id=uuid4(),
                doc_metadata=doc_metadata,
                status=IngestionStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # DB에 작업 저장
            await self._save_job(job, content)
            
            # 백그라운드에서 처리 시작
            asyncio.create_task(self._process_job(job_id, content))
            
            self.logger.info(f"문서 수집 작업 제출: {job_id} ({filename})")
            return job_id
            
        except Exception as e:
            self.logger.error(f"문서 제출 오류: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        job_id,
                        filename,
                        doc_hash,
                        doc_type,
                        status,
                        created_at,
                        updated_at,
                        chunks_created,
                        error_message,
                        retry_count
                    FROM ingestion_jobs
                    WHERE job_id = $1
                """, job_id)
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            self.logger.error(f"작업 상태 조회 오류: {e}")
            return None
    
    async def _check_existing_job(self, doc_hash: str) -> Optional[Dict[str, Any]]:
        """기존 작업 확인 (중복 방지)"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT job_id, status, created_at
                    FROM ingestion_jobs
                    WHERE doc_hash = $1
                    AND status IN ('completed', 'processing')
                    ORDER BY created_at DESC
                    LIMIT 1
                """, doc_hash)
                
                return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"기존 작업 확인 오류: {e}")
            return None
    
    async def _save_job(self, job: IngestionJob, content: bytes):
        """작업을 DB에 저장"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ingestion_jobs (
                        job_id, filename, doc_hash, doc_type, content_type,
                        size_bytes, status, created_at, updated_at, content_blob
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                str(job.job_id),
                job.doc_metadata.filename,
                job.doc_metadata.doc_hash,
                job.doc_metadata.doc_type.value,
                job.doc_metadata.content_type,
                job.doc_metadata.size_bytes,
                job.status.value,
                job.created_at,
                job.updated_at,
                content
                )
                
        except Exception as e:
            self.logger.error(f"작업 저장 오류: {e}")
            raise
    
    async def _process_job(self, job_id: str, content: bytes):
        """작업 처리 (백그라운드)"""
        try:
            # 작업 상태를 processing으로 변경
            await self._update_job_status(job_id, IngestionStatus.PROCESSING)
            
            # 작업 정보 로드
            job_info = await self.get_job_status(job_id)
            if not job_info:
                raise ValueError(f"작업을 찾을 수 없습니다: {job_id}")
            
            doc_metadata = DocumentMetadata(
                filename=job_info['filename'],
                content_type=job_info.get('content_type', ''),
                size_bytes=job_info['size_bytes'],
                doc_hash=job_info['doc_hash'],
                doc_type=DocumentType(job_info['doc_type'])
            )
            
            # 1단계: 문서 파싱
            parser = self.parsers[doc_metadata.doc_type]
            parse_result = parser.parse(content, doc_metadata)
            
            if not parse_result.success:
                await self._handle_job_error(job_id, f"파싱 실패: {parse_result.error_message}")
                return
            
            # 2단계: 문서 저장 (documents 테이블)
            doc_id = await self._save_document(doc_metadata, parse_result.metadata)
            
            # 3단계: 청킹
            chunks = self.chunker.chunk_document(parse_result.text, doc_metadata)
            if not chunks:
                await self._handle_job_error(job_id, "청킹 결과 없음")
                return
            
            # 4단계: 청크 저장 및 임베딩
            await self._save_chunks(doc_id, chunks)
            
            # 5단계: 임베딩 생성
            await self._generate_embeddings(doc_id, chunks)
            
            # 작업 완료
            await self._update_job_status(
                job_id, 
                IngestionStatus.COMPLETED,
                chunks_created=len(chunks)
            )
            
            self.logger.info(f"문서 처리 완료: {job_id} ({len(chunks)}개 청크)")
            
        except Exception as e:
            self.logger.error(f"작업 처리 오류 ({job_id}): {e}")
            await self._handle_job_error(job_id, str(e))
    
    async def _save_document(self, metadata: DocumentMetadata, 
                           parsed_metadata: Dict[str, Any]) -> str:
        """문서를 documents 테이블에 저장"""
        try:
            doc_id = str(uuid4())
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO documents (
                        doc_id, filename, content_type, size_bytes,
                        doc_hash, title, author, created_at, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (doc_hash) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        updated_at = NOW()
                    RETURNING doc_id
                """,
                doc_id,
                metadata.filename,
                metadata.content_type,
                metadata.size_bytes,
                metadata.doc_hash,
                parsed_metadata.get('title'),
                parsed_metadata.get('author'),
                datetime.now(timezone.utc),
                parsed_metadata
                )
                
            return doc_id
            
        except Exception as e:
            self.logger.error(f"문서 저장 오류: {e}")
            raise
    
    async def _save_chunks(self, doc_id: str, chunks: List[Any]):
        """청크들을 chunks 테이블에 저장"""
        try:
            async with self.db_pool.acquire() as conn:
                for chunk in chunks:
                    await conn.execute("""
                        INSERT INTO chunks (
                            chunk_id, doc_id, text, span, chunk_index, metadata
                        ) VALUES ($1, $2, $3, int4range($4, $5), $6, $7)
                    """,
                    str(chunk.chunk_id),
                    doc_id,
                    chunk.text,
                    chunk.start_char,
                    chunk.end_char,
                    chunk.chunk_index,
                    chunk.metadata
                    )
                    
        except Exception as e:
            self.logger.error(f"청크 저장 오류: {e}")
            raise
    
    async def _generate_embeddings(self, doc_id: str, chunks: List[Any]):
        """청크들의 임베딩 생성"""
        try:
            async with self.db_pool.acquire() as conn:
                for chunk in chunks:
                    # 임베딩 생성
                    embedding = await self.embedding_service.get_embedding(chunk.text)
                    
                    # 임베딩 저장
                    await conn.execute("""
                        INSERT INTO embeddings (
                            chunk_id, embedding_vector, model_name
                        ) VALUES ($1, $2, $3)
                    """,
                    str(chunk.chunk_id),
                    embedding,
                    self.embedding_service.model_name
                    )
                    
        except Exception as e:
            self.logger.error(f"임베딩 생성 오류: {e}")
            raise
    
    async def _update_job_status(self, job_id: str, status: IngestionStatus, 
                               chunks_created: int = 0, error_message: str = None):
        """작업 상태 업데이트"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ingestion_jobs
                    SET status = $2, updated_at = $3, chunks_created = $4,
                        error_message = $5
                    WHERE job_id = $1
                """,
                job_id, status.value, datetime.now(timezone.utc),
                chunks_created, error_message
                )
                
        except Exception as e:
            self.logger.error(f"작업 상태 업데이트 오류: {e}")
    
    async def _handle_job_error(self, job_id: str, error_message: str):
        """작업 오류 처리"""
        try:
            # 재시도 카운트 증가
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    UPDATE ingestion_jobs
                    SET retry_count = retry_count + 1, 
                        error_message = $2,
                        updated_at = $3
                    WHERE job_id = $1
                    RETURNING retry_count
                """, job_id, error_message, datetime.now(timezone.utc))
                
                retry_count = result['retry_count'] if result else 0
                
                # DLQ 이동 또는 실패 상태로 변경
                if retry_count >= self.dlq_threshold:
                    await self._update_job_status(job_id, IngestionStatus.DLQ, error_message=error_message)
                    self.logger.warning(f"작업을 DLQ로 이동: {job_id} (재시도 {retry_count}회)")
                else:
                    await self._update_job_status(job_id, IngestionStatus.FAILED, error_message=error_message)
                    
        except Exception as e:
            self.logger.error(f"오류 처리 중 오류: {e}")
    
    async def get_job_list(self, status: Optional[IngestionStatus] = None, 
                          limit: int = 50) -> List[Dict[str, Any]]:
        """작업 목록 조회"""
        try:
            async with self.db_pool.acquire() as conn:
                if status:
                    results = await conn.fetch("""
                        SELECT job_id, filename, doc_type, status, created_at,
                               updated_at, chunks_created, retry_count
                        FROM ingestion_jobs
                        WHERE status = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                    """, status.value, limit)
                else:
                    results = await conn.fetch("""
                        SELECT job_id, filename, doc_type, status, created_at,
                               updated_at, chunks_created, retry_count
                        FROM ingestion_jobs
                        ORDER BY created_at DESC
                        LIMIT $1
                    """, limit)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"작업 목록 조회 오류: {e}")
            return []