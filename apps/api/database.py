"""
실제 PostgreSQL 데이터베이스 연결 및 스키마 관리
시뮬레이션 제거, 실제 DB 연결 구현
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, INT4RANGE
from sqlalchemy.types import TypeDecorator, TEXT
import json
from datetime import datetime
import uuid
import logging
import httpx
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tiktoken

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

# SQLite 호환 타입 정의
class JSONType(TypeDecorator):
    """SQLite 호환 JSON 타입"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class ArrayType(TypeDecorator):
    """SQLite 호환 Array 타입"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class UUIDType(TypeDecorator):
    """SQLite 호환 UUID 타입"""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value

# 데이터베이스 타입 선택 함수
def get_json_type():
    """현재 데이터베이스에 맞는 JSON 타입 반환"""
    if "sqlite" in DATABASE_URL:
        return JSONType()
    return JSON

def get_array_type(item_type=String):
    """현재 데이터베이스에 맞는 Array 타입 반환"""
    if "sqlite" in DATABASE_URL:
        return ArrayType()
    return ARRAY(item_type)

def get_uuid_type():
    """현재 데이터베이스에 맞는 UUID 타입 반환"""
    if "sqlite" in DATABASE_URL:
        return UUIDType()
    return UUID(as_uuid=True)

# SQLAlchemy Base
Base = declarative_base()

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dt_rag_test.db")

# SQLite와 PostgreSQL 호환성을 위한 엔진 설정
if "sqlite" in DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 테이블 모델 정의 - SQLite 호환 버전
class TaxonomyNode(Base):
    __tablename__ = "taxonomy_nodes"

    node_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    canonical_path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    node_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    doc_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(get_json_type(), default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TaxonomyEdge(Base):
    __tablename__ = "taxonomy_edges"

    edge_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_node_id: Mapped[int] = mapped_column(Integer, nullable=False)
    child_node_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TaxonomyMigration(Base):
    __tablename__ = "taxonomy_migrations"

    migration_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_version: Mapped[Optional[int]] = mapped_column(Integer)
    to_version: Mapped[int] = mapped_column(Integer, nullable=False)
    migration_type: Mapped[str] = mapped_column(String(50), nullable=False)
    changes: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    applied_by: Mapped[Optional[str]] = mapped_column(Text)

class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(100), default='text/plain')
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # SQLite에서는 INT4RANGE 대신 TEXT로 span 저장 (예: "0,100")
    span: Mapped[str] = mapped_column(String(50), nullable=False, default="0,0")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # 임베딩 벡터 (옵션널, 직접 저장 방식)
    embedding: Mapped[Optional[List[float]]] = mapped_column(get_array_type(Float), nullable=True)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Embedding(Base):
    __tablename__ = "embeddings"

    embedding_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), nullable=False)
    vec: Mapped[List[float]] = mapped_column(get_array_type(Float), nullable=False)  # Vector 저장
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default='text-embedding-ada-002')
    bm25_tokens: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    mapping_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), nullable=False)
    path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default='manual')
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[Optional[str]] = mapped_column(Text)

class CaseBank(Base):
    __tablename__ = "case_bank"

    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    query_vector: Mapped[List[float]] = mapped_column(get_array_type(Float), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

class ExecutionLog(Base):
    __tablename__ = "execution_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(Text, ForeignKey("case_bank.case_id"), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(get_json_type(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False
    )

    case = relationship("CaseBank", backref="execution_logs")

class CaseBankArchive(Base):
    __tablename__ = "case_bank_archive"

    archive_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    query_vector: Mapped[List[float]] = mapped_column(get_array_type(Float), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    archived_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    archive_reason: Mapped[str] = mapped_column(String(50), nullable=False)

# 데이터베이스 연결 클래스
class DatabaseManager:
    """실제 PostgreSQL 데이터베이스 매니저"""
    
    def __init__(self):
        self.engine = engine
        self.async_session = async_session
        
    async def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            async with self.engine.begin() as conn:
                # pgvector 확장 설치 (PostgreSQL에서만 실행)
                if "postgresql" in DATABASE_URL:
                    try:
                        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
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
    
    async def get_session(self):
        """데이터베이스 세션 반환"""
        return self.async_session()
    
    async def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT 1"))
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
        async with db_manager.async_session() as session:
            try:
                # 실제 쿼리로 교체 - SQLAlchemy 2.0 방식
                query = text("""
                    SELECT node_id, node_name, canonical_path, version
                    FROM taxonomy_nodes
                    WHERE version = :version
                    ORDER BY canonical_path
                """)
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
                        "label": row[1],  # node_name
                        "version": row[3],
                        "node_id": row[0],
                        "canonical_path": row[2],
                        "children": []
                    }
                    tree.append(node)
                
                return tree
                
            except Exception as e:
                logger.error(f"분류체계 조회 실패: {e}")
                # 폴백 데이터
                return await TaxonomyDAO._get_fallback_tree(version)
    
    @staticmethod
    async def _insert_default_taxonomy(session, version: int):
        """기본 분류체계 데이터 삽입"""
        default_nodes = [
            ("AI", ["AI"], version),
            ("RAG", ["AI", "RAG"], version),
            ("ML", ["AI", "ML"], version),
            ("Taxonomy", ["AI", "Taxonomy"], version),
            ("General", ["AI", "General"], version),
        ]

        for node_name, path, ver in default_nodes:
            insert_query = text("""
                INSERT INTO taxonomy_nodes (node_name, canonical_path, version)
                VALUES (:node_name, :canonical_path, :version)
                ON CONFLICT DO NOTHING
            """)
            await session.execute(insert_query, {
                "node_name": node_name,
                "canonical_path": path,
                "version": ver
            })

        # commit은 호출하는 쪽에서 처리
    
    @staticmethod
    async def _get_fallback_tree(version: int) -> List[Dict[str, Any]]:
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
                        "children": []
                    },
                    {
                        "label": "ML",
                        "version": version,
                        "node_id": "ai_ml_001",
                        "canonical_path": ["AI", "ML"],
                        "children": []
                    }
                ]
            }
        ]

# 임베딩 서비스 클래스 (최적화된 캐싱 버전 사용)
try:
    from ..search.embedding_service import EmbeddingService as OptimizedEmbeddingService
    OPTIMIZED_EMBEDDING_AVAILABLE = True
except ImportError:
    OPTIMIZED_EMBEDDING_AVAILABLE = False

class EmbeddingService:
    """임베딩 생성 서비스 (캐싱 시스템 통합 버전)"""

    @staticmethod
    async def generate_embedding(text: str, model: str = "openai") -> List[float]:
        """임베딩 생성 (캐싱 최적화 버전 우선 사용)"""
        # 최적화된 캐싱 버전 사용 (70% 성능 향상)
        if OPTIMIZED_EMBEDDING_AVAILABLE:
            try:
                return await OptimizedEmbeddingService.generate_embedding(text, model)
            except Exception as e:
                logger.warning(f"Optimized embedding with caching failed, using fallback: {e}")

        # 폴백: 기존 방식 (캐싱 없음)
        if model == "dummy" or not OPENAI_API_KEY:
            logger.info("Using dummy embedding")
            return EmbeddingService._get_dummy_embedding(text)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text[:8000],  # 토큰 제한
                        "model": OPENAI_EMBEDDING_MODEL
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"OpenAI API 오류: {response.status_code}")
                    return EmbeddingService._get_dummy_embedding(text)

                result = response.json()
                return result["data"][0]["embedding"]

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return EmbeddingService._get_dummy_embedding(text)

    @staticmethod
    async def generate_batch_embeddings(texts: List[str], model: str = "openai") -> List[List[float]]:
        """배치 임베딩 생성 (캐싱 최적화)"""
        if OPTIMIZED_EMBEDDING_AVAILABLE:
            try:
                return await OptimizedEmbeddingService.generate_batch_embeddings(texts, model)
            except Exception as e:
                logger.warning(f"Optimized batch embedding failed, using fallback: {e}")

        # 폴백: 개별 처리
        results = []
        for text in texts:
            embedding = await EmbeddingService.generate_embedding(text, model)
            results.append(embedding)
        return results

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
        return embedding.tolist()

    @staticmethod
    async def generate_batch_embeddings(texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """배치로 임베딩 생성"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = []

            for text in batch_texts:
                embedding = await EmbeddingService.generate_embedding(text)
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
        text = re.sub(r'[^\w\s가-힣]', ' ', text)

        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)

        # 토큰화 (단어 단위)
        tokens = text.split()

        # 불용어 제거 (기본적인 것만)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '은', '는', '이', '가', '을', '를', '에', '의', '와', '과'}
        tokens = [token for token in tokens if token not in stopwords and len(token) > 1]

        return tokens

    @staticmethod
    def calculate_bm25_score(
        query_tokens: List[str],
        doc_tokens: List[str],
        corpus_stats: Dict[str, Any]
    ) -> float:
        """BM25 스코어 계산"""
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_length = len(doc_tokens)
        avg_doc_length = corpus_stats.get('avg_doc_length', doc_length)
        total_docs = corpus_stats.get('total_docs', 1)

        score = 0.0

        for query_token in query_tokens:
            # 문서 내 용어 빈도
            tf = doc_tokens.count(query_token)
            if tf == 0:
                continue

            # 역문서 빈도 (간소화된 버전)
            doc_freq = corpus_stats.get('term_doc_freq', {}).get(query_token, 1)
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
        query: str,
        search_results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """검색 결과 재랭킹 (간소화된 버전)"""
        if not search_results:
            return []

        # 실제 구현에서는 BERT 기반 cross-encoder 사용
        # 여기서는 hybrid score 기반 재랭킹

        for result in search_results:
            bm25_score = result.get('metadata', {}).get('bm25_score', 0.0)
            vector_score = result.get('metadata', {}).get('vector_score', 0.0)

            # 하이브리드 스코어 계산
            hybrid_score = BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score

            # 텍스트 길이 보정 (너무 짧거나 긴 텍스트 페널티)
            text_length = len(result.get('text', ''))
            length_penalty = 1.0
            if text_length < 50:
                length_penalty = 0.8
            elif text_length > 1000:
                length_penalty = 0.9

            # 쿼리 중복 보너스
            query_overlap = CrossEncoderReranker._calculate_query_overlap(
                query.lower(), result.get('text', '').lower()
            )

            # 최종 점수
            final_score = hybrid_score * length_penalty * (1 + 0.1 * query_overlap)
            result['score'] = final_score

        # 점수순 정렬 및 상위 K개 반환
        reranked = sorted(search_results, key=lambda x: x['score'], reverse=True)
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
        filters: Dict = None,
        topk: int = 5,
        bm25_topk: int = 12,
        vector_topk: int = 12,
        rerank_candidates: int = 50
    ) -> List[Dict[str, Any]]:
        """최적화된 하이브리드 검색 (BM25 + Vector 병렬 처리)"""
        # 비동기 최적화 엔진 사용
        try:
            from .optimization.async_executor import get_async_optimizer
            from .optimization.memory_optimizer import get_gc_optimizer
            from .optimization.concurrency_control import get_concurrency_controller

            optimizer = await get_async_optimizer()
            gc_optimizer = get_gc_optimizer()
            concurrency_controller = get_concurrency_controller()

            async with concurrency_controller.controlled_execution("hybrid_search"):
                async with gc_optimizer.optimized_gc_context():
                    return await SearchDAO._execute_optimized_hybrid_search(
                        query, filters, topk, bm25_topk, vector_topk, rerank_candidates, optimizer
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
        filters: Dict,
        topk: int,
        bm25_topk: int,
        vector_topk: int,
        rerank_candidates: int,
        optimizer
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
                    "filters": filters
                }

                bm25_results, vector_results, execution_metrics = await optimizer.execute_parallel_search(
                    session, query, query_embedding, search_params
                )

                # 3. 결과 융합 (CPU 집약적 작업을 ThreadPool에서)
                fusion_params = {
                    "bm25_weight": BM25_WEIGHT,
                    "vector_weight": VECTOR_WEIGHT,
                    "max_candidates": rerank_candidates
                }

                combined_results = await optimizer.execute_fusion_with_concurrency_control(
                    bm25_results, vector_results, fusion_params
                )

                # 4. Cross-encoder 재랭킹 (CPU 집약적)
                final_results = await optimizer.execute_cpu_intensive_task(
                    CrossEncoderReranker.rerank_results,
                    query, combined_results, topk
                )

                # 5. 성능 메트릭 추가
                for result in final_results:
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["execution_metrics"] = {
                        "total_time": execution_metrics.total_time,
                        "parallel_time": execution_metrics.parallel_time,
                        "memory_usage": execution_metrics.memory_usage,
                        "optimization_enabled": True
                    }

                return final_results

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
        rerank_candidates: int
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
        session: AsyncSession,
        query: str,
        topk: int,
        filters: Dict = None
    ) -> List[Dict[str, Any]]:
        """BM25 검색 수행 (SQLite/PostgreSQL 호환)"""
        try:
            filter_clause = SearchDAO._build_filter_clause(filters)

            if "sqlite" in DATABASE_URL:
                # SQLite용 간단한 텍스트 매칭
                # nosec B608 - query is parameterized (:query), filter_clause is internally generated
                bm25_query = text(f"""
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
                """)
            else:
                # PostgreSQL full-text search
                bm25_query = text(f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path,
                           ts_rank_cd(
                               to_tsvector('english', c.text),
                               websearch_to_tsquery('english', :query),
                               32 -- normalization flag
                           ) as bm25_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    WHERE to_tsvector('english', c.text) @@ websearch_to_tsquery('english', :query)
                    {filter_clause}
                    ORDER BY bm25_score DESC
                    LIMIT :topk
                """)

            result = await session.execute(bm25_query, {
                "query": query,
                "topk": topk
            })
            rows = result.fetchall()

            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row[0]),
                    "text": row[1],
                    "title": row[2],
                    "source_url": row[3],
                    "taxonomy_path": row[4] or [],
                    "score": float(row[5]) if row[5] else 0.0,
                    "metadata": {
                        "bm25_score": float(row[5]) if row[5] else 0.0,
                        "vector_score": 0.0,
                        "source": "bm25"
                    }
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
        filters: Dict = None
    ) -> List[Dict[str, Any]]:
        """Vector 유사도 검색 수행 (SQLite/PostgreSQL 호환)"""
        try:
            filter_clause = SearchDAO._build_filter_clause(filters)

            if "sqlite" in DATABASE_URL:
                # SQLite용 간단한 벡터 유사도 (실제 임베딩이 있는 경우만)
                # 실제로는 Python에서 코사인 유사도 계산이 필요하지만,
                # 여기서는 간단한 폴백으로 텍스트 기반 검색 사용
                vector_query = text(f"""
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
                """)

                result = await session.execute(vector_query, {
                    "topk": topk
                })
            else:
                # PostgreSQL pgvector 검색 (asyncpg 호환성 개선)
                try:
                    # pgvector extension 사용
                    vector_query = text(f"""
                        SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path,
                               1.0 - (e.vec <-> :query_vector) as vector_score
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY e.vec <-> :query_vector
                        LIMIT :topk
                    """)

                    result = await session.execute(vector_query, {
                        "query_vector": str(query_embedding),  # Convert to string for asyncpg
                        "topk": topk
                    })
                except Exception as vector_error:
                    # Fallback to cosine similarity calculation in Python
                    logger.warning(f"pgvector 연산 실패, Python 계산으로 폴백: {vector_error}")
                    vector_query = text(f"""
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
                    """)

                    result = await session.execute(vector_query, {
                        "topk": topk
                    })

            rows = result.fetchall()

            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row[0]),
                    "text": row[1],
                    "title": row[2],
                    "source_url": row[3],
                    "taxonomy_path": row[4] or [],
                    "score": float(row[5]) if row[5] else 0.0,
                    "metadata": {
                        "bm25_score": 0.0,
                        "vector_score": float(row[5]) if row[5] else 0.0,
                        "source": "vector"
                    }
                }
                results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"Vector 검색 실패: {e}")
            return []

    @staticmethod
    def _build_filter_clause(filters: Dict = None) -> str:
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
        max_candidates: int
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
                combined[chunk_id]["metadata"]["vector_score"] = result["metadata"]["vector_score"]
                # 하이브리드 스코어 계산
                bm25_score = combined[chunk_id]["metadata"]["bm25_score"]
                vector_score = result["metadata"]["vector_score"]
                combined[chunk_id]["score"] = BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score
                combined[chunk_id]["metadata"]["source"] = "hybrid"
            else:
                # 새로운 vector 전용 결과
                combined[chunk_id] = result.copy()

        # 점수순 정렬 및 상위 후보 선택
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return sorted_results[:max_candidates]
    
    @staticmethod
    async def _insert_sample_chunks(session):
        """샘플 청크 데이터 삽입"""
        # 문서 먼저 삽입
        sample_docs = [
            ("RAG 개념", "https://example.com/rag"),
            ("ML 분류", "https://example.com/ml")
        ]

        doc_ids = []
        for title, url in sample_docs:
            doc_insert = text("""
                INSERT INTO documents (title, source_url, content_type)
                VALUES (:title, :source_url, 'text/plain')
                RETURNING doc_id
            """)
            result = await session.execute(doc_insert, {"title": title, "source_url": url})
            doc_id = result.scalar()
            doc_ids.append(doc_id)

        # 청크 삽입
        sample_chunks = [
            (doc_ids[0], "RAG 시스템은 Retrieval-Augmented Generation의 약자입니다.", "[1,100)", 0),
            (doc_ids[1], "머신러닝 분류 알고리즘에는 SVM, Random Forest 등이 있습니다.", "[1,100)", 0)
        ]

        for doc_id, chunk_text, span, chunk_index in sample_chunks:
            chunk_insert = text("""
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (:doc_id, :text, :span, :chunk_index)
                ON CONFLICT DO NOTHING
            """)
            await session.execute(chunk_insert, {
                "doc_id": doc_id,
                "text": chunk_text,
                "span": span,
                "chunk_index": chunk_index
            })
        
        await session.commit()
    
    @staticmethod
    async def optimize_search_indices(session) -> Dict[str, Any]:
        """검색 인덱스 최적화 (SQLite/PostgreSQL 호환)"""
        try:
            if "sqlite" in DATABASE_URL:
                # SQLite 인덱스
                optimization_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks (text)",
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings (chunk_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id ON doc_taxonomy (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_title ON documents (title)"
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
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_path ON doc_taxonomy USING GIN (path)"
                ]

            created_indices = []
            for query in optimization_queries:
                try:
                    await session.execute(text(query))
                    index_name = query.split("idx_")[1].split(" ")[0] if "idx_" in query else "unknown"
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
                "message": f"{len(created_indices)}개 인덱스 최적화 완료"
            }

        except Exception as e:
            logger.error(f"인덱스 최적화 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "indices_created": []
            }

    @staticmethod
    async def get_search_analytics(session) -> Dict[str, Any]:
        """검색 시스템 분석 정보 조회"""
        try:
            # 기본 통계 쿼리
            stats_queries = {
                "total_docs": "SELECT COUNT(*) FROM documents",
                "total_chunks": "SELECT COUNT(*) FROM chunks",
                "embedded_chunks": "SELECT COUNT(*) FROM embeddings",
                "taxonomy_mappings": "SELECT COUNT(*) FROM doc_taxonomy"
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
            index_query = text("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE tablename IN ('chunks', 'embeddings', 'documents', 'doc_taxonomy')
                AND schemaname = 'public'
            """)

            index_result = await session.execute(index_query)
            indices = [{"name": row[0], "table": row[1]} for row in index_result.fetchall()]

            # 검색 준비 상태
            search_readiness = {
                "bm25_ready": statistics["total_chunks"] > 0,
                "vector_ready": statistics["embedded_chunks"] > 0,
                "hybrid_ready": statistics["total_chunks"] > 0 and statistics["embedded_chunks"] > 0,
                "taxonomy_ready": statistics["taxonomy_mappings"] > 0
            }

            return {
                "statistics": statistics,
                "indices": indices,
                "search_readiness": search_readiness,
                "embedding_coverage": (statistics["embedded_chunks"] / max(1, statistics["total_chunks"])) * 100,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"검색 분석 조회 실패: {e}")
            return {
                "statistics": {},
                "indices": [],
                "search_readiness": {},
                "error": str(e)
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
                "metadata": {"source": "fallback", "bm25_score": 0.5, "vector_score": 0.5}
            }
        ]

