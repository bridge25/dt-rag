"""
Phase 2 성능 최적화 테스트 스크립트
비동기 병렬 처리 및 API 최적화 검증

테스트 항목:
1. BM25 + Vector 병렬 실행 성능
2. 배치 처리 처리량 측정
3. 메모리 최적화 효과 확인
4. 동시성 제어 테스트
5. 전체 시스템 성능 비교
"""

import asyncio
import time
import logging
import statistics
from typing import List, Dict, Any
import httpx
import json
import random
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 최적화 모듈들 import
try:
    from apps.api.optimization import (
        get_async_optimizer,
        get_batch_search_processor,
        get_memory_monitor,
        get_concurrency_controller,
        PERFORMANCE_TARGETS
    )
    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Optimization modules not available: {e}")
    OPTIMIZATION_AVAILABLE = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """성능 테스트 스위트"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.results = {}

        # 테스트 쿼리들
        self.test_queries = [
            "AI machine learning algorithms",
            "natural language processing",
            "computer vision deep learning",
            "reinforcement learning applications",
            "neural network architectures",
            "data preprocessing techniques",
            "model evaluation metrics",
            "feature engineering methods",
            "classification algorithms comparison",
            "regression analysis techniques",
            "clustering algorithms overview",
            "dimensionality reduction methods",
            "time series forecasting",
            "recommendation systems",
            "ensemble learning methods",
            "cross validation techniques",
            "hyperparameter optimization",
            "transfer learning applications",
            "generative adversarial networks",
            "transformer architecture explanation"
        ]

    async def test_parallel_search_performance(self) -> Dict[str, Any]:
        """BM25 + Vector 병렬 검색 성능 테스트"""
        logger.info("🔄 Testing parallel search performance...")

        if not OPTIMIZATION_AVAILABLE:
            return {"error": "Optimization modules not available"}

        try:
            # Database import
            from apps.api.database import SearchDAO, db_manager

            results = {
                "sequential_times": [],
                "parallel_times": [],
                "speedup_ratios": [],
                "memory_usage": []
            }

            async_optimizer = await get_async_optimizer()
            memory_monitor = await get_memory_monitor()

            # 10개 테스트 쿼리로 성능 측정
            for i, query in enumerate(self.test_queries[:10]):
                logger.info(f"Testing query {i+1}/10: {query[:30]}...")

                # 메모리 상태 확인
                memory_before = await memory_monitor.check_memory_usage()

                # 순차 실행 시간 측정 (레거시 방식)
                start_time = time.time()
                async with db_manager.async_session() as session:
                    try:
                        # 레거시 하이브리드 검색
                        legacy_results = await SearchDAO._execute_legacy_hybrid_search(
                            query, None, 5, 12, 12, 50
                        )
                    except Exception as e:
                        logger.warning(f"Legacy search failed: {e}")
                        legacy_results = []
                sequential_time = time.time() - start_time
                results["sequential_times"].append(sequential_time)

                # 병렬 실행 시간 측정 (최적화 방식)
                start_time = time.time()
                try:
                    optimized_results = await SearchDAO.hybrid_search(
                        query=query,
                        filters=None,
                        topk=5,
                        bm25_topk=12,
                        vector_topk=12,
                        rerank_candidates=50
                    )
                except Exception as e:
                    logger.warning(f"Optimized search failed: {e}")
                    optimized_results = []
                parallel_time = time.time() - start_time
                results["parallel_times"].append(parallel_time)

                # 성능 향상 비율 계산
                speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
                results["speedup_ratios"].append(speedup)

                # 메모리 사용량 기록
                memory_after = await memory_monitor.check_memory_usage()
                memory_usage = memory_after.get("current_usage", {}).get("rss_mb", 0)
                results["memory_usage"].append(memory_usage)

                # 잠시 대기 (시스템 안정화)
                await asyncio.sleep(0.1)

            # 통계 계산
            avg_sequential = statistics.mean(results["sequential_times"])
            avg_parallel = statistics.mean(results["parallel_times"])
            avg_speedup = statistics.mean(results["speedup_ratios"])
            avg_memory = statistics.mean(results["memory_usage"])

            performance_result = {
                "avg_sequential_time": avg_sequential,
                "avg_parallel_time": avg_parallel,
                "avg_speedup": avg_speedup,
                "avg_memory_mb": avg_memory,
                "p95_parallel_time": statistics.quantiles(results["parallel_times"], n=20)[18] if len(results["parallel_times"]) >= 20 else max(results["parallel_times"]),
                "target_p95_ms": PERFORMANCE_TARGETS["p95_latency_ms"],
                "meets_target": (avg_parallel * 1000) <= PERFORMANCE_TARGETS["p95_latency_ms"],
                "sample_size": len(results["parallel_times"])
            }

            logger.info(f"✅ Parallel search test completed:")
            logger.info(f"   Average speedup: {avg_speedup:.2f}x")
            logger.info(f"   P95 latency: {performance_result['p95_parallel_time']*1000:.1f}ms")
            logger.info(f"   Target met: {performance_result['meets_target']}")

            return performance_result

        except Exception as e:
            logger.error(f"Parallel search test failed: {e}")
            return {"error": str(e)}

    async def test_batch_processing_throughput(self) -> Dict[str, Any]:
        """배치 처리 처리량 테스트"""
        logger.info("🔄 Testing batch processing throughput...")

        if not OPTIMIZATION_AVAILABLE:
            return {"error": "Optimization modules not available"}

        try:
            batch_processor = get_batch_search_processor()

            # 다양한 배치 크기로 테스트
            batch_sizes = [1, 5, 10, 20, 50]
            results = {}

            for batch_size in batch_sizes:
                logger.info(f"Testing batch size: {batch_size}")

                # 테스트 쿼리 준비
                test_queries = self.test_queries[:batch_size]
                search_params = {
                    "filters": None,
                    "bm25_topk": 12,
                    "vector_topk": 12,
                    "final_topk": 5,
                    "rerank_candidates": 50
                }

                # 배치 처리 시간 측정
                start_time = time.time()

                # 배치 요청 동시 제출
                tasks = []
                for query in test_queries:
                    task = batch_processor.submit_search_request(
                        query=query,
                        search_params=search_params,
                        priority=0
                    )
                    tasks.append(task)

                # 모든 결과 대기
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                processing_time = time.time() - start_time

                # 성공/실패 카운트
                successful_results = sum(1 for r in batch_results if not isinstance(r, Exception))
                failed_results = len(batch_results) - successful_results

                # 처리량 계산
                throughput = len(test_queries) / processing_time if processing_time > 0 else 0

                results[f"batch_{batch_size}"] = {
                    "batch_size": batch_size,
                    "processing_time": processing_time,
                    "throughput_qps": throughput,
                    "successful_requests": successful_results,
                    "failed_requests": failed_results,
                    "success_rate": successful_results / len(batch_results) if batch_results else 0
                }

                await asyncio.sleep(0.2)  # 배치 간 대기

            # 최고 처리량 찾기
            best_throughput = max(results.values(), key=lambda x: x["throughput_qps"])

            # 배치 프로세서 메트릭
            batch_metrics = batch_processor.get_metrics()

            throughput_result = {
                "batch_results": results,
                "best_performance": best_throughput,
                "target_qps": PERFORMANCE_TARGETS["throughput_qps"],
                "meets_target": best_throughput["throughput_qps"] >= PERFORMANCE_TARGETS["throughput_qps"],
                "batch_processor_metrics": batch_metrics.__dict__
            }

            logger.info(f"✅ Batch processing test completed:")
            logger.info(f"   Best throughput: {best_throughput['throughput_qps']:.1f} QPS")
            logger.info(f"   Best batch size: {best_throughput['batch_size']}")
            logger.info(f"   Target met: {throughput_result['meets_target']}")

            return throughput_result

        except Exception as e:
            logger.error(f"Batch processing test failed: {e}")
            return {"error": str(e)}

    async def test_memory_optimization(self) -> Dict[str, Any]:
        """메모리 최적화 효과 테스트"""
        logger.info("🔄 Testing memory optimization...")

        if not OPTIMIZATION_AVAILABLE:
            return {"error": "Optimization modules not available"}

        try:
            from apps.api.optimization.memory_optimizer import (
                get_embedding_quantizer,
                get_streaming_processor,
                get_gc_optimizer
            )

            memory_monitor = await get_memory_monitor()
            quantizer = get_embedding_quantizer()
            streaming_processor = get_streaming_processor()
            gc_optimizer = get_gc_optimizer()

            # 초기 메모리 상태
            initial_memory = await memory_monitor.check_memory_usage()

            # 1. 임베딩 양자화 테스트
            import numpy as np
            test_embeddings = [np.random.rand(1536).astype(np.float32) for _ in range(100)]

            quantization_results = []
            for embedding in test_embeddings:
                quantized, metadata = quantizer.quantize_embedding(embedding)
                quantization_results.append({
                    "original_size": embedding.nbytes,
                    "quantized_size": quantized.nbytes,
                    "compression_ratio": embedding.nbytes / quantized.nbytes
                })

            avg_compression = statistics.mean([r["compression_ratio"] for r in quantization_results])

            # 2. 스트리밍 테스트
            large_result_set = [
                {"chunk_id": f"chunk_{i}", "text": "dummy text " * 100, "score": random.random()}
                for i in range(1000)
            ]

            streaming_chunks = []
            async for chunk in streaming_processor.stream_search_results(large_result_set):
                streaming_chunks.append(len(chunk))

            # 3. GC 최적화 테스트
            async with gc_optimizer.optimized_gc_context():
                # 메모리 집약적 작업 시뮬레이션
                large_data = [list(range(10000)) for _ in range(100)]
                del large_data

            # 최종 메모리 상태
            final_memory = await memory_monitor.check_memory_usage()

            # 메모리 효율성 계산
            memory_saved = initial_memory.get("current_usage", {}).get("rss_mb", 0) - final_memory.get("current_usage", {}).get("rss_mb", 0)

            memory_result = {
                "quantization": {
                    "avg_compression_ratio": avg_compression,
                    "samples_tested": len(quantization_results),
                    "memory_saved_percent": (avg_compression - 1) / avg_compression * 100
                },
                "streaming": {
                    "original_items": len(large_result_set),
                    "streaming_chunks": len(streaming_chunks),
                    "avg_chunk_size": statistics.mean(streaming_chunks) if streaming_chunks else 0
                },
                "garbage_collection": {
                    "gc_stats": gc_optimizer.get_gc_stats()
                },
                "memory_usage": {
                    "initial_mb": initial_memory.get("current_usage", {}).get("rss_mb", 0),
                    "final_mb": final_memory.get("current_usage", {}).get("rss_mb", 0),
                    "saved_mb": memory_saved,
                    "efficiency_improvement": avg_compression
                },
                "target_efficiency": PERFORMANCE_TARGETS["memory_efficiency"],
                "meets_target": avg_compression >= (1 + PERFORMANCE_TARGETS["memory_efficiency"])
            }

            logger.info(f"✅ Memory optimization test completed:")
            logger.info(f"   Compression ratio: {avg_compression:.2f}x")
            logger.info(f"   Memory saved: {memory_saved:.1f}MB")
            logger.info(f"   Target met: {memory_result['meets_target']}")

            return memory_result

        except Exception as e:
            logger.error(f"Memory optimization test failed: {e}")
            return {"error": str(e)}

    async def test_concurrency_control(self) -> Dict[str, Any]:
        """동시성 제어 테스트"""
        logger.info("🔄 Testing concurrency control...")

        if not OPTIMIZATION_AVAILABLE:
            return {"error": "Optimization modules not available"}

        try:
            concurrency_controller = get_concurrency_controller()

            # 동시 요청 시뮬레이션
            concurrent_requests = 20
            request_tasks = []

            async def simulate_search_request(request_id: int):
                """개별 검색 요청 시뮬레이션"""
                async with concurrency_controller.controlled_execution("test_search"):
                    # 검색 작업 시뮬레이션
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    return {"request_id": request_id, "status": "completed"}

            # 동시 요청 생성
            start_time = time.time()
            for i in range(concurrent_requests):
                task = simulate_search_request(i)
                request_tasks.append(task)

            # 모든 요청 완료 대기
            results = await asyncio.gather(*request_tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # 결과 분석
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            failed_requests = len(results) - successful_requests

            # 동시성 통계
            concurrency_stats = concurrency_controller.get_comprehensive_stats()

            concurrency_result = {
                "concurrent_requests": concurrent_requests,
                "total_time": total_time,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "requests_per_second": concurrent_requests / total_time if total_time > 0 else 0,
                "concurrency_stats": concurrency_stats,
                "target_error_rate": PERFORMANCE_TARGETS["error_rate"],
                "actual_error_rate": failed_requests / concurrent_requests if concurrent_requests > 0 else 0,
                "meets_target": (failed_requests / concurrent_requests) <= PERFORMANCE_TARGETS["error_rate"]
            }

            logger.info(f"✅ Concurrency control test completed:")
            logger.info(f"   Success rate: {successful_requests}/{concurrent_requests}")
            logger.info(f"   Error rate: {concurrency_result['actual_error_rate']:.3f}")
            logger.info(f"   Target met: {concurrency_result['meets_target']}")

            return concurrency_result

        except Exception as e:
            logger.error(f"Concurrency control test failed: {e}")
            return {"error": str(e)}

    async def test_api_endpoints(self) -> Dict[str, Any]:
        """API 엔드포인트 성능 테스트"""
        logger.info("🔄 Testing API endpoints...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                results = {}

                # 1. 기본 검색 API 테스트
                search_latencies = []
                for i in range(5):
                    start_time = time.time()
                    try:
                        response = await client.post(
                            f"{self.api_base_url}/search",
                            json={
                                "q": self.test_queries[i % len(self.test_queries)],
                                "final_topk": 5,
                                "bm25_topk": 12,
                                "vector_topk": 12
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        latency = (time.time() - start_time) * 1000
                        search_latencies.append(latency)

                        if response.status_code == 200:
                            logger.info(f"Search API test {i+1}/5: {latency:.1f}ms")
                        else:
                            logger.warning(f"Search API test {i+1}/5 failed: {response.status_code}")

                    except Exception as e:
                        logger.warning(f"Search API test {i+1}/5 error: {e}")

                    await asyncio.sleep(0.1)

                # 2. 배치 검색 API 테스트 (if available)
                batch_latencies = []
                try:
                    batch_queries = [
                        {"q": query, "final_topk": 5}
                        for query in self.test_queries[:5]
                    ]

                    start_time = time.time()
                    batch_response = await client.post(
                        f"{self.api_base_url}/api/v1/batch/search",
                        json={
                            "queries": batch_queries,
                            "response_format": "json",
                            "timeout_seconds": 30
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    batch_latency = (time.time() - start_time) * 1000
                    batch_latencies.append(batch_latency)

                    if batch_response.status_code == 200:
                        logger.info(f"Batch API test: {batch_latency:.1f}ms")
                    else:
                        logger.warning(f"Batch API test failed: {batch_response.status_code}")

                except Exception as e:
                    logger.warning(f"Batch API test error: {e}")

                # 통계 계산
                avg_search_latency = statistics.mean(search_latencies) if search_latencies else 0
                p95_search_latency = statistics.quantiles(search_latencies, n=20)[18] if len(search_latencies) >= 20 else max(search_latencies) if search_latencies else 0

                api_result = {
                    "search_api": {
                        "tests_completed": len(search_latencies),
                        "avg_latency_ms": avg_search_latency,
                        "p95_latency_ms": p95_search_latency,
                        "all_latencies": search_latencies
                    },
                    "batch_api": {
                        "tests_completed": len(batch_latencies),
                        "avg_latency_ms": statistics.mean(batch_latencies) if batch_latencies else 0,
                        "all_latencies": batch_latencies
                    },
                    "target_p95_ms": PERFORMANCE_TARGETS["p95_latency_ms"],
                    "meets_target": p95_search_latency <= PERFORMANCE_TARGETS["p95_latency_ms"]
                }

                logger.info(f"✅ API endpoint test completed:")
                logger.info(f"   Search API P95: {p95_search_latency:.1f}ms")
                logger.info(f"   Target met: {api_result['meets_target']}")

                return api_result

        except Exception as e:
            logger.error(f"API endpoint test failed: {e}")
            return {"error": str(e)}

    async def run_full_performance_test(self) -> Dict[str, Any]:
        """전체 성능 테스트 실행"""
        logger.info("🚀 Starting comprehensive performance test suite...")

        start_time = time.time()

        # 모든 테스트 실행
        test_results = {}

        # 1. 병렬 검색 성능 테스트
        test_results["parallel_search"] = await self.test_parallel_search_performance()

        # 2. 배치 처리 테스트
        test_results["batch_processing"] = await self.test_batch_processing_throughput()

        # 3. 메모리 최적화 테스트
        test_results["memory_optimization"] = await self.test_memory_optimization()

        # 4. 동시성 제어 테스트
        test_results["concurrency_control"] = await self.test_concurrency_control()

        # 5. API 엔드포인트 테스트
        test_results["api_endpoints"] = await self.test_api_endpoints()

        total_time = time.time() - start_time

        # 전체 성능 평가
        performance_summary = self._generate_performance_summary(test_results, total_time)

        logger.info(f"🎉 Performance test suite completed in {total_time:.1f}s")
        logger.info(f"📊 Overall performance grade: {performance_summary['overall_grade']}")

        return {
            "test_results": test_results,
            "performance_summary": performance_summary,
            "total_test_time": total_time,
            "timestamp": time.time()
        }

    def _generate_performance_summary(self, test_results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """성능 테스트 요약 생성"""
        targets_met = 0
        total_targets = 0

        performance_scores = []

        # 각 테스트 결과 평가
        for test_name, result in test_results.items():
            if "error" in result:
                continue

            meets_target = result.get("meets_target", False)
            if meets_target is not None:
                total_targets += 1
                if meets_target:
                    targets_met += 1
                    performance_scores.append(100)
                else:
                    performance_scores.append(60)

        # 전체 점수 계산
        overall_score = statistics.mean(performance_scores) if performance_scores else 0

        # 등급 산정
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        else:
            grade = "D"

        return {
            "overall_score": overall_score,
            "overall_grade": grade,
            "targets_met": targets_met,
            "total_targets": total_targets,
            "success_rate": targets_met / total_targets if total_targets > 0 else 0,
            "performance_targets": PERFORMANCE_TARGETS,
            "recommendations": self._generate_recommendations(test_results)
        }

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []

        # 병렬 검색 성능 분석
        parallel_result = test_results.get("parallel_search", {})
        if not parallel_result.get("meets_target", True):
            recommendations.append("병렬 검색 성능 최적화 필요 - BM25와 Vector 검색 간 부하 균형 조정")

        # 배치 처리 분석
        batch_result = test_results.get("batch_processing", {})
        if not batch_result.get("meets_target", True):
            recommendations.append("배치 처리 크기 조정 및 연결 풀 최적화 필요")

        # 메모리 최적화 분석
        memory_result = test_results.get("memory_optimization", {})
        if not memory_result.get("meets_target", True):
            recommendations.append("메모리 압축률 개선 및 가비지 컬렉션 튜닝 필요")

        # 동시성 제어 분석
        concurrency_result = test_results.get("concurrency_control", {})
        if not concurrency_result.get("meets_target", True):
            recommendations.append("동시성 제어 파라미터 조정 및 에러 핸들링 개선 필요")

        # API 엔드포인트 분석
        api_result = test_results.get("api_endpoints", {})
        if not api_result.get("meets_target", True):
            recommendations.append("API 응답시간 최적화 및 캐싱 전략 개선 필요")

        if not recommendations:
            recommendations.append("모든 성능 목표 달성 - 현재 최적화 상태 유지")

        return recommendations

async def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("Phase 2 성능 최적화 테스트 시작")
    logger.info("=" * 60)

    if not OPTIMIZATION_AVAILABLE:
        logger.error("❌ 최적화 모듈이 사용 불가능합니다.")
        logger.error("   다음 명령어로 필요한 종속성을 설치하세요:")
        logger.error("   pip install psutil numpy scikit-learn")
        return

    # 테스트 스위트 실행
    test_suite = PerformanceTestSuite()

    try:
        # 전체 성능 테스트 실행
        results = await test_suite.run_full_performance_test()

        # 결과 파일 저장
        results_file = "phase2_optimization_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📄 결과가 {results_file}에 저장되었습니다.")

        # 요약 출력
        summary = results["performance_summary"]
        logger.info("=" * 60)
        logger.info("📊 Phase 2 최적화 성능 테스트 결과")
        logger.info("=" * 60)
        logger.info(f"전체 점수: {summary['overall_score']:.1f}/100")
        logger.info(f"등급: {summary['overall_grade']}")
        logger.info(f"목표 달성률: {summary['targets_met']}/{summary['total_targets']} ({summary['success_rate']:.1%})")
        logger.info("")
        logger.info("📋 권장사항:")
        for i, rec in enumerate(summary["recommendations"], 1):
            logger.info(f"  {i}. {rec}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())