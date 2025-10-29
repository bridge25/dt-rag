"""
OpenAI text-embedding-3-large 기반 실제 벡터 임베딩 서비스
PostgreSQL pgvector와 통합된 1536차원 벡터 생성 시스템
"""

# @CODE:EMBED-001 | SPEC: .moai/specs/SPEC-EMBED-001/spec.md | TEST: tests/test_embedding_service.py

import os
import asyncio
import logging
import hashlib
from typing import List, Optional, Dict, Any, cast
import numpy as np

# Langfuse integration for LLM cost tracking
try:
    from .monitoring.langfuse_client import observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    # Fallback: no-op decorator
    def observe(name: str = "", as_type: str = "span", **kwargs: Any) -> Any:
        def decorator(func: Any) -> Any:
            return func

        return decorator

    LANGFUSE_AVAILABLE = False

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingService:
    """OpenAI 기반 실제 임베딩 서비스 (1536차원)"""

    SUPPORTED_MODELS = {
        "text-embedding-3-large": {
            "name": "text-embedding-3-large",
            "dimensions": 1536,
            "description": "OpenAI's most capable embedding model",
            "cost_per_1k_tokens": 0.00013,
        },
        "text-embedding-3-small": {
            "name": "text-embedding-3-small",
            "dimensions": 1536,
            "description": "OpenAI's efficient embedding model",
            "cost_per_1k_tokens": 0.00002,
        },
        "text-embedding-ada-002": {
            "name": "text-embedding-ada-002",
            "dimensions": 1536,
            "description": "OpenAI's legacy embedding model",
            "cost_per_1k_tokens": 0.0001,
        },
        "all-mpnet-base-v2": {
            "name": "sentence-transformers/all-mpnet-base-v2",
            "dimensions": 768,
            "description": "Fallback: Sentence Transformers model",
            "cost_per_1k_tokens": 0.0,
        },
    }

    TARGET_DIMENSIONS: int = 1536

    def __init__(self, model_name: str = "text-embedding-3-large"):
        self.model_name = model_name
        self.model_config = self.SUPPORTED_MODELS.get(model_name)
        self._openai_client: Optional[Any] = None
        self._sentence_transformer: Optional[Any] = None
        self._model_loaded = False
        self.embedding_cache: Dict[str, List[float]] = {}

        if not self.model_config:
            logger.warning(f"지원되지 않는 모델: {model_name}, 기본 모델로 변경")
            self.model_name = "text-embedding-3-large"
            self.model_config = self.SUPPORTED_MODELS[self.model_name]

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and OPENAI_AVAILABLE:
            self._openai_client = AsyncOpenAI(api_key=api_key)
            logger.info(
                f"OpenAI 클라이언트 초기화: {self.model_name} ({self.model_config['dimensions']}차원)"
            )
        else:
            logger.warning("OPENAI_API_KEY 없음, Sentence Transformers 폴백 사용")
            self.model_name = "all-mpnet-base-v2"
            self.model_config = self.SUPPORTED_MODELS[self.model_name]

    def _load_sentence_transformer(self) -> Optional[SentenceTransformer]:
        """Sentence Transformer 폴백 모델 로드"""
        if self._sentence_transformer is not None:
            return self._sentence_transformer

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers 패키지가 설치되지 않음")
            return None

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 14d: index (Fix 56-57 - assert model_config is not None)
        assert self.model_config is not None, "model_config must be initialized in __init__"

        try:
            logger.info(f"폴백 모델 로딩 중: {self.model_config['name']}")
            self._sentence_transformer = SentenceTransformer(self.model_config["name"])
            self._model_loaded = True
            logger.info(f"폴백 모델 로딩 완료: {self.model_name}")
            return self._sentence_transformer

        except Exception as e:
            logger.error(f"폴백 모델 로딩 실패: {e}")
            self._model_loaded = False
            return None

    def _pad_or_truncate_vector(self, vector: np.ndarray) -> List[float]:
        """벡터를 1536차원으로 맞추기"""
        current_dim = len(vector)

        if current_dim == self.TARGET_DIMENSIONS:
            return cast(List[float], vector.tolist())
        elif current_dim < self.TARGET_DIMENSIONS:
            padded = np.zeros(self.TARGET_DIMENSIONS)
            padded[:current_dim] = vector
            return cast(List[float], padded.tolist())
        else:
            return cast(List[float], vector[: self.TARGET_DIMENSIONS].tolist())

    @observe(name="generate_embedding", as_type="embedding")  # type: ignore[misc]  # Langfuse decorator lacks type stubs
    async def generate_embedding(
        self, text: str, use_cache: bool = True
    ) -> List[float]:
        """텍스트를 1536차원 벡터로 변환 (Langfuse cost tracking enabled)"""
        if not text or not text.strip():
            return self._generate_zero_vector()

        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self.embedding_cache:
                logger.debug(f"캐시에서 임베딩 반환: {text[:50]}...")
                return self.embedding_cache[cache_key]

        try:
            processed_text = self._preprocess_text(text)

            if self._openai_client:
                embedding = await self._generate_openai_embedding(processed_text)
            else:
                embedding = await self._generate_sentence_transformer_embedding(
                    processed_text
                )

            final_embedding = self._normalize_vector(embedding)

            if use_cache:
                self.embedding_cache[cache_key] = final_embedding
                if len(self.embedding_cache) > 1000:
                    oldest_key = next(iter(self.embedding_cache))
                    del self.embedding_cache[oldest_key]

            logger.info(
                f"임베딩 생성 완료 - 텍스트: {len(text)}자, 벡터: {len(final_embedding)}차원"
            )
            return final_embedding

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return await self._generate_dummy_embedding(text)

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """OpenAI API로 임베딩 생성 (SPEC-ENV-VALIDATE-001 Phase 4)"""
        assert self._openai_client is not None  # Ensured by caller
        try:
            response = await self._openai_client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float",
                dimensions=1536,
            )
            embedding = response.data[0].embedding
            return cast(List[float], embedding)

        except Exception as e:
            error_type = type(e).__name__

            if "AuthenticationError" in error_type or (
                hasattr(e, "response")
                and getattr(e.response, "status_code", None) == 401
            ):
                logger.error(
                    "OpenAI API authentication failed (401): Invalid API key. "
                    "Please check OPENAI_API_KEY environment variable."
                )

            raise

    async def _generate_sentence_transformer_embedding(self, text: str) -> List[float]:
        """Sentence Transformers 폴백"""
        model = self._load_sentence_transformer()
        if model is None:
            logger.warning("폴백 모델 사용 불가, 더미 벡터 생성")
            return await self._generate_dummy_embedding(text)

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: model.encode([text], convert_to_numpy=True)[0]
        )

        return self._pad_or_truncate_vector(embedding)

    @observe(name="batch_generate_embeddings", as_type="embedding")  # type: ignore[misc]  # Langfuse decorator lacks type stubs
    async def batch_generate_embeddings(
        self, texts: List[str], batch_size: int = 100, show_progress: bool = True
    ) -> List[List[float]]:
        """배치로 임베딩 생성 (Langfuse cost tracking enabled)"""
        if not texts:
            return []

        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_num = i // batch_size + 1

            if show_progress:
                logger.info(f"배치 처리 중: {batch_num}/{total_batches}")

            try:
                processed_texts = [self._preprocess_text(text) for text in batch_texts]

                if self._openai_client:
                    response = await self._openai_client.embeddings.create(
                        model=self.model_name,
                        input=processed_texts,
                        encoding_format="float",
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                else:
                    model = self._load_sentence_transformer()
                    if model is None:
                        batch_embeddings = []
                        for text in batch_texts:
                            dummy_emb = await self._generate_dummy_embedding(text)
                            batch_embeddings.append(dummy_emb)
                    else:
                        loop = asyncio.get_event_loop()
                        raw_embeddings = await loop.run_in_executor(
                            None,
                            lambda: model.encode(
                                processed_texts, convert_to_numpy=True
                            ),
                        )
                        batch_embeddings = [
                            self._pad_or_truncate_vector(emb) for emb in raw_embeddings
                        ]

                normalized_embeddings = [
                    self._normalize_vector(emb) for emb in batch_embeddings
                ]
                embeddings.extend(normalized_embeddings)

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"배치 {batch_num} 처리 실패: {e}")
                for text in batch_texts:
                    dummy_emb = await self._generate_dummy_embedding(text)
                    embeddings.append(dummy_emb)

        logger.info(f"배치 임베딩 생성 완료: {len(texts)}개 텍스트")
        return embeddings

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """코사인 유사도 계산"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            if len(vec1) != len(vec2):
                logger.warning(f"벡터 크기 불일치: {len(vec1)} vs {len(vec2)}")
                return 0.0

            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(np.clip(similarity, -1.0, 1.0))

        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0

    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""

        processed = text.strip()
        max_length = 8000
        if len(processed) > max_length:
            processed = processed[:max_length]
            logger.debug(f"텍스트 잘림: {max_length}자로 제한")

        return processed

    def _get_cache_key(self, text: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """L2 정규화"""
        vec_array = np.array(vector)
        norm = np.linalg.norm(vec_array)

        if norm == 0:
            return vector

        normalized = vec_array / norm
        return cast(List[float], normalized.tolist())

    def _generate_zero_vector(self) -> List[float]:
        """제로 벡터 생성"""
        return cast(List[float], [0.0] * self.TARGET_DIMENSIONS)

    async def _generate_dummy_embedding(self, text: str) -> List[float]:
        """더미 임베딩 생성"""
        logger.debug(f"더미 임베딩 생성: {text[:30]}...")

        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
        np.random.seed(seed)

        vector = np.random.normal(0, 0.1, self.TARGET_DIMENSIONS)

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return cast(List[float], vector.tolist())

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "model_config": self.model_config,
            "target_dimensions": self.TARGET_DIMENSIONS,
            "model_loaded": self._model_loaded,
            "cache_size": len(self.embedding_cache),
            "openai_available": OPENAI_AVAILABLE and self._openai_client is not None,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
        }

    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인 (SPEC-ENV-VALIDATE-001 Phase 3)"""
        try:
            from .config import _validate_openai_api_key

            api_key = os.getenv("OPENAI_API_KEY")
            api_key_valid = _validate_openai_api_key(api_key) if api_key else False

            if self._openai_client:
                result = {
                    "status": "healthy",
                    "model_name": self.model_name,
                    "model_loaded": True,
                    "target_dimensions": self.TARGET_DIMENSIONS,
                    "openai_available": True,
                    "cache_size": len(self.embedding_cache),
                    "api_key_configured": api_key_valid,
                    "fallback_mode": False,
                }

                if not api_key_valid:
                    result["warning"] = "OPENAI_API_KEY format is invalid"

                return result

            elif self._sentence_transformer:
                return {
                    "status": "degraded",
                    "model_name": self.model_name,
                    "model_loaded": True,
                    "target_dimensions": self.TARGET_DIMENSIONS,
                    "fallback_mode": True,
                    "cache_size": len(self.embedding_cache),
                    "api_key_configured": False,
                    "warning": "OPENAI_API_KEY not configured - using Sentence Transformers fallback",
                }
            else:
                return {
                    "status": "unhealthy",
                    "model_loaded": False,
                    "fallback_mode": True,
                    "error": "모델 로딩 실패",
                    "api_key_configured": False,
                    "warning": "OPENAI_API_KEY not configured and fallback model loading failed",
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_loaded": False,
                "fallback_mode": True,
                "api_key_configured": False,
            }

    def clear_cache(self) -> int:
        """캐시 클리어"""
        cache_size = len(self.embedding_cache)
        self.embedding_cache.clear()
        logger.info(f"임베딩 캐시 클리어: {cache_size}개 항목 제거")
        return cache_size