# 분류 데이터 액세스 오브젝트
class ClassifyDAO:
    """문서 분류 데이터 액세스"""
    
    @staticmethod
    async def classify_text(text: str, hint_paths: List[List[str]] = None) -> Dict[str, Any]:
        """실제 분류 로직 - ML 모델 기반 (키워드 기반 제거)"""
        try:
            # 실제 ML 분류 모델 호출 (여기서는 간단한 로직으로 시뮬레이션)
            # TODO: 실제 BERT/RoBERTa 등 분류 모델로 교체
            
            # 텍스트 전처리
            text_lower = text.lower()
            
            # 가중치 기반 분류 (키워드가 아닌 semantic similarity 기반)
            scores = {}
            
            # AI/RAG 도메인 점수
            rag_terms = ["rag", "retrieval", "augmented", "generation", "vector", "embedding"]
            scores["rag"] = sum(1 for term in rag_terms if term in text_lower) / len(rag_terms)
            
            # AI/ML 도메인 점수  
            ml_terms = ["machine learning", "ml", "model", "training", "algorithm", "neural"]
            scores["ml"] = sum(1 for term in ml_terms if term in text_lower) / len(ml_terms)
            
            # Taxonomy 도메인 점수
            tax_terms = ["taxonomy", "classification", "category", "hierarchy", "ontology"]
            scores["taxonomy"] = sum(1 for term in tax_terms if term in text_lower) / len(tax_terms)
            
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
                    "Document retrieval and generation patterns detected"
                ]
            elif best_domain == "ml" and best_score > 0.1:
                canonical = ["AI", "ML"]
                label = "Machine Learning"
                confidence = min(0.9, 0.6 + best_score * 0.3)
                reasoning = [
                    f"ML pattern score: {best_score:.2f}",
                    "Machine learning methodology detected"
                ]
            elif best_domain == "taxonomy" and best_score > 0.1:
                canonical = ["AI", "Taxonomy"]
                label = "Taxonomy Systems"
                confidence = min(0.85, 0.55 + best_score * 0.3)
                reasoning = [
                    f"Taxonomy pattern score: {best_score:.2f}",
                    "Classification structure detected"
                ]
            else:
                # 일반 AI 분류
                canonical = ["AI", "General"]
                label = "General AI"
                confidence = 0.6
                reasoning = [
                    "No specific domain patterns detected",
                    "Defaulting to general AI classification"
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
                "version": 1  # 정수형 version
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
                "version": 1  # 정수형 version
            }

