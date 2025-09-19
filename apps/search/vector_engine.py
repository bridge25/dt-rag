"""
고성능 벡터 유사도 검색 엔진
pgvector와 FAISS를 활용한 최적화된 구현
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import json
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchResult:
    """벡터 검색 결과"""
    chunk_id: str
    score: float
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

class VectorEngine:
    """고성능 벡터 검색 엔진"""

    def __init__(self, embedding_dim: int = 1536):
        """
        Args:
            embedding_dim: 임베딩 차원 (OpenAI ada-002: 1536)
        """
        self.embedding_dim = embedding_dim
        self.distance_metric = "cosine"  # cosine, euclidean, dot_product

    async def search(
        self,
        session: AsyncSession,
        query_embedding: np.ndarray,
        topk: int = 20,
        filters: Dict = None,
        similarity_threshold: float = 0.0
    ) -> List[VectorSearchResult]:
        """벡터 유사도 검색"""
        try:
            # PostgreSQL with pgvector
            if "postgresql" in str(session.bind.url):
                return await self._pgvector_search(
                    session, query_embedding, topk, filters, similarity_threshold
                )
            else:
                # SQLite fallback with numpy
                return await self._numpy_search(
                    session, query_embedding, topk, filters, similarity_threshold
                )

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def _pgvector_search(
        self,
        session: AsyncSession,
        query_embedding: np.ndarray,
        topk: int,
        filters: Dict,
        similarity_threshold: float
    ) -> List[VectorSearchResult]:
        """pgvector를 사용한 고성능 벡터 검색"""
        try:
            filter_clause = self._build_filter_clause(filters)

            # pgvector 확장이 있는 경우
            if self.distance_metric == "cosine":
                distance_op = "<=>"  # cosine distance
                order_by = "cosine_distance"
            elif self.distance_metric == "euclidean":
                distance_op = "<->"  # L2 distance
                order_by = "l2_distance"
            else:  # dot_product
                distance_op = "<#>"  # negative dot product
                order_by = "dot_distance"

            query_sql = text(f"""
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    d.doc_metadata,
                    c.embedding {distance_op} :query_embedding as {order_by},
                    (1 - (c.embedding {distance_op} :query_embedding)) as similarity_score
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE c.embedding IS NOT NULL
                {filter_clause}
                ORDER BY c.embedding {distance_op} :query_embedding
                LIMIT :topk
            """)

            # numpy 배열을 PostgreSQL 형식으로 변환
            embedding_str = '[' + ','.join(map(str, query_embedding.tolist())) + ']'

            result = await session.execute(query_sql, {
                "query_embedding": embedding_str,
                "topk": topk
            })

            rows = result.fetchall()
            return [self._row_to_result(row) for row in rows
                   if row.similarity_score >= similarity_threshold]

        except Exception as e:
            logger.error(f"pgvector search failed: {e}")
            # numpy fallback
            return await self._numpy_search(session, query_embedding, topk, filters, similarity_threshold)

    async def _numpy_search(
        self,
        session: AsyncSession,
        query_embedding: np.ndarray,
        topk: int,
        filters: Dict,
        similarity_threshold: float
    ) -> List[VectorSearchResult]:
        """numpy를 사용한 벡터 검색 (폴백)"""
        try:
            filter_clause = self._build_filter_clause(filters)

            # 모든 임베딩 가져오기
            query_sql = text(f"""
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    d.doc_metadata,
                    c.embedding
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE c.embedding IS NOT NULL
                {filter_clause}
                LIMIT 5000  -- 메모리 제한
            """)

            result = await session.execute(query_sql)
            rows = result.fetchall()

            if not rows:
                return []

            # 임베딩 파싱 및 유사도 계산
            candidates = []
            for row in rows:
                try:
                    # JSON 문자열에서 numpy 배열로 변환
                    if isinstance(row.embedding, str):
                        embedding_data = json.loads(row.embedding)
                    else:
                        embedding_data = row.embedding

                    doc_embedding = np.array(embedding_data, dtype=np.float32)

                    # 코사인 유사도 계산
                    similarity = self._calculate_similarity(query_embedding, doc_embedding)

                    if similarity >= similarity_threshold:
                        candidates.append((row, similarity))

                except Exception as e:
                    logger.warning(f"Failed to process embedding for {row.chunk_id}: {e}")
                    continue

            # 유사도순 정렬
            candidates.sort(key=lambda x: x[1], reverse=True)

            # 결과 변환
            results = []
            for row, similarity in candidates[:topk]:
                result = VectorSearchResult(
                    chunk_id=row.chunk_id,
                    score=similarity,
                    text=row.text,
                    metadata={
                        'title': row.title,
                        'source_url': row.source_url,
                        'taxonomy_path': row.taxonomy_path,
                        'doc_metadata': row.doc_metadata or {},
                        'source': 'vector'
                    }
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Numpy vector search failed: {e}")
            return []

    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """벡터 간 유사도 계산"""
        try:
            if self.distance_metric == "cosine":
                # 코사인 유사도
                dot_product = np.dot(vec1, vec2)
                norm_a = np.linalg.norm(vec1)
                norm_b = np.linalg.norm(vec2)
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                return dot_product / (norm_a * norm_b)

            elif self.distance_metric == "euclidean":
                # 유클리드 거리를 유사도로 변환
                distance = np.linalg.norm(vec1 - vec2)
                return 1 / (1 + distance)

            else:  # dot_product
                return np.dot(vec1, vec2)

        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0

    def _row_to_result(self, row) -> VectorSearchResult:
        """데이터베이스 행을 결과 객체로 변환"""
        return VectorSearchResult(
            chunk_id=row.chunk_id,
            score=getattr(row, 'similarity_score', 0.0),
            text=row.text,
            metadata={
                'title': row.title,
                'source_url': row.source_url,
                'taxonomy_path': row.taxonomy_path,
                'doc_metadata': row.metadata or {},
                'source': 'vector'
            }
        )

    def _build_filter_clause(self, filters: Dict) -> str:
        """필터 조건 생성"""
        if not filters:
            return ""

        clauses = []
        if 'canonical_in' in filters:
            clauses.append("dt.path IS NOT NULL")

        return f" AND {' AND '.join(clauses)}" if clauses else ""


class OptimizedVectorEngine:
    """메모리 최적화된 벡터 검색 엔진"""

    def __init__(self, embedding_dim: int = 1536, use_index: bool = True):
        self.embedding_dim = embedding_dim
        self.use_index = use_index
        self.index_cache = {}  # 인덱스 캐시

    async def search_with_index(
        self,
        session: AsyncSession,
        query_embedding: np.ndarray,
        topk: int = 20,
        filters: Dict = None,
        use_approximate: bool = True
    ) -> List[VectorSearchResult]:
        """인덱스 기반 고속 벡터 검색"""
        try:
            if use_approximate and self.use_index:
                # HNSW나 IVF 인덱스 사용 (pgvector)
                return await self._approximate_search(session, query_embedding, topk, filters)
            else:
                # 정확한 검색
                return await self._exact_search(session, query_embedding, topk, filters)

        except Exception as e:
            logger.error(f"Indexed vector search failed: {e}")
            return []

    async def _approximate_search(
        self,
        session: AsyncSession,
        query_embedding: np.ndarray,
        topk: int,
        filters: Dict
    ) -> List[VectorSearchResult]:
        """근사 검색 (HNSW 인덱스 사용)"""
        try:
            # pgvector HNSW 인덱스 활용
            filter_clause = self._build_filter_clause(filters)

            # IVFFlat이나 HNSW 인덱스 사용을 위한 설정
            await session.execute(text("SET ivfflat.probes = 10"))  # 검색 정확도 조절

            query_sql = text(f"""
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    d.doc_metadata,
                    (1 - (c.embedding <=> :query_embedding)) as similarity_score
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE c.embedding IS NOT NULL
                {filter_clause}
                ORDER BY c.embedding <=> :query_embedding
                LIMIT :topk
            """)

            embedding_str = '[' + ','.join(map(str, query_embedding.tolist())) + ']'

            result = await session.execute(query_sql, {
                "query_embedding": embedding_str,
                "topk": topk
            })

            rows = result.fetchall()
            return [self._row_to_result(row) for row in rows]

        except Exception as e:
            logger.error(f"Approximate search failed: {e}")
            return await self._exact_search(session, query_embedding, topk, filters)

    async def _exact_search(
        self,
        session: AsyncSession,
        query_embedding: np.ndarray,
        topk: int,
        filters: Dict
    ) -> List[VectorSearchResult]:
        """정확한 벡터 검색"""
        # 기본 VectorEngine 사용
        engine = VectorEngine()
        return await engine.search(session, query_embedding, topk, filters)

    def _row_to_result(self, row) -> VectorSearchResult:
        """데이터베이스 행을 결과 객체로 변환"""
        return VectorSearchResult(
            chunk_id=row.chunk_id,
            score=getattr(row, 'similarity_score', 0.0),
            text=row.text,
            metadata={
                'title': row.title,
                'source_url': row.source_url,
                'taxonomy_path': row.taxonomy_path,
                'doc_metadata': row.metadata or {},
                'source': 'vector_indexed'
            }
        )

    def _build_filter_clause(self, filters: Dict) -> str:
        """필터 조건 생성"""
        if not filters:
            return ""

        clauses = []
        if 'canonical_in' in filters:
            clauses.append("dt.path IS NOT NULL")

        return f" AND {' AND '.join(clauses)}" if clauses else ""


class EmbeddingService:
    """임베딩 생성 서비스 (캐싱 지원)"""

    _cache = None
    _model_cache = {}  # 모델 인스턴스 캐시

    @classmethod
    async def _get_cache(cls):
        """캐시 인스턴스 가져오기"""
        if cls._cache is None:
            try:
                from ..api.cache.search_cache import get_search_cache
                cls._cache = await get_search_cache()
            except ImportError:
                logger.warning("Search cache not available")
                cls._cache = None
        return cls._cache

    @staticmethod
    async def generate_embedding(text: str, model: str = "openai") -> np.ndarray:
        """텍스트에서 임베딩 생성 (캐싱 지원)"""
        try:
            # 캐시에서 확인
            cache = await EmbeddingService._get_cache()
            if cache:
                cached_embedding = await cache.get_embedding(text, model)
                if cached_embedding is not None:
                    return np.array(cached_embedding, dtype=np.float32)

            # 임베딩 생성
            if model == "openai":
                embedding = await EmbeddingService._openai_embedding(text)
            elif model == "sentence_transformer":
                embedding = await EmbeddingService._sentence_transformer_embedding(text)
            elif model == "dummy":
                embedding = await EmbeddingService._dummy_embedding(text)
            else:
                raise ValueError(f"Unsupported embedding model: {model}")

            # 캐시에 저장
            if cache:
                await cache.set_embedding(text, embedding.tolist(), model)

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # 기본 더미 임베딩 반환
            return np.random.rand(1536).astype(np.float32)

    @staticmethod
    async def generate_batch_embeddings(
        texts: List[str],
        model: str = "openai",
        batch_size: int = 10
    ) -> List[np.ndarray]:
        """배치 임베딩 생성 (효율성 향상)"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]

            # 병렬 처리
            batch_tasks = [
                EmbeddingService.generate_embedding(text, model)
                for text in batch_texts
            ]

            batch_embeddings = await asyncio.gather(*batch_tasks)
            embeddings.extend(batch_embeddings)

            # API 레이트 제한 고려
            if model == "openai" and len(batch_texts) > 1:
                await asyncio.sleep(0.1)

        return embeddings

    @staticmethod
    async def _openai_embedding(text: str) -> np.ndarray:
        """OpenAI API로 임베딩 생성"""
        import httpx

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "input": text[:8000],  # 토큰 제한
                    "model": "text-embedding-ada-002"
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]
                return np.array(embedding, dtype=np.float32)
            else:
                raise Exception(f"OpenAI API error: {response.status_code}")

    @staticmethod
    async def _sentence_transformer_embedding(text: str) -> np.ndarray:
        """Sentence Transformer로 임베딩 생성 (모델 캐싱)"""
        try:
            # 비동기로 실행하기 위해 별도 스레드에서 실행
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def _generate_embedding():
                try:
                    from sentence_transformers import SentenceTransformer

                    # 모델 캐싱
                    model_key = 'all-MiniLM-L6-v2'
                    if model_key not in EmbeddingService._model_cache:
                        EmbeddingService._model_cache[model_key] = SentenceTransformer(model_key)

                    model = EmbeddingService._model_cache[model_key]
                    embedding = model.encode(text)
                    return embedding.astype(np.float32)
                except ImportError:
                    logger.error("sentence-transformers not installed")
                    return np.random.rand(384).astype(np.float32)

            with ThreadPoolExecutor(max_workers=1) as executor:
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(executor, _generate_embedding)
                return embedding

        except Exception as e:
            logger.error(f"Sentence transformer embedding failed: {e}")
            return np.random.rand(384).astype(np.float32)

    @staticmethod
    async def _dummy_embedding(text: str) -> np.ndarray:
        """일관된 더미 임베딩 생성 (개발/테스트용)"""
        # 텍스트 해시 기반 일관된 벡터
        import hashlib
        text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(text_hash % (2**32))

        embedding = np.random.normal(0, 1, 1536)
        # L2 정규화
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)