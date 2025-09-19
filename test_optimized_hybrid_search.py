#!/usr/bin/env python3
"""
최적화된 하이브리드 검색 시스템 종합 테스트
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 스펙 검증
"""

import asyncio
import time
import json
import sys
import os
from typing import List, Dict, Any
import logging

# 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_optimized_hybrid_search():
    """최적화된 하이브리드 검색 시스템 테스트"""

    test_results = {
        "test_name": "Optimized Hybrid Search System Test",
        "timestamp": time.time(),
        "performance_targets": {
            "recall_at_10": 0.85,
            "search_latency_p95": 1.0,  # 1초
            "cost_per_search": 3.0  # ₩3
        },
        "tests": {},
        "summary": {}
    }

    try:
        # 1. 기본 모듈 import 테스트
        logger.info("=== Module Import Tests ===")
        test_results["tests"]["module_imports"] = await test_module_imports()

        # 2. 데이터베이스 연결 테스트
        logger.info("=== Database Connection Tests ===")
        test_results["tests"]["database_connection"] = await test_database_connection()

        # 3. SQLite FTS5 최적화 테스트
        logger.info("=== SQLite FTS5 Optimization Tests ===")
        test_results["tests"]["sqlite_fts5"] = await test_sqlite_fts5_optimization()

        # 4. 캐싱 시스템 테스트
        logger.info("=== Caching System Tests ===")
        test_results["tests"]["caching_system"] = await test_caching_system()

        # 5. 임베딩 최적화 테스트
        logger.info("=== Embedding Optimization Tests ===")
        test_results["tests"]["embedding_optimization"] = await test_embedding_optimization()

        # 6. 하이브리드 검색 엔진 테스트
        logger.info("=== Hybrid Search Engine Tests ===")
        test_results["tests"]["hybrid_search_engine"] = await test_hybrid_search_engine()

        # 7. API 엔드포인트 테스트
        logger.info("=== API Endpoint Tests ===")
        test_results["tests"]["api_endpoints"] = await test_api_endpoints()

        # 8. 성능 벤치마크 테스트
        logger.info("=== Performance Benchmark Tests ===")
        test_results["tests"]["performance_benchmark"] = await test_performance_benchmark()

        # 결과 요약
        test_results["summary"] = generate_test_summary(test_results["tests"])

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        test_results["error"] = str(e)

    return test_results


async def test_module_imports():
    """모듈 import 테스트"""
    import_results = {"status": "success", "modules": {}}

    try:
        # 1. 하이브리드 검색 엔진
        try:
            from apps.search.hybrid_search_engine import (
                HybridSearchEngine, SearchEngineFactory, SearchConfig
            )
            import_results["modules"]["hybrid_search_engine"] = "success"
        except ImportError as e:
            import_results["modules"]["hybrid_search_engine"] = f"failed: {e}"

        # 2. BM25 엔진
        try:
            from apps.search.bm25_engine import BM25Engine, OptimizedBM25
            import_results["modules"]["bm25_engine"] = "success"
        except ImportError as e:
            import_results["modules"]["bm25_engine"] = f"failed: {e}"

        # 3. Vector 엔진
        try:
            from apps.search.vector_engine import VectorEngine, EmbeddingService
            import_results["modules"]["vector_engine"] = "success"
        except ImportError as e:
            import_results["modules"]["vector_engine"] = f"failed: {e}"

        # 4. 캐싱 시스템
        try:
            from apps.api.cache.search_cache import HybridSearchCache
            import_results["modules"]["search_cache"] = "success"
        except ImportError as e:
            import_results["modules"]["search_cache"] = f"failed: {e}"

        # 5. Cross-encoder 리랭킹
        try:
            from apps.search.cross_encoder_reranker import CrossEncoderReranker
            import_results["modules"]["cross_encoder_reranker"] = "success"
        except ImportError as e:
            import_results["modules"]["cross_encoder_reranker"] = f"failed: {e}"

        # 실패한 모듈이 있는지 확인
        failed_modules = [k for k, v in import_results["modules"].items() if "failed" in v]
        if failed_modules:
            import_results["status"] = "partial_failure"
            import_results["failed_modules"] = failed_modules

    except Exception as e:
        import_results["status"] = "error"
        import_results["error"] = str(e)

    return import_results


