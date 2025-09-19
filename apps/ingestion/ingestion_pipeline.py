"""
Document Ingestion Pipeline

통합 문서 처리 파이프라인:
- 문서 파싱 → 청킹 → PII 필터링 → 임베딩 생성 → 데이터베이스 저장
- 배치 처리 및 진행률 모니터링
- 에러 처리 및 복구
- 품질 보증 및 검증
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import traceback
import time

# 내부 모듈
from .document_parser import DocumentParserFactory, ParsedDocument, get_parser_factory
from .chunking_strategy import ChunkingStrategyFactory, DocumentChunk, default_chunker
from .pii_filter import PIIFilter, PIIFilterResult, default_pii_filter, MaskingStrategy, PIIType

# 데이터베이스 모듈
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.database import db_manager, EmbeddingService, Document, DocumentChunk as DBChunk, Embedding

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """처리 상태"""
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    PII_FILTERING = "pii_filtering"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class ProcessingResult:
    """문서 처리 결과"""
    document_id: str
    source: str
    status: ProcessingStatus
    chunks_created: int = 0
    pii_detected: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings_created: int = 0
    file_size: int = 0
    content_type: str = ""

@dataclass
class BatchProcessingResult:
    """배치 처리 결과"""
    total_documents: int
    successful: int
    failed: int
    skipped: int
    total_chunks: int
    total_embeddings: int
    processing_time: float
    error_summary: Dict[str, int]
    results: List[ProcessingResult]

class ProgressCallback:
    """진행률 콜백 인터페이스"""

    def __init__(self, callback_func: Optional[Callable] = None):
        self.callback_func = callback_func

    async def update(self, current: int, total: int, status: str, details: Dict[str, Any] = None):
        """진행률 업데이트"""
        if self.callback_func:
            await self.callback_func(current, total, status, details or {})
        else:
            percentage = (current / total * 100) if total > 0 else 0
            logger.info(f"진행률: {current}/{total} ({percentage:.1f}%) - {status}")

class IngestionPipeline:
    """문서 처리 파이프라인"""

    def __init__(
        self,
        parser_factory: Optional[DocumentParserFactory] = None,
        chunking_strategy: Optional[str] = "token_based",
        chunking_params: Optional[Dict[str, Any]] = None,
        pii_filter: Optional[PIIFilter] = None,
        enable_embeddings: bool = True,
        batch_size: int = 10,
        max_retries: int = 3,
        quality_threshold: float = 0.8
    ):
        # 컴포넌트 초기화
        self.parser_factory = parser_factory or get_parser_factory()

        # 청킹 전략 설정
        if chunking_params is None:
            chunking_params = {"chunk_size": 500, "chunk_overlap": 128}

        self.chunking_strategy = ChunkingStrategyFactory.create_strategy(
            chunking_strategy, **chunking_params
        )

        self.pii_filter = pii_filter or default_pii_filter
        self.enable_embeddings = enable_embeddings
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.quality_threshold = quality_threshold

        # 통계 및 메트릭
        self.processing_stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "pii_filtered": 0,
            "errors": 0
        }

    async def process_document(
        self,
        source: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
        custom_chunk_strategy: Optional[str] = None,
        custom_pii_settings: Optional[Dict] = None
    ) -> ProcessingResult:
        """단일 문서 처리"""
        start_time = time.time()
        document_id = str(uuid.uuid4())

        result = ProcessingResult(
            document_id=document_id,
            source=str(source),
            status=ProcessingStatus.PENDING,
            metadata=metadata or {}
        )

        try:
            # 1. 문서 파싱
            result.status = ProcessingStatus.PARSING
            parsed_doc = await self._parse_document(source)
            result.file_size = parsed_doc.get_file_size()
            result.content_type = parsed_doc.metadata.get('mime_type', 'unknown')

            # 2. 청킹
            result.status = ProcessingStatus.CHUNKING
            chunks = await self._chunk_document(parsed_doc, custom_chunk_strategy)
            result.chunks_created = len(chunks)

            # 3. PII 필터링
            result.status = ProcessingStatus.PII_FILTERING
            filtered_chunks = await self._filter_pii(chunks, custom_pii_settings)
            result.pii_detected = sum(
                len(chunk_result.detected_pii)
                for chunk_result in filtered_chunks
            )

            # 4. 임베딩 생성
            embeddings = []
            if self.enable_embeddings:
                result.status = ProcessingStatus.EMBEDDING
                embeddings = await self._generate_embeddings(filtered_chunks)
                result.embeddings_created = len(embeddings)

            # 5. 데이터베이스 저장
            result.status = ProcessingStatus.STORING
            await self._store_document_data(
                parsed_doc, filtered_chunks, embeddings, result
            )

            # 6. 품질 검증
            quality_score = await self._validate_quality(result)
            result.metadata['quality_score'] = quality_score

            if quality_score >= self.quality_threshold:
                result.status = ProcessingStatus.COMPLETED
            else:
                result.status = ProcessingStatus.FAILED
                result.error_message = f"품질 점수 미달: {quality_score:.2f} < {self.quality_threshold}"

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            logger.error(f"문서 처리 실패 ({source}): {e}")
            logger.debug(traceback.format_exc())

        finally:
            result.processing_time = time.time() - start_time
            self._update_stats(result)

        return result

    async def process_batch(
        self,
        sources: List[Union[str, Path]],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        concurrent_limit: int = 5
    ) -> BatchProcessingResult:
        """배치 문서 처리"""
        start_time = time.time()

        if metadata_list is None:
            metadata_list = [{}] * len(sources)
        elif len(metadata_list) != len(sources):
            raise ValueError("metadata_list 길이가 sources와 일치하지 않습니다")

        # 진행률 콜백 초기화
        if progress_callback is None:
            progress_callback = ProgressCallback()

        results = []
        error_summary = {}

        # 세마포어로 동시 처리 수 제한
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def process_single(source, metadata, index):
            async with semaphore:
                await progress_callback.update(
                    index, len(sources),
                    f"처리 중: {Path(source).name if isinstance(source, (str, Path)) else source}",
                    {"current_file": str(source)}
                )

                return await self.process_document(source, metadata)

        # 배치 처리 실행
        tasks = [
            process_single(source, metadata, i)
            for i, (source, metadata) in enumerate(zip(sources, metadata_list))
        ]

        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 정리
        for i, result in enumerate(completed_results):
            if isinstance(result, Exception):
                # 예외 처리
                error_result = ProcessingResult(
                    document_id=str(uuid.uuid4()),
                    source=str(sources[i]),
                    status=ProcessingStatus.FAILED,
                    error_message=str(result)
                )
                results.append(error_result)
                error_type = type(result).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
            else:
                results.append(result)
                if result.status == ProcessingStatus.FAILED and result.error_message:
                    error_type = "ProcessingError"
                    error_summary[error_type] = error_summary.get(error_type, 0) + 1

        # 통계 계산
        successful = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
        skipped = sum(1 for r in results if r.status == ProcessingStatus.SKIPPED)
        total_chunks = sum(r.chunks_created for r in results)
        total_embeddings = sum(r.embeddings_created for r in results)

        # 최종 진행률 업데이트
        await progress_callback.update(
            len(sources), len(sources), "배치 처리 완료",
            {
                "successful": successful,
                "failed": failed,
                "total_chunks": total_chunks,
                "total_embeddings": total_embeddings
            }
        )

        return BatchProcessingResult(
            total_documents=len(sources),
            successful=successful,
            failed=failed,
            skipped=skipped,
            total_chunks=total_chunks,
            total_embeddings=total_embeddings,
            processing_time=time.time() - start_time,
            error_summary=error_summary,
            results=results
        )

    async def _parse_document(self, source: Union[str, Path]) -> ParsedDocument:
        """문서 파싱"""
        try:
            return await self.parser_factory.parse_document(source)
        except Exception as e:
            logger.error(f"문서 파싱 실패: {source} - {e}")
            raise

    async def _chunk_document(
        self,
        parsed_doc: ParsedDocument,
        custom_strategy: Optional[str] = None
    ) -> List[DocumentChunk]:
        """문서 청킹"""
        try:
            # 커스텀 전략이 있으면 사용
            if custom_strategy:
                chunker = ChunkingStrategyFactory.create_strategy(custom_strategy)
            else:
                chunker = self.chunking_strategy

            # 청킹 메타데이터 준비
            chunk_metadata = {
                **parsed_doc.metadata,
                "original_length": len(parsed_doc.content),
                "parser_type": parsed_doc.source_type
            }

            chunks = await chunker.chunk_text(parsed_doc.content, chunk_metadata)

            if not chunks:
                logger.warning("청킹 결과가 비어있습니다")

            return chunks

        except Exception as e:
            logger.error(f"문서 청킹 실패: {e}")
            raise

    async def _filter_pii(
        self,
        chunks: List[DocumentChunk],
        custom_settings: Optional[Dict] = None
    ) -> List[PIIFilterResult]:
        """PII 필터링"""
        filtered_results = []

        try:
            for chunk in chunks:
                # 커스텀 PII 설정 적용
                if custom_settings:
                    strategies = custom_settings.get('strategies')
                    confidence = custom_settings.get('confidence_threshold', 0.8)
                else:
                    strategies = None
                    confidence = 0.8

                # PII 필터링 실행
                filter_result = await self.pii_filter.filter_text(
                    chunk.text,
                    custom_strategies=strategies,
                    confidence_threshold=confidence
                )

                # 청크에 필터링된 텍스트 적용
                chunk.text = filter_result.filtered_text
                chunk.metadata['pii_filtered'] = True
                chunk.metadata['pii_detection_time'] = filter_result.processing_time
                chunk.metadata['pii_count'] = len(filter_result.detected_pii)

                filtered_results.append(filter_result)

        except Exception as e:
            logger.error(f"PII 필터링 실패: {e}")
            raise

        return filtered_results

    async def _generate_embeddings(
        self,
        pii_results: List[PIIFilterResult]
    ) -> List[List[float]]:
        """임베딩 생성"""
        if not self.enable_embeddings:
            return []

        try:
            # 필터링된 텍스트들 추출
            texts = [result.filtered_text for result in pii_results]

            # 배치로 임베딩 생성
            embeddings = await EmbeddingService.generate_batch_embeddings(
                texts, batch_size=self.batch_size
            )

            return embeddings

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise

    async def _store_document_data(
        self,
        parsed_doc: ParsedDocument,
        pii_results: List[PIIFilterResult],
        embeddings: List[List[float]],
        result: ProcessingResult
    ) -> None:
        """데이터베이스 저장"""
        try:
            async with await db_manager.get_session() as session:
                # 1. 문서 레코드 생성
                doc_record = Document(
                    doc_id=uuid.UUID(result.document_id),
                    source_url=result.source if result.source.startswith('http') else None,
                    title=parsed_doc.metadata.get('title'),
                    content_type=result.content_type,
                    file_size=result.file_size,
                    checksum=parsed_doc.get_checksum(),
                    metadata={
                        **parsed_doc.metadata,
                        "processing_stats": {
                            "chunks_created": result.chunks_created,
                            "pii_detected": result.pii_detected,
                            "embeddings_created": result.embeddings_created
                        }
                    }
                )

                session.add(doc_record)
                await session.flush()

                # 2. 청크 레코드 생성
                chunk_records = []
                for i, pii_result in enumerate(pii_results):
                    chunk_id = uuid.uuid4()

                    # PostgreSQL range 타입 사용
                    span_start = 0  # 간소화된 구현
                    span_end = len(pii_result.filtered_text)
                    span_value = f"[{span_start},{span_end})"

                    chunk_record = DBChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_record.doc_id,
                        text=pii_result.filtered_text,
                        span=span_value,
                        chunk_index=i,
                        metadata={
                            "pii_filtered": True,
                            "pii_count": len(pii_result.detected_pii),
                            "compliance_flags": pii_result.compliance_flags
                        }
                    )

                    chunk_records.append(chunk_record)
                    session.add(chunk_record)

                await session.flush()

                # 3. 임베딩 레코드 생성
                if embeddings:
                    for chunk_record, embedding in zip(chunk_records, embeddings):
                        embedding_record = Embedding(
                            embedding_id=uuid.uuid4(),
                            chunk_id=chunk_record.chunk_id,
                            vec=embedding,
                            model_name='text-embedding-ada-002'
                        )
                        session.add(embedding_record)

                await session.commit()
                logger.info(f"문서 데이터 저장 완료: {result.document_id}")

        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {e}")
            if session:
                await session.rollback()
            raise

    async def _validate_quality(self, result: ProcessingResult) -> float:
        """처리 품질 검증"""
        quality_score = 1.0

        # 기본 품질 지표들
        if result.chunks_created == 0:
            quality_score -= 0.5

        if result.status == ProcessingStatus.FAILED:
            quality_score -= 0.3

        if result.error_message:
            quality_score -= 0.2

        # 처리 시간 기준 (너무 빠르면 문제 있을 수 있음)
        if result.processing_time < 0.1:
            quality_score -= 0.1

        # PII 필터링 품질
        if result.pii_detected > 0:
            # PII가 탐지되었다면 필터링이 제대로 작동한 것
            quality_score += 0.1

        return max(0.0, min(1.0, quality_score))

    def _update_stats(self, result: ProcessingResult):
        """통계 업데이트"""
        self.processing_stats["documents_processed"] += 1
        self.processing_stats["chunks_created"] += result.chunks_created
        self.processing_stats["embeddings_generated"] += result.embeddings_created
        self.processing_stats["pii_filtered"] += result.pii_detected

        if result.status == ProcessingStatus.FAILED:
            self.processing_stats["errors"] += 1

    async def get_processing_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """문서 처리 상태 조회"""
        try:
            async with await db_manager.get_session() as session:
                # 실제 구현에서는 processing_jobs 테이블에서 조회
                # 여기서는 기본 정보 반환
                return {
                    "document_id": document_id,
                    "status": "completed",  # 실제로는 DB에서 조회
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"처리 상태 조회 실패: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """파이프라인 통계 반환"""
        return {
            "processing_stats": self.processing_stats,
            "configuration": {
                "chunking_strategy": self.chunking_strategy.__class__.__name__,
                "pii_filter_mode": self.pii_filter.compliance_mode,
                "embeddings_enabled": self.enable_embeddings,
                "batch_size": self.batch_size,
                "quality_threshold": self.quality_threshold
            },
            "capabilities": {
                "supported_formats": self.parser_factory.get_supported_extensions(),
                "pii_types": [t.value for t in PIIType],
                "masking_strategies": [s.value for s in MaskingStrategy]
            }
        }

    async def process_url_batch(
        self,
        urls: List[str],
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchProcessingResult:
        """URL 배치 처리 (웹 스크래핑)"""
        logger.info(f"URL 배치 처리 시작: {len(urls)}개")

        # URL 메타데이터 생성
        metadata_list = [
            {"source_type": "url", "original_url": url}
            for url in urls
        ]

        return await self.process_batch(
            urls, metadata_list, progress_callback
        )

    async def process_directory(
        self,
        directory_path: Union[str, Path],
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchProcessingResult:
        """디렉토리 일괄 처리"""
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"유효하지 않은 디렉토리: {directory_path}")

        # 파일 수집
        if file_patterns is None:
            file_patterns = ['*.txt', '*.pdf', '*.html', '*.md', '*.csv', '*.json']

        files = []
        for pattern in file_patterns:
            if recursive:
                files.extend(directory.rglob(pattern))
            else:
                files.extend(directory.glob(pattern))

        logger.info(f"디렉토리 처리: {len(files)}개 파일 발견")

        # 메타데이터 생성
        metadata_list = [
            {
                "source_type": "file",
                "directory": str(directory),
                "relative_path": str(f.relative_to(directory)),
                "file_size": f.stat().st_size
            }
            for f in files
        ]

        return await self.process_batch(
            files, metadata_list, progress_callback
        )

# 기본 파이프라인 인스턴스
default_pipeline = IngestionPipeline()

# 유틸리티 함수들
async def process_single_document(
    source: Union[str, Path],
    **kwargs
) -> ProcessingResult:
    """단일 문서 처리 편의 함수"""
    return await default_pipeline.process_document(source, **kwargs)

async def process_documents(
    sources: List[Union[str, Path]],
    **kwargs
) -> BatchProcessingResult:
    """다중 문서 처리 편의 함수"""
    return await default_pipeline.process_batch(sources, **kwargs)