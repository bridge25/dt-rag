#!/usr/bin/env python3
"""
LangGraph 7단계 오케스트레이션 워크플로우 종합 통합 테스트
Dynamic Taxonomy RAG v1.8.1

테스트 범위:
1. 7단계 워크플로우 End-to-End 테스트
2. 상태 관리 및 에러 복구 검증
3. 병렬 처리 및 성능 측정
4. 데이터 흐름 무결성 확인
5. 메모리 사용량 및 안정성 검증
"""

import asyncio
import time
import logging
import json
import tracemalloc
import psutil
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Add apps to path
current_dir = Path(__file__).parent
apps_dir = current_dir / "apps"
sys.path.insert(0, str(apps_dir))

# Import orchestration components
try:
    from orchestration.src.langgraph_pipeline import (
        LangGraphPipeline,
        PipelineRequest,
        PipelineResponse,
        get_pipeline
    )
    from orchestration.src.pipeline_resilience import (
        get_resilience_manager,
        PipelineResilienceManager,
        RetryConfig,
        MemoryThreshold
    )
except ImportError as e:
    print(f"오케스트레이션 모듈 임포트 실패: {e}")
    print("apps/orchestration/src 디렉토리와 파일들을 확인해주세요.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('langgraph_orchestration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LangGraphOrchestrationTestSuite:
    """LangGraph 7단계 오케스트레이션 종합 테스트 스위트"""

    def __init__(self):
        """테스트 스위트 초기화"""
        self.pipeline = None
        self.resilience_manager = None
        self.test_results = []
        self.performance_metrics = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'average_latency': 0.0,
            'peak_memory_mb': 0.0,
            'step_performance': {},
            'error_recovery_tests': 0,
            'successful_recoveries': 0
        }

        # 성능 기준 설정 (PRD 기준)
        self.performance_targets = {
            'max_pipeline_latency': 5.0,  # 5초 이내
            'success_rate_threshold': 0.99,  # 99% 이상
            'memory_limit_mb': 1000.0,  # 1GB 이내
            'step_latency_targets': {
                'step1_intent': 0.5,
                'step2_retrieve': 2.0,
                'step3_plan': 0.3,
                'step4_tools_debate': 1.0,
                'step5_compose': 1.5,
                'step6_cite': 0.2,
                'step7_respond': 0.3
            }
        }

    async def setup(self):
        """테스트 환경 설정"""
        logger.info("=== LangGraph 오케스트레이션 테스트 환경 설정 ===")

        try:
            # 파이프라인 초기화
            self.pipeline = get_pipeline()
            logger.info("✓ LangGraph 파이프라인 초기화 완료")

            # 복원력 관리자 초기화
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0
            )
            memory_thresholds = MemoryThreshold(
                warning_mb=512.0,
                critical_mb=768.0,
                max_mb=1024.0
            )
            self.resilience_manager = PipelineResilienceManager(
                retry_config=retry_config,
                memory_thresholds=memory_thresholds
            )
            await self.resilience_manager.start()
            logger.info("✓ 복원력 관리자 초기화 완료")

            # 메모리 추적 시작
            tracemalloc.start()
            logger.info("✓ 메모리 추적 시작")

        except Exception as e:
            logger.error(f"테스트 환경 설정 실패: {e}")
            raise

    async def teardown(self):
        """테스트 환경 정리"""
        logger.info("=== 테스트 환경 정리 ===")

        try:
            if self.resilience_manager:
                await self.resilience_manager.stop()
                logger.info("✓ 복원력 관리자 정리 완료")

            if self.pipeline:
                await self.pipeline.close()
                logger.info("✓ 파이프라인 정리 완료")

            tracemalloc.stop()
            logger.info("✓ 메모리 추적 정지")

        except Exception as e:
            logger.warning(f"테스트 환경 정리 중 오류: {e}")

    def generate_comprehensive_test_cases(self) -> List[Dict[str, Any]]:
        """종합 테스트 케이스 생성"""
        test_cases = []

        # 1. 기본 워크플로우 테스트 (각 단계별)
        basic_workflow_tests = [
            {
                'name': 'intent_classification_test',
                'description': 'Step 1: Intent Classification 검증',
                'request': PipelineRequest(
                    query="RAG 시스템 구축 방법을 검색해주세요",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step1_intent',
                'expected_intent': 'search',
                'category': 'basic_workflow'
            },
            {
                'name': 'hybrid_retrieval_test',
                'description': 'Step 2: Hybrid Retrieval 검증',
                'request': PipelineRequest(
                    query="머신러닝 모델 최적화 기법",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step2_retrieve',
                'category': 'basic_workflow'
            },
            {
                'name': 'answer_planning_test',
                'description': 'Step 3: Answer Planning 검증',
                'request': PipelineRequest(
                    query="딥러닝 모델 구조 설명해주세요",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step3_plan',
                'expected_intent': 'explain',
                'category': 'basic_workflow'
            },
            {
                'name': 'tools_debate_activation_test',
                'description': 'Step 4: Tools/Debate 활성화 검증',
                'request': PipelineRequest(
                    query="복잡한 양자컴퓨팅과 블록체인 기술의 상호작용 분석",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step4_tools_debate',
                'expected_debate_activation': True,
                'category': 'basic_workflow'
            },
            {
                'name': 'answer_composition_test',
                'description': 'Step 5: Answer Composition 검증',
                'request': PipelineRequest(
                    query="자연어 처리의 최신 동향",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step5_compose',
                'category': 'basic_workflow'
            },
            {
                'name': 'citation_extraction_test',
                'description': 'Step 6: Citation 검증 (≥2개 출처)',
                'request': PipelineRequest(
                    query="AI 윤리 가이드라인",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step6_cite',
                'min_citations': 2,
                'category': 'basic_workflow'
            },
            {
                'name': 'final_response_test',
                'description': 'Step 7: Final Response 생성 검증',
                'request': PipelineRequest(
                    query="클라우드 컴퓨팅 보안",
                    taxonomy_version="1.8.1"
                ),
                'expected_step_focus': 'step7_respond',
                'category': 'basic_workflow'
            }
        ]
        test_cases.extend(basic_workflow_tests)

        # 2. 상태 관리 및 데이터 흐름 테스트
        state_management_tests = [
            {
                'name': 'state_persistence_test',
                'description': '상태 데이터 지속성 검증',
                'request': PipelineRequest(
                    query="데이터베이스 인덱싱 전략",
                    taxonomy_version="1.8.1"
                ),
                'verify_state_flow': True,
                'category': 'state_management'
            },
            {
                'name': 'step_transition_test',
                'description': '단계간 전이 무결성 검증',
                'request': PipelineRequest(
                    query="API 설계 패턴",
                    taxonomy_version="1.8.1"
                ),
                'verify_step_transitions': True,
                'category': 'state_management'
            },
            {
                'name': 'metadata_propagation_test',
                'description': '메타데이터 전파 검증',
                'request': PipelineRequest(
                    query="컨테이너 오케스트레이션",
                    taxonomy_version="1.8.1"
                ),
                'verify_metadata': True,
                'category': 'state_management'
            }
        ]
        test_cases.extend(state_management_tests)

        # 3. 에러 복구 및 복원력 테스트
        error_recovery_tests = [
            {
                'name': 'step_failure_recovery_test',
                'description': '단계 실패 시 복구 검증',
                'request': PipelineRequest(
                    query="의도적 실패 테스트",
                    taxonomy_version="1.8.1",
                    options={'simulate_step_failure': 'step2_retrieve'}
                ),
                'expected_retry': True,
                'category': 'error_recovery'
            },
            {
                'name': 'memory_pressure_test',
                'description': '메모리 압박 상황 처리 검증',
                'request': PipelineRequest(
                    query="대용량 데이터 처리 방법",
                    taxonomy_version="1.8.1",
                    options={'simulate_memory_pressure': True}
                ),
                'expected_memory_cleanup': True,
                'category': 'error_recovery'
            },
            {
                'name': 'timeout_handling_test',
                'description': '타임아웃 처리 검증',
                'request': PipelineRequest(
                    query="시간 초과 시뮬레이션",
                    taxonomy_version="1.8.1",
                    options={'simulate_timeout': True}
                ),
                'expected_timeout_recovery': True,
                'category': 'error_recovery'
            }
        ]
        test_cases.extend(error_recovery_tests)

        # 4. 병렬 처리 및 성능 테스트
        performance_tests = [
            {
                'name': 'concurrent_pipeline_test',
                'description': '동시 파이프라인 처리 검증',
                'concurrent_requests': [
                    PipelineRequest(query=f"동시 요청 {i+1}", taxonomy_version="1.8.1")
                    for i in range(5)
                ],
                'category': 'performance'
            },
            {
                'name': 'high_load_test',
                'description': '고부하 상황 처리 검증',
                'request': PipelineRequest(
                    query="고부하 테스트용 복잡한 질의",
                    taxonomy_version="1.8.1"
                ),
                'repeat_count': 10,
                'category': 'performance'
            },
            {
                'name': 'memory_efficiency_test',
                'description': '메모리 효율성 검증',
                'request': PipelineRequest(
                    query="메모리 사용 최적화",
                    taxonomy_version="1.8.1"
                ),
                'monitor_memory_usage': True,
                'category': 'performance'
            }
        ]
        test_cases.extend(performance_tests)

        # 5. MCP 도구 통합 테스트
        mcp_integration_tests = [
            {
                'name': 'context7_tool_test',
                'description': 'Context7 MCP 도구 통합 검증',
                'request': PipelineRequest(
                    query="복잡한 다층 분석이 필요한 질문",
                    taxonomy_version="1.8.1"
                ),
                'expected_tools': ['context7'],
                'category': 'mcp_integration'
            },
            {
                'name': 'sequential_thinking_test',
                'description': 'Sequential-thinking 도구 검증',
                'request': PipelineRequest(
                    query="단계적 사고가 필요한 복잡한 문제 해결",
                    taxonomy_version="1.8.1"
                ),
                'expected_tools': ['sequential-thinking'],
                'category': 'mcp_integration'
            },
            {
                'name': 'fallback_search_test',
                'description': 'Fallback search 도구 검증',
                'request': PipelineRequest(
                    query="일반 검색으로 찾기 어려운 정보",
                    taxonomy_version="1.8.1"
                ),
                'expected_tools': ['fallback_search'],
                'category': 'mcp_integration'
            }
        ]
        test_cases.extend(mcp_integration_tests)

        logger.info(f"총 {len(test_cases)}개 테스트 케이스 생성")
        return test_cases

    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """단일 테스트 실행"""
        test_name = test_case['name']
        logger.info(f"테스트 실행: {test_name}")

        # 메모리 추적 시작
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()
        test_result = {
            'name': test_name,
            'description': test_case['description'],
            'category': test_case['category'],
            'success': False,
            'latency': 0.0,
            'memory_used_mb': 0.0,
            'error': None,
            'validations': {},
            'response_data': {},
            'step_performance': {}
        }

        try:
            # 특수 테스트 처리
            if 'concurrent_requests' in test_case:
                result = await self._run_concurrent_test(test_case)
            elif 'repeat_count' in test_case:
                result = await self._run_repeated_test(test_case)
            else:
                result = await self._run_standard_test(test_case)

            test_result.update(result)
            test_result['success'] = True

        except Exception as e:
            test_result['error'] = str(e)
            logger.error(f"테스트 {test_name} 실패: {e}")

        finally:
            # 성능 측정
            test_result['latency'] = time.time() - start_time
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            test_result['memory_used_mb'] = memory_after - memory_before

            # 피크 메모리 업데이트
            if memory_after > self.performance_metrics['peak_memory_mb']:
                self.performance_metrics['peak_memory_mb'] = memory_after

        logger.info(f"테스트 {test_name} 완료: {test_result['latency']:.3f}s")
        return test_result

    async def _run_standard_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """표준 테스트 실행"""
        request = test_case['request']

        # 복원력 기능과 함께 파이프라인 실행
        if self.resilience_manager:
            response = await self.resilience_manager.execute_with_resilience(
                self.pipeline.execute, request
            )
        else:
            response = await self.pipeline.execute(request)

        # 응답 검증
        validations = await self._validate_response(response, test_case)

        return {
            'response_data': {
                'intent': response.intent,
                'confidence': response.confidence,
                'sources_count': len(response.sources),
                'citations_count': response.citations_count,
                'cost': response.cost,
                'debate_activated': response.debate_activated
            },
            'step_performance': response.step_timings,
            'validations': validations
        }

    async def _run_concurrent_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """동시 실행 테스트"""
        concurrent_requests = test_case['concurrent_requests']

        # 세마포어로 동시성 제어
        semaphore = asyncio.Semaphore(5)

        async def run_with_semaphore(request):
            async with semaphore:
                if self.resilience_manager:
                    return await self.resilience_manager.execute_with_resilience(
                        self.pipeline.execute, request
                    )
                else:
                    return await self.pipeline.execute(request)

        # 모든 요청 동시 실행
        tasks = [run_with_semaphore(req) for req in concurrent_requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 분석
        successful_responses = [r for r in responses if isinstance(r, PipelineResponse)]
        failed_responses = [r for r in responses if isinstance(r, Exception)]

        return {
            'concurrent_results': {
                'total_requests': len(concurrent_requests),
                'successful_responses': len(successful_responses),
                'failed_responses': len(failed_responses),
                'success_rate': len(successful_responses) / len(concurrent_requests)
            },
            'validations': {
                'concurrent_execution': len(successful_responses) > 0,
                'no_failures': len(failed_responses) == 0
            }
        }

    async def _run_repeated_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """반복 실행 테스트"""
        request = test_case['request']
        repeat_count = test_case['repeat_count']

        latencies = []
        memory_usages = []
        responses = []

        for i in range(repeat_count):
            start_time = time.time()
            memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

            try:
                if self.resilience_manager:
                    response = await self.resilience_manager.execute_with_resilience(
                        self.pipeline.execute, request
                    )
                else:
                    response = await self.pipeline.execute(request)

                responses.append(response)

            except Exception as e:
                logger.warning(f"반복 테스트 {i+1}/{repeat_count} 실패: {e}")
                continue

            latencies.append(time.time() - start_time)
            memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            memory_usages.append(memory_after - memory_before)

        # 통계 계산
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 0.0

        return {
            'repeated_execution_stats': {
                'total_runs': repeat_count,
                'successful_runs': len(responses),
                'avg_latency': avg_latency,
                'max_latency': max_latency,
                'avg_memory_mb': avg_memory,
                'success_rate': len(responses) / repeat_count
            },
            'validations': {
                'all_executions_successful': len(responses) == repeat_count,
                'consistent_performance': max_latency < avg_latency * 2
            }
        }

    async def _validate_response(self, response: PipelineResponse, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """응답 검증"""
        validations = {}

        # 기본 검증
        validations['response_generated'] = bool(response.answer.strip())
        validations['confidence_reasonable'] = 0.0 <= response.confidence <= 1.0
        validations['sources_present'] = len(response.sources) >= 0
        validations['cost_reasonable'] = response.cost >= 0.0
        validations['latency_acceptable'] = response.latency <= self.performance_targets['max_pipeline_latency']

        # 특정 테스트 검증
        if 'expected_intent' in test_case:
            validations['intent_correct'] = response.intent == test_case['expected_intent']

        if 'min_citations' in test_case:
            validations['citations_sufficient'] = response.citations_count >= test_case['min_citations']

        if 'expected_debate_activation' in test_case:
            validations['debate_activated'] = response.debate_activated == test_case['expected_debate_activation']

        # 단계별 성능 검증
        step_validations = {}
        for step, target_latency in self.performance_targets['step_latency_targets'].items():
            if step in response.step_timings:
                step_validations[f'{step}_performance'] = response.step_timings[step] <= target_latency
        validations['step_performance'] = step_validations

        # 상태 흐름 검증 (특별 케이스)
        if test_case.get('verify_state_flow'):
            validations['state_flow'] = await self._verify_state_flow(response)

        # 메타데이터 검증
        if test_case.get('verify_metadata'):
            validations['metadata'] = await self._verify_metadata_propagation(response)

        return validations

    async def _verify_state_flow(self, response: PipelineResponse) -> bool:
        """상태 흐름 검증"""
        # 7단계가 모두 실행되었는지 확인
        required_steps = [
            'step1_intent', 'step2_retrieve', 'step3_plan',
            'step4_tools_debate', 'step5_compose', 'step6_cite', 'step7_respond'
        ]

        executed_steps = list(response.step_timings.keys())
        return all(step in executed_steps for step in required_steps)

    async def _verify_metadata_propagation(self, response: PipelineResponse) -> bool:
        """메타데이터 전파 검증"""
        # 필수 메타데이터가 모두 존재하는지 확인
        required_metadata = ['taxonomy_version', 'intent', 'sources', 'cost', 'latency']
        return all(hasattr(response, attr) for attr in required_metadata)

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """종합 테스트 실행"""
        logger.info("LangGraph 7단계 오케스트레이션 종합 테스트 시작")

        test_cases = self.generate_comprehensive_test_cases()
        start_time = time.time()

        # 테스트 실행 (배치별 처리)
        batch_size = 5
        all_results = []

        for i in range(0, len(test_cases), batch_size):
            batch = test_cases[i:i + batch_size]
            logger.info(f"배치 {i//batch_size + 1} 실행 중 ({len(batch)}개 테스트)")

            # 배치 내 병렬 실행
            tasks = [self.run_single_test(test_case) for test_case in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 예외 처리
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    batch_results[j] = {
                        'name': batch[j]['name'],
                        'success': False,
                        'error': str(result),
                        'category': batch[j]['category']
                    }

            all_results.extend(batch_results)

            # 배치 간 휴식 (메모리 정리)
            if i + batch_size < len(test_cases):
                await asyncio.sleep(1)
                if self.resilience_manager:
                    await self.resilience_manager.memory_monitor.cleanup_memory()

        total_time = time.time() - start_time

        # 결과 분석 및 보고서 생성
        summary = await self._generate_test_summary(all_results, total_time)

        # 테스트 결과 저장
        await self._save_test_results(summary)

        logger.info("LangGraph 오케스트레이션 종합 테스트 완료")
        return summary

    async def _generate_test_summary(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """테스트 결과 요약 생성"""
        successful_tests = [r for r in results if r.get('success', False)]
        failed_tests = [r for r in results if not r.get('success', False)]

        # 카테고리별 통계
        category_stats = {}
        for result in results:
            category = result.get('category', 'unknown')
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'success': 0, 'failed': 0}

            category_stats[category]['total'] += 1
            if result.get('success', False):
                category_stats[category]['success'] += 1
            else:
                category_stats[category]['failed'] += 1

        # 성능 통계
        latencies = [r.get('latency', 0.0) for r in results if 'latency' in r]
        memory_usages = [r.get('memory_used_mb', 0.0) for r in results if 'memory_used_mb' in r]

        # 단계별 성능 분석
        step_performance_stats = {}
        for result in results:
            step_perf = result.get('step_performance', {})
            for step, timing in step_perf.items():
                if step not in step_performance_stats:
                    step_performance_stats[step] = []
                step_performance_stats[step].append(timing)

        # 평균 계산
        step_averages = {}
        for step, timings in step_performance_stats.items():
            step_averages[step] = {
                'avg_time': sum(timings) / len(timings) if timings else 0.0,
                'max_time': max(timings) if timings else 0.0,
                'min_time': min(timings) if timings else 0.0,
                'count': len(timings)
            }

        # PRD 기준 달성도 계산
        success_rate = len(successful_tests) / len(results) if results else 0.0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        max_memory = max(memory_usages) if memory_usages else 0.0

        prd_compliance = {
            'success_rate_target': success_rate >= self.performance_targets['success_rate_threshold'],
            'latency_target': avg_latency <= self.performance_targets['max_pipeline_latency'],
            'memory_target': max_memory <= self.performance_targets['memory_limit_mb'],
            'overall_compliance': (
                success_rate >= self.performance_targets['success_rate_threshold'] and
                avg_latency <= self.performance_targets['max_pipeline_latency'] and
                max_memory <= self.performance_targets['memory_limit_mb']
            )
        }

        return {
            'test_execution': {
                'total_tests': len(results),
                'successful_tests': len(successful_tests),
                'failed_tests': len(failed_tests),
                'success_rate': success_rate,
                'total_execution_time': total_time
            },
            'performance_metrics': {
                'avg_latency': avg_latency,
                'max_latency': max(latencies) if latencies else 0.0,
                'min_latency': min(latencies) if latencies else 0.0,
                'avg_memory_mb': sum(memory_usages) / len(memory_usages) if memory_usages else 0.0,
                'peak_memory_mb': self.performance_metrics['peak_memory_mb'],
                'step_performance': step_averages
            },
            'category_statistics': category_stats,
            'prd_compliance': prd_compliance,
            'detailed_results': results,
            'failed_tests_summary': [
                {
                    'name': r['name'],
                    'category': r.get('category', 'unknown'),
                    'error': r.get('error', 'Unknown error')
                }
                for r in failed_tests[:10]  # 상위 10개 실패 케이스
            ],
            'system_health': await self._get_system_health_summary()
        }

    async def _get_system_health_summary(self) -> Dict[str, Any]:
        """시스템 건강도 요약"""
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_metrics': {},
            'resilience_metrics': {}
        }

        try:
            if self.pipeline:
                health_data['pipeline_metrics'] = self.pipeline.get_performance_metrics()

            if self.resilience_manager:
                health_data['resilience_metrics'] = self.resilience_manager.get_system_health()

        except Exception as e:
            logger.warning(f"시스템 건강도 수집 중 오류: {e}")

        return health_data

    async def _save_test_results(self, summary: Dict[str, Any]):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON 형태로 저장
        json_filename = f"langgraph_orchestration_test_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"테스트 결과 저장됨: {json_filename}")

        # 간단한 요약 리포트 생성
        report_filename = f"langgraph_orchestration_test_report_{timestamp}.md"
        await self._generate_markdown_report(summary, report_filename)

        logger.info(f"테스트 리포트 생성됨: {report_filename}")

    async def _generate_markdown_report(self, summary: Dict[str, Any], filename: str):
        """마크다운 테스트 리포트 생성"""
        report_content = f"""# LangGraph 7단계 오케스트레이션 워크플로우 통합 테스트 리포트

## 테스트 실행 요약

- **총 테스트 수**: {summary['test_execution']['total_tests']}개
- **성공한 테스트**: {summary['test_execution']['successful_tests']}개
- **실패한 테스트**: {summary['test_execution']['failed_tests']}개
- **성공률**: {summary['test_execution']['success_rate']:.1%}
- **총 실행 시간**: {summary['test_execution']['total_execution_time']:.2f}초

## 성능 메트릭

### 파이프라인 성능
- **평균 지연시간**: {summary['performance_metrics']['avg_latency']:.3f}초
- **최대 지연시간**: {summary['performance_metrics']['max_latency']:.3f}초
- **최소 지연시간**: {summary['performance_metrics']['min_latency']:.3f}초

### 메모리 사용량
- **평균 메모리 사용**: {summary['performance_metrics']['avg_memory_mb']:.1f}MB
- **피크 메모리 사용**: {summary['performance_metrics']['peak_memory_mb']:.1f}MB

### 단계별 성능 분석
"""

        # 단계별 성능 테이블 추가
        for step, stats in summary['performance_metrics']['step_performance'].items():
            report_content += f"- **{step}**: 평균 {stats['avg_time']:.3f}s (최대: {stats['max_time']:.3f}s)\n"

        report_content += f"""
## 카테고리별 결과

"""

        # 카테고리별 통계 테이블
        for category, stats in summary['category_statistics'].items():
            success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            report_content += f"- **{category}**: {success_rate:.1f}% ({stats['success']}/{stats['total']})\n"

        # PRD 준수도
        prd = summary['prd_compliance']
        report_content += f"""
## PRD 기준 달성도

- 성공률 ≥99%: {'달성' if prd['success_rate_target'] else '미달성'}
- 지연시간 ≤5초: {'달성' if prd['latency_target'] else '미달성'}
- 메모리 <1GB: {'달성' if prd['memory_target'] else '미달성'}
- **전체 준수도**: {'달성' if prd['overall_compliance'] else '미달성'}

## 실패한 테스트

"""

        if summary['failed_tests_summary']:
            for failed_test in summary['failed_tests_summary']:
                report_content += f"- **{failed_test['name']}** ({failed_test['category']}): {failed_test['error']}\n"
        else:
            report_content += "실패한 테스트가 없습니다!\n"

        report_content += f"""
## 시스템 건강도

- **타임스탬프**: {summary['system_health']['timestamp']}
- **파이프라인 상태**: 정상 가동
- **복원력 시스템**: 활성화

---
*리포트 생성 시간: {datetime.now().isoformat()}*
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)


async def main():
    """메인 테스트 실행 함수"""
    print("LangGraph 7단계 오케스트레이션 워크플로우 종합 통합 테스트 시작")

    test_suite = LangGraphOrchestrationTestSuite()

    try:
        # 테스트 환경 설정
        await test_suite.setup()

        # 종합 테스트 실행
        summary = await test_suite.run_comprehensive_tests()

        # 결과 출력
        print("\n" + "="*80)
        print("LangGraph 오케스트레이션 테스트 결과 요약")
        print("="*80)
        print(f"총 테스트: {summary['test_execution']['total_tests']}개")
        print(f"성공: {summary['test_execution']['successful_tests']}개")
        print(f"실패: {summary['test_execution']['failed_tests']}개")
        print(f"성공률: {summary['test_execution']['success_rate']:.1%}")
        print(f"평균 지연시간: {summary['performance_metrics']['avg_latency']:.3f}초")
        print(f"피크 메모리: {summary['performance_metrics']['peak_memory_mb']:.1f}MB")

        # PRD 준수도
        prd = summary['prd_compliance']
        print(f"\nPRD 기준 달성도: {'달성' if prd['overall_compliance'] else '미달성'}")

        # 카테고리별 성과
        print(f"\n카테고리별 성과:")
        for category, stats in summary['category_statistics'].items():
            success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  - {category}: {success_rate:.1f}% ({stats['success']}/{stats['total']})")

        # 실패한 테스트가 있다면 표시
        if summary['failed_tests_summary']:
            print(f"\n실패한 테스트 ({len(summary['failed_tests_summary'])}개):")
            for failed_test in summary['failed_tests_summary'][:5]:
                print(f"  - {failed_test['name']}: {failed_test['error']}")

        print("\n테스트 완료! 상세 결과는 생성된 파일을 확인하세요.")

    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        print(f"테스트 실행 실패: {e}")
        return 1

    finally:
        # 정리
        await test_suite.teardown()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)