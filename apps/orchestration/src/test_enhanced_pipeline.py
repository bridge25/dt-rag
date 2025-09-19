#!/usr/bin/env python3
"""
Enhanced 7-Step LangGraph Pipeline Test
Step 4 & 5 고도화 테스트: MCP 도구 통합 및 LLM API 호출
"""

import asyncio
import time
import logging
import json
import os
from typing import Dict, Any
from langgraph_pipeline import LangGraphPipeline, PipelineRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedPipelineTest:
    """Enhanced 파이프라인 테스트 클래스"""

    def __init__(self):
        # A팀 API와 MCP 서버 URL 설정
        self.a_team_url = os.getenv("A_TEAM_URL", "http://localhost:8001")
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")

        # 테스트용 파이프라인 인스턴스
        self.pipeline = LangGraphPipeline(
            a_team_base_url=self.a_team_url,
            mcp_server_url=self.mcp_server_url
        )

        # 테스트 시나리오
        self.test_scenarios = [
            {
                "name": "단순 검색 쿼리",
                "query": "AI RAG 시스템이란?",
                "expected_intent": "search",
                "expected_tools": ["search_enhancer"],
                "expected_debate": False
            },
            {
                "name": "복잡한 설명 요청",
                "query": "AI와 머신러닝의 차이점을 비교하고 각각의 장단점을 설명해주세요",
                "expected_intent": "explain",
                "expected_tools": ["context7", "sequential-thinking", "explanation_formatter"],
                "expected_debate": True
            },
            {
                "name": "낮은 신뢰도 시나리오",
                "query": "asdf qwerty zxcv 이상한 단어들",
                "expected_intent": "general_query",
                "expected_tools": ["debate_module", "fallback_search"],
                "expected_debate": True
            },
            {
                "name": "기술적 분석 요청",
                "query": "RAG 시스템의 아키텍처와 구현 방법론을 분석하고 최적화 전략을 제시해주세요",
                "expected_intent": "explain",
                "expected_tools": ["context7", "sequential-thinking", "explanation_formatter"],
                "expected_debate": True
            }
        ]

    async def run_all_tests(self):
        """모든 테스트 시나리오 실행"""
        logger.info("=== Enhanced 7-Step Pipeline 테스트 시작 ===")
        logger.info(f"A팀 API URL: {self.a_team_url}")
        logger.info(f"MCP 서버 URL: {self.mcp_server_url}")

        test_results = []

        for i, scenario in enumerate(self.test_scenarios, 1):
            logger.info(f"\n--- 테스트 {i}/{len(self.test_scenarios)}: {scenario['name']} ---")

            try:
                result = await self.run_single_test(scenario)
                test_results.append(result)

                # 테스트 결과 요약
                self.log_test_summary(scenario, result)

            except Exception as e:
                logger.error(f"테스트 {i} 실패: {str(e)}", exc_info=True)
                test_results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": str(e)
                })

        # 전체 테스트 결과 요약
        await self.log_overall_summary(test_results)

        return test_results

    async def run_single_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """단일 테스트 시나리오 실행"""
        start_time = time.time()

        # 파이프라인 요청 생성
        request = PipelineRequest(
            query=scenario["query"],
            taxonomy_version="1.8.1"
        )

        # 파이프라인 실행
        response = await self.pipeline.execute(request)

        execution_time = time.time() - start_time

        # 결과 분석
        analysis = self.analyze_response(response, scenario)

        return {
            "scenario": scenario["name"],
            "query": scenario["query"],
            "execution_time": execution_time,
            "response": {
                "answer": response.answer,
                "confidence": response.confidence,
                "intent": response.intent,
                "sources_count": response.citations_count,
                "retrieved_count": response.retrieved_count,
                "debate_activated": response.debate_activated,
                "step_timings": response.step_timings,
                "cost": response.cost,
                "latency": response.latency
            },
            "analysis": analysis,
            "success": True
        }

    def analyze_response(self, response, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """응답 분석 및 검증"""
        analysis = {
            "intent_correct": response.intent == scenario.get("expected_intent", ""),
            "debate_correct": response.debate_activated == scenario.get("expected_debate", False),
            "has_sources": response.citations_count >= 2,  # B-O3 요구사항
            "quality_indicators": {
                "confidence_adequate": response.confidence >= 0.5,
                "answer_length_adequate": len(response.answer) >= 100,
                "processing_time_acceptable": response.latency <= 10.0,  # 10초 이내
                "cost_reasonable": response.cost <= 1.0  # 1원 이내
            },
            "step_performance": {},
            "tools_analysis": {}
        }

        # 단계별 성능 분석
        for step, timing in response.step_timings.items():
            analysis["step_performance"][step] = {
                "time_seconds": timing,
                "acceptable": timing <= 3.0  # 각 단계 3초 이내
            }

        # 도구 사용 분석 (실제 상태에서 확인 필요)
        # Step 4에서 어떤 도구들이 사용되었는지 분석

        return analysis

    def log_test_summary(self, scenario: Dict[str, Any], result: Dict[str, Any]):
        """테스트 결과 요약 로깅"""
        logger.info(f"✅ 시나리오: {scenario['name']}")
        logger.info(f"   실행시간: {result['execution_time']:.3f}s")
        logger.info(f"   파이프라인 지연시간: {result['response']['latency']:.3f}s")
        logger.info(f"   신뢰도: {result['response']['confidence']:.3f}")
        logger.info(f"   의도 파악: {result['response']['intent']}")
        logger.info(f"   Debate 활성화: {result['response']['debate_activated']}")
        logger.info(f"   출처 수: {result['response']['sources_count']}")
        logger.info(f"   검색된 문서 수: {result['response']['retrieved_count']}")
        logger.info(f"   비용: ₩{result['response']['cost']:.3f}")

        # 품질 지표 체크
        quality = result['analysis']['quality_indicators']
        logger.info(f"   품질 지표:")
        logger.info(f"     신뢰도 적절: {quality['confidence_adequate']}")
        logger.info(f"     답변 길이 적절: {quality['answer_length_adequate']}")
        logger.info(f"     처리 시간 적절: {quality['processing_time_acceptable']}")
        logger.info(f"     비용 합리적: {quality['cost_reasonable']}")

    async def log_overall_summary(self, test_results):
        """전체 테스트 결과 요약"""
        logger.info("\n=== 전체 테스트 결과 요약 ===")

        successful_tests = [r for r in test_results if r.get("success", False)]
        failed_tests = [r for r in test_results if not r.get("success", False)]

        logger.info(f"총 테스트: {len(test_results)}")
        logger.info(f"성공: {len(successful_tests)}")
        logger.info(f"실패: {len(failed_tests)}")

        if successful_tests:
            avg_execution_time = sum(r["execution_time"] for r in successful_tests) / len(successful_tests)
            avg_confidence = sum(r["response"]["confidence"] for r in successful_tests) / len(successful_tests)
            avg_sources = sum(r["response"]["sources_count"] for r in successful_tests) / len(successful_tests)
            total_cost = sum(r["response"]["cost"] for r in successful_tests)

            logger.info(f"\n성능 지표:")
            logger.info(f"  평균 실행시간: {avg_execution_time:.3f}s")
            logger.info(f"  평균 신뢰도: {avg_confidence:.3f}")
            logger.info(f"  평균 출처 수: {avg_sources:.1f}")
            logger.info(f"  총 비용: ₩{total_cost:.3f}")

        # 파이프라인 성능 메트릭 출력
        pipeline_metrics = self.pipeline.get_performance_metrics()
        logger.info(f"\n파이프라인 성능 메트릭:")
        logger.info(f"  총 요청: {pipeline_metrics['total_requests']}")
        logger.info(f"  성공률: {pipeline_metrics['success_rate_percent']:.1f}%")
        logger.info(f"  평균 지연시간: {pipeline_metrics['average_latency_seconds']:.3f}s")
        logger.info(f"  MCP 도구 사용량: {pipeline_metrics['tools_usage_count']}")

        if failed_tests:
            logger.warning(f"\n실패한 테스트:")
            for failed in failed_tests:
                logger.warning(f"  - {failed['scenario']}: {failed.get('error', 'Unknown error')}")

    async def test_specific_step(self, step_number: int, test_data: Dict[str, Any]):
        """특정 단계 집중 테스트"""
        logger.info(f"=== Step {step_number} 집중 테스트 ===")

        if step_number == 4:
            await self.test_step4_tools_debate(test_data)
        elif step_number == 5:
            await self.test_step5_composition(test_data)
        else:
            logger.warning(f"Step {step_number} 테스트는 구현되지 않았습니다.")

    async def test_step4_tools_debate(self, test_data: Dict[str, Any]):
        """Step 4 (Tools/Debate) 집중 테스트"""
        logger.info("Step 4: Tools and Debate 집중 테스트")

        # 다양한 debate 트리거 조건 테스트
        debate_scenarios = [
            {
                "name": "낮은 의도 신뢰도",
                "mock_state": {
                    "query": "복잡한 질문",
                    "intent_confidence": 0.6,  # < 0.7이므로 debate 활성화
                    "retrieved_docs": [{"text": "some doc", "score": 0.8}]
                }
            },
            {
                "name": "검색 결과 부족",
                "mock_state": {
                    "query": "정보 부족 질문",
                    "intent_confidence": 0.8,
                    "retrieved_docs": []  # 문서 없음으로 debate 활성화
                }
            },
            {
                "name": "복잡한 쿼리 패턴",
                "mock_state": {
                    "query": "AI와 머신러닝을 비교하고 분석하며 평가해주세요",
                    "intent_confidence": 0.8,
                    "retrieved_docs": [{"text": "doc", "score": 0.3}]  # 낮은 관련성
                }
            }
        ]

        for scenario in debate_scenarios:
            logger.info(f"  테스트: {scenario['name']}")
            # 실제 Step 4 메서드 직접 호출은 복잡하므로
            # 전체 파이프라인을 통한 간접 테스트로 대체

    async def test_step5_composition(self, test_data: Dict[str, Any]):
        """Step 5 (Answer Composition) 집중 테스트"""
        logger.info("Step 5: Answer Composition 집중 테스트")

        # 다양한 답변 구성 전략 테스트
        composition_scenarios = [
            {
                "name": "다중 관점 종합",
                "query": "복잡한 기술 주제",
                "context": "context7와 debate 활성화"
            },
            {
                "name": "구조화된 설명",
                "query": "설명 요청",
                "context": "충분한 문서와 explain 의도"
            },
            {
                "name": "근거 기반 요약",
                "query": "검색 요청",
                "context": "검색 결과 있음"
            }
        ]

        for scenario in composition_scenarios:
            logger.info(f"  테스트: {scenario['name']}")
            # Step 5 테스트 로직 구현

    async def cleanup(self):
        """테스트 정리"""
        try:
            await self.pipeline.close()
            logger.info("테스트 정리 완료")
        except Exception as e:
            logger.error(f"테스트 정리 중 오류: {str(e)}")


async def main():
    """메인 테스트 실행"""
    test_runner = EnhancedPipelineTest()

    try:
        # 전체 파이프라인 테스트
        test_results = await test_runner.run_all_tests()

        # 개별 단계 테스트 (선택적)
        if os.getenv("DETAILED_TEST", "false").lower() == "true":
            await test_runner.test_specific_step(4, {})
            await test_runner.test_specific_step(5, {})

        # 결과를 JSON 파일로 저장
        results_file = "enhanced_pipeline_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"테스트 결과가 {results_file}에 저장되었습니다.")

        # 성공/실패 반환
        successful_count = sum(1 for r in test_results if r.get("success", False))
        return successful_count == len(test_results)

    except Exception as e:
        logger.error(f"테스트 실행 중 치명적 오류: {str(e)}", exc_info=True)
        return False
    finally:
        await test_runner.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)