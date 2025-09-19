"""
통합 하이브리드 검색 엔진
BM25 + Vector + Cross-Encoder 리랭킹을 결합한 고성능 검색 시스템
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession

from .bm25_engine import BM25Engine, OptimizedBM25
from .vector_engine import VectorEngine, OptimizedVectorEngine, EmbeddingService
from .hybrid_fusion import HybridScoreFusion, AdaptiveFusion, FusionMethod, NormalizationMethod
from .cross_encoder_reranker import CrossEncoderReranker, MultiStageReranker

logger = logging.getLogger(__name__)

@dataclass
class SearchConfig:
    """검색 설정"""
    # BM25 설정
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    bm25_topk: int = 20

    # Vector 설정
    vector_topk: int = 20
    vector_similarity_threshold: float = 0.0
    embedding_model: str = "openai"

    # Fusion 설정
    fusion_method: FusionMethod = FusionMethod.WEIGHTED_SUM
    normalization_method: NormalizationMethod = NormalizationMethod.MIN_MAX
    bm25_weight: float = 0.5
    vector_weight: float = 0.5

    # Reranking 설정
    enable_reranking: bool = True
    rerank_candidates: int = 50
    final_topk: int = 10
    use_multi_stage: bool = True

    # Performance 설정
    use_adaptive_fusion: bool = True
    use_optimized_engines: bool = True
    max_query_time: float = 2.0  # 최대 쿼리 시간 (초)

@dataclass
class SearchResult:
    """검색 결과"""
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    sources: List[str]
    processing_info: Dict[str, Any]

@dataclass
class SearchResponse:
    """검색 응답"""
    results: List[SearchResult]
    total_time: float
    bm25_time: float
    vector_time: float
    fusion_time: float
    rerank_time: float
    total_candidates: int
    query_id: str

class HybridSearchEngine:
    """통합 하이브리드 검색 엔진"""

    def __init__(self, config: SearchConfig = None):
        """
        Args:
            config: 검색 설정
        """
        self.config = config or SearchConfig()

        # 엔진 초기화
        if self.config.use_optimized_engines:
            self.bm25_engine = OptimizedBM25(self.config.bm25_k1, self.config.bm25_b)
            self.vector_engine = OptimizedVectorEngine()
        else:
            self.bm25_engine = BM25Engine(self.config.bm25_k1, self.config.bm25_b)
            self.vector_engine = VectorEngine()

        # 융합 엔진
        if self.config.use_adaptive_fusion:
            self.fusion_engine = AdaptiveFusion()
        else:
            self.fusion_engine = HybridScoreFusion(
                fusion_method=self.config.fusion_method,
                normalization_method=self.config.normalization_method,
                bm25_weight=self.config.bm25_weight,
                vector_weight=self.config.vector_weight
            )

        # 리랭킹 엔진
        if self.config.use_multi_stage:
            self.reranker = MultiStageReranker()
        else:
            self.reranker = CrossEncoderReranker()

        # 성능 추적
        self.performance_history = []

    async def search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any] = None,
        query_id: str = None
    ) -> SearchResponse:
        """통합 하이브리드 검색 실행"""
        start_time = time.time()
        query_id = query_id or f"query_{int(time.time())}"

        try:
            logger.info(f"Starting hybrid search for query: '{query[:50]}...'")

            # 병렬 검색 실행
            bm25_task = self._run_bm25_search(session, query, filters)
            vector_task = self._run_vector_search(session, query, filters)

            bm25_results, bm25_time = await bm25_task
            vector_results, vector_time = await vector_task

            logger.info(f"BM25: {len(bm25_results)} results in {bm25_time:.3f}s")
            logger.info(f"Vector: {len(vector_results)} results in {vector_time:.3f}s")

            # 결과 융합
            fusion_start = time.time()
            if self.config.use_adaptive_fusion:
                fused_candidates = self.fusion_engine.adaptive_fuse(
                    query, bm25_results, vector_results
                )
            else:
                fused_candidates = self.fusion_engine.fuse_results(
                    bm25_results, vector_results, self.config.rerank_candidates
                )
            fusion_time = time.time() - fusion_start

            logger.info(f"Fusion: {len(fused_candidates)} candidates in {fusion_time:.3f}s")

            # 리랭킹 (선택적)
            rerank_time = 0.0
            if self.config.enable_reranking and len(fused_candidates) > self.config.final_topk:
                rerank_start = time.time()

                # 후보를 딕셔너리 형태로 변환
                candidate_dicts = []
                for candidate in fused_candidates:
                    candidate_dict = {
                        'chunk_id': candidate.chunk_id,
                        'text': candidate.text,
                        'score': candidate.final_score or 0.0,
                        'metadata': candidate.metadata
                    }
                    candidate_dicts.append(candidate_dict)

                if self.config.use_multi_stage:
                    reranked_results = await self.reranker.multi_stage_rerank(
                        query, candidate_dicts, self.config.final_topk
                    )
                else:
                    reranked_results = await self.reranker.rerank(
                        query, candidate_dicts, self.config.final_topk
                    )

                rerank_time = time.time() - rerank_start
                logger.info(f"Reranking: {len(reranked_results)} results in {rerank_time:.3f}s")
            else:
                # 리랭킹 없이 상위 결과 선택
                reranked_results = []
                for candidate in fused_candidates[:self.config.final_topk]:
                    result_dict = {
                        'chunk_id': candidate.chunk_id,
                        'text': candidate.text,
                        'score': candidate.final_score or 0.0,
                        'metadata': candidate.metadata
                    }
                    reranked_results.append(result_dict)

            # 최종 결과 변환
            final_results = []
            for i, result in enumerate(reranked_results):
                search_result = SearchResult(
                    chunk_id=result['chunk_id'],
                    text=result['text'],
                    score=result['score'],
                    metadata=result['metadata'],
                    sources=result['metadata'].get('sources', ['hybrid']),
                    processing_info={
                        'final_rank': i + 1,
                        'bm25_included': any(src.startswith('bm25') for src in result['metadata'].get('sources', [])),
                        'vector_included': any(src.startswith('vector') for src in result['metadata'].get('sources', [])),
                        'reranked': self.config.enable_reranking
                    }
                )
                final_results.append(search_result)

            total_time = time.time() - start_time

            # 성능 기록
            self._record_performance(total_time, len(final_results))

            # 응답 생성
            response = SearchResponse(
                results=final_results,
                total_time=total_time,
                bm25_time=bm25_time,
                vector_time=vector_time,
                fusion_time=fusion_time,
                rerank_time=rerank_time,
                total_candidates=len(fused_candidates),
                query_id=query_id
            )

            logger.info(f"Search completed in {total_time:.3f}s, returned {len(final_results)} results")
            return response

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    async def _run_bm25_search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """BM25 검색 실행"""
        start_time = time.time()
        try:
            if self.config.use_optimized_engines:
                results = await self.bm25_engine.search_with_preprocessing(
                    session, query, self.config.bm25_topk, filters
                )
            else:
                results = await self.bm25_engine.search(
                    session, query, self.config.bm25_topk, filters
                )

            # 결과 형식 통일
            formatted_results = []
            for result in results:
                formatted_result = {
                    'chunk_id': result.get('chunk_id', ''),
                    'text': result.get('text', ''),
                    'bm25_score': result.get('bm25_score', 0.0),
                    'metadata': {
                        'title': result.get('title', ''),
                        'source_url': result.get('source_url', ''),
                        'taxonomy_path': result.get('taxonomy_path', []),
                        'source': 'bm25'
                    }
                }
                formatted_results.append(formatted_result)

            return formatted_results, time.time() - start_time

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return [], time.time() - start_time

    async def _run_vector_search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Vector 검색 실행"""
        start_time = time.time()
        try:
            # 쿼리 임베딩 생성
            query_embedding = await EmbeddingService.generate_embedding(
                query, self.config.embedding_model
            )

            if self.config.use_optimized_engines:
                results = await self.vector_engine.search_with_index(
                    session, query_embedding, self.config.vector_topk, filters
                )
            else:
                results = await self.vector_engine.search(
                    session, query_embedding, self.config.vector_topk, filters,
                    self.config.vector_similarity_threshold
                )

            # 결과 형식 통일
            formatted_results = []
            for result in results:
                if hasattr(result, 'chunk_id'):
                    # VectorSearchResult 객체
                    formatted_result = {
                        'chunk_id': result.chunk_id,
                        'text': result.text,
                        'score': result.score,
                        'metadata': result.metadata
                    }
                else:
                    # 딕셔너리 형태
                    formatted_result = {
                        'chunk_id': result.get('chunk_id', ''),
                        'text': result.get('text', ''),
                        'score': result.get('score', 0.0),
                        'metadata': result.get('metadata', {})
                    }
                    formatted_result['metadata']['source'] = 'vector'

                formatted_results.append(formatted_result)

            return formatted_results, time.time() - start_time

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return [], time.time() - start_time

    def _record_performance(self, total_time: float, result_count: int):
        """성능 기록"""
        performance_record = {
            'timestamp': time.time(),
            'total_time': total_time,
            'result_count': result_count,
            'config': asdict(self.config)
        }

        self.performance_history.append(performance_record)

        # 최근 100개 기록만 유지
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        if not self.performance_history:
            return {}

        times = [record['total_time'] for record in self.performance_history]
        counts = [record['result_count'] for record in self.performance_history]

        return {
            'total_queries': len(self.performance_history),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_results': sum(counts) / len(counts),
            'p95_time': sorted(times)[int(len(times) * 0.95)] if times else 0,
            'p99_time': sorted(times)[int(len(times) * 0.99)] if times else 0
        }

    async def warm_up(self, session: AsyncSession):
        """검색 엔진 웜업"""
        logger.info("Warming up hybrid search engine...")

        try:
            # 모델 초기화
            if hasattr(self.reranker, 'cross_encoder'):
                await self.reranker.cross_encoder.initialize_model()

            # BM25 통계 초기화
            if hasattr(self.bm25_engine, 'initialize_corpus_stats'):
                await self.bm25_engine.initialize_corpus_stats(session)

            # 더미 검색으로 웜업
            await self.search(session, "test query", query_id="warmup")

            logger.info("Warm up completed")

        except Exception as e:
            logger.warning(f"Warm up failed: {e}")