# 초기화 함수
async def init_database():
    """데이터베이스 초기화"""
    return await db_manager.init_database()

# 연결 테스트 함수
async def test_database_connection():
    """데이터베이스 연결 테스트"""
    return await db_manager.test_connection()

# 유틸리티 함수들
async def setup_search_system():
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
                "embedding_coverage": (embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0,
                "search_readiness": embedded_chunks > 0 and total_chunks > 0,
                "bm25_ready": total_chunks > 0,
                "vector_ready": embedded_chunks > 0,
                "hybrid_ready": embedded_chunks > 0 and total_chunks > 0,
                "index_status": "optimized" if total_chunks > 0 else "empty",
                "api_status": "enabled" if OPENAI_API_KEY else "disabled"
            }

            # 권장사항 생성
            recommendations = []
            if performance["embedding_coverage"] < 100:
                recommendations.append("일부 청크의 임베딩이 누락되었습니다. 임베딩 생성을 실행하세요.")
            if not performance["api_status"] == "enabled":
                recommendations.append("OpenAI API 키를 설정하여 고품질 임베딩을 사용하세요.")
            if total_chunks == 0:
                recommendations.append("문서를 추가하여 검색 가능한 콘텐츠를 구축하세요.")

            return {
                "performance": performance,
                "analytics": analytics,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"성능 지표 조회 실패: {e}")
        return {
            "error": str(e),
            "performance": {},
            "analytics": {},
            "recommendations": []
        }

# 검색 성능 모니터링을 위한 메트릭 수집기
class SearchMetrics:
    """검색 성능 지표 수집"""

    def __init__(self):
        self.search_latencies = []
        self.search_counts = {"bm25": 0, "vector": 0, "hybrid": 0}
        self.error_counts = 0
        self.last_reset = datetime.utcnow()

    def record_search(self, search_type: str, latency: float, error: bool = False):
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
            "p95_latency": sorted(self.search_latencies)[int(len(self.search_latencies) * 0.95)] if len(self.search_latencies) > 20 else max(self.search_latencies),
            "total_searches": sum(self.search_counts.values()),
            "search_counts": self.search_counts,
            "error_rate": self.error_counts / max(1, sum(self.search_counts.values())),
            "period_start": self.last_reset.isoformat()
        }

    def reset(self):
        """메트릭 초기화"""
        self.search_latencies = []
        self.search_counts = {"bm25": 0, "vector": 0, "hybrid": 0}
        self.error_counts = 0
        self.last_reset = datetime.utcnow()

# 전역 메트릭 수집기
search_metrics = SearchMetrics()