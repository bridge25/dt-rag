"""
B-O3: E2E 테스트 30건 실행 시스템
파이프라인 품질 검증을 위한 종합 테스트
"""

# @CODE:MYPY-001:PHASE2:BATCH5 | SPEC: .moai/specs/SPEC-MYPY-001/spec.md

import asyncio
import logging
import os
import time
import tracemalloc
from typing import Any, Dict, List, Union

import psutil
from apps.orchestration.src.langgraph_pipeline import LangGraphPipeline, PipelineRequest
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineE2ETest:
    """B-O3 파이프라인 E2E 테스트 시스템"""

    def __init__(self) -> None:
        self.pipeline = LangGraphPipeline()
        self.test_cases = self._generate_test_cases()
        self.results: List[Dict[str, Any]] = []

    def _generate_test_cases(self) -> List[Dict[str, Any]]:
        """30건 테스트 케이스 생성"""
        test_cases = []

        # 1-10: 검색 의도 테스트
        search_queries = [
            "RAG 시스템 구축 방법을 검색해주세요",
            "머신러닝 모델 훈련 과정 찾아주세요",
            "블록체인 기술 동향 조회하고 싶어요",
            "AI 보안 위협 관련 자료 검색",
            "데이터베이스 최적화 방법 찾기",
            "자연어 처리 최신 연구 검색",
            "클라우드 아키텍처 패턴 조회",
            "딥러닝 성능 최적화 검색",
            "API 설계 모범 사례 찾기",
            "컨테이너 오케스트레이션 검색",
        ]

        for i, query in enumerate(search_queries):
            test_cases.append(
                {
                    "case_id": f"search_{i+1:02d}",
                    "category": "search",
                    "request": PipelineRequest(
                        query=query,
                        taxonomy_version="1.8.1",
                        options={"expected_intent": "search"},
                    ),
                    "expected": {
                        "intent": "search",
                        "min_sources": 2,
                        "min_confidence": 0.6,
                        "max_latency": 3.0,
                    },
                }
            )

        # 11-20: 설명 의도 테스트
        explain_queries = [
            "RAG 시스템이 무엇인지 설명해주세요",
            "머신러닝과 딥러닝의 차이점 알려줘",
            "블록체인의 작동 원리 설명",
            "트랜스포머 모델 구조 설명해줘",
            "마이크로서비스 아키텍처란?",
            "BERT 모델의 특징 설명",
            "도커와 쿠버네티스 차이점",
            "GraphQL vs REST API 비교",
            "NoSQL 데이터베이스 장단점",
            "CI/CD 파이프라인이란 무엇인가",
        ]

        for i, query in enumerate(explain_queries):
            test_cases.append(
                {
                    "case_id": f"explain_{i+1:02d}",
                    "category": "explain",
                    "request": PipelineRequest(
                        query=query,
                        taxonomy_version="1.8.1",
                        options={"expected_intent": "explain"},
                    ),
                    "expected": {
                        "intent": "explain",
                        "min_sources": 1,
                        "min_confidence": 0.7,
                        "max_latency": 4.0,
                    },
                }
            )

        # 21-25: 분류 의도 테스트
        classify_queries = [
            "이 텍스트를 AI 카테고리로 분류해주세요",
            "머신러닝 관련 문서를 적절한 카테고리에 분류",
            "블록체인 기술 문서의 카테고리 분류",
            "자연어 처리 논문 카테고리 분류",
            "데이터베이스 관련 글의 분류",
        ]

        for i, query in enumerate(classify_queries):
            test_cases.append(
                {
                    "case_id": f"classify_{i+1:02d}",
                    "category": "classify",
                    "request": PipelineRequest(
                        query=query,
                        taxonomy_version="1.8.1",
                        chunk_id=f"test_chunk_{i+1}",
                        options={"expected_intent": "classify"},
                    ),
                    "expected": {
                        "intent": "classify",
                        "min_sources": 0,
                        "min_confidence": 0.5,
                        "max_latency": 2.0,
                    },
                }
            )

        # 26-30: 에지 케이스 테스트
        edge_cases = [
            {
                "query": "빈 쿼리 테스트용",
                "expected_error": False,
                "description": "빈 쿼리 대체",
            },
            {
                "query": "a" * 1000,
                "expected_error": False,
                "description": "매우 긴 쿼리",
            },
            {"query": "!@#$%^&*()", "expected_error": False, "description": "특수문자"},
            {
                "query": "한글 English 日本語 混合",
                "expected_error": False,
                "description": "다국어",
            },
            {
                "query": "매우 모호한 질문입니다",
                "expected_error": False,
                "description": "모호한 질문",
            },
        ]

        for i, case in enumerate(edge_cases):
            test_cases.append(
                {
                    "case_id": f"edge_{i+1:02d}",
                    "category": "edge_case",
                    "request": PipelineRequest(
                        query=case["query"], taxonomy_version="1.8.1"
                    ),
                    "expected": {
                        "intent": "general_query",
                        "min_sources": 0,
                        "min_confidence": 0.0,
                        "max_latency": 5.0,
                        "expected_error": case.get("expected_error", False),
                    },
                }
            )

        logger.info(f"테스트 케이스 {len(test_cases)}건 생성 완료")
        return test_cases

    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """단일 테스트 케이스 실행"""
        case_id = test_case["case_id"]
        request = test_case["request"]
        expected = test_case["expected"]

        logger.info(f"테스트 실행: {case_id}")

        # 메모리 추적 시작
        tracemalloc.start()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()
        result = {
            "case_id": case_id,
            "category": test_case["category"],
            "query": request.query,
            "success": False,
            "error": None,
            "latency": 0.0,
            "memory_used": 0.0,
            "validation_results": {},
        }

        try:
            # 파이프라인 실행
            response = await self.pipeline.execute(request)

            # 실행 시간 측정
            result["latency"] = time.time() - start_time

            # 메모리 사용량 측정
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            result["memory_used"] = memory_after - memory_before

            # 응답 검증
            validation_results = self._validate_response(response, expected)
            result["validation_results"] = validation_results
            result["success"] = validation_results["all_passed"]

            # 응답 데이터 저장
            result["response"] = {
                "intent": response.intent,
                "confidence": response.confidence,
                "sources_count": len(response.sources),
                "citations_count": response.citations_count,  # type: ignore[attr-defined]
                "cost": response.cost,
                "step_timings": response.step_timings,
            }

        except Exception as e:
            result["error"] = str(e)
            result["latency"] = time.time() - start_time

            # 예상된 에러인지 확인
            if expected.get("expected_error", False):
                result["success"] = True
                result["validation_results"] = {
                    "expected_error": True,
                    "all_passed": True,
                }
            else:
                logger.error(f"테스트 {case_id} 실행 실패: {e}")

        finally:
            # 메모리 추적 정리
            tracemalloc.stop()

        logger.info(
            f"테스트 {case_id} 완료: success={result['success']}, latency={result['latency']:.3f}s"
        )
        return result

    def _validate_response(
        self, response: Any, expected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """응답 검증"""
        validation = {}

        # 의도 검증
        validation["intent_correct"] = response.intent == expected.get(
            "intent", response.intent
        )

        # 신뢰도 검증
        min_confidence = expected.get("min_confidence", 0.0)
        validation["confidence_sufficient"] = response.confidence >= min_confidence

        # 출처 개수 검증
        min_sources = expected.get("min_sources", 0)
        validation["sources_sufficient"] = len(response.sources) >= min_sources

        # 응답 시간 검증
        max_latency = expected.get("max_latency", 10.0)
        validation["latency_acceptable"] = response.latency <= max_latency

        # 비용 검증 (₩10 미만)
        validation["cost_reasonable"] = response.cost < 10.0

        # 전체 통과 여부
        validation["all_passed"] = all(
            [
                validation["intent_correct"],
                validation["confidence_sufficient"],
                validation["sources_sufficient"],
                validation["latency_acceptable"],
                validation["cost_reasonable"],
            ]
        )

        return validation

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 케이스 실행"""
        logger.info("=== B-O3 E2E 테스트 30건 시작 ===")
        start_time = time.time()

        # 병렬 실행 (최대 5개 동시)
        semaphore = asyncio.Semaphore(5)

        async def run_with_semaphore(test_case: Any) -> Dict[str, Any]:
            async with semaphore:
                return await self.run_single_test(test_case)

        # 모든 테스트 실행
        tasks = [run_with_semaphore(case) for case in self.test_cases]
        raw_results: List[Union[Dict[str, Any], BaseException]] = list(
            await asyncio.gather(*tasks, return_exceptions=True)
        )

        # 예외 처리
        processed_results: List[Dict[str, Any]] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, BaseException):
                processed_results.append(
                    {
                        "case_id": self.test_cases[i]["case_id"],
                        "success": False,
                        "error": str(result),
                        "latency": 0.0,
                        "validation_results": {"all_passed": False},
                    }
                )
            else:
                processed_results.append(result)

        self.results = processed_results

        # 결과 분석
        total_time = time.time() - start_time
        summary = self._analyze_results(total_time)

        logger.info("=== B-O3 E2E 테스트 완료 ===")
        logger.info(f"총 실행 시간: {total_time:.1f}초")
        logger.info(f"성공률: {summary['success_rate']:.1%}")
        logger.info(f"평균 지연시간: {summary['avg_latency']:.3f}초")

        return summary

    def _analyze_results(self, total_time: float) -> Dict[str, Any]:
        """결과 분석"""
        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)

        # 지연시간 통계
        latencies = [r["latency"] for r in self.results if "latency" in r]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0

        # 메모리 사용량 통계
        memory_usages = [r.get("memory_used", 0.0) for r in self.results]
        avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 0.0
        max_memory = max(memory_usages) if memory_usages else 0.0

        # 카테고리별 성공률
        category_stats: Dict[str, Dict[str, Any]] = {}
        for result in self.results:
            category = result.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "success": 0}
            category_stats[category]["total"] += 1
            if result["success"]:
                category_stats[category]["success"] += 1

        for category in category_stats:
            stats = category_stats[category]
            stats["success_rate"] = stats["success"] / stats["total"]

        return {
            "total_tests": total_count,
            "success_count": success_count,
            "failure_count": total_count - success_count,
            "success_rate": success_count / total_count,
            "total_time": total_time,
            "avg_latency": avg_latency,
            "max_latency": max_latency,
            "avg_memory_mb": avg_memory,
            "max_memory_mb": max_memory,
            "category_stats": category_stats,
            "detailed_results": self.results,
        }


# 스크립트 실행용
async def main() -> None:
    """E2E 테스트 메인 실행"""
    test_runner = PipelineE2ETest()
    summary = await test_runner.run_all_tests()

    # 결과 출력
    print("\n" + "=" * 50)
    print("B-O3 E2E 테스트 결과 요약")
    print("=" * 50)
    print(f"총 테스트: {summary['total_tests']}건")
    print(f"성공: {summary['success_count']}건")
    print(f"실패: {summary['failure_count']}건")
    print(f"성공률: {summary['success_rate']:.1%}")
    print(f"평균 지연시간: {summary['avg_latency']:.3f}초")
    print(f"최대 지연시간: {summary['max_latency']:.3f}초")
    print(f"평균 메모리 사용: {summary['avg_memory_mb']:.1f}MB")
    print(f"최대 메모리 사용: {summary['max_memory_mb']:.1f}MB")

    print("\n카테고리별 성공률:")
    for category, stats in summary["category_stats"].items():
        print(
            f"  {category}: {stats['success_rate']:.1%} ({stats['success']}/{stats['total']})"
        )

    # 실패한 테스트 상세 정보
    failures = [r for r in summary["detailed_results"] if not r["success"]]
    if failures:
        print(f"\n실패한 테스트 {len(failures)}건:")
        for failure in failures[:5]:  # 최대 5개만 출력
            print(f"  {failure['case_id']}: {failure.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