class SearchEngineFactory:
    """검색 엔진 팩토리"""

    @staticmethod
    def create_fast_engine() -> HybridSearchEngine:
        """빠른 검색 엔진 (정확도 < 속도)"""
        config = SearchConfig(
            bm25_topk=10,
            vector_topk=10,
            enable_reranking=False,
            use_multi_stage=False,
            use_optimized_engines=True,
            final_topk=5
        )
        return HybridSearchEngine(config)

    @staticmethod
    def create_accurate_engine() -> HybridSearchEngine:
        """정확한 검색 엔진 (속도 < 정확도)"""
        config = SearchConfig(
            bm25_topk=30,
            vector_topk=30,
            enable_reranking=True,
            use_multi_stage=True,
            rerank_candidates=100,
            use_adaptive_fusion=True,
            final_topk=10
        )
        return HybridSearchEngine(config)

    @staticmethod
    def create_balanced_engine() -> HybridSearchEngine:
        """균형잡힌 검색 엔진"""
        config = SearchConfig(
            bm25_topk=20,
            vector_topk=20,
            enable_reranking=True,
            use_multi_stage=False,
            rerank_candidates=50,
            use_adaptive_fusion=True,
            final_topk=8
        )
        return HybridSearchEngine(config)

    @staticmethod
    def create_custom_engine(
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        enable_reranking: bool = True,
        final_topk: int = 10
    ) -> HybridSearchEngine:
        """커스텀 검색 엔진"""
        config = SearchConfig(
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            enable_reranking=enable_reranking,
            final_topk=final_topk
        )
        return HybridSearchEngine(config)


# 전역 검색 엔진 인스턴스 (싱글톤 패턴)
_search_engine_instance = None

async def get_search_engine() -> HybridSearchEngine:
    """전역 검색 엔진 인스턴스 조회"""
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = SearchEngineFactory.create_balanced_engine()
    return _search_engine_instance

async def set_search_engine(engine: HybridSearchEngine):
    """전역 검색 엔진 인스턴스 설정"""
    global _search_engine_instance
    _search_engine_instance = engine