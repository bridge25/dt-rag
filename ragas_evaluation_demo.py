"""
RAGAS Evaluation System Demo

실제 동작하는 RAGAS 평가 시스템 데모입니다.
DT-RAG v1.8.1에서 사용할 수 있는 모든 기능을 보여줍니다.

실행 방법:
python ragas_evaluation_demo.py
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import our RAGAS evaluation system
from apps.evaluation.ragas_engine import RAGASEvaluator
from apps.evaluation.quality_monitor import QualityMonitor
from apps.evaluation.experiment_tracker import ExperimentTracker
from apps.evaluation.sample_data import SampleDataGenerator
from apps.evaluation.models import EvaluationRequest, QualityThresholds, ExperimentConfig

class RAGASDemo:
    """RAGAS 평가 시스템 실제 데모"""

    def __init__(self):
        print("🚀 DT-RAG RAGAS 평가 시스템 v1.8.1 데모")
        print("=" * 60)

        # 시스템 구성 요소 초기화
        self.evaluator = RAGASEvaluator()
        self.quality_monitor = QualityMonitor()
        self.experiment_tracker = ExperimentTracker()
        self.sample_generator = SampleDataGenerator()

        # API 키 확인
        self.has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        print(f"🔑 Gemini API: {'✅ Available' if self.has_gemini else '❌ Not available (using fallbacks)'}")
        print()

    async def demo_basic_evaluation(self):
        """기본 RAGAS 평가 데모"""
        print("📊 1. 기본 RAGAS 평가 데모")
        print("-" * 40)

        # 실제 RAG 시나리오 예시
        query = "RAG 시스템에서 Context Precision이란 무엇인가요?"

        response = """Context Precision은 RAG 시스템에서 검색된 컨텍스트의 정확도를 측정하는 지표입니다.
        이는 검색된 컨텍스트 중에서 실제로 쿼리와 관련이 있는 컨텍스트의 비율을 나타냅니다.
        Context Precision = (관련있는 컨텍스트 수) / (전체 검색된 컨텍스트 수) 로 계산됩니다.
        높은 Context Precision은 검색 시스템이 불필요한 정보를 최소화하고 관련성 높은 정보만을 제공함을 의미합니다."""

        contexts = [
            "Context Precision은 검색된 컨텍스트 중 실제로 관련있는 컨텍스트의 비율을 측정하는 RAGAS 메트릭입니다.",
            "RAGAS에서 Context Precision은 검색 품질을 평가하는 핵심 지표 중 하나로, 불필요한 정보의 검색을 최소화하는 것이 목표입니다.",
            "Context Precision이 높을수록 RAG 시스템이 더 정확한 정보 검색을 수행한다고 볼 수 있습니다.",
            "사과는 빨간색이고 달콤한 과일입니다."  # 관련성 없는 컨텍스트 (테스트용)
        ]

        print(f"🔍 질문: {query}")
        print(f"💬 답변: {response[:100]}...")
        print(f"📚 컨텍스트 수: {len(contexts)}개")
        print("\n⏳ 평가 중...")

        start_time = time.time()

        # RAGAS 평가 실행
        result = await self.evaluator.evaluate_rag_response(
            query=query,
            response=response,
            retrieved_contexts=contexts
        )

        end_time = time.time()
        evaluation_time = end_time - start_time

        # 결과 출력
        print(f"⚡ 평가 완료 ({evaluation_time:.2f}초)")
        print("\n📈 RAGAS 메트릭 결과:")
        print(f"  • Faithfulness (사실성):     {result.metrics.faithfulness:.3f}")
        print(f"  • Context Precision (정밀도): {result.metrics.context_precision:.3f}")
        print(f"  • Context Recall (재현율):    {result.metrics.context_recall:.3f}")
        print(f"  • Answer Relevancy (관련성):  {result.metrics.answer_relevancy:.3f}")

        if result.quality_flags:
            print(f"\n⚠️  품질 경고: {', '.join(result.quality_flags)}")
        else:
            print("\n✅ 품질 검사 통과")

        if result.recommendations:
            print("\n💡 개선 권장사항:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")

        return result

    async def demo_quality_monitoring(self):
        """품질 모니터링 데모"""
        print("\n🔍 2. 품질 모니터링 시스템 데모")
        print("-" * 40)

        # 다양한 품질의 평가 데이터 생성
        evaluation_requests = self.sample_generator.generate_evaluation_requests(15)

        print(f"📊 {len(evaluation_requests)}개의 평가 데이터 처리 중...")

        alert_count = 0
        processed_count = 0

        for i, request in enumerate(evaluation_requests):
            # 평가 실행
            result = await self.evaluator.evaluate_rag_response(
                query=request.query,
                response=request.response,
                retrieved_contexts=request.retrieved_contexts
            )

            # 품질 모니터링에 기록
            alerts = await self.quality_monitor.record_evaluation(result)
            alert_count += len(alerts)
            processed_count += 1

            # 진행상황 표시 (매 5개마다)
            if (i + 1) % 5 == 0:
                print(f"  ✓ {i + 1}개 처리 완료")

        # 품질 상태 확인
        quality_status = await self.quality_monitor.get_quality_status()

        print(f"\n📋 품질 모니터링 결과:")
        print(f"  • 처리된 평가: {processed_count}개")
        print(f"  • 발생한 알림: {alert_count}개")

        current_metrics = quality_status.get('current_metrics', {})
        if current_metrics:
            print(f"\n📊 현재 품질 지표:")
            for metric, value in current_metrics.items():
                if not metric.endswith('_trend') and not metric.endswith('_p95'):
                    print(f"  • {metric}: {value:.3f}")

        # 품질 게이트 상태
        quality_gates = quality_status.get('quality_gates', {})
        if quality_gates.get('gates'):
            print(f"\n🚪 품질 게이트 상태:")
            overall_passing = quality_gates.get('overall_passing', False)
            print(f"  • 전체 통과 여부: {'✅ 통과' if overall_passing else '❌ 실패'}")

            for gate_name, gate_info in quality_gates['gates'].items():
                status = "✅" if gate_info.get('passing') else "❌"
                value = gate_info.get('current_value', 0)
                threshold = gate_info.get('threshold', 0)
                print(f"  • {gate_name}: {status} ({value:.3f} / {threshold:.3f})")

        # 권장사항
        recommendations = quality_status.get('recommendations', [])
        if recommendations:
            print(f"\n💡 시스템 권장사항:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        return quality_status

    async def demo_ab_testing(self):
        """A/B 테스트 데모"""
        print("\n🧪 3. A/B 테스트 시스템 데모")
        print("-" * 40)

        # 실험 설정
        config = ExperimentConfig(
            experiment_id="demo_retrieval_test",
            name="검색 알고리즘 성능 비교",
            description="BM25 vs 하이브리드 검색 성능 비교 실험",
            control_config={
                "search_type": "bm25_only",
                "top_k": 10,
                "rerank": False
            },
            treatment_config={
                "search_type": "hybrid",
                "bm25_weight": 0.3,
                "vector_weight": 0.7,
                "top_k": 10,
                "rerank": True
            },
            minimum_sample_size=30
        )

        print(f"🔬 실험 설정: {config.name}")
        print(f"📋 설명: {config.description}")
        print(f"👥 최소 샘플 크기: {config.minimum_sample_size}")

        # 실험 생성 및 시작
        experiment_id = await self.experiment_tracker.create_experiment(config)
        await self.experiment_tracker.start_experiment(experiment_id)

        print(f"🚀 실험 시작: {experiment_id}")

        # 가상 사용자 데이터 생성
        print("\n👥 가상 사용자 상호작용 시뮬레이션...")

        for user_idx in range(60):
            user_id = f"demo_user_{user_idx}"

            # 사용자 그룹 할당
            group = self.experiment_tracker.assign_user_to_experiment(user_id, experiment_id)

            # 그룹에 따른 성능 시뮬레이션
            if group == "control":
                # 대조군: 약간 낮은 성능
                performance_modifier = 0.95
            else:
                # 실험군: 약간 높은 성능
                performance_modifier = 1.05

            # 모의 평가 결과 생성
            from apps.evaluation.models import EvaluationResult, EvaluationMetrics
            import random

            mock_result = EvaluationResult(
                evaluation_id=f"demo_{user_id}",
                query="demo query",
                metrics=EvaluationMetrics(
                    faithfulness=min(0.99, 0.82 * performance_modifier + random.gauss(0, 0.03)),
                    context_precision=min(0.99, 0.78 * performance_modifier + random.gauss(0, 0.04)),
                    context_recall=min(0.99, 0.74 * performance_modifier + random.gauss(0, 0.05)),
                    answer_relevancy=min(0.99, 0.80 * performance_modifier + random.gauss(0, 0.03))
                ),
                quality_flags=[],
                recommendations=[],
                timestamp=datetime.utcnow()
            )

            await self.experiment_tracker.record_experiment_result(
                experiment_id, user_id, mock_result
            )

            # 진행상황 표시
            if (user_idx + 1) % 20 == 0:
                print(f"  ✓ {user_idx + 1}명 처리 완료")

        # 실험 결과 분석
        print("\n📊 실험 결과 분석 중...")
        results = await self.experiment_tracker.analyze_experiment_results(experiment_id)

        if results:
            print(f"\n🎯 실험 결과:")
            print(f"  • 대조군 샘플: {results.control_samples}개")
            print(f"  • 실험군 샘플: {results.treatment_samples}개")
            print(f"  • 통계적 유의성: {'✅ 유의함' if results.is_statistically_significant else '❌ 유의하지 않음'}")
            print(f"  • 권장사항: {results.recommendation}")

            print(f"\n📈 메트릭별 비교:")
            for metric, comparison in results.metric_comparisons.items():
                if comparison and 'control_mean' in comparison:
                    control_mean = comparison['control_mean']
                    treatment_mean = comparison['treatment_mean']
                    improvement = ((treatment_mean - control_mean) / control_mean * 100)
                    significance = "📈" if comparison.get('is_significant') else "📊"

                    print(f"  • {metric}:")
                    print(f"    - 대조군: {control_mean:.3f}")
                    print(f"    - 실험군: {treatment_mean:.3f}")
                    print(f"    - 변화율: {improvement:+.1f}% {significance}")

            print(f"\n📝 요약: {results.summary}")

        # 실험 종료
        await self.experiment_tracker.stop_experiment(experiment_id, "데모 완료")
        print(f"⏹️  실험 종료")

        return results

    async def demo_golden_dataset(self):
        """골든 데이터셋 데모"""
        print("\n🏆 4. 골든 데이터셋 관리 데모")
        print("-" * 40)

        # 골든 데이터셋 생성
        golden_entries = self.sample_generator.generate_golden_dataset(20)
        print(f"📚 {len(golden_entries)}개의 골든 데이터셋 항목 생성")

        # 데이터셋 검증
        validation_errors = []
        quality_scores = []

        for i, entry in enumerate(golden_entries):
            # 기본 검증
            entry_score = 1.0

            if len(entry.query.split()) < 3:
                validation_errors.append(f"항목 {i}: 질문이 너무 짧음")
                entry_score -= 0.2

            if len(entry.ground_truth_answer.split()) < 10:
                validation_errors.append(f"항목 {i}: 답변이 너무 짧음")
                entry_score -= 0.2

            if len(entry.expected_contexts) < 2:
                validation_errors.append(f"항목 {i}: 예상 컨텍스트가 부족")
                entry_score -= 0.3

            quality_scores.append(max(0, entry_score))

        # 검증 결과
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        valid_entries = len([s for s in quality_scores if s > 0.8])

        print(f"\n✅ 데이터셋 검증 결과:")
        print(f"  • 전체 품질 점수: {overall_quality:.2f}")
        print(f"  • 유효한 항목: {valid_entries}/{len(golden_entries)}")
        print(f"  • 검증 오류: {len(validation_errors)}개")

        if validation_errors[:3]:  # 처음 3개 오류만 표시
            print(f"  • 주요 오류:")
            for error in validation_errors[:3]:
                print(f"    - {error}")

        # 카테고리별 분포
        category_dist = {}
        difficulty_dist = {}

        for entry in golden_entries:
            category = entry.category or "미분류"
            category_dist[category] = category_dist.get(category, 0) + 1

            difficulty = entry.difficulty_level
            difficulty_dist[difficulty] = difficulty_dist.get(difficulty, 0) + 1

        print(f"\n📊 데이터셋 분포:")
        print(f"  • 카테고리별:")
        for category, count in category_dist.items():
            print(f"    - {category}: {count}개")

        print(f"  • 난이도별:")
        for difficulty, count in difficulty_dist.items():
            print(f"    - {difficulty}: {count}개")

        # 샘플 벤치마크 실행
        print(f"\n🎯 샘플 벤치마크 실행 (5개 항목)...")

        benchmark_results = []
        for entry in golden_entries[:5]:
            result = await self.evaluator.evaluate_rag_response(
                query=entry.query,
                response=entry.ground_truth_answer,
                retrieved_contexts=entry.expected_contexts
            )
            benchmark_results.append(result)

        # 벤치마크 결과
        if benchmark_results:
            avg_faithfulness = sum(r.metrics.faithfulness for r in benchmark_results if r.metrics.faithfulness) / len(benchmark_results)
            avg_precision = sum(r.metrics.context_precision for r in benchmark_results if r.metrics.context_precision) / len(benchmark_results)
            avg_recall = sum(r.metrics.context_recall for r in benchmark_results if r.metrics.context_recall) / len(benchmark_results)
            avg_relevancy = sum(r.metrics.answer_relevancy for r in benchmark_results if r.metrics.answer_relevancy) / len(benchmark_results)

            print(f"📈 벤치마크 결과 (평균):")
            print(f"  • Faithfulness: {avg_faithfulness:.3f}")
            print(f"  • Context Precision: {avg_precision:.3f}")
            print(f"  • Context Recall: {avg_recall:.3f}")
            print(f"  • Answer Relevancy: {avg_relevancy:.3f}")

        return {
            "entries_count": len(golden_entries),
            "quality_score": overall_quality,
            "valid_entries": valid_entries,
            "benchmark_results": len(benchmark_results)
        }

    async def demo_performance_analysis(self):
        """성능 분석 데모"""
        print("\n⚡ 5. 성능 분석 데모")
        print("-" * 40)

        # 다양한 크기의 평가 실행
        test_sizes = [1, 5, 10, 20]
        performance_results = []

        for size in test_sizes:
            print(f"📊 {size}개 평가 성능 테스트...")

            requests = self.sample_generator.generate_evaluation_requests(size)

            start_time = time.time()

            # 순차 실행
            for request in requests:
                await self.evaluator.evaluate_rag_response(
                    query=request.query,
                    response=request.response,
                    retrieved_contexts=request.retrieved_contexts
                )

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / size

            performance_results.append({
                "size": size,
                "total_time": total_time,
                "avg_time": avg_time,
                "evals_per_second": size / total_time
            })

            print(f"  ✓ 완료: {total_time:.2f}초 (평균 {avg_time:.2f}초/건)")

        print(f"\n📈 성능 분석 결과:")
        print(f"{'크기':<6} {'총시간':<10} {'평균시간':<10} {'처리량(건/초)':<12}")
        print("-" * 42)

        for result in performance_results:
            print(f"{result['size']:<6} {result['total_time']:<10.2f} {result['avg_time']:<10.2f} {result['evals_per_second']:<12.1f}")

        # 메모리 사용량 추정
        import sys
        current_memory = sys.getsizeof(self.evaluator) + sys.getsizeof(self.quality_monitor)
        print(f"\n💾 메모리 사용량: ~{current_memory / 1024:.1f} KB")

        return performance_results

    async def run_complete_demo(self):
        """전체 데모 실행"""
        print("🎬 DT-RAG RAGAS 평가 시스템 완전 데모 시작!")
        print()

        demo_results = {}

        try:
            # 1. 기본 평가 데모
            demo_results['basic_evaluation'] = await self.demo_basic_evaluation()

            # 2. 품질 모니터링 데모
            demo_results['quality_monitoring'] = await self.demo_quality_monitoring()

            # 3. A/B 테스트 데모
            demo_results['ab_testing'] = await self.demo_ab_testing()

            # 4. 골든 데이터셋 데모
            demo_results['golden_dataset'] = await self.demo_golden_dataset()

            # 5. 성능 분석 데모
            demo_results['performance'] = await self.demo_performance_analysis()

            # 전체 요약
            print("\n" + "=" * 60)
            print("🎉 RAGAS 평가 시스템 데모 완료!")
            print("=" * 60)
            print()
            print("✅ 구현된 주요 기능:")
            print("  • RAGAS 4대 메트릭 평가 (Faithfulness, Precision, Recall, Relevancy)")
            print("  • 실시간 품질 모니터링 및 알림")
            print("  • A/B 테스트 및 실험 관리")
            print("  • 골든 데이터셋 관리")
            print("  • 성능 분석 및 벤치마킹")
            print("  • 품질 게이트 및 자동화 워크플로우")
            print()
            print("🚀 프로덕션 사용 준비 완료!")
            print("   - API 엔드포인트: /evaluation/*")
            print("   - 실시간 대시보드: /evaluation/dashboard")
            print("   - 품질 모니터링: 자동 활성화")
            print()

            # 결과를 파일로 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"ragas_demo_results_{timestamp}.json"

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "demo_completed": True,
                    "gemini_api_available": self.has_gemini,
                    "summary": "RAGAS evaluation system demo completed successfully",
                    "results_summary": {
                        "basic_evaluation_completed": bool(demo_results.get('basic_evaluation')),
                        "quality_monitoring_active": bool(demo_results.get('quality_monitoring')),
                        "ab_testing_functional": bool(demo_results.get('ab_testing')),
                        "golden_dataset_ready": bool(demo_results.get('golden_dataset')),
                        "performance_tested": bool(demo_results.get('performance'))
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"📄 데모 결과가 {results_file}에 저장되었습니다.")

            return demo_results

        except Exception as e:
            print(f"\n❌ 데모 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

async def main():
    """메인 함수"""
    print("🌟 DT-RAG v1.8.1 RAGAS 평가 시스템")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

    # 환경 확인
    if not os.getenv("GEMINI_API_KEY"):
        print("💡 팁: GEMINI_API_KEY 환경변수를 설정하면 더 정확한 LLM 기반 평가가 가능합니다.")
        print("    현재는 폴백 알고리즘을 사용합니다.")
        print()

    # 데모 실행
    demo = RAGASDemo()
    results = await demo.run_complete_demo()

    print("\n🏁 데모 프로그램을 종료합니다.")

if __name__ == "__main__":
    asyncio.run(main())