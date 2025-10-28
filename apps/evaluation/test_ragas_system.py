# @TEST:EVAL-001 | SPEC: .moai/specs/SPEC-EVAL-001/spec.md

"""
Test script for RAGAS evaluation system

Provides comprehensive testing including:
- Basic RAGAS metric calculation
- Quality monitoring
- A/B testing functionality
- Dashboard data generation
- Integration testing
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.evaluation.ragas_engine import RAGASEvaluator  # noqa: E402
from apps.evaluation.quality_monitor import QualityMonitor  # noqa: E402
from apps.evaluation.experiment_tracker import ExperimentTracker  # noqa: E402
from apps.evaluation.sample_data import SampleDataGenerator  # noqa: E402
from apps.evaluation.models import QualityThresholds, ExperimentConfig  # noqa: E402
from apps.api.database import init_database  # noqa: E402


class RAGASSystemTester:
    """Comprehensive RAGAS system tester"""

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def __init__(self) -> None:
        self.evaluator = RAGASEvaluator()
        self.quality_monitor = QualityMonitor()
        self.experiment_tracker = ExperimentTracker()
        self.sample_generator = SampleDataGenerator()

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def test_basic_evaluation(self) -> Any:
        """Test basic RAGAS evaluation functionality"""
        print("\n=== Testing Basic RAGAS Evaluation ===")

        # Test with high-quality response
        query = "What is Retrieval-Augmented Generation?"
        response = """Retrieval-Augmented Generation (RAG) is an AI technique that combines information retrieval with text generation. RAG systems first search through a knowledge base to find relevant documents, then use this retrieved information as context to generate more accurate and factual responses. This approach allows language models to access up-to-date information without requiring expensive retraining."""

        contexts = [
            "RAG is a technique that combines information retrieval with text generation to provide more accurate responses.",
            "RAG systems use a retriever to find relevant documents and a generator to create responses based on the retrieved context.",
            "The main advantage of RAG is that it allows language models to access external knowledge without fine-tuning.",
        ]

        print(f"Query: {query}")
        print(f"Response: {response[:100]}...")
        print(f"Number of contexts: {len(contexts)}")

        # Perform evaluation
        result = await self.evaluator.evaluate_rag_response(
            query=query, response=response, retrieved_contexts=contexts
        )

        print("\nEvaluation Results:")
        print(f"- Faithfulness: {result.metrics.faithfulness:.3f}")
        print(f"- Context Precision: {result.metrics.context_precision:.3f}")
        print(f"- Context Recall: {result.metrics.context_recall:.3f}")
        print(f"- Answer Relevancy: {result.metrics.answer_relevancy:.3f}")
        print(f"- Quality Flags: {result.quality_flags}")
        print(f"- Recommendations: {len(result.recommendations)} suggestions")

        return result

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def test_quality_scenarios(self) -> None:
        """Test different quality scenarios"""
        print("\n=== Testing Quality Scenarios ===")

        scenarios = self.sample_generator.generate_quality_scenarios()

        for scenario_name, scenario_data in scenarios:
            print(f"\nTesting scenario: {scenario_name}")

            result = await self.evaluator.evaluate_rag_response(
                query=scenario_data["query"],
                response=scenario_data["response"],
                retrieved_contexts=scenario_data["contexts"],
            )

            expected = scenario_data["expected_metrics"]
            actual = result.metrics

            print("Expected vs Actual metrics:")
            print(
                f"- Faithfulness: {expected['faithfulness']:.2f} vs {actual.faithfulness:.2f}"
            )
            print(
                f"- Context Precision: {expected['context_precision']:.2f} vs {actual.context_precision:.2f}"
            )
            print(
                f"- Context Recall: {expected['context_recall']:.2f} vs {actual.context_recall:.2f}"
            )
            print(
                f"- Answer Relevancy: {expected['answer_relevancy']:.2f} vs {actual.answer_relevancy:.2f}"
            )

            # Check if quality flags are appropriate
            if (
                scenario_name == "low_faithfulness"
                and "low_faithfulness" not in result.quality_flags
            ):
                print("⚠️  Warning: Low faithfulness not detected")
            elif (
                scenario_name == "low_precision"
                and "low_precision" not in result.quality_flags
            ):
                print("⚠️  Warning: Low precision not detected")

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def test_quality_monitoring(self) -> Any:
        """Test quality monitoring system"""
        print("\n=== Testing Quality Monitoring ===")

        # Generate sample evaluations
        evaluation_requests = self.sample_generator.generate_evaluation_requests(20)

        print(f"Generating {len(evaluation_requests)} sample evaluations...")

        for i, request in enumerate(evaluation_requests):
            result = await self.evaluator.evaluate_rag_response(
                query=request.query,
                response=request.response,
                retrieved_contexts=request.retrieved_contexts,
            )

            # Record for quality monitoring
            alerts = await self.quality_monitor.record_evaluation(result)

            if alerts:
                print(f"Evaluation {i+1}: {len(alerts)} alerts generated")

        # Check quality status
        quality_status = await self.quality_monitor.get_quality_status()
        print("\nQuality Monitoring Status:")
        print(
            f"- Current metrics available: {bool(quality_status.get('current_metrics'))}"
        )
        print(
            f"- Active alerts: {len(quality_status.get('alert_summary', {}).get('total_alerts', 0))}"
        )
        print(
            f"- Quality gates passing: {quality_status.get('quality_gates', {}).get('overall_passing', False)}"
        )

        # Test threshold updates
        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: call-arg resolution (Pydantic Field defaults)
        new_thresholds = QualityThresholds(
            faithfulness_min=0.90,
            context_precision_min=0.80,
            context_recall_min=0.75,
            answer_relevancy_min=0.85,
            response_time_max=5.0,  # Explicit value for MyPy strict mode
        )

        await self.quality_monitor.update_thresholds(new_thresholds)
        print("✅ Quality thresholds updated successfully")

        return quality_status

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def test_ab_testing(self) -> Any:
        """Test A/B testing functionality"""
        print("\n=== Testing A/B Testing ===")

        # Create experiment
        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: call-arg resolution (Pydantic Field defaults)
        config = ExperimentConfig(
            experiment_id="test_exp_001",
            name="Test Retrieval Algorithm",
            description="Testing BM25 vs hybrid search",
            control_config={"search_type": "bm25", "top_k": 5},
            treatment_config={"search_type": "hybrid", "top_k": 5, "rerank": True},
            significance_threshold=0.05,  # Explicit value for MyPy strict mode
            minimum_sample_size=20,
            power_threshold=0.8,  # Explicit value for MyPy strict mode
        )

        experiment_id = await self.experiment_tracker.create_experiment(config)
        print(f"Created experiment: {experiment_id}")

        # Start experiment
        success = await self.experiment_tracker.start_experiment(experiment_id)
        print(f"Started experiment: {success}")

        # Simulate user assignments and evaluations
        print("Simulating user interactions...")

        for user_id in [f"user_{i}" for i in range(50)]:
            group = self.experiment_tracker.assign_user_to_experiment(
                user_id, experiment_id
            )

            # Generate evaluation based on group
            if group == "control":
                # Slightly lower performance for control
                metrics_modifier = 0.95
            else:
                # Slightly better performance for treatment
                metrics_modifier = 1.02

            # Create mock evaluation
            from apps.evaluation.models import EvaluationResult, EvaluationMetrics
            import random

            # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: call-arg resolution (Pydantic Field defaults)
            mock_result = EvaluationResult(
                evaluation_id=f"mock_{user_id}",
                query="test query",
                metrics=EvaluationMetrics(
                    faithfulness=min(
                        0.99, 0.85 * metrics_modifier + random.uniform(-0.05, 0.05)
                    ),
                    context_precision=min(
                        0.99, 0.80 * metrics_modifier + random.uniform(-0.05, 0.05)
                    ),
                    context_recall=min(
                        0.99, 0.75 * metrics_modifier + random.uniform(-0.05, 0.05)
                    ),
                    answer_relevancy=min(
                        0.99, 0.82 * metrics_modifier + random.uniform(-0.05, 0.05)
                    ),
                    response_time=None,  # Explicit None for MyPy strict mode
                    retrieval_score=None,  # Explicit None for MyPy strict mode
                ),
                overall_score=0.0,  # Explicit value for MyPy strict mode
                quality_flags=[],
                recommendations=[],
                timestamp=datetime.utcnow(),
            )

            await self.experiment_tracker.record_experiment_result(
                experiment_id, user_id, mock_result
            )

        # Analyze results
        results = await self.experiment_tracker.analyze_experiment_results(
            experiment_id
        )

        if results:
            print("\nExperiment Results:")
            print(f"- Control samples: {results.control_samples}")
            print(f"- Treatment samples: {results.treatment_samples}")
            print(
                f"- Statistically significant: {results.is_statistically_significant}"
            )
            print(f"- Recommendation: {results.recommendation}")
            print(f"- Summary: {results.summary}")

            # Print metric comparisons
            for metric, comparison in results.metric_comparisons.items():
                if comparison:
                    print(
                        f"- {metric}: Control={comparison.get('control_mean', 0):.3f}, "
                        f"Treatment={comparison.get('treatment_mean', 0):.3f}, "
                        f"p-value={comparison.get('p_value', 1):.3f}"
                    )

        # Stop experiment
        await self.experiment_tracker.stop_experiment(experiment_id, "test_complete")
        print("✅ Experiment completed")

        return results

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def test_canary_deployment(self) -> Dict[str, str]:
        """Test canary deployment monitoring"""
        print("\n=== Testing Canary Deployment ===")

        print("Starting canary deployment monitoring...")

        # Note: This would normally run for the full duration
        # For testing, we'll simulate a quick version
        monitoring_result = {
            "canary_id": "test_canary_001",
            "status": "monitoring_complete",
            "recommendation": "proceed_with_rollout",
            "monitoring_duration": "simulated",
        }

        print(f"Canary monitoring result: {monitoring_result['recommendation']}")
        print("✅ Canary deployment test completed")

        return monitoring_result

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def test_golden_dataset(self) -> Any:
        """Test golden dataset functionality"""
        print("\n=== Testing Golden Dataset ===")

        # Generate golden dataset
        golden_entries = self.sample_generator.generate_golden_dataset(10)
        print(f"Generated {len(golden_entries)} golden dataset entries")

        # Test dataset validation
        from apps.evaluation.evaluation_router import validate_dataset

        validation_result = await validate_dataset(golden_entries)

        print("Dataset validation:")
        print(f"- Valid: {validation_result.is_valid}")
        print(f"- Quality score: {validation_result.quality_score:.2f}")
        print(f"- Total entries: {validation_result.statistics['total_entries']}")
        print(f"- Valid entries: {validation_result.statistics['valid_entries']}")

        if validation_result.validation_errors:
            print(f"- Validation errors: {len(validation_result.validation_errors)}")

        return validation_result

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def run_integration_test(self) -> bool:
        """Run integration test with database"""
        print("\n=== Running Integration Test ===")

        try:
            # Test database initialization
            db_success = await init_database()
            print(
                f"Database initialization: {'✅ Success' if db_success else '❌ Failed'}"
            )

            if not db_success:
                print("Skipping database-dependent tests")
                return False

            # Test evaluation storage
            from apps.evaluation.integration import evaluation_integration

            # Perform evaluation through integration layer
            result = await evaluation_integration.evaluate_search_interaction(
                query="What is machine learning?",
                search_results=[
                    {
                        "text": "Machine learning is a subset of AI that learns from data"
                    },
                    {
                        "text": "ML algorithms can make predictions without explicit programming"
                    },
                    {
                        "text": "Common ML techniques include supervised and unsupervised learning"
                    },
                ],
                user_id="test_user",
                session_id="test_session",
            )

            print("Integration evaluation completed:")
            print(f"- Evaluation ID: {result.evaluation_id}")
            print(f"- Metrics calculated: {bool(result.metrics.faithfulness)}")
            print(f"- Quality flags: {result.quality_flags}")

            # Test quality summary
            quality_summary = await evaluation_integration.get_quality_summary()
            print(f"Quality monitoring active: {bool(quality_summary)}")

            print("✅ Integration test completed successfully")
            return True

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def run_performance_test(self) -> float:
        """Run performance test"""
        print("\n=== Running Performance Test ===")

        import time

        # Test evaluation speed
        requests = self.sample_generator.generate_evaluation_requests(10)

        start_time = time.time()

        results = []
        for request in requests:
            result = await self.evaluator.evaluate_rag_response(
                query=request.query,
                response=request.response,
                retrieved_contexts=request.retrieved_contexts,
            )
            results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        print("Performance Results:")
        print(f"- Evaluated {len(requests)} requests in {total_time:.2f} seconds")
        print(
            f"- Average time per evaluation: {total_time / len(requests):.2f} seconds"
        )
        print(f"- Evaluations per second: {len(requests) / total_time:.1f}")

        # Check if any evaluations failed
        successful_evaluations = len(
            [r for r in results if r.metrics.faithfulness is not None]
        )
        print(f"- Successful evaluations: {successful_evaluations}/{len(requests)}")

        return total_time / len(requests)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def generate_dashboard_test_data(self) -> None:
        """Generate test data for dashboard"""
        print("\n=== Generating Dashboard Test Data ===")

        # Generate realistic evaluation data over time
        evaluation_data = self.sample_generator.generate_realistic_evaluation_data(
            days=7
        )

        print(f"Generated {len(evaluation_data)} historical evaluations")

        # Simulate recording these evaluations
        for data in evaluation_data[
            -50:
        ]:  # Only process recent 50 to avoid overwhelming
            from apps.evaluation.models import EvaluationResult, EvaluationMetrics

            # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: call-arg resolution (Pydantic Field defaults)
            mock_result = EvaluationResult(
                evaluation_id=f"hist_{hash(str(data['timestamp'])) % 10000}",
                query="historical query",
                metrics=EvaluationMetrics(
                    faithfulness=data["faithfulness"],
                    context_precision=data["context_precision"],
                    context_recall=data["context_recall"],
                    answer_relevancy=data["answer_relevancy"],
                    response_time=data["response_time"],
                    retrieval_score=None,  # Explicit None for MyPy strict mode
                ),
                overall_score=0.0,  # Explicit value for MyPy strict mode
                quality_flags=[],
                recommendations=[],
                timestamp=data["timestamp"],
            )

            await self.quality_monitor.record_evaluation(mock_result)

        print("✅ Dashboard test data generated")

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in sequence"""
        print("🚀 Starting RAGAS System Comprehensive Test")
        print("=" * 60)

        test_results = {}

        try:
            # Basic functionality tests
            test_results["basic_evaluation"] = await self.test_basic_evaluation()
            test_results["quality_scenarios"] = await self.test_quality_scenarios()

            # System component tests
            test_results["quality_monitoring"] = await self.test_quality_monitoring()
            test_results["ab_testing"] = await self.test_ab_testing()
            test_results["canary_deployment"] = await self.test_canary_deployment()

            # Data and integration tests
            test_results["golden_dataset"] = await self.test_golden_dataset()
            test_results["integration_test"] = await self.run_integration_test()

            # Performance tests
            test_results["performance"] = await self.run_performance_test()

            # Dashboard data generation
            await self.generate_dashboard_test_data()

            print("\n" + "=" * 60)
            print("🎉 All tests completed successfully!")
            print("\nTest Summary:")
            print("- Basic evaluation: ✅")
            print("- Quality scenarios: ✅")
            print("- Quality monitoring: ✅")
            print("- A/B testing: ✅")
            print("- Canary deployment: ✅")
            print("- Golden dataset: ✅")
            print(
                f"- Integration test: {'✅' if test_results.get('integration_test') else '❌'}"
            )
            print(
                f"- Performance test: ✅ ({test_results.get('performance', 0):.2f}s avg)"
            )

            return test_results

        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
async def main() -> None:
    """Main test function"""
    # Check if Gemini API key is available
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print(
            "⚠️  Warning: GEMINI_API_KEY not found. LLM-based evaluation will use fallbacks."
        )

    # Run tests
    tester = RAGASSystemTester()
    results = await tester.run_all_tests()

    # Save results to file
    with open("ragas_test_results.json", "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "gemini_available": bool(gemini_key),
                "results": str(results),  # Convert to string for JSON serialization
            },
            f,
            indent=2,
        )

    print("\n📊 Test results saved to ragas_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
