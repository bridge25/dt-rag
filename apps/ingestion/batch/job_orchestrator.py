import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from sqlalchemy import select, cast, Text
from sqlalchemy.dialects.postgresql import ARRAY
from apps.ingestion.contracts.signals import (
    DocumentUploadCommandV1,
    DocumentProcessedEventV1,
    ProcessingStatusV1,
    ChunkV1,
)
from apps.ingestion.parsers import ParserFactory
from apps.ingestion.chunking import IntelligentChunker
from apps.ingestion.pii import PIIDetector
from apps.api.embedding_service import EmbeddingService
from apps.core.db_session import async_session
from apps.api.database import Document, DocumentChunk, Embedding, DocTaxonomy, TaxonomyNode
from .job_queue import JobQueue

logger = logging.getLogger(__name__)


# @CODE:JOB-OPTIMIZE-001:INIT
class JobOrchestrator:
    def __init__(
        self,
        job_queue: Optional[JobQueue] = None,
        embedding_service: Optional[EmbeddingService] = None,
        max_workers: int = 10,
    ):
        self.job_queue = job_queue or JobQueue()
        self.embedding_service = embedding_service or EmbeddingService()
        self.max_workers = max_workers
        self.chunker = IntelligentChunker(chunk_size=500, overlap_size=128)
        self.pii_detector = PIIDetector()
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.internal_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.dispatcher_task: Optional[asyncio.Task] = None

    async def start(self):
        self.running = True
        await self.job_queue.initialize()

        self.dispatcher_task = asyncio.create_task(self._dispatcher())
        logger.info("Dispatcher task created")

        logger.info(f"Starting Job Orchestrator with {self.max_workers} workers")

        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker(worker_id=i))
            self.workers.append(worker_task)

        logger.info("Job Orchestrator started successfully")

    async def stop(self):
        self.running = False
        logger.info("Stopping Job Orchestrator...")

        if self.dispatcher_task:
            self.dispatcher_task.cancel()

        for worker_task in self.workers:
            worker_task.cancel()

        all_tasks = self.workers + ([self.dispatcher_task] if self.dispatcher_task else [])
        await asyncio.gather(*all_tasks, return_exceptions=True)

        self.workers.clear()
        self.dispatcher_task = None
        logger.info("Job Orchestrator stopped")

    # @CODE:JOB-OPTIMIZE-001:DISPATCHER
    async def _dispatcher(self):
        """Single Redis connection for job reception and internal queue distribution"""
        logger.info("Dispatcher started")
        retry_count = 0
        max_retries = 3

        while self.running and retry_count < max_retries:
            try:
                job_payload = await self.job_queue.dequeue_job(timeout=5)

                if job_payload:
                    await self.internal_queue.put(job_payload)
                    logger.debug(
                        f"Job dispatched to internal queue",
                        extra={
                            "job_id": job_payload['job_id'],
                            "queue_size": self.internal_queue.qsize()
                        }
                    )
                    retry_count = 0

            except asyncio.CancelledError:
                logger.info("Dispatcher cancelled")
                break
            except ConnectionError as e:
                retry_count += 1
                logger.error(
                    f"Dispatcher connection error (retry {retry_count}/{max_retries})",
                    extra={"error": str(e)}
                )
                await asyncio.sleep(min(2 ** retry_count, 30))
            except Exception as e:
                logger.error(f"Dispatcher unexpected error: {e}")
                await asyncio.sleep(1)

        if retry_count >= max_retries:
            logger.critical("Dispatcher exceeded max retries")

        logger.info("Dispatcher stopped")

    # @CODE:JOB-OPTIMIZE-001:WORKER
    async def _worker(self, worker_id: int):
        logger.info(f"Worker {worker_id} started")

        QUEUE_TIMEOUT = 5.0

        while self.running:
            try:
                try:
                    job_payload = await asyncio.wait_for(
                        self.internal_queue.get(), timeout=QUEUE_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    continue

                job_id = job_payload["job_id"]
                command_id = job_payload["command_id"]
                job_data = job_payload["data"]

                logger.info(f"Worker {worker_id} processing job {job_id}")

                await self.job_queue.set_job_status(
                    job_id=job_id,
                    command_id=command_id,
                    status="processing",
                    progress_percentage=0.0,
                    current_stage="Starting",
                    started_at=datetime.utcnow().isoformat(),
                )

                try:
                    event = await self._process_document(command_id, job_data)

                    await self.job_queue.set_job_status(
                        job_id=job_id,
                        command_id=command_id,
                        status=event.status.value,
                        progress_percentage=100.0,
                        current_stage="Completed",
                        chunks_processed=event.total_chunks,
                        total_chunks=event.total_chunks,
                        completed_at=datetime.utcnow().isoformat(),
                    )

                    logger.info(f"Worker {worker_id} completed job {job_id}")

                except Exception as e:
                    logger.error(f"Worker {worker_id} failed job {job_id}: {e}")

                    if await self._should_retry(job_id, e):
                        priority = job_data.get("priority", 5)
                        retry_success = await self.job_queue.retry_job(
                            job_id=job_id,
                            command_id=command_id,
                            job_data=job_data,
                            priority=priority
                        )
                        if retry_success:
                            logger.info(f"Job {job_id} scheduled for retry")
                            continue

                    await self.job_queue.set_job_status(
                        job_id=job_id,
                        command_id=command_id,
                        status="failed",
                        progress_percentage=0.0,
                        current_stage="Failed",
                        error_message=str(e),
                        completed_at=datetime.utcnow().isoformat(),
                    )

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def _process_document(
        self, command_id: str, job_data: Dict[str, Any]
    ) -> DocumentProcessedEventV1:
        start_time = datetime.utcnow()

        file_name = job_data["file_name"]
        file_content = bytes.fromhex(job_data["file_content_hex"])
        file_format = job_data["file_format"]

        logger.info(f"Processing document: {file_name} (format: {file_format})")

        parser = ParserFactory.get_parser(file_format)
        parsed_text = parser.parse(file_content, file_name)

        logger.info(f"Parsed {len(parsed_text)} characters from {file_name}")

        chunks = self.chunker.chunk_text(parsed_text)

        logger.info(f"Created {len(chunks)} chunks from {file_name}")

        chunk_signals = []
        for idx, chunk in enumerate(chunks):
            masked_text, pii_matches = self.pii_detector.detect_and_mask(chunk.text)

            has_pii = len(pii_matches) > 0
            pii_types = [match.pii_type.value for match in pii_matches]

            chunk_signal = ChunkV1(
                text=masked_text,
                token_count=chunk.token_count,
                position=idx,
                has_pii=has_pii,
                pii_types=pii_types,
            )

            chunk_signals.append(chunk_signal)

        logger.info(f"PII detection completed for {file_name}")

        total_tokens = sum(chunk.token_count for chunk in chunks)

        processing_duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        doc_id = uuid.uuid4()

        async with async_session() as session:
            try:
                document = Document(
                    doc_id=doc_id,
                    source_url=job_data.get("source_url"),
                    title=file_name,
                    content_type=f"application/{file_format}",
                    doc_metadata=job_data.get("metadata", {}),
                    processed_at=datetime.utcnow()
                )
                session.add(document)

                # @CODE:SCHEMA-SYNC-001:QUERY
                taxonomy_path = job_data.get("taxonomy_path")
                if taxonomy_path:
                    query = select(TaxonomyNode.node_id).where(
                        TaxonomyNode.canonical_path == cast(taxonomy_path, ARRAY(Text))
                    )
                    result = await session.execute(query)
                    node_id = result.scalar_one_or_none()

                    if not node_id:
                        error_msg = f"Taxonomy path {taxonomy_path} not found in taxonomy_nodes table"
                        logger.error(error_msg, extra={"taxonomy_path": taxonomy_path})
                        raise ValueError(error_msg)

                    doc_taxonomy = DocTaxonomy(
                        doc_id=doc_id,
                        node_id=node_id,
                        version="1.0.0",
                        path=taxonomy_path,
                        confidence=1.0,
                        hitl_required=False
                    )
                    session.add(doc_taxonomy)
                    logger.info(
                        f"Assigned taxonomy to document",
                        extra={
                            "doc_id": str(doc_id),
                            "node_id": str(node_id),
                            "taxonomy_path": taxonomy_path,
                            "version": "1.0.0"
                        }
                    )

                all_chunk_texts = [chunk_signal.text for chunk_signal in chunk_signals]

                logger.info(f"Generating embeddings for {len(all_chunk_texts)} chunks in batch")
                embedding_vectors = await self.embedding_service.batch_generate_embeddings(
                    all_chunk_texts,
                    batch_size=50,
                    show_progress=True
                )

                for idx, (chunk_signal, embedding_vector) in enumerate(zip(chunk_signals, embedding_vectors)):
                    chunk_id = uuid.uuid4()

                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        text=chunk_signal.text,
                        span=f"{chunk_signal.position},{chunk_signal.position + len(chunk_signal.text)}",
                        chunk_index=idx,
                        chunk_metadata={
                            "taxonomy_path": job_data.get("taxonomy_path"),
                            "author": job_data.get("author"),
                            "language": job_data.get("language")
                        },
                        token_count=chunk_signal.token_count,
                        has_pii=chunk_signal.has_pii,
                        pii_types=chunk_signal.pii_types,
                        created_at=datetime.utcnow()
                    )
                    session.add(chunk)

                    embedding = Embedding(
                        embedding_id=uuid.uuid4(),
                        chunk_id=chunk_id,
                        vec=embedding_vector,
                        model_name=self.embedding_service.model_name,
                        created_at=datetime.utcnow()
                    )
                    session.add(embedding)

                await session.commit()
                logger.info(f"Stored document {doc_id} with {len(chunk_signals)} chunks in database")

            except Exception as e:
                await session.rollback()
                logger.error(f"Database storage failed for {file_name}: {e}")
                raise

        correlation_id = job_data.get("correlation_id", command_id)

        event = DocumentProcessedEventV1(
            correlationId=correlation_id,
            command_id=command_id,
            status=ProcessingStatusV1.COMPLETED,
            document_id=str(doc_id),
            chunks=chunk_signals,
            total_chunks=len(chunk_signals),
            total_tokens=total_tokens,
            processing_duration_ms=processing_duration_ms,
        )

        return event

    async def submit_job(self, command: DocumentUploadCommandV1) -> str:
        job_id = str(uuid.uuid4())

        job_data = {
            "correlation_id": command.correlationId,
            "idempotency_key": command.idempotencyKey,
            "file_name": command.file_name,
            "file_content_hex": command.file_content.hex(),
            "file_format": command.file_format.value,
            "taxonomy_path": command.taxonomy_path,
            "source_url": command.source_url,
            "author": command.author,
            "language": command.language,
            "metadata": command.metadata,
        }

        success = await self.job_queue.enqueue_job(
            job_id=job_id,
            command_id=command.command_id,
            job_data=job_data,
            priority=command.priority,
            idempotency_key=command.idempotencyKey,
        )

        if not success:
            raise RuntimeError(f"Failed to enqueue job {job_id}")

        logger.info(f"Submitted job {job_id} for command {command.command_id}")

        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await self.job_queue.get_job_status(job_id)

    async def _should_retry(self, job_id: str, error: Exception) -> bool:
        status = await self.job_queue.get_job_status(job_id)
        if not status:
            return False

        retry_count = status.get("retry_count", 0)
        max_retries = status.get("max_retries", 3)

        if retry_count >= max_retries:
            logger.info(f"Job {job_id} reached max retries ({max_retries})")
            return False

        non_retryable_errors = [
            "ParserError",
            "ValidationError",
            "AuthenticationError"
        ]

        error_type = type(error).__name__
        if any(err in error_type for err in non_retryable_errors):
            logger.info(f"Job {job_id} has non-retryable error: {error_type}")
            return False

        logger.info(f"Job {job_id} eligible for retry ({retry_count}/{max_retries})")
        return True
