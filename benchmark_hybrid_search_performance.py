#!/usr/bin/env python3
"""
Dynamic Taxonomy RAG v1.8.1 하이브리드 검색 성능 벤치마크
BM25 + Vector + Cross-encoder 하이브리드 검색 시스템 종합 성능 측정

성능 목표:
- 검색 응답 시간: < 100ms
- API 응답 시간: < 200ms
- 정확도: > 85%
- 처리량: > 100 req/sec
"""

import asyncio
import time
import json
import statistics
import sys
import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

try:
    from database import SearchDAO, db_manager, EmbeddingService
except ImportError:
    print("데이터베이스 모듈을 찾을 수 없습니다. apps/api 경로를 확인해주세요.")
    sys.exit(1)

@dataclass
class BenchmarkResult:
    """벤치마크 결과 데이터 클래스"""
    test_name: str
    query_count: int
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    throughput: float
    error_rate: float
    accuracy: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class HybridSearchBenchmark:
    """하이브리드 검색 성능 벤치마크 클래스"""

    def __init__(self, api_base_url: str = "http://localhost:8000", api_key: str = None):
        self.api_base_url = api_base_url
        self.api_key = api_key or os.getenv("API_KEY", "test-key")
        self.results = []

        # 테스트 쿼리 세트
        self.test_queries = {
            "simple": [
                "AI",
                "machine learning",
                "classification",
                "vector search",
                "embedding"
            ],
            "medium": [
                "AI machine learning algorithms",
                "vector similarity search optimization",
                "document classification taxonomy",
                "embedding model performance",
                "hybrid search ranking"
            ],
            "complex": [
                "how to implement BM25 algorithm for text retrieval",
                "comparison of vector similarity search methods in RAG systems",
                "optimizing cross-encoder reranking for document retrieval accuracy",
                "hybrid search combining BM25 and vector similarity with taxonomy filtering",
                "performance benchmarking of embedding models for semantic search applications"
            ]
        }

        # 다양한 필터 조건
        self.test_filters = [
            None,  # 필터 없음
            {"canonical_in": [["AI", "ML"]]},
            {"canonical_in": [["AI", "NLP"], ["Tech", "Search"]]},
            {"source_type": "document"},
            {"canonical_in": [["AI"]], "source_type": "document"}
        ]

    async def initialize_database(self):
        """데이터베이스 연결 및 초기화"""
        print("데이터베이스 연결 초기화 중...")
        try:
            async with db_manager.async_session() as session:
                # 간단한 연결 테스트
                await SearchDAO._get_chunk_count(session)
                print("✓ 데이터베이스 연결 성공")
                return True
        except Exception as e:
            print(f"✗ 데이터베이스 연결 실패: {e}")
            return False

    async def benchmark_bm25_search(self, query_complexity: str = "medium", iterations: int = 100):
        """BM25 검색 성능 벤치마크"""
        print(f"\n=== BM25 검색 벤치마크 ({query_complexity}, {iterations}회) ===")

        queries = self.test_queries[query_complexity]
        latencies = []
        errors = 0

        start_time = time.time()

        async with db_manager.async_session() as session:
            for i in range(iterations):
                query = queries[i % len(queries)]
                filters = self.test_filters[i % len(self.test_filters)]

                try:
                    search_start = time.time()
                    results = await SearchDAO._perform_bm25_search(
                        session=session,
                        query=query,
                        topk=10,
                        filters=filters
                    )
                    latency = time.time() - search_start
                    latencies.append(latency * 1000)  # ms 단위

                    if i % 20 == 0:
                        print(f"진행률: {i+1}/{iterations} ({latency*1000:.1f}ms)")

                except Exception as e:
                    errors += 1
                    print(f"오류 발생 (쿼리 {i+1}): {e}")

        total_time = time.time() - start_time
        throughput = iterations / total_time

        return BenchmarkResult(
            test_name=f"BM25_{query_complexity}",
            query_count=iterations,
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p50_latency=statistics.median(latencies),
            p95_latency=np.percentile(latencies, 95),
            p99_latency=np.percentile(latencies, 99),
            throughput=throughput,
            error_rate=errors / iterations * 100
        )

    async def benchmark_vector_search(self, query_complexity: str = "medium", iterations: int = 50):
        """Vector 검색 성능 벤치마크"""
        print(f"\n=== Vector 검색 벤치마크 ({query_complexity}, {iterations}회) ===")

        queries = self.test_queries[query_complexity]
        latencies = []
        embedding_times = []
        search_times = []
        errors = 0

        start_time = time.time()

        async with db_manager.async_session() as session:
            for i in range(iterations):
                query = queries[i % len(queries)]
                filters = self.test_filters[i % len(self.test_filters)]

                try:
                    # 임베딩 생성 시간 측정
                    embed_start = time.time()
                    query_embedding = await EmbeddingService.generate_embedding(query)
                    embed_time = time.time() - embed_start
                    embedding_times.append(embed_time * 1000)

                    # Vector 검색 시간 측정
                    search_start = time.time()
                    results = await SearchDAO._perform_vector_search(
                        session=session,
                        query_embedding=query_embedding,
                        topk=10,
                        filters=filters
                    )
                    search_time = time.time() - search_start
                    search_times.append(search_time * 1000)

                    total_latency = embed_time + search_time
                    latencies.append(total_latency * 1000)

                    if i % 10 == 0:
                        print(f"진행률: {i+1}/{iterations} (임베딩: {embed_time*1000:.1f}ms, 검색: {search_time*1000:.1f}ms)")

                except Exception as e:
                    errors += 1
                    print(f"오류 발생 (쿼리 {i+1}): {e}")

        total_time = time.time() - start_time
        throughput = iterations / total_time

        print(f"평균 임베딩 시간: {statistics.mean(embedding_times):.1f}ms")
        print(f"평균 검색 시간: {statistics.mean(search_times):.1f}ms")

        return BenchmarkResult(
            test_name=f"Vector_{query_complexity}",
            query_count=iterations,
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p50_latency=statistics.median(latencies),
            p95_latency=np.percentile(latencies, 95),
            p99_latency=np.percentile(latencies, 99),
            throughput=throughput,
            error_rate=errors / iterations * 100
        )

    async def benchmark_hybrid_search(self, query_complexity: str = "medium", iterations: int = 50):
        """하이브리드 검색 성능 벤치마크"""
        print(f"\n=== 하이브리드 검색 벤치마크 ({query_complexity}, {iterations}회) ===")

        queries = self.test_queries[query_complexity]
        latencies = []
        errors = 0
        accuracy_scores = []

        start_time = time.time()

        for i in range(iterations):
            query = queries[i % len(queries)]
            filters = self.test_filters[i % len(self.test_filters)]

            try:
                search_start = time.time()
                results = await SearchDAO.hybrid_search(
                    query=query,
                    filters=filters,
                    topk=5,
                    bm25_topk=12,
                    vector_topk=12,
                    rerank_candidates=20
                )
                latency = time.time() - search_start
                latencies.append(latency * 1000)

                # 결과 품질 평가 (간단한 점수 기반)
                if results:
                    avg_score = statistics.mean([r.get('score', 0) for r in results])
                    accuracy_scores.append(avg_score)

                if i % 10 == 0:
                    print(f"진행률: {i+1}/{iterations} ({latency*1000:.1f}ms, 결과: {len(results)}개)")

            except Exception as e:
                errors += 1
                print(f"오류 발생 (쿼리 {i+1}): {e}")

        total_time = time.time() - start_time
        throughput = iterations / total_time
        avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0

        return BenchmarkResult(
            test_name=f"Hybrid_{query_complexity}",
            query_count=iterations,
            avg_latency=statistics.mean(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            p50_latency=statistics.median(latencies),
            p95_latency=np.percentile(latencies, 95),
            p99_latency=np.percentile(latencies, 99),
            throughput=throughput,
            error_rate=errors / iterations * 100,
            accuracy=avg_accuracy
        )

    def benchmark_api_endpoints(self, iterations: int = 100):
        """API 엔드포인트 성능 벤치마크 (동기)"""
        print(f"\n=== API 엔드포인트 벤치마크 ({iterations}회) ===")

        latencies = []
        errors = 0

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        start_time = time.time()

        for i in range(iterations):
            query = self.test_queries["medium"][i % len(self.test_queries["medium"])]
            filters = self.test_filters[i % len(self.test_filters)]

            payload = {
                "q": query,
                "filters": filters,
                "final_topk": 5
            }

            try:
                api_start = time.time()
                response = requests.post(
                    f"{self.api_base_url}/search",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                latency = time.time() - api_start

                if response.status_code == 200:
                    latencies.append(latency * 1000)
                else:
                    errors += 1
                    print(f"API 오류 {response.status_code}: {response.text}")

                if i % 20 == 0:
                    print(f"진행률: {i+1}/{iterations} ({latency*1000:.1f}ms)")

            except Exception as e:
                errors += 1
                print(f"요청 오류 (쿼리 {i+1}): {e}")

        total_time = time.time() - start_time
        throughput = iterations / total_time

        return BenchmarkResult(
            test_name="API_Endpoint",
            query_count=iterations,
            avg_latency=statistics.mean(latencies) if latencies else 0,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p50_latency=statistics.median(latencies) if latencies else 0,
            p95_latency=np.percentile(latencies, 95) if latencies else 0,
            p99_latency=np.percentile(latencies, 99) if latencies else 0,
            throughput=throughput,
            error_rate=errors / iterations * 100
        )

    def benchmark_concurrent_requests(self, concurrent_users: int = 10, requests_per_user: int = 10):
        """동시 요청 처리 성능 벤치마크"""
        print(f"\n=== 동시 요청 벤치마크 ({concurrent_users}명, 각 {requests_per_user}회) ===")

        def make_request(user_id: int, request_id: int):
            """단일 HTTP 요청 실행"""
            query = self.test_queries["medium"][request_id % len(self.test_queries["medium"])]

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            payload = {
                "q": query,
                "final_topk": 5
            }

            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.api_base_url}/search",
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                latency = time.time() - start_time

                return {
                    "user_id": user_id,
                    "request_id": request_id,
                    "latency": latency * 1000,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
            except Exception as e:
                latency = time.time() - start_time
                return {
                    "user_id": user_id,
                    "request_id": request_id,
                    "latency": latency * 1000,
                    "status_code": 0,
                    "success": False,
                    "error": str(e)
                }

        # 동시 요청 실행
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []

            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)

            # 결과 수집
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if len(results) % 20 == 0:
                    print(f"완료된 요청: {len(results)}/{len(futures)}")

        total_time = time.time() - start_time
        successful_results = [r for r in results if r["success"]]

        if successful_results:
            latencies = [r["latency"] for r in successful_results]
            throughput = len(successful_results) / total_time
            error_rate = (len(results) - len(successful_results)) / len(results) * 100

            return BenchmarkResult(
                test_name=f"Concurrent_{concurrent_users}users",
                query_count=len(results),
                avg_latency=statistics.mean(latencies),
                min_latency=min(latencies),
                max_latency=max(latencies),
                p50_latency=statistics.median(latencies),
                p95_latency=np.percentile(latencies, 95),
                p99_latency=np.percentile(latencies, 99),
                throughput=throughput,
                error_rate=error_rate
            )
        else:
            return BenchmarkResult(
                test_name=f"Concurrent_{concurrent_users}users",
                query_count=len(results),
                avg_latency=0,
                min_latency=0,
                max_latency=0,
                p50_latency=0,
                p95_latency=0,
                p99_latency=0,
                throughput=0,
                error_rate=100
            )

    def generate_performance_report(self):
        """성능 벤치마크 보고서 생성"""
        print("\n" + "="*80)
        print("하이브리드 검색 성능 벤치마크 보고서")
        print("="*80)

        for result in self.results:
            print(f"\n[{result.test_name}]")
            print(f"쿼리 수: {result.query_count}")
            print(f"평균 지연시간: {result.avg_latency:.2f}ms")
            print(f"P50 지연시간: {result.p50_latency:.2f}ms")
            print(f"P95 지연시간: {result.p95_latency:.2f}ms")
            print(f"P99 지연시간: {result.p99_latency:.2f}ms")
            print(f"처리량: {result.throughput:.2f} req/sec")
            print(f"오류율: {result.error_rate:.2f}%")

            if result.accuracy is not None:
                print(f"정확도 점수: {result.accuracy:.3f}")

            # 성능 목표 달성 여부 확인
            targets_met = []
            if result.avg_latency < 100:
                targets_met.append("✓ 지연시간 목표 달성")
            else:
                targets_met.append("✗ 지연시간 목표 미달성")

            if result.throughput > 100:
                targets_met.append("✓ 처리량 목표 달성")
            else:
                targets_met.append("✗ 처리량 목표 미달성")

            if result.error_rate < 5:
                targets_met.append("✓ 안정성 목표 달성")
            else:
                targets_met.append("✗ 안정성 목표 미달성")

            print("목표 달성도:")
            for target in targets_met:
                print(f"  {target}")

    def save_results_to_file(self, filename: str = None):
        """벤치마크 결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hybrid_search_benchmark_{timestamp}.json"

        results_data = []
        for result in self.results:
            results_data.append({
                "test_name": result.test_name,
                "query_count": result.query_count,
                "avg_latency": result.avg_latency,
                "min_latency": result.min_latency,
                "max_latency": result.max_latency,
                "p50_latency": result.p50_latency,
                "p95_latency": result.p95_latency,
                "p99_latency": result.p99_latency,
                "throughput": result.throughput,
                "error_rate": result.error_rate,
                "accuracy": result.accuracy,
                "timestamp": datetime.now().isoformat()
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n벤치마크 결과가 저장되었습니다: {filename}")
        return filename

    async def run_comprehensive_benchmark(self):
        """종합 성능 벤치마크 실행"""
        print("Dynamic Taxonomy RAG v1.8.1 하이브리드 검색 성능 벤치마크")
        print("="*80)

        # 데이터베이스 초기화
        if not await self.initialize_database():
            print("데이터베이스 연결에 실패했습니다. 벤치마크를 중단합니다.")
            return

        try:
            # 1. BM25 검색 벤치마크
            for complexity in ["simple", "medium", "complex"]:
                iterations = 100 if complexity == "simple" else 50
                result = await self.benchmark_bm25_search(complexity, iterations)
                self.results.append(result)

            # 2. Vector 검색 벤치마크
            for complexity in ["simple", "medium", "complex"]:
                iterations = 50 if complexity == "simple" else 30
                result = await self.benchmark_vector_search(complexity, iterations)
                self.results.append(result)

            # 3. 하이브리드 검색 벤치마크
            for complexity in ["simple", "medium", "complex"]:
                iterations = 50 if complexity == "simple" else 30
                result = await self.benchmark_hybrid_search(complexity, iterations)
                self.results.append(result)

            # 4. API 엔드포인트 벤치마크
            print("\nAPI 서버가 실행 중인지 확인하고 있습니다...")
            try:
                response = requests.get(f"{self.api_base_url}/health", timeout=5)
                if response.status_code == 200:
                    api_result = self.benchmark_api_endpoints(100)
                    self.results.append(api_result)

                    # 5. 동시 요청 벤치마크
                    concurrent_result = self.benchmark_concurrent_requests(10, 10)
                    self.results.append(concurrent_result)
                else:
                    print("API 서버가 응답하지 않습니다. API 벤치마크를 건너뜁니다.")
            except Exception as e:
                print(f"API 서버 연결 실패: {e}")
                print("API 벤치마크를 건너뜁니다.")

            # 결과 보고서 생성
            self.generate_performance_report()

            # 결과 파일 저장
            self.save_results_to_file()

        except Exception as e:
            print(f"벤치마크 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """메인 실행 함수"""
    benchmark = HybridSearchBenchmark()
    await benchmark.run_comprehensive_benchmark()

if __name__ == "__main__":
    asyncio.run(main())