"""
하이브리드 검색 시스템 성능 테스트
정확도, 속도, 확장성 등을 종합적으로 평가
"""

import asyncio
import pytest
import time
import statistics
import json
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import numpy as np

from apps.search import (
    HybridSearchEngine,
    SearchConfig,
    SearchEngineFactory,
    FusionMethod,
    NormalizationMethod,
    get_performance_monitor,
    QueryOptimizer
)

@pytest.fixture
async def db_session():
    """테스트용 데이터베이스 세션"""
    engine = create_async_engine("sqlite+aiosqlite:///dt_rag_test.db")
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        yield session

    await engine.dispose()

@pytest.fixture
def test_queries():
    """테스트용 쿼리 집합"""
    return [
        "machine learning algorithms",
        "neural network architecture",
        "database optimization",
        "API security best practices",
        "cloud computing costs",
        "data preprocessing techniques",
        "web application performance",
        "microservices architecture",
        "kubernetes deployment",
        "tensorflow implementation"
    ]

@pytest.fixture
def search_engines():
    """다양한 검색 엔진 설정"""
    return {
        'fast': SearchEngineFactory.create_fast_engine(),
        'accurate': SearchEngineFactory.create_accurate_engine(),
        'balanced': SearchEngineFactory.create_balanced_engine(),
        'bm25_only': _create_bm25_only_engine(),
        'vector_only': _create_vector_only_engine(),
        'rrf_fusion': _create_rrf_fusion_engine()
    }

def _create_bm25_only_engine():
    """BM25 전용 엔진"""
    config = SearchConfig(
        bm25_weight=1.0,
        vector_weight=0.0,
        enable_reranking=False,
        final_topk=10
    )
    return HybridSearchEngine(config)

def _create_vector_only_engine():
    """Vector 전용 엔진"""
    config = SearchConfig(
        bm25_weight=0.0,
        vector_weight=1.0,
        enable_reranking=False,
        final_topk=10
    )
    return HybridSearchEngine(config)

def _create_rrf_fusion_engine():
    """RRF 융합 엔진"""
    config = SearchConfig(
        fusion_method=FusionMethod.RRF,
        bm25_weight=0.5,
        vector_weight=0.5,
        enable_reranking=True,
        final_topk=10
    )
    return HybridSearchEngine(config)

class PerformanceTester:
    """성능 테스트 클래스"""

    def __init__(self):
        self.results = {}
        self.detailed_metrics = {}

    async def run_latency_test(
        self,
        session: AsyncSession,
        engines: Dict[str, HybridSearchEngine],
        queries: List[str],
        iterations: int = 3
    ) -> Dict[str, Dict[str, float]]:
        """검색 지연시간 테스트"""
        results = {}

        for engine_name, engine in engines.items():
            engine_results = []

            for query in queries:
                query_times = []

                for _ in range(iterations):
                    start_time = time.time()
                    await engine.search(session, query)
                    elapsed = time.time() - start_time
                    query_times.append(elapsed)

                engine_results.extend(query_times)

            # 통계 계산
            results[engine_name] = {
                'mean': statistics.mean(engine_results),
                'median': statistics.median(engine_results),
                'std': statistics.stdev(engine_results) if len(engine_results) > 1 else 0,
                'min': min(engine_results),
                'max': max(engine_results),
                'p95': np.percentile(engine_results, 95),
                'p99': np.percentile(engine_results, 99)
            }

        return results

    async def run_throughput_test(
        self,
        session: AsyncSession,
        engines: Dict[str, HybridSearchEngine],
        queries: List[str],
        concurrent_users: List[int] = [1, 5, 10, 20]
    ) -> Dict[str, Dict[int, float]]:
        """처리량 테스트"""
        results = {}

        for engine_name, engine in engines.items():
            engine_results = {}

            for user_count in concurrent_users:
                # 동시 사용자 시뮬레이션
                tasks = []
                start_time = time.time()

                for i in range(user_count):
                    query = queries[i % len(queries)]
                    task = engine.search(session, query)
                    tasks.append(task)

                await asyncio.gather(*tasks)
                elapsed = time.time() - start_time

                # QPS (Queries Per Second) 계산
                qps = user_count / elapsed
                engine_results[user_count] = qps

            results[engine_name] = engine_results

        return results

    async def run_accuracy_test(
        self,
        session: AsyncSession,
        engines: Dict[str, HybridSearchEngine],
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """정확도 테스트 (상대적 비교)"""
        results = {}

        for engine_name, engine in engines.items():
            precision_scores = []
            recall_scores = []
            f1_scores = []

            for test_case in test_cases:
                query = test_case['query']
                expected_chunks = set(test_case.get('expected_chunks', []))

                response = await engine.search(session, query)
                retrieved_chunks = set(r.chunk_id for r in response.results)

                # 정밀도, 재현율, F1 점수 계산
                if retrieved_chunks:
                    precision = len(expected_chunks & retrieved_chunks) / len(retrieved_chunks)
                    precision_scores.append(precision)

                if expected_chunks:
                    recall = len(expected_chunks & retrieved_chunks) / len(expected_chunks)
                    recall_scores.append(recall)

                if precision_scores and recall_scores:
                    p = precision_scores[-1]
                    r = recall_scores[-1]
                    f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0
                    f1_scores.append(f1)

            results[engine_name] = {
                'avg_precision': statistics.mean(precision_scores) if precision_scores else 0,
                'avg_recall': statistics.mean(recall_scores) if recall_scores else 0,
                'avg_f1': statistics.mean(f1_scores) if f1_scores else 0
            }

        return results

    async def run_scalability_test(
        self,
        session: AsyncSession,
        engine: HybridSearchEngine,
        base_queries: List[str],
        scale_factors: List[int] = [1, 2, 5, 10]
    ) -> Dict[int, Dict[str, float]]:
        """확장성 테스트"""
        results = {}

        for scale_factor in scale_factors:
            # 쿼리 수 증가
            scaled_queries = (base_queries * scale_factor)[:100]  # 최대 100개로 제한

            start_time = time.time()
            tasks = [engine.search(session, query) for query in scaled_queries]
            responses = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time

            # 메트릭 계산
            total_results = sum(len(r.results) for r in responses)
            avg_latency = elapsed / len(scaled_queries)
            qps = len(scaled_queries) / elapsed

            results[scale_factor] = {
                'query_count': len(scaled_queries),
                'total_time': elapsed,
                'avg_latency': avg_latency,
                'qps': qps,
                'total_results': total_results,
                'avg_results_per_query': total_results / len(scaled_queries)
            }

        return results

    def generate_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        return {
            'timestamp': time.time(),
            'latency_results': self.results.get('latency', {}),
            'throughput_results': self.results.get('throughput', {}),
            'accuracy_results': self.results.get('accuracy', {}),
            'scalability_results': self.results.get('scalability', {}),
            'detailed_metrics': self.detailed_metrics
        }

@pytest.mark.asyncio
async def test_search_latency(db_session, search_engines, test_queries):
    """검색 지연시간 테스트"""
    tester = PerformanceTester()

    results = await tester.run_latency_test(
        db_session, search_engines, test_queries, iterations=3
    )

    tester.results['latency'] = results

    # 성능 기준 검증
    for engine_name, metrics in results.items():
        # P95 지연시간이 2초 이하인지 확인
        assert metrics['p95'] < 2.0, f"{engine_name} P95 latency too high: {metrics['p95']:.3f}s"

        # 평균 지연시간이 1초 이하인지 확인
        assert metrics['mean'] < 1.0, f"{engine_name} mean latency too high: {metrics['mean']:.3f}s"

    print(f"Latency test results: {json.dumps(results, indent=2)}")

@pytest.mark.asyncio
async def test_search_throughput(db_session, search_engines, test_queries):
    """검색 처리량 테스트"""
    tester = PerformanceTester()

    results = await tester.run_throughput_test(
        db_session, search_engines, test_queries, concurrent_users=[1, 5, 10]
    )

    tester.results['throughput'] = results

    # 처리량 기준 검증
    for engine_name, metrics in results.items():
        # 단일 사용자 QPS가 최소 1 이상인지 확인
        assert metrics[1] >= 1.0, f"{engine_name} single-user QPS too low: {metrics[1]:.2f}"

    print(f"Throughput test results: {json.dumps(results, indent=2)}")

@pytest.mark.asyncio
async def test_fusion_methods_comparison(db_session, test_queries):
    """융합 방법 비교 테스트"""
    fusion_engines = {
        'weighted_sum': HybridSearchEngine(SearchConfig(
            fusion_method=FusionMethod.WEIGHTED_SUM,
            bm25_weight=0.5, vector_weight=0.5
        )),
        'rrf': HybridSearchEngine(SearchConfig(
            fusion_method=FusionMethod.RRF,
            bm25_weight=0.5, vector_weight=0.5
        )),
        'comb_sum': HybridSearchEngine(SearchConfig(
            fusion_method=FusionMethod.CombSUM,
            bm25_weight=0.5, vector_weight=0.5
        )),
        'comb_mnz': HybridSearchEngine(SearchConfig(
            fusion_method=FusionMethod.CombMNZ,
            bm25_weight=0.5, vector_weight=0.5
        ))
    }

    results = {}

    for method_name, engine in fusion_engines.items():
        method_results = []

        for query in test_queries[:5]:  # 샘플 쿼리로 제한
            start_time = time.time()
            response = await engine.search(db_session, query)
            elapsed = time.time() - start_time

            method_results.append({
                'query': query,
                'latency': elapsed,
                'result_count': len(response.results),
                'top_score': response.results[0].score if response.results else 0
            })

        results[method_name] = {
            'avg_latency': statistics.mean(r['latency'] for r in method_results),
            'avg_results': statistics.mean(r['result_count'] for r in method_results),
            'avg_top_score': statistics.mean(r['top_score'] for r in method_results)
        }

    print(f"Fusion methods comparison: {json.dumps(results, indent=2)}")

    # 모든 융합 방법이 합리적인 성능을 보이는지 확인
    for method, metrics in results.items():
        assert metrics['avg_latency'] < 2.0, f"{method} fusion too slow"
        assert metrics['avg_results'] > 0, f"{method} fusion returned no results"

@pytest.mark.asyncio
async def test_reranking_effectiveness(db_session, test_queries):
    """리랭킹 효과 테스트"""
    # 리랭킹 없는 엔진
    no_rerank_engine = HybridSearchEngine(SearchConfig(
        enable_reranking=False,
        final_topk=10
    ))

    # 리랭킹 있는 엔진
    with_rerank_engine = HybridSearchEngine(SearchConfig(
        enable_reranking=True,
        use_multi_stage=True,
        final_topk=10
    ))

    improvements = []

    for query in test_queries[:3]:  # 샘플로 제한
        # 리랭킹 없는 결과
        no_rerank_response = await no_rerank_engine.search(db_session, query)

        # 리랭킹 있는 결과
        with_rerank_response = await with_rerank_engine.search(db_session, query)

        # 점수 개선 정도 측정
        if (no_rerank_response.results and with_rerank_response.results):
            no_rerank_top_score = no_rerank_response.results[0].score
            with_rerank_top_score = with_rerank_response.results[0].score

            if no_rerank_top_score > 0:
                improvement = (with_rerank_top_score - no_rerank_top_score) / no_rerank_top_score
                improvements.append(improvement)

    if improvements:
        avg_improvement = statistics.mean(improvements)
        print(f"Average reranking improvement: {avg_improvement:.2%}")

        # 리랭킹이 평균적으로 개선을 보이는지 확인 (최소한 중립적이어야 함)
        assert avg_improvement >= -0.1, f"Reranking showing significant degradation: {avg_improvement:.2%}"

@pytest.mark.asyncio
async def test_query_optimization_impact(test_queries):
    """쿼리 최적화 영향 테스트"""
    optimization_results = []

    for original_query in test_queries:
        # 쿼리 복잡도 분석
        complexity = QueryOptimizer.analyze_query_complexity(original_query)

        # 쿼리 최적화
        optimized_query = QueryOptimizer.optimize_query(original_query)

        optimization_results.append({
            'original': original_query,
            'optimized': optimized_query,
            'complexity': complexity,
            'changed': original_query != optimized_query
        })

    # 결과 분석
    changed_count = sum(1 for r in optimization_results if r['changed'])
    avg_complexity = statistics.mean(r['complexity']['complexity_score'] for r in optimization_results)

    print(f"Query optimization results:")
    print(f"  Queries changed: {changed_count}/{len(test_queries)}")
    print(f"  Average complexity: {avg_complexity:.2f}")

    # 최적화가 적절히 작동하는지 확인
    assert 0 <= avg_complexity <= 1.0, f"Invalid complexity scores"

@pytest.mark.asyncio
async def test_memory_usage_stability(db_session, test_queries):
    """메모리 사용량 안정성 테스트"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    engine = SearchEngineFactory.create_balanced_engine()

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_samples = [initial_memory]

    # 연속 검색 수행
    for i in range(20):
        query = test_queries[i % len(test_queries)]
        await engine.search(db_session, query)

        if i % 5 == 0:  # 5번마다 메모리 체크
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_growth = final_memory - initial_memory

    print(f"Memory usage: {initial_memory:.1f}MB → {final_memory:.1f}MB (+{memory_growth:.1f}MB)")

    # 메모리 증가가 합리적인 범위 내인지 확인 (최대 100MB 증가)
    assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f}MB"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])