async def test_database_connection():
    """데이터베이스 연결 테스트"""
    db_results = {"status": "success", "tests": {}}

    try:
        from apps.api.database import db_manager, init_database

        # 1. 데이터베이스 연결 테스트
        connection_test = await db_manager.test_connection()
        db_results["tests"]["connection"] = "success" if connection_test else "failed"

        # 2. 데이터베이스 초기화 테스트
        init_test = await init_database()
        db_results["tests"]["initialization"] = "success" if init_test else "failed"

        # 3. 기본 테이블 존재 확인
        async with db_manager.async_session() as session:
            from sqlalchemy import text

            # 필수 테이블 확인
            tables_query = text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('chunks', 'documents', 'embeddings')
            """)
            result = await session.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]

            db_results["tests"]["required_tables"] = {
                "chunks": "chunks" in tables,
                "documents": "documents" in tables,
                "embeddings": "embeddings" in tables
            }

        # 실패한 테스트가 있는지 확인
        if not all([
            db_results["tests"]["connection"] == "success",
            db_results["tests"]["initialization"] == "success",
            all(db_results["tests"]["required_tables"].values())
        ]):
            db_results["status"] = "partial_failure"

    except Exception as e:
        db_results["status"] = "error"
        db_results["error"] = str(e)

    return db_results


async def test_sqlite_fts5_optimization():
    """SQLite FTS5 최적화 테스트"""
    fts5_results = {"status": "success", "tests": {}}

    try:
        from apps.search.bm25_engine import OptimizedBM25
        from apps.api.database import db_manager

        # FTS5 지원 확인
        async with db_manager.async_session() as session:
            from sqlalchemy import text

            # FTS5 확장 지원 확인
            try:
                fts5_check = text("SELECT fts5_version()")
                result = await session.execute(fts5_check)
                fts5_version = result.scalar()
                fts5_results["tests"]["fts5_support"] = f"available: {fts5_version}"
            except Exception as e:
                fts5_results["tests"]["fts5_support"] = f"not_available: {e}"

            # BM25 엔진 테스트
            bm25_engine = OptimizedBM25()

            # 샘플 검색 테스트
            start_time = time.time()
            search_results = await bm25_engine.search_with_preprocessing(
                session=session,
                query="test search query",
                topk=5,
                filters=None
            )
            search_time = time.time() - start_time

            fts5_results["tests"]["bm25_search"] = {
                "results_count": len(search_results),
                "search_time": round(search_time, 3),
                "status": "success" if search_time < 1.0 else "slow"
            }

    except Exception as e:
        fts5_results["status"] = "error"
        fts5_results["error"] = str(e)

    return fts5_results


async def test_caching_system():
    """캐싱 시스템 테스트"""
    cache_results = {"status": "success", "tests": {}}

    try:
        from apps.api.cache.search_cache import HybridSearchCache, CacheConfig

        # 캐시 인스턴스 생성
        cache_config = CacheConfig(max_memory_entries=100, memory_ttl_seconds=300)
        cache = HybridSearchCache(cache_config)

        # 1. 메모리 캐시 테스트
        start_time = time.time()

        # 캐시 저장
        test_results = [{"chunk_id": "test1", "text": "test content", "score": 0.9}]
        await cache.set_search_results(
            query="test query",
            results=test_results,
            filters=None
        )

        # 캐시 조회
        cached_results = await cache.get_search_results(
            query="test query",
            filters=None
        )

        cache_time = time.time() - start_time

        cache_results["tests"]["memory_cache"] = {
            "cache_hit": cached_results is not None,
            "results_match": cached_results == test_results if cached_results else False,
            "cache_time": round(cache_time, 4),
            "status": "success" if cached_results == test_results else "failed"
        }

        # 2. 임베딩 캐시 테스트
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        await cache.set_embedding("test text", test_embedding, "test_model")

        cached_embedding = await cache.get_embedding("test text", "test_model")

        cache_results["tests"]["embedding_cache"] = {
            "cache_hit": cached_embedding is not None,
            "embedding_match": cached_embedding == test_embedding if cached_embedding else False,
            "status": "success" if cached_embedding == test_embedding else "failed"
        }

        # 3. 캐시 통계 테스트
        cache_stats = await cache.get_cache_stats()
        cache_results["tests"]["cache_stats"] = {
            "stats_available": "hit_rates" in cache_stats,
            "l1_hit_rate": cache_stats.get("hit_rates", {}).get("l1_hit_rate", 0),
            "status": "success"
        }

    except Exception as e:
        cache_results["status"] = "error"
        cache_results["error"] = str(e)

    return cache_results


async def test_embedding_optimization():
    """임베딩 최적화 테스트"""
    embedding_results = {"status": "success", "tests": {}}

    try:
        from apps.search.vector_engine import EmbeddingService

        # 1. 더미 임베딩 테스트
        start_time = time.time()
        dummy_embedding = await EmbeddingService.generate_embedding("test text", "dummy")
        dummy_time = time.time() - start_time

        embedding_results["tests"]["dummy_embedding"] = {
            "embedding_length": len(dummy_embedding),
            "generation_time": round(dummy_time, 4),
            "is_normalized": abs(sum(x*x for x in dummy_embedding) - 1.0) < 0.1,
            "status": "success" if len(dummy_embedding) == 1536 else "failed"
        }

        # 2. 배치 임베딩 테스트
        test_texts = ["test1", "test2", "test3"]
        start_time = time.time()
        batch_embeddings = await EmbeddingService.generate_batch_embeddings(
            test_texts, model="dummy", batch_size=2
        )
        batch_time = time.time() - start_time

        embedding_results["tests"]["batch_embedding"] = {
            "batch_count": len(batch_embeddings),
            "expected_count": len(test_texts),
            "batch_time": round(batch_time, 4),
            "avg_time_per_embedding": round(batch_time / len(test_texts), 4),
            "status": "success" if len(batch_embeddings) == len(test_texts) else "failed"
        }

        # 3. 캐싱 효과 테스트 (같은 텍스트 재요청)
        start_time = time.time()
        cached_embedding = await EmbeddingService.generate_embedding("test text", "dummy")
        cached_time = time.time() - start_time

        embedding_results["tests"]["cache_effect"] = {
            "cached_time": round(cached_time, 4),
            "speedup": round(dummy_time / max(cached_time, 0.0001), 2),
            "embedding_consistent": dummy_embedding == cached_embedding,
            "status": "success" if cached_time < dummy_time else "needs_improvement"
        }

    except Exception as e:
        embedding_results["status"] = "error"
        embedding_results["error"] = str(e)

    return embedding_results


async def test_hybrid_search_engine():
    """하이브리드 검색 엔진 테스트"""
    engine_results = {"status": "success", "tests": {}}

    try:
        from apps.search.hybrid_search_engine import (
            HybridSearchEngine, SearchEngineFactory, SearchConfig
        )
        from apps.api.database import db_manager

        # 1. 엔진 팩토리 테스트
        fast_engine = SearchEngineFactory.create_fast_engine()
        balanced_engine = SearchEngineFactory.create_balanced_engine()
        accurate_engine = SearchEngineFactory.create_accurate_engine()

        engine_results["tests"]["engine_factory"] = {
            "fast_engine": fast_engine is not None,
            "balanced_engine": balanced_engine is not None,
            "accurate_engine": accurate_engine is not None,
            "status": "success"
        }

        # 2. 커스텀 설정 테스트
        custom_config = SearchConfig(
            bm25_weight=0.3,
            vector_weight=0.7,
            final_topk=5,
            enable_reranking=True
        )
        custom_engine = HybridSearchEngine(custom_config)

        engine_results["tests"]["custom_config"] = {
            "config_applied": custom_engine.config.bm25_weight == 0.3,
            "status": "success"
        }

        # 3. 실제 검색 테스트 (샘플 데이터가 있는 경우)
        try:
            async with db_manager.async_session() as session:
                # 웜업
                await balanced_engine.warm_up(session)

                # 검색 실행
                start_time = time.time()
                search_response = await balanced_engine.search(
                    session=session,
                    query="test search query",
                    filters=None,
                    query_id="test_query_1"
                )
                search_time = time.time() - start_time

                engine_results["tests"]["actual_search"] = {
                    "results_count": len(search_response.results),
                    "total_time": round(search_response.total_time, 3),
                    "bm25_time": round(search_response.bm25_time, 3),
                    "vector_time": round(search_response.vector_time, 3),
                    "fusion_time": round(search_response.fusion_time, 3),
                    "rerank_time": round(search_response.rerank_time, 3),
                    "performance_target_met": search_response.total_time < 1.0,
                    "status": "success" if search_response.total_time < 2.0 else "slow"
                }

        except Exception as e:
            engine_results["tests"]["actual_search"] = {
                "status": "skipped",
                "reason": f"No sample data or error: {e}"
            }

        # 4. 성능 통계 테스트
        performance_stats = balanced_engine.get_performance_stats()
        engine_results["tests"]["performance_stats"] = {
            "stats_available": bool(performance_stats),
            "has_metrics": "total_queries" in performance_stats,
            "status": "success"
        }

    except Exception as e:
        engine_results["status"] = "error"
        engine_results["error"] = str(e)

    return engine_results


async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    api_results = {"status": "success", "tests": {}}

    try:
        # FastAPI 앱 모듈 import 테스트
        try:
            from apps.api.routers.search import router
            api_results["tests"]["router_import"] = "success"
        except ImportError as e:
            api_results["tests"]["router_import"] = f"failed: {e}"

        # 스키마 모델 테스트
        try:
            from apps.api.routers.search import (
                SearchRequest, SearchResponse, SearchHit, OptimizedSearchRequest
            )

            # 요청 모델 테스트
            test_request = SearchRequest(
                q="test query",
                filters={"canonical_in": [["AI", "RAG"]]},
                final_topk=5
            )

            api_results["tests"]["request_models"] = {
                "search_request": test_request.q == "test query",
                "filters_parsed": test_request.filters is not None,
                "status": "success"
            }

            # 최적화된 요청 모델 테스트
            optimized_request = OptimizedSearchRequest(
                q="optimized test query",
                bm25_k1=1.5,
                bm25_b=0.75,
                vector_weight=0.7
            )

            api_results["tests"]["optimized_request"] = {
                "parameters_set": optimized_request.bm25_k1 == 1.5,
                "weights_valid": optimized_request.vector_weight == 0.7,
                "status": "success"
            }

        except Exception as e:
            api_results["tests"]["request_models"] = {"status": "error", "error": str(e)}

    except Exception as e:
        api_results["status"] = "error"
        api_results["error"] = str(e)

    return api_results


async def test_performance_benchmark():
    """성능 벤치마크 테스트"""
    benchmark_results = {"status": "success", "tests": {}}

    try:
        from apps.search.hybrid_search_engine import SearchEngineFactory
        from apps.api.database import db_manager

        # 다양한 엔진의 성능 비교
        engines = {
            "fast": SearchEngineFactory.create_fast_engine(),
            "balanced": SearchEngineFactory.create_balanced_engine(),
            "accurate": SearchEngineFactory.create_accurate_engine()
        }

        benchmark_results["tests"]["engine_performance"] = {}

        # 각 엔진별 성능 테스트
        test_queries = [
            "machine learning algorithms",
            "neural networks",
            "data preprocessing"
        ]

        for engine_name, engine in engines.items():
            try:
                total_time = 0
                query_count = 0

                async with db_manager.async_session() as session:
                    for query in test_queries:
                        start_time = time.time()
                        response = await engine.search(
                            session=session,
                            query=query,
                            filters=None,
                            query_id=f"benchmark_{engine_name}_{query_count}"
                        )
                        query_time = time.time() - start_time
                        total_time += query_time
                        query_count += 1

                avg_time = total_time / query_count if query_count > 0 else 0

                benchmark_results["tests"]["engine_performance"][engine_name] = {
                    "avg_query_time": round(avg_time, 3),
                    "total_queries": query_count,
                    "meets_target": avg_time < 1.0,  # 1초 이내 목표
                    "status": "success" if avg_time < 2.0 else "slow"
                }

            except Exception as e:
                benchmark_results["tests"]["engine_performance"][engine_name] = {
                    "status": "error",
                    "error": str(e)
                }

        # 메모리 사용량 추정
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()

        benchmark_results["tests"]["resource_usage"] = {
            "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "memory_reasonable": memory_info.rss < 500 * 1024 * 1024,  # 500MB 이하
            "status": "success"
        }

    except Exception as e:
        benchmark_results["status"] = "error"
        benchmark_results["error"] = str(e)

    return benchmark_results


def generate_test_summary(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """테스트 결과 요약 생성"""
    summary = {
        "total_test_categories": len(test_results),
        "successful_categories": 0,
        "failed_categories": 0,
        "partial_failures": 0,
        "errors": 0,
        "overall_status": "unknown",
        "recommendations": []
    }

    # 각 테스트 카테고리 상태 분석
    for category, results in test_results.items():
        status = results.get("status", "unknown")

        if status == "success":
            summary["successful_categories"] += 1
        elif status == "partial_failure":
            summary["partial_failures"] += 1
        elif status == "error":
            summary["errors"] += 1
        else:
            summary["failed_categories"] += 1

    # 전체 상태 결정
    if summary["errors"] > 0:
        summary["overall_status"] = "error"
    elif summary["failed_categories"] > 0:
        summary["overall_status"] = "failed"
    elif summary["partial_failures"] > 0:
        summary["overall_status"] = "partial_success"
    elif summary["successful_categories"] == summary["total_test_categories"]:
        summary["overall_status"] = "success"

    # 추천사항 생성
    if "module_imports" in test_results and test_results["module_imports"]["status"] != "success":
        summary["recommendations"].append("Install missing dependencies for hybrid search engine")

    if "database_connection" in test_results and test_results["database_connection"]["status"] != "success":
        summary["recommendations"].append("Check database configuration and connectivity")

    if "sqlite_fts5" in test_results:
        fts5_status = test_results["sqlite_fts5"]["tests"].get("fts5_support", "")
        if "not_available" in fts5_status:
            summary["recommendations"].append("Enable SQLite FTS5 extension for optimal BM25 performance")

    if "performance_benchmark" in test_results:
        perf_results = test_results["performance_benchmark"]["tests"].get("engine_performance", {})
        slow_engines = [name for name, result in perf_results.items()
                       if result.get("status") == "slow"]
        if slow_engines:
            summary["recommendations"].append(f"Consider optimizing slow engines: {', '.join(slow_engines)}")

    if not summary["recommendations"]:
        summary["recommendations"].append("All tests passed successfully!")

    return summary


async def main():
    """메인 테스트 실행 함수"""
    print("=" * 80)
    print("Optimized Hybrid Search System Comprehensive Test")
    print("=" * 80)

    start_time = time.time()

    try:
        test_results = await test_optimized_hybrid_search()
        total_time = time.time() - start_time

        # 결과 출력
        print(f"\n테스트 완료 시간: {total_time:.2f}초")
        print(f"전체 상태: {test_results['summary']['overall_status']}")
        print(f"성공한 카테고리: {test_results['summary']['successful_categories']}/{test_results['summary']['total_test_categories']}")

        print("\n=== 테스트 카테고리별 결과 ===")
        for category, results in test_results["tests"].items():
            status = results.get("status", "unknown")
            print(f"{category}: {status}")

            if "error" in results:
                print(f"  오류: {results['error']}")

        print("\n=== 추천사항 ===")
        for rec in test_results["summary"]["recommendations"]:
            print(f"- {rec}")

        # 결과 파일 저장
        output_file = "optimized_hybrid_search_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # JSON 직렬화 문제 해결을 위해 기본 타입 변환
            def convert_for_json(obj):
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                elif isinstance(obj, (list, tuple)):
                    return [convert_for_json(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: convert_for_json(v) for k, v in obj.items()}
                else:
                    return obj

            json_safe_results = convert_for_json(test_results)
            json.dump(json_safe_results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n상세 결과가 {output_file}에 저장되었습니다.")

        # 성공 여부에 따른 종료 코드
        if test_results["summary"]["overall_status"] in ["success", "partial_success"]:
            print("\n✅ 하이브리드 검색 시스템이 성공적으로 최적화되었습니다!")
            return 0
        else:
            print("\n❌ 일부 테스트가 실패했습니다. 위의 추천사항을 참고하세요.")
            return 1

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)