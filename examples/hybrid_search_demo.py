"""
하이브리드 검색 시스템 사용 예제
실제 사용법과 최적화 팁을 포함한 데모
"""

import asyncio
import time
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 하이브리드 검색 시스템 import
from apps.search import (
    HybridSearchEngine,
    SearchConfig,
    SearchEngineFactory,
    FusionMethod,
    NormalizationMethod,
    get_cache,
    get_performance_monitor,
    QueryOptimizer
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridSearchDemo:
    """하이브리드 검색 데모 클래스"""

    def __init__(self, database_url: str):
        """
        Args:
            database_url: 데이터베이스 연결 URL
        """
        self.database_url = database_url
        self.engine = None
        self.session_maker = None
        self.search_engines = {}

    async def initialize(self):
        """시스템 초기화"""
        logger.info("Initializing hybrid search demo...")

        # 데이터베이스 연결
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10
        )
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # 다양한 검색 엔진 생성
        self.search_engines = {
            'fast': SearchEngineFactory.create_fast_engine(),
            'accurate': SearchEngineFactory.create_accurate_engine(),
            'balanced': SearchEngineFactory.create_balanced_engine(),
            'custom': self._create_custom_engine()
        }

        # 검색 엔진 웜업
        async with self.session_maker() as session:
            for name, engine in self.search_engines.items():
                logger.info(f"Warming up {name} engine...")
                await engine.warm_up(session)

        logger.info("Demo initialization completed")

    def _create_custom_engine(self) -> HybridSearchEngine:
        """커스텀 검색 엔진 생성"""
        config = SearchConfig(
            # BM25 설정
            bm25_k1=1.8,  # 높은 값으로 term frequency 강조
            bm25_b=0.6,   # 문서 길이 정규화 조정
            bm25_topk=25,

            # Vector 설정
            vector_topk=25,
            vector_similarity_threshold=0.1,  # 낮은 유사도 결과 필터링

            # Fusion 설정
            fusion_method=FusionMethod.RRF,  # Reciprocal Rank Fusion
            normalization_method=NormalizationMethod.MIN_MAX,
            bm25_weight=0.6,  # BM25 약간 우선
            vector_weight=0.4,

            # Reranking 설정
            enable_reranking=True,
            rerank_candidates=40,
            final_topk=8,
            use_multi_stage=True,

            # 성능 설정
            use_adaptive_fusion=True,
            use_optimized_engines=True,
            max_query_time=1.5
        )
        return HybridSearchEngine(config)

    async def run_basic_search_demo(self):
        """기본 검색 데모"""
        logger.info("=== Basic Search Demo ===")

        test_queries = [
            "machine learning algorithms",
            "neural network architecture",
            "데이터베이스 최적화",
            "API 보안 가이드",
            "클라우드 컴퓨팅 비용"
        ]

        async with self.session_maker() as session:
            for query in test_queries:
                logger.info(f"Searching for: '{query}'")

                # 균형잡힌 엔진으로 검색
                engine = self.search_engines['balanced']
                response = await engine.search(session, query)

                logger.info(f"Found {len(response.results)} results in {response.total_time:.3f}s")
                logger.info(f"BM25: {response.bm25_time:.3f}s, Vector: {response.vector_time:.3f}s, "
                           f"Fusion: {response.fusion_time:.3f}s, Rerank: {response.rerank_time:.3f}s")

                # 상위 3개 결과 출력
                for i, result in enumerate(response.results[:3]):
                    logger.info(f"  {i+1}. Score: {result.score:.3f} | "
                               f"Sources: {result.sources} | "
                               f"Text: {result.text[:100]}...")

                print()

    async def run_comparison_demo(self):
        """검색 엔진 비교 데모"""
        logger.info("=== Search Engine Comparison Demo ===")

        query = "deep learning neural networks"
        filters = {"canonical_in": [["AI", "ML"]]}

        async with self.session_maker() as session:
            results = {}

            for name, engine in self.search_engines.items():
                start_time = time.time()
                response = await engine.search(session, query, filters)
                total_time = time.time() - start_time

                results[name] = {
                    'response': response,
                    'total_time': total_time,
                    'result_count': len(response.results)
                }

                logger.info(f"{name.upper()} Engine:")
                logger.info(f"  Results: {len(response.results)}")
                logger.info(f"  Time: {response.total_time:.3f}s")
                logger.info(f"  Top score: {response.results[0].score:.3f}" if response.results else "  No results")

            # 성능 비교 요약
            logger.info("\n=== Performance Summary ===")
            for name, result in results.items():
                logger.info(f"{name}: {result['result_count']} results in {result['total_time']:.3f}s")

    async def run_adaptive_fusion_demo(self):
        """적응형 융합 데모"""
        logger.info("=== Adaptive Fusion Demo ===")

        test_scenarios = [
            {
                'query': 'api',  # 짧은 쿼리
                'description': 'Short query (BM25 should be prioritized)'
            },
            {
                'query': 'How to implement neural network backpropagation algorithm?',  # 긴 쿼리
                'description': 'Long query (Vector should be prioritized)'
            },
            {
                'query': '"exact phrase matching"',  # 구문 검색
                'description': 'Phrase query (BM25 should be prioritized)'
            },
            {
                'query': 'machine learning deep learning AI',  # 기술 용어
                'description': 'Technical terms (Vector should be prioritized)'
            }
        ]

        # 적응형 융합 엔진 사용
        engine = self.search_engines['accurate']  # adaptive fusion enabled

        async with self.session_maker() as session:
            for scenario in test_scenarios:
                logger.info(f"\nScenario: {scenario['description']}")
                logger.info(f"Query: '{scenario['query']}'")

                response = await engine.search(session, scenario['query'])

                if response.results:
                    # 결과 분석
                    bm25_sources = sum(1 for r in response.results if 'bm25' in r.sources)
                    vector_sources = sum(1 for r in response.results if 'vector' in r.sources)

                    logger.info(f"Results: {len(response.results)}")
                    logger.info(f"BM25 sources: {bm25_sources}, Vector sources: {vector_sources}")
                    logger.info(f"Top result score: {response.results[0].score:.3f}")

    async def run_performance_optimization_demo(self):
        """성능 최적화 데모"""
        logger.info("=== Performance Optimization Demo ===")

        # 캐시 시스템 데모
        cache = await get_cache()
        performance_monitor = get_performance_monitor()

        test_query = "performance optimization techniques"

        async with self.session_maker() as session:
            # 첫 번째 검색 (캐시 미스)
            logger.info("First search (cache miss):")
            start_time = time.time()
            response1 = await self.search_engines['balanced'].search(session, test_query)
            first_time = time.time() - start_time
            logger.info(f"Time: {first_time:.3f}s, Results: {len(response1.results)}")

            # 두 번째 검색 (캐시 히트 가능)
            logger.info("Second search (potential cache hit):")
            start_time = time.time()
            response2 = await self.search_engines['balanced'].search(session, test_query)
            second_time = time.time() - start_time
            logger.info(f"Time: {second_time:.3f}s, Results: {len(response2.results)}")

            # 캐시 통계
            cache_stats = cache.get_cache_stats()
            logger.info(f"Cache stats: {cache_stats}")

            # 성능 모니터링
            performance_report = performance_monitor.get_performance_report()
            logger.info(f"Performance report: {performance_report}")

    async def run_query_optimization_demo(self):
        """쿼리 최적화 데모"""
        logger.info("=== Query Optimization Demo ===")

        test_queries = [
            "machine    learning   algorithms!!!",  # 공백과 특수문자 정리
            "AI AI machine learning AI",  # 중복 단어 제거
            "How to optimize database performance?",  # 일반적인 쿼리
        ]

        for original_query in test_queries:
            optimized_query = QueryOptimizer.optimize_query(original_query)
            complexity = QueryOptimizer.analyze_query_complexity(original_query)

            logger.info(f"Original: '{original_query}'")
            logger.info(f"Optimized: '{optimized_query}'")
            logger.info(f"Complexity: {complexity['estimated_difficulty']} "
                       f"(score: {complexity['complexity_score']:.2f})")
            print()

    async def run_batch_processing_demo(self):
        """배치 처리 데모"""
        logger.info("=== Batch Processing Demo ===")

        from apps.search.optimization import BatchProcessor

        batch_processor = BatchProcessor(max_workers=4)
        queries = [
            "database optimization",
            "web security",
            "cloud computing",
            "machine learning",
            "API design patterns"
        ]

        async with self.session_maker() as session:
            start_time = time.time()

            # 배치 검색 처리
            results = await batch_processor.process_search_batch(
                queries,
                self.search_engines['fast'],
                session
            )

            batch_time = time.time() - start_time

            logger.info(f"Processed {len(queries)} queries in {batch_time:.3f}s")
            logger.info(f"Average time per query: {batch_time/len(queries):.3f}s")

            for i, (query, result) in enumerate(zip(queries, results)):
                if 'error' not in result:
                    logger.info(f"  {i+1}. '{query}': {len(result.results)} results")
                else:
                    logger.info(f"  {i+1}. '{query}': ERROR - {result['error']}")

    async def run_comprehensive_demo(self):
        """종합 데모 실행"""
        logger.info("🚀 Starting Hybrid Search System Comprehensive Demo")

        try:
            await self.initialize()

            # 각 데모 실행
            await self.run_basic_search_demo()
            await self.run_comparison_demo()
            await self.run_adaptive_fusion_demo()
            await self.run_performance_optimization_demo()
            await self.run_query_optimization_demo()
            await self.run_batch_processing_demo()

            logger.info("✅ All demos completed successfully!")

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise

        finally:
            if self.engine:
                await self.engine.dispose()


async def main():
    """메인 실행 함수"""
    # 데이터베이스 URL (환경에 맞게 수정)
    DATABASE_URL = "sqlite+aiosqlite:///dt_rag_test.db"
    # DATABASE_URL = "postgresql+asyncpg://user:password@localhost/db_name"

    demo = HybridSearchDemo(DATABASE_URL)
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())