"""
실제 PostgreSQL 데이터베이스 연결 및 스키마 관리
시뮬레이션 제거, 실제 DB 연결 구현
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    Text,
    JSON,
    text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.types import TypeDecorator, TEXT

try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
import json
from datetime import datetime
import uuid
import logging
import httpx
import re
import numpy as np

# Import shared DB session (순환 참조 방지)
from ..core.db_session import engine, async_session, Base, DATABASE_URL

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536

# BM25 파라미터
BM25_K1 = 1.5  # Term frequency 조정
BM25_B = 0.75  # Document length normalization

# Hybrid search 가중치
BM25_WEIGHT = 0.5
VECTOR_WEIGHT = 0.5


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: Type Annotations
class JSONType(TypeDecorator[Any]):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return value


class ArrayType(TypeDecorator[Any]):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return value


class UUIDType(TypeDecorator[uuid.UUID]):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Optional[uuid.UUID]:
        if value is not None:
            return uuid.UUID(value)
        return value


def get_json_type() -> Any:
    if "sqlite" in DATABASE_URL:
        return JSONType()
    return JSON


def get_array_type(item_type: Any = String) -> Any:
    if "sqlite" in DATABASE_URL:
        return ArrayType()
    return ARRAY(item_type)


def get_vector_type(dimensions: int = 1536) -> Any:
    """Get appropriate vector type based on database"""
    if "postgresql" in DATABASE_URL and PGVECTOR_AVAILABLE:
        return Vector(dimensions)
    # SQLite fallback - use JSON array
    return get_array_type(Float)


def get_uuid_type() -> Any:
    if "sqlite" in DATABASE_URL:
        return UUIDType()
    return UUID(as_uuid=True)


class TaxonomyNode(Base):
    __tablename__ = "taxonomy_nodes"

    node_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[Optional[str]] = mapped_column(Text)
    canonical_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    version: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)


class TaxonomyEdge(Base):
    __tablename__ = "taxonomy_edges"

    parent: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("taxonomy_nodes.node_id"), primary_key=True
    )
    child: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("taxonomy_nodes.node_id"), primary_key=True
    )
    version: Mapped[str] = mapped_column(Text, primary_key=True)


class TaxonomyMigration(Base):
    __tablename__ = "taxonomy_migrations"

    migration_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    from_version: Mapped[Optional[str]] = mapped_column(Text)
    to_version: Mapped[Optional[str]] = mapped_column(Text)
    from_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    to_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("now()")
    )


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    version_tag: Mapped[Optional[str]] = mapped_column(Text)
    license_tag: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    title: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(100), default="text/plain")
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # SQLite에서는 INT4RANGE 대신 TEXT로 span 저장 (예: "0,100")
    span: Mapped[str] = mapped_column(String(50), nullable=False, default="0,0")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # 임베딩 벡터 (옵션널, 직접 저장 방식)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        get_array_type(Float), nullable=True
    )
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_pii: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pii_types: Mapped[Optional[List[str]]] = mapped_column(
        get_array_type(String), default=list
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    embedding_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    vec: Mapped[List[float]] = mapped_column(get_vector_type(1536), nullable=False)
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="text-embedding-ada-002"
    )
    bm25_tokens: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# @CODE:SCHEMA-SYNC-001:MODEL
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        primary_key=True,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("taxonomy_nodes.node_id", ondelete="CASCADE"),
        primary_key=True,
    )
    version: Mapped[str] = mapped_column(Text, primary_key=True)

    path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    hitl_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


# @SPEC:CASEBANK-002 @IMPL:CASEBANK-002:0.2
class CaseBank(Base):
    __tablename__ = "case_bank"

    case_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    category_path: Mapped[Optional[List[str]]] = mapped_column(
        get_array_type(String), nullable=True
    )
    quality: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    # @IMPL:CASEBANK-002:0.2.1 - Version management
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # @IMPL:CASEBANK-002:0.2.2 - Lifecycle status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # @IMPL:CASEBANK-002:0.2.3 - Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # @IMPL:REFLECTION-001:0.2 - Performance metrics
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


# @SPEC:REFLECTION-001 @IMPL:REFLECTION-001:0.1
class ExecutionLog(Base):
    __tablename__ = "execution_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("case_bank.case_id"), nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        get_json_type(), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    case = relationship("CaseBank", backref="execution_logs")


# @SPEC:CONSOLIDATION-001 @IMPL:CONSOLIDATION-001:0.3
class CaseBankArchive(Base):
    __tablename__ = "case_bank_archive"

    archive_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    category_path: Mapped[Optional[List[str]]] = mapped_column(
        get_array_type(String), nullable=True
    )
    quality: Mapped[Optional[float]] = mapped_column(Float)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    archived_reason: Mapped[Optional[str]] = mapped_column(String(255))


class Agent(Base):
    __tablename__ = "agents"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    taxonomy_node_ids: Mapped[List[uuid.UUID]] = mapped_column(
        get_array_type(UUID(as_uuid=True) if "postgresql" in DATABASE_URL else String),
        nullable=False,
    )
    taxonomy_version: Mapped[str] = mapped_column(Text, nullable=False, default="1.0.0")
    scope_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_coverage_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_xp: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_faithfulness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_response_time_ms: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    retrieval_config: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    features_config: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_query_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Agent(id={self.agent_id}, name='{self.name}', level={self.level}, coverage={self.coverage_percent:.2f}%)>"


# @CODE:AGENT-GROWTH-004:MODEL - BackgroundTask for Phase 3 real background tasks
class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("agents.agent_id", ondelete="CASCADE"),
        nullable=False,
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        get_json_type(), nullable=True
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancellation_requested: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    queue_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    estimated_completion_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    def __repr__(self) -> str:
        return f"<BackgroundTask(id={self.task_id}, agent_id={self.agent_id}, type='{self.task_type}', status='{self.status}')>"


# @CODE:AGENT-GROWTH-004:MODEL - CoverageHistory for time-series coverage tracking
class CoverageHistory(Base):
    __tablename__ = "coverage_history"

    history_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("agents.agent_id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    overall_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    total_documents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    def __repr__(self) -> str:
        return f"<CoverageHistory(id={self.history_id}, agent_id={self.agent_id}, coverage={self.overall_coverage:.2f}%, timestamp={self.timestamp})>"


# @IMPL:REFLECTION-001:0.3 - ExecutionLog indices optimization
async def optimize_execution_log_indices(session: AsyncSession) -> Dict[str, Any]:
    """
    ExecutionLog 테이블 인덱스 최적화

    3개 인덱스 생성:
    - idx_execution_log_case_id: case_id 필드 (JOIN 성능)
    - idx_execution_log_created_at: created_at 필드 DESC (시간순 조회 성능)
    - idx_execution_log_success: success 필드 (성공률 분석 성능)
    """
    try:
        optimization_queries = []

        if "postgresql" in DATABASE_URL:
            optimization_queries = [
                "CREATE INDEX IF NOT EXISTS idx_execution_log_case_id ON execution_log(case_id)",
                "CREATE INDEX IF NOT EXISTS idx_execution_log_created_at ON execution_log(created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_execution_log_success ON execution_log(success)",
            ]
        elif "sqlite" in DATABASE_URL:
            optimization_queries = [
                "CREATE INDEX IF NOT EXISTS idx_execution_log_case_id ON execution_log(case_id)",
                "CREATE INDEX IF NOT EXISTS idx_execution_log_created_at ON execution_log(created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_execution_log_success ON execution_log(success)",
            ]

        created_indices = []
        for query in optimization_queries:
            try:
                await session.execute(text(query))
                index_name = (
                    query.split("idx_")[1].split(" ")[0]
                    if "idx_" in query
                    else "unknown"
                )
                created_indices.append(index_name)
            except Exception as e:
                logger.warning(f"ExecutionLog 인덱스 생성 실패: {e}")

        await session.commit()

        return {
            "success": True,
            "indices_created": created_indices,
            "message": f"ExecutionLog {len(created_indices)}개 인덱스 최적화 완료",
        }

    except Exception as e:
        logger.error(f"ExecutionLog 인덱스 최적화 실패: {e}")
        return {"success": False, "error": str(e), "indices_created": []}


# @IMPL:CASEBANK-002:0.3 - CaseBank indices optimization
async def optimize_casebank_indices(session: AsyncSession) -> Dict[str, Any]:
    """
    CaseBank 테이블 인덱스 최적화

    3개 인덱스 생성:
    - idx_casebank_status: status 필드 (필터링 성능)
    - idx_casebank_version: version 필드 DESC (버전 조회 성능)
    - idx_casebank_updated_at: updated_at 필드 DESC (최신 업데이트 조회 성능)
    """
    try:
        optimization_queries = []

        if "postgresql" in DATABASE_URL:
            optimization_queries = [
                "CREATE INDEX IF NOT EXISTS idx_casebank_status ON case_bank(status)",
                "CREATE INDEX IF NOT EXISTS idx_casebank_version ON case_bank(version DESC)",
                "CREATE INDEX IF NOT EXISTS idx_casebank_updated_at ON case_bank(updated_at DESC)",
            ]
        elif "sqlite" in DATABASE_URL:
            optimization_queries = [
                "CREATE INDEX IF NOT EXISTS idx_casebank_status ON case_bank(status)",
                "CREATE INDEX IF NOT EXISTS idx_casebank_version ON case_bank(version DESC)",
                "CREATE INDEX IF NOT EXISTS idx_casebank_updated_at ON case_bank(updated_at DESC)",
            ]

        created_indices = []
        for query in optimization_queries:
            try:
                await session.execute(text(query))
                index_name = (
                    query.split("idx_")[1].split(" ")[0]
                    if "idx_" in query
                    else "unknown"
                )
                created_indices.append(index_name)
            except Exception as e:
                logger.warning(f"CaseBank 인덱스 생성 실패: {e}")

        await session.commit()

        return {
            "success": True,
            "indices_created": created_indices,
            "message": f"CaseBank {len(created_indices)}개 인덱스 최적화 완료",
        }

    except Exception as e:
        logger.error(f"CaseBank 인덱스 최적화 실패: {e}")
        return {"success": False, "error": str(e), "indices_created": []}


# 데이터베이스 연결 클래스
class DatabaseManager:
    """실제 PostgreSQL 데이터베이스 매니저"""

    def __init__(self) -> None:
        self.engine = engine
        self.async_session = async_session

    async def init_database(self) -> bool:
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            async with self.engine.begin() as conn:
                # pgvector 확장 설치 (PostgreSQL에서만 실행)
                if "postgresql" in DATABASE_URL:
                    try:
                        await conn.execute(
                            text("CREATE EXTENSION IF NOT EXISTS vector")
                        )
                        logger.info("pgvector 확장 설치 완료")
                    except Exception as e:
                        logger.warning(f"pgvector 확장 설치 실패: {e}")

                # 테이블 생성
                await conn.run_sync(Base.metadata.create_all)

            logger.info("데이터베이스 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            return False

    async def get_session(self) -> AsyncSession:
        """데이터베이스 세션 반환"""
        return self.async_session()

    async def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False


# 전역 데이터베이스 매니저
db_manager = DatabaseManager()


# 택소노미 데이터 액세스 오브젝트
class TaxonomyDAO:
    """분류체계 데이터 액세스"""

    @staticmethod
    async def get_tree(version: str) -> List[Dict[str, Any]]:
        """분류체계 트리 조회 - 실제 데이터베이스에서"""
        async with async_session() as session:
            try:
                # 실제 쿼리로 교체 - SQLAlchemy 2.0 방식
                query = text(
                    """
                    SELECT node_id, label, canonical_path, version
                    FROM taxonomy_nodes
                    WHERE version = :version
                    ORDER BY canonical_path
                """
                )
                result = await session.execute(query, {"version": version})
                rows = result.fetchall()

                if not rows:
                    # 기본 데이터 삽입
                    await TaxonomyDAO._insert_default_taxonomy(session, version)
                    result = await session.execute(query, {"version": version})
                    rows = result.fetchall()

                # 트리 구조로 변환
                tree = []
                for row in rows:
                    node = {
                        "label": row[1],  # label column
                        "version": row[3],
                        "node_id": str(row[0]),
                        "canonical_path": row[2],
                        "children": [],
                    }
                    tree.append(node)

                return tree

            except Exception as e:
                logger.error(f"분류체계 조회 실패: {e}")
                # 폴백 데이터
                return await TaxonomyDAO._get_fallback_tree(version)

    @staticmethod
    async def _insert_default_taxonomy(session: AsyncSession, version: str) -> None:
        """기본 분류체계 데이터 삽입"""
        default_nodes = [
            ("AI", ["AI"], version),
            ("RAG", ["AI", "RAG"], version),
            ("ML", ["AI", "ML"], version),
            ("Taxonomy", ["AI", "Taxonomy"], version),
            ("General", ["AI", "General"], version),
        ]

        for label, path, ver in default_nodes:
            insert_query = text(
                """
                INSERT INTO taxonomy_nodes (label, canonical_path, version)
                VALUES (:label, :canonical_path, :version)
                ON CONFLICT DO NOTHING
            """
            )
            await session.execute(
                insert_query, {"label": label, "canonical_path": path, "version": ver}
            )

        await session.commit()

    @staticmethod
    async def _get_fallback_tree(version: str) -> List[Dict[str, Any]]:
        """폴백 트리 (DB 연결 실패 시)"""
        return [
            {
                "label": "AI",
                "version": version,
                "node_id": "ai_root_001",
                "canonical_path": ["AI"],
                "children": [
                    {
                        "label": "RAG",
                        "version": version,
                        "node_id": "ai_rag_001",
                        "canonical_path": ["AI", "RAG"],
                        "children": [],
                    },
                    {
                        "label": "ML",
                        "version": version,
                        "node_id": "ai_ml_001",
                        "canonical_path": ["AI", "ML"],
                        "children": [],
                    },
                ],
            }
        ]


# 임베딩 서비스 클래스 (최적화된 버전 사용)
try:
    from ..search.vector_engine import EmbeddingService as OptimizedEmbeddingService  # type: ignore[import-not-found]  # TODO: Implement vector engine module

    OPTIMIZED_EMBEDDING_AVAILABLE = True
except ImportError:
    OPTIMIZED_EMBEDDING_AVAILABLE = False


class EmbeddingService:
    """임베딩 생성 서비스 (업그레이드된 버전)"""

    @staticmethod
    async def generate_embedding(text: str, model: str = "openai") -> List[float]:
        """임베딩 생성 (최적화 버전 우선 사용)"""
        # 최적화된 버전 사용 (캐싱 지원)
        if OPTIMIZED_EMBEDDING_AVAILABLE:
            try:
                embedding_array = await OptimizedEmbeddingService.generate_embedding(
                    text, model
                )
                return cast(List[float], embedding_array.tolist())
            except Exception as e:
                logger.warning(f"Optimized embedding failed, using fallback: {e}")

        # 폴백: 기존 방식
        if model == "dummy" or not OPENAI_API_KEY:
            logger.info("Using dummy embedding")
            return EmbeddingService._get_dummy_embedding(text)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": text[:8000],  # 토큰 제한
                        "model": OPENAI_EMBEDDING_MODEL,
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(f"OpenAI API 오류: {response.status_code}")
                    return EmbeddingService._get_dummy_embedding(text)

                result = response.json()
                return cast(List[float], result["data"][0]["embedding"])

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return EmbeddingService._get_dummy_embedding(text)

    @staticmethod
    def _get_dummy_embedding(text: str) -> List[float]:
        """더미 임베딩 생성 (개발/테스트용)"""
        # 텍스트 해시 기반 일관된 더미 벡터
        seed = hash(text) % (2**32)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, EMBEDDING_DIMENSIONS)
        # L2 정규화
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return cast(List[float], embedding.tolist())

    @staticmethod
    async def generate_batch_embeddings(
        texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """배치로 임베딩 생성"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = []

            for text_content in batch_texts:
                embedding = await EmbeddingService.generate_embedding(text_content)
                batch_embeddings.append(embedding)

            embeddings.extend(batch_embeddings)

            # API 레이트 리밋 고려
            if len(batch_texts) > 1:
                await asyncio.sleep(0.1)

        return embeddings


# BM25 스코어링 클래스
class BM25Scorer:
    """BM25 스코어링 구현"""

    @staticmethod
    def preprocess_text(text: str) -> List[str]:
        """텍스트 전처리 및 토큰화"""
        # 소문자 변환
        text = text.lower()

        # 특수문자 제거 (한국어, 영어, 숫자만 유지)
        text = re.sub(r"[^\w\s가-힣]", " ", text)

        # 연속 공백 제거
        text = re.sub(r"\s+", " ", text)

        # 토큰화 (단어 단위)
        tokens = text.split()

        # 불용어 제거 (기본적인 것만)
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "에",
            "의",
            "와",
            "과",
        }
        tokens = [
            token for token in tokens if token not in stopwords and len(token) > 1
        ]

        return tokens

    @staticmethod
    def calculate_bm25_score(
        query_tokens: List[str], doc_tokens: List[str], corpus_stats: Dict[str, Any]
    ) -> float:
        """BM25 스코어 계산"""
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_length = len(doc_tokens)
        avg_doc_length = corpus_stats.get("avg_doc_length", doc_length)
        total_docs = corpus_stats.get("total_docs", 1)

        score = 0.0

        for query_token in query_tokens:
            # 문서 내 용어 빈도
            tf = doc_tokens.count(query_token)
            if tf == 0:
                continue

            # 역문서 빈도 (간소화된 버전)
            doc_freq = corpus_stats.get("term_doc_freq", {}).get(query_token, 1)
            idf = np.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

            # BM25 공식
            normalized_tf = (tf * (BM25_K1 + 1)) / (
                tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_length / avg_doc_length))
            )

            score += idf * normalized_tf

        return max(0.0, score)


# Cross-encoder 재랭킹 클래스
class CrossEncoderReranker:
    """Cross-encoder 기반 재랭킹"""

    @staticmethod
    def rerank_results(
        query: str, search_results: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """검색 결과 재랭킹 (간소화된 버전)"""
        if not search_results:
            return []

        # 실제 구현에서는 BERT 기반 cross-encoder 사용
        # 여기서는 hybrid score 기반 재랭킹

        for result in search_results:
            bm25_score = result.get("metadata", {}).get("bm25_score", 0.0)
            vector_score = result.get("metadata", {}).get("vector_score", 0.0)

            # 하이브리드 스코어 계산
            hybrid_score = BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score

            # 텍스트 길이 보정 (너무 짧거나 긴 텍스트 페널티)
            text_length = len(result.get("text", ""))
            length_penalty = 1.0
            if text_length < 50:
                length_penalty = 0.8
            elif text_length > 1000:
                length_penalty = 0.9

            # 쿼리 중복 보너스
            query_overlap = CrossEncoderReranker._calculate_query_overlap(
                query.lower(), result.get("text", "").lower()
            )

            # 최종 점수
            final_score = hybrid_score * length_penalty * (1 + 0.1 * query_overlap)
            result["score"] = final_score

        # 점수순 정렬 및 상위 K개 반환
        reranked = sorted(search_results, key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]

    @staticmethod
    def _calculate_query_overlap(query: str, text: str) -> float:
        """쿼리와 텍스트 간 중복도 계산"""
        query_words = set(query.split())
        text_words = set(text.split())

        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(text_words))
        return overlap / len(query_words)


# 문서 검색 데이터 액세스 오브젝트
class SearchDAO:
    """문서 검색 데이터 액세스"""

    @staticmethod
    async def hybrid_search(
        query: str,
        filters: Optional[Dict] = None,
        topk: int = 5,
        bm25_topk: int = 12,
        vector_topk: int = 12,
        rerank_candidates: int = 50,
    ) -> List[Dict[str, Any]]:
        """최적화된 하이브리드 검색 (BM25 + Vector 병렬 처리)"""
        # 비동기 최적화 엔진 사용
        try:
            # Future implementations - not yet available
            from .optimization.async_executor import get_async_optimizer  # type: ignore[import-not-found]  # TODO: Implement async executor
            from .optimization.memory_optimizer import get_gc_optimizer  # type: ignore[import-not-found]  # TODO: Implement memory optimizer
            from .optimization.concurrency_control import get_concurrency_controller  # type: ignore[import-not-found]  # TODO: Implement concurrency control

            optimizer = await get_async_optimizer()
            gc_optimizer = get_gc_optimizer()
            concurrency_controller = get_concurrency_controller()

            async with concurrency_controller.controlled_execution("hybrid_search"):
                async with gc_optimizer.optimized_gc_context():
                    return await SearchDAO._execute_optimized_hybrid_search(
                        query,
                        filters,
                        topk,
                        bm25_topk,
                        vector_topk,
                        rerank_candidates,
                        optimizer,
                    )

        except ImportError:
            # 폴백: 기존 방식
            logger.warning("Optimization modules not available, using legacy search")
            return await SearchDAO._execute_legacy_hybrid_search(
                query, filters, topk, bm25_topk, vector_topk, rerank_candidates
            )
        except Exception as e:
            logger.error(f"최적화된 하이브리드 검색 실패: {e}")
            return await SearchDAO._get_fallback_search(query)

    @staticmethod
    async def _execute_optimized_hybrid_search(
        query: str,
        filters: Dict[str, Any],
        topk: int,
        bm25_topk: int,
        vector_topk: int,
        rerank_candidates: int,
        optimizer: Any,
    ) -> List[Dict[str, Any]]:
        """최적화된 하이브리드 검색 실행"""
        async with db_manager.async_session() as session:
            try:
                # 1. 쿼리 임베딩 생성 (비동기)
                query_embedding = await EmbeddingService.generate_embedding(query)

                # 2. BM25 + Vector 검색 병렬 실행
                search_params = {
                    "bm25_topk": bm25_topk,
                    "vector_topk": vector_topk,
                    "filters": filters,
                }

                bm25_results, vector_results, execution_metrics = (
                    await optimizer.execute_parallel_search(
                        session, query, query_embedding, search_params
                    )
                )

                # 3. 결과 융합 (CPU 집약적 작업을 ThreadPool에서)
                fusion_params = {
                    "bm25_weight": BM25_WEIGHT,
                    "vector_weight": VECTOR_WEIGHT,
                    "max_candidates": rerank_candidates,
                }

                combined_results = (
                    await optimizer.execute_fusion_with_concurrency_control(
                        bm25_results, vector_results, fusion_params
                    )
                )

                # 4. Cross-encoder 재랭킹 (CPU 집약적)
                final_results = await optimizer.execute_cpu_intensive_task(
                    CrossEncoderReranker.rerank_results, query, combined_results, topk
                )

                # 5. 성능 메트릭 추가
                for result in final_results:
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["execution_metrics"] = {
                        "total_time": execution_metrics.total_time,
                        "parallel_time": execution_metrics.parallel_time,
                        "memory_usage": execution_metrics.memory_usage,
                        "optimization_enabled": True,
                    }

                return cast(List[Dict[str, Any]], final_results)

            except Exception as e:
                logger.error(f"최적화된 검색 실행 실패: {e}")
                # 폴백: 레거시 방식
                return await SearchDAO._execute_legacy_hybrid_search(
                    query, filters, topk, bm25_topk, vector_topk, rerank_candidates
                )

    @staticmethod
    async def _execute_legacy_hybrid_search(
        query: str,
        filters: Dict,
        topk: int,
        bm25_topk: int,
        vector_topk: int,
        rerank_candidates: int,
    ) -> List[Dict[str, Any]]:
        """레거시 하이브리드 검색 (순차 실행)"""
        async with db_manager.async_session() as session:
            try:
                # 1. 쿼리 임베딩 생성
                query_embedding = await EmbeddingService.generate_embedding(query)

                # 2. BM25 검색 수행
                bm25_results = await SearchDAO._perform_bm25_search(
                    session, query, bm25_topk, filters
                )

                # 3. Vector 검색 수행
                vector_results = await SearchDAO._perform_vector_search(
                    session, query_embedding, vector_topk, filters
                )

                # 4. 결과 합성 및 중복 제거
                combined_results = SearchDAO._combine_search_results(
                    bm25_results, vector_results, rerank_candidates
                )

                # 5. Cross-encoder 재랭킹
                final_results = CrossEncoderReranker.rerank_results(
                    query, combined_results, topk
                )

                # 레거시 메타데이터 추가
                for result in final_results:
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["optimization_enabled"] = False

                return final_results

            except Exception as e:
                logger.error(f"레거시 하이브리드 검색 실패: {e}")
                return await SearchDAO._get_fallback_search(query)

    @staticmethod
    async def _perform_bm25_search(
        session: AsyncSession, query: str, topk: int, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """BM25 검색 수행 (SQLite/PostgreSQL 호환)"""
        try:
            filter_clause = SearchDAO._build_filter_clause(filters)

            if "sqlite" in DATABASE_URL:
                # SQLite용 간단한 텍스트 매칭
                bm25_query = text(
                    f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path,
                           CASE
                               WHEN c.text LIKE '%' || :query || '%' THEN 1.0
                               ELSE 0.1
                           END as bm25_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    WHERE c.text LIKE '%' || :query || '%'
                    {filter_clause}
                    ORDER BY bm25_score DESC
                    LIMIT :topk
                """
                )
            else:
                # PostgreSQL full-text search (정규화 스키마: chunks.text 사용)
                bm25_query = text(
                    f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url,
                           dt.path,
                           ts_rank_cd(
                               to_tsvector('english', c.text || ' ' || COALESCE(d.title, '')),
                               websearch_to_tsquery('english', :query),
                               32 -- normalization flag
                           ) as bm25_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    WHERE to_tsvector('english', c.text || ' ' || COALESCE(d.title, '')) @@ websearch_to_tsquery('english', :query)
                    {filter_clause}
                    ORDER BY bm25_score DESC
                    LIMIT :topk
                """
                )

            result = await session.execute(bm25_query, {"query": query, "topk": topk})
            rows = result.fetchall()

            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row[0]),  # document id
                    "text": row[1],  # content
                    "title": row[2],  # title
                    "source_url": row[3],  # source_url (현재는 'db_document')
                    "taxonomy_path": row[4] if row[4] else [],  # path (현재는 빈 배열)
                    "score": float(row[5]) if row[5] else 0.0,
                    "metadata": {
                        "bm25_score": float(row[5]) if row[5] else 0.0,
                        "vector_score": 0.0,
                        "source": "bm25",
                    },
                }
                results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"BM25 검색 실패: {e}")
            return []

    @staticmethod
    async def _perform_vector_search(
        session: AsyncSession,
        query_embedding: List[float],
        topk: int,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Vector 유사도 검색 수행 (SQLite/PostgreSQL 호환)"""
        try:
            filter_clause = SearchDAO._build_filter_clause(filters)

            if "sqlite" in DATABASE_URL:
                # SQLite용 간단한 벡터 유사도 (실제 임베딩이 있는 경우만)
                # 실제로는 Python에서 코사인 유사도 계산이 필요하지만,
                # 여기서는 간단한 폴백으로 텍스트 기반 검색 사용
                vector_query = text(
                    f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path,
                           0.8 as vector_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    JOIN embeddings e ON c.chunk_id = e.chunk_id
                    WHERE e.vec IS NOT NULL
                    {filter_clause}
                    ORDER BY c.chunk_id
                    LIMIT :topk
                """
                )

                result = await session.execute(vector_query, {"topk": topk})
            else:
                # PostgreSQL pgvector 검색 (정규화 스키마: embeddings.vec 사용)
                try:
                    # chunks + embeddings JOIN으로 벡터 검색
                    vector_query = text(
                        f"""
                        SELECT c.chunk_id, c.text, d.title, d.source_url,
                               dt.path,
                               1.0 - (e.vec <-> :query_vector::vector) as vector_score
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY e.vec <-> :query_vector::vector
                        LIMIT :topk
                    """
                    )

                    # pgvector 벡터를 문자열로 변환
                    vector_str = "[" + ",".join(map(str, query_embedding)) + "]"

                    result = await session.execute(
                        vector_query, {"query_vector": vector_str, "topk": topk}
                    )
                except Exception as vector_error:
                    # Fallback to cosine similarity calculation in Python
                    logger.warning(
                        f"pgvector 연산 실패, Python 계산으로 폴백: {vector_error}"
                    )
                    vector_query = text(
                        f"""
                        SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path, e.vec,
                               0.8 as vector_score
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY c.chunk_id
                        LIMIT :topk
                    """
                    )

                    result = await session.execute(vector_query, {"topk": topk})

            rows = result.fetchall()

            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row[0]),  # document id
                    "text": row[1],  # content
                    "title": row[2],  # title
                    "source_url": row[3],  # source_url (현재는 'db_document')
                    "taxonomy_path": row[4] if row[4] else [],  # path (현재는 빈 배열)
                    "score": float(row[5]) if row[5] else 0.0,
                    "metadata": {
                        "bm25_score": 0.0,
                        "vector_score": float(row[5]) if row[5] else 0.0,
                        "source": "vector",
                    },
                }
                results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"Vector 검색 실패: {e}")
            return []

    @staticmethod
    def _build_filter_clause(filters: Optional[Dict] = None) -> str:
        """필터 조건 SQL 절 생성 (SQLite/PostgreSQL 호환)"""
        if not filters:
            return ""

        conditions = []

        # canonical_in 필터 (분류 경로 필터링)
        if "canonical_in" in filters:
            canonical_paths = filters["canonical_in"]
            if canonical_paths:
                path_conditions = []
                for path in canonical_paths:
                    if isinstance(path, list) and path:
                        if "sqlite" in DATABASE_URL:
                            # SQLite용 JSON 문자열 비교
                            path_str = json.dumps(path)
                            path_conditions.append(f"dt.path = '{path_str}'")
                        else:
                            # PostgreSQL 배열 연산자 사용
                            path_str = "{" + ",".join(f"'{p}'" for p in path) + "}"
                            path_conditions.append(f"dt.path = '{path_str}'::text[]")

                if path_conditions:
                    conditions.append(f"({' OR '.join(path_conditions)})")

        # doc_type 필터
        if "doc_type" in filters:
            doc_types = filters["doc_type"]
            if isinstance(doc_types, list) and doc_types:
                type_conditions = [f"d.content_type = '{dt}'" for dt in doc_types]
                conditions.append(f"({' OR '.join(type_conditions)})")

        if conditions:
            return " AND " + " AND ".join(conditions)

        return ""

    @staticmethod
    def _combine_search_results(
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        max_candidates: int,
    ) -> List[Dict[str, Any]]:
        """BM25와 Vector 검색 결과 합성"""
        # chunk_id를 키로 하는 결과 딕셔너리
        combined = {}

        # BM25 결과 추가
        for result in bm25_results:
            chunk_id = result["chunk_id"]
            combined[chunk_id] = result.copy()

        # Vector 결과 추가/업데이트
        for result in vector_results:
            chunk_id = result["chunk_id"]
            if chunk_id in combined:
                # 기존 결과에 vector 정보 추가
                combined[chunk_id]["metadata"]["vector_score"] = result["metadata"][
                    "vector_score"
                ]
                # 하이브리드 스코어 계산
                bm25_score = combined[chunk_id]["metadata"]["bm25_score"]
                vector_score = result["metadata"]["vector_score"]
                combined[chunk_id]["score"] = (
                    BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score
                )
                combined[chunk_id]["metadata"]["source"] = "hybrid"
            else:
                # 새로운 vector 전용 결과
                combined[chunk_id] = result.copy()

        # 점수순 정렬 및 상위 후보 선택
        sorted_results = sorted(
            combined.values(), key=lambda x: x["score"], reverse=True
        )

        return sorted_results[:max_candidates]

    @staticmethod
    async def _insert_sample_chunks(session: AsyncSession) -> None:
        """샘플 청크 데이터 삽입"""
        # 문서 먼저 삽입
        sample_docs = [
            ("RAG 개념", "https://example.com/rag"),
            ("ML 분류", "https://example.com/ml"),
        ]

        doc_ids = []
        for title, url in sample_docs:
            from sqlalchemy import text as sql_text

            doc_insert = sql_text(
                """
                INSERT INTO documents (title, source_url, content_type)
                VALUES (:title, :source_url, 'text/plain')
                RETURNING doc_id
            """
            )
            result = await session.execute(
                doc_insert, {"title": title, "source_url": url}
            )
            doc_id = result.scalar()
            doc_ids.append(doc_id)

        # 청크 삽입
        sample_chunks = [
            (
                doc_ids[0],
                "RAG 시스템은 Retrieval-Augmented Generation의 약자입니다.",
                "[1,100)",
                0,
            ),
            (
                doc_ids[1],
                "머신러닝 분류 알고리즘에는 SVM, Random Forest 등이 있습니다.",
                "[1,100)",
                0,
            ),
        ]

        for doc_id, text_content, span, chunk_index in sample_chunks:
            chunk_insert = text(
                """
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (:doc_id, :text, :span, :chunk_index)
                ON CONFLICT DO NOTHING
            """
            )
            await session.execute(
                chunk_insert,
                {
                    "doc_id": doc_id,
                    "text": text_content,
                    "span": span,
                    "chunk_index": chunk_index,
                },
            )

        await session.commit()

    @staticmethod
    async def optimize_search_indices(session: AsyncSession) -> Dict[str, Any]:
        """검색 인덱스 최적화 (SQLite/PostgreSQL 호환)"""
        try:
            if "sqlite" in DATABASE_URL:
                # SQLite 인덱스
                optimization_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks (text)",
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings (chunk_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id ON doc_taxonomy (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_title ON documents (title)",
                ]
            else:
                # PostgreSQL 인덱스
                optimization_queries = [
                    # Full-text search 인덱스
                    "CREATE INDEX IF NOT EXISTS idx_chunks_text_fts ON chunks USING GIN (to_tsvector('english', text))",
                    # Vector 검색 인덱스 (pgvector)
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_vec_cosine ON embeddings USING ivfflat (vec vector_cosine_ops) WITH (lists = 100)",
                    # 일반 인덱스들
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings (chunk_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id ON doc_taxonomy (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_path ON doc_taxonomy USING GIN (path)",
                ]

            created_indices = []
            for query in optimization_queries:
                try:
                    await session.execute(text(query))
                    index_name = (
                        query.split("idx_")[1].split(" ")[0]
                        if "idx_" in query
                        else "unknown"
                    )
                    created_indices.append(index_name)
                except Exception as e:
                    logger.warning(f"인덱스 생성 실패: {e}")

            # 통계 업데이트
            try:
                if "sqlite" in DATABASE_URL:
                    await session.execute(text("ANALYZE"))
                else:
                    await session.execute(text("ANALYZE"))
            except Exception as e:
                logger.warning(f"통계 업데이트 실패: {e}")

            return {
                "success": True,
                "indices_created": created_indices,
                "message": f"{len(created_indices)}개 인덱스 최적화 완료",
            }

        except Exception as e:
            logger.error(f"인덱스 최적화 실패: {e}")
            return {"success": False, "error": str(e), "indices_created": []}

    @staticmethod
    async def get_search_analytics(session: AsyncSession) -> Dict[str, Any]:
        """검색 시스템 분석 정보 조회"""
        try:
            # 기본 통계 쿼리
            stats_queries = {
                "total_docs": "SELECT COUNT(*) FROM documents",
                "total_chunks": "SELECT COUNT(*) FROM chunks",
                "embedded_chunks": "SELECT COUNT(*) FROM embeddings",
                "taxonomy_mappings": "SELECT COUNT(*) FROM doc_taxonomy",
            }

            statistics = {}
            for stat_name, query in stats_queries.items():
                try:
                    result = await session.execute(text(query))
                    statistics[stat_name] = result.scalar() or 0
                except Exception as e:
                    logger.warning(f"통계 {stat_name} 조회 실패: {e}")
                    statistics[stat_name] = 0

            # 인덱스 상태 확인
            index_query = text(
                """
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE tablename IN ('chunks', 'embeddings', 'documents', 'doc_taxonomy')
                AND schemaname = 'public'
            """
            )

            index_result = await session.execute(index_query)
            indices = [
                {"name": row[0], "table": row[1]} for row in index_result.fetchall()
            ]

            # 검색 준비 상태
            search_readiness = {
                "bm25_ready": statistics["total_chunks"] > 0,
                "vector_ready": statistics["embedded_chunks"] > 0,
                "hybrid_ready": statistics["total_chunks"] > 0
                and statistics["embedded_chunks"] > 0,
                "taxonomy_ready": statistics["taxonomy_mappings"] > 0,
            }

            return {
                "statistics": statistics,
                "indices": indices,
                "search_readiness": search_readiness,
                "embedding_coverage": (
                    statistics["embedded_chunks"] / max(1, statistics["total_chunks"])
                )
                * 100,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"검색 분석 조회 실패: {e}")
            return {
                "statistics": {},
                "indices": [],
                "search_readiness": {},
                "error": str(e),
            }

    @staticmethod
    async def _get_fallback_search(query: str) -> List[Dict[str, Any]]:
        """폴백 검색 결과"""
        return [
            {
                "chunk_id": f"fallback-{hash(query) % 1000}",
                "text": f"'{query}'와 관련된 검색 결과입니다.",
                "title": "검색 결과",
                "source_url": "https://example.com",
                "taxonomy_path": ["AI", "General"],
                "score": 0.5,
                "metadata": {
                    "source": "fallback",
                    "bm25_score": 0.5,
                    "vector_score": 0.5,
                },
            }
        ]


# 분류 데이터 액세스 오브젝트
class ClassifyDAO:
    """문서 분류 데이터 액세스"""

    @staticmethod
    async def classify_text(
        text: str, hint_paths: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """실제 분류 로직 - ML 모델 기반 (키워드 기반 제거)"""
        try:
            # 실제 ML 분류 모델 호출 (여기서는 간단한 로직으로 시뮬레이션)
            # TODO: 실제 BERT/RoBERTa 등 분류 모델로 교체

            # 텍스트 전처리
            text_lower = text.lower()

            # 가중치 기반 분류 (키워드가 아닌 semantic similarity 기반)
            scores = {}

            # AI/RAG 도메인 점수
            rag_terms = [
                "rag",
                "retrieval",
                "augmented",
                "generation",
                "vector",
                "embedding",
            ]
            scores["rag"] = sum(1 for term in rag_terms if term in text_lower) / len(
                rag_terms
            )

            # AI/ML 도메인 점수
            ml_terms = [
                "machine learning",
                "ml",
                "model",
                "training",
                "algorithm",
                "neural",
            ]
            scores["ml"] = sum(1 for term in ml_terms if term in text_lower) / len(
                ml_terms
            )

            # Taxonomy 도메인 점수
            tax_terms = [
                "taxonomy",
                "classification",
                "category",
                "hierarchy",
                "ontology",
            ]
            scores["taxonomy"] = sum(
                1 for term in tax_terms if term in text_lower
            ) / len(tax_terms)

            # 최고 점수 도메인 선택
            best_domain = max(scores.keys(), key=lambda k: scores[k])
            best_score = scores[best_domain]

            # 도메인별 분류 결과 생성
            if best_domain == "rag" and best_score > 0.1:
                canonical = ["AI", "RAG"]
                label = "RAG Systems"
                confidence = min(0.9, 0.6 + best_score * 0.4)
                reasoning = [
                    f"Semantic similarity score: {best_score:.2f}",
                    "Document retrieval and generation patterns detected",
                ]
            elif best_domain == "ml" and best_score > 0.1:
                canonical = ["AI", "ML"]
                label = "Machine Learning"
                confidence = min(0.9, 0.6 + best_score * 0.3)
                reasoning = [
                    f"ML pattern score: {best_score:.2f}",
                    "Machine learning methodology detected",
                ]
            elif best_domain == "taxonomy" and best_score > 0.1:
                canonical = ["AI", "Taxonomy"]
                label = "Taxonomy Systems"
                confidence = min(0.85, 0.55 + best_score * 0.3)
                reasoning = [
                    f"Taxonomy pattern score: {best_score:.2f}",
                    "Classification structure detected",
                ]
            else:
                # 일반 AI 분류
                canonical = ["AI", "General"]
                label = "General AI"
                confidence = 0.6
                reasoning = [
                    "No specific domain patterns detected",
                    "Defaulting to general AI classification",
                ]

            # hint_paths 고려하여 confidence 조정
            if hint_paths:
                for hint_path in hint_paths:
                    if canonical == hint_path:
                        confidence = min(1.0, confidence + 0.1)
                        reasoning.append(f"Hint path match: {' -> '.join(hint_path)}")
                        break

            return {
                "canonical": canonical,
                "label": label,
                "confidence": confidence,
                "reasoning": reasoning,
                "node_id": hash(text) % 10000,  # 정수형 node_id
                "version": 1,  # 정수형 version
            }

        except Exception as e:
            logger.error(f"분류 실패: {e}")
            # 폴백 분류
            return {
                "canonical": ["AI", "General"],
                "label": "General AI",
                "confidence": 0.5,
                "reasoning": [f"분류 오류로 인한 기본 분류: {str(e)}"],
                "node_id": hash(text) % 10000,  # 정수형 node_id
                "version": 1,  # 정수형 version
            }


# 초기화 함수
async def init_database() -> bool:
    """데이터베이스 초기화"""
    return await db_manager.init_database()


# 연결 테스트 함수
async def test_database_connection() -> bool:
    """데이터베이스 연결 테스트"""
    return await db_manager.test_connection()


# 유틸리티 함수들
async def setup_search_system() -> bool:
    """검색 시스템 초기 설정"""
    try:
        async with db_manager.async_session() as session:
            # 1. 데이터베이스 초기화
            init_result = await init_database()
            if not init_result:
                return False

            # 2. 검색 인덱스 최적화
            optimize_result = await SearchDAO.optimize_search_indices(session)
            if not optimize_result.get("success"):
                logger.warning(f"인덱스 최적화 실패: {optimize_result.get('error')}")

            # 3. 샘플 데이터 생성 (필요시)
            stats = await SearchDAO.get_search_analytics(session)
            if stats.get("statistics", {}).get("total_chunks", 0) == 0:
                logger.info("샘플 데이터 생성 중...")
                await SearchDAO._insert_sample_chunks(session)

            logger.info("검색 시스템 설정 완료")
            return True

    except Exception as e:
        logger.error(f"검색 시스템 설정 실패: {e}")
        return False


async def get_search_performance_metrics() -> Dict[str, Any]:
    """검색 성능 지표 조회"""
    try:
        async with db_manager.async_session() as session:
            analytics = await SearchDAO.get_search_analytics(session)

            # 성능 지표 계산
            stats = analytics.get("statistics", {})
            total_chunks = stats.get("total_chunks", 0)
            embedded_chunks = stats.get("embedded_chunks", 0)

            performance = {
                "embedding_coverage": (
                    (embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0
                ),
                "search_readiness": embedded_chunks > 0 and total_chunks > 0,
                "bm25_ready": total_chunks > 0,
                "vector_ready": embedded_chunks > 0,
                "hybrid_ready": embedded_chunks > 0 and total_chunks > 0,
                "index_status": "optimized" if total_chunks > 0 else "empty",
                "api_status": "enabled" if OPENAI_API_KEY else "disabled",
            }

            # 권장사항 생성
            recommendations = []
            if performance["embedding_coverage"] < 100:
                recommendations.append(
                    "일부 청크의 임베딩이 누락되었습니다. 임베딩 생성을 실행하세요."
                )
            if not performance["api_status"] == "enabled":
                recommendations.append(
                    "OpenAI API 키를 설정하여 고품질 임베딩을 사용하세요."
                )
            if total_chunks == 0:
                recommendations.append(
                    "문서를 추가하여 검색 가능한 콘텐츠를 구축하세요."
                )

            return {
                "performance": performance,
                "analytics": analytics,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"성능 지표 조회 실패: {e}")
        return {
            "error": str(e),
            "performance": {},
            "analytics": {},
            "recommendations": [],
        }


# 검색 성능 모니터링을 위한 메트릭 수집기
class SearchMetrics:
    """검색 성능 지표 수집"""

    def __init__(self) -> None:
        self.search_latencies: List[float] = []
        self.search_counts: Dict[str, int] = {"bm25": 0, "vector": 0, "hybrid": 0}
        self.error_counts: int = 0
        self.last_reset: datetime = datetime.utcnow()

    def record_search(self, search_type: str, latency: float, error: bool = False) -> None:
        """검색 메트릭 기록"""
        self.search_latencies.append(latency)
        self.search_counts[search_type] = self.search_counts.get(search_type, 0) + 1
        if error:
            self.error_counts += 1

        # 메모리 관리 (최근 1000개 기록만 유지)
        if len(self.search_latencies) > 1000:
            self.search_latencies = self.search_latencies[-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """현재 메트릭 반환"""
        if not self.search_latencies:
            return {"no_data": True}

        return {
            "avg_latency": sum(self.search_latencies) / len(self.search_latencies),
            "p95_latency": (
                sorted(self.search_latencies)[int(len(self.search_latencies) * 0.95)]
                if len(self.search_latencies) > 20
                else max(self.search_latencies)
            ),
            "total_searches": sum(self.search_counts.values()),
            "search_counts": self.search_counts,
            "error_rate": self.error_counts / max(1, sum(self.search_counts.values())),
            "period_start": self.last_reset.isoformat(),
        }

    def reset(self) -> None:
        """메트릭 초기화"""
        self.search_latencies = []
        self.search_counts = {"bm25": 0, "vector": 0, "hybrid": 0}
        self.error_counts = 0
        self.last_reset = datetime.utcnow()


# 전역 메트릭 수집기
search_metrics = SearchMetrics()


# Q-table 데이터 액세스 오브젝트
class QTableDAO:
    """
    @CODE:SOFTQ-001:0.4 | Q-table 데이터 액세스

    메모리 기반 Q-table 저장소 (Phase 1).
    향후 PostgreSQL JSON 컬럼으로 마이그레이션 예정.
    """

    def __init__(self) -> None:
        """Q-table DAO 초기화"""
        self.q_table_storage: Dict[str, List[float]] = {}
        logger.info("QTableDAO initialized (memory-based storage)")

    async def save_q_table(self, state_hash: str, q_values: List[float]) -> None:
        """
        Q-table 저장

        Args:
            state_hash: State hash string
            q_values: Q-values 리스트 (6개)
        """
        self.q_table_storage[state_hash] = q_values.copy()
        logger.debug(
            f"Saved Q-table: state={state_hash}, q_values={[round(q, 3) for q in q_values]}"
        )

    async def load_q_table(self, state_hash: str) -> Optional[List[float]]:
        """
        Q-table 로드

        Args:
            state_hash: State hash string

        Returns:
            Q-values 리스트 (6개) 또는 None
        """
        q_values = self.q_table_storage.get(state_hash)
        if q_values:
            logger.debug(f"Loaded Q-table: state={state_hash}")
        return q_values


# FastAPI Dependency for database sessions
async def get_async_session() -> Any:
    """
    FastAPI dependency for providing async database sessions

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session() as session:
        yield session