class DocumentEmbeddingService:
    """문서 임베딩 업데이트 및 관리 서비스"""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def update_document_embeddings(
        self, document_ids: Optional[List[str]] = None, batch_size: int = 100
    ) -> Dict[str, Any]:
        """문서들의 임베딩 업데이트"""
        from .database import db_manager, text

        try:
            async with db_manager.async_session() as session:
                if document_ids:
                    doc_ids_str = "', '".join(document_ids)
                    query = text(
                        f"""
                        SELECT c.chunk_id, c.text, c.doc_id
                        FROM chunks c
                        LEFT JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE c.doc_id IN ('{doc_ids_str}') AND e.chunk_id IS NULL
                        ORDER BY c.chunk_id
                    """
                    )
                else:
                    query = text(
                        """
                        SELECT c.chunk_id, c.text, c.doc_id
                        FROM chunks c
                        LEFT JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.chunk_id IS NULL
                        ORDER BY c.chunk_id
                    """
                    )

                result = await session.execute(query)
                chunks = result.fetchall()

                if not chunks:
                    return {
                        "success": True,
                        "message": "모든 청크에 임베딩이 이미 존재합니다",
                        "updated_count": 0,
                        "total_chunks": 0,
                    }

                logger.info(f"임베딩 업데이트 대상: {len(chunks)}개 청크")

                updated_count = 0
                total_chunks = len(chunks)

                for i in range(0, len(chunks), batch_size):
                    batch_chunks = chunks[i : i + batch_size]
                    batch_texts = [chunk[1] for chunk in batch_chunks]

                    embeddings = await self.embedding_service.batch_generate_embeddings(
                        batch_texts, batch_size=batch_size
                    )

                    for j, (chunk_id, text_content, doc_id) in enumerate(batch_chunks):
                        if j < len(embeddings):
                            embedding = embeddings[j]

                            insert_query = text(
                                """
                                INSERT INTO embeddings (chunk_id, vec, model_name)
                                VALUES (:chunk_id, :vec, :model_name)
                                ON CONFLICT (chunk_id) DO UPDATE SET
                                    vec = EXCLUDED.vec,
                                    model_name = EXCLUDED.model_name,
                                    created_at = NOW()
                            """
                            )

                            await session.execute(
                                insert_query,
                                {
                                    "chunk_id": chunk_id,
                                    "vec": embedding,
                                    "model_name": self.embedding_service.model_name,
                                },
                            )

                            updated_count += 1

                    await session.commit()

                    logger.info(
                        f"배치 {i//batch_size + 1} 완료: {updated_count}/{total_chunks} 청크 처리"
                    )

                return {
                    "success": True,
                    "message": "임베딩 업데이트 완료",
                    "updated_count": updated_count,
                    "total_chunks": total_chunks,
                    "model_name": self.embedding_service.model_name,
                }

        except Exception as e:
            logger.error(f"문서 임베딩 업데이트 실패: {e}")
            return {"success": False, "error": str(e), "updated_count": 0}

    async def get_embedding_status(self) -> Dict[str, Any]:
        """임베딩 상태 조회"""
        from .database import db_manager, text

        try:
            async with db_manager.async_session() as session:
                stats_queries = {
                    "total_chunks": "SELECT COUNT(*) FROM chunks",
                    "embedded_chunks": "SELECT COUNT(*) FROM embeddings",
                    "missing_embeddings": """
                        SELECT COUNT(*) FROM chunks c
                        LEFT JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.chunk_id IS NULL
                    """,
                }

                stats = {}
                for stat_name, query in stats_queries.items():
                    result = await session.execute(text(query))
                    stats[stat_name] = result.scalar() or 0

                model_query = text(
                    """
                    SELECT model_name, COUNT(*) as count
                    FROM embeddings
                    GROUP BY model_name
                    ORDER BY count DESC
                """
                )

                model_result = await session.execute(model_query)
                model_distribution = {row[0]: row[1] for row in model_result.fetchall()}

                coverage_pct = 0.0
                if stats["total_chunks"] > 0:
                    coverage_pct = (
                        stats["embedded_chunks"] / stats["total_chunks"]
                    ) * 100

                return {
                    "statistics": stats,
                    "model_distribution": model_distribution,
                    "embedding_coverage_percent": coverage_pct,
                    "current_model": self.embedding_service.model_name,
                    "target_dimensions": self.embedding_service.TARGET_DIMENSIONS,
                    "service_status": self.embedding_service.health_check(),
                }

        except Exception as e:
            logger.error(f"임베딩 상태 조회 실패: {e}")
            return {
                "error": str(e),
                "statistics": {},
                "model_distribution": {},
                "embedding_coverage_percent": 0.0,
            }


embedding_service = EmbeddingService()
document_embedding_service = DocumentEmbeddingService(embedding_service)


async def generate_embedding(text: str, use_cache: bool = True) -> List[float]:
    """전역 임베딩 생성 함수"""
    result = await embedding_service.generate_embedding(text, use_cache=use_cache)
    return cast(List[float], result)


async def generate_embeddings(
    texts: List[str], batch_size: int = 100
) -> List[List[float]]:
    """전역 배치 임베딩 생성 함수"""
    result = await embedding_service.batch_generate_embeddings(
        texts, batch_size=batch_size
    )
    return cast(List[List[float]], result)


def calculate_similarity(emb1: List[float], emb2: List[float]) -> float:
    """전역 유사도 계산 함수"""
    return embedding_service.calculate_similarity(emb1, emb2)


async def update_document_embeddings(
    document_ids: Optional[List[str]] = None, batch_size: int = 100
) -> Dict[str, Any]:
    """문서 임베딩 업데이트 함수"""
    return await document_embedding_service.update_document_embeddings(
        document_ids, batch_size
    )


async def get_embedding_status() -> Dict[str, Any]:
    """임베딩 상태 조회 함수"""
    return await document_embedding_service.get_embedding_status()


def get_service_info() -> Dict[str, Any]:
    """서비스 정보 조회 함수"""
    return embedding_service.get_model_info()


def health_check() -> Dict[str, Any]:
    """서비스 헬스체크 함수"""
    return embedding_service.health_check()
