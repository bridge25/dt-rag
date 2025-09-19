#!/usr/bin/env python3
"""
Comprehensive RAGAS Evaluation System Test

Tests the complete RAGAS evaluation pipeline:
- RAGAS engine functionality
- Golden dataset loading
- Evaluation API endpoints
- Quality gates monitoring
- Performance metrics
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project modules
try:
    from apps.evaluation.core.ragas_engine import RAGASEvaluationEngine, RAGResponse
    from apps.evaluation.core.golden_dataset import GoldenDatasetManager, GoldenDataPoint
    from apps.monitoring.core.metrics_collector import MetricsCollector
    from apps.monitoring.core.ragas_metrics_extension import extend_metrics_collector
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    IMPORTS_SUCCESSFUL = False

class RAGASSystemTester:
    """Comprehensive tester for RAGAS evaluation system"""

    def __init__(self):
        self.ragas_engine = None
        self.golden_dataset_manager = None
        self.metrics_collector = None

        if IMPORTS_SUCCESSFUL:
            self.ragas_engine = RAGASEvaluationEngine(use_openai=False)  # Use fallback for testing
            self.golden_dataset_manager = GoldenDatasetManager()
            self.metrics_collector = MetricsCollector(port=8091)  # Different port for testing

            # Extend metrics collector with RAGAS metrics
            extend_metrics_collector(self.metrics_collector)

        self.test_results = {}

    async def run_comprehensive_test(self):
        """Run all RAGAS system tests"""
        logger.info("Starting comprehensive RAGAS evaluation system test")

        if not IMPORTS_SUCCESSFUL:
            logger.error("Cannot run tests - import failures")
            return {"status": "failed", "reason": "import_failures"}

        try:
            # Test 1: Basic RAGAS engine functionality
            await self.test_ragas_engine_basic()

            # Test 2: Golden dataset loading and validation
            await self.test_golden_dataset_operations()

            # Test 3: Complete evaluation pipeline
            await self.test_evaluation_pipeline()

            # Test 4: Quality gates and thresholds
            await self.test_quality_gates()

            # Test 5: Metrics collection and monitoring
            await self.test_metrics_collection()

            # Test 6: Performance and scalability
            await self.test_performance_characteristics()

            # Generate final report
            return self.generate_test_report()

        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def test_ragas_engine_basic(self):
        """Test basic RAGAS engine basic functionality"""
        logger.info("Testing RAGAS engine basic functionality")

        try:
            # Create sample test data
            test_queries = [
                "What is Retrieval-Augmented Generation?",
                "How does vector search work in RAG systems?",
                "What are the benefits of hybrid search?"
            ]

            test_responses = [
                RAGResponse(
                    answer="RAG combines information retrieval with text generation to provide accurate, grounded responses.",
                    retrieved_docs=[
                        {
                            'text': "RAG is a framework that retrieves relevant documents and uses them for generation.",
                            'title': "RAG Overview",
                            'taxonomy_path': ["AI", "NLP", "RAG"],
                            'score': 0.9
                        },
                        {
                            'text': "The framework combines parametric and non-parametric knowledge effectively.",
                            'title': "RAG Architecture",
                            'taxonomy_path': ["AI", "NLP", "RAG", "Architecture"],
                            'score': 0.85
                        }
                    ],
                    confidence=0.88,
                    metadata={'search_type': 'hybrid', 'model': 'test'}
                ),
                RAGResponse(
                    answer="Vector search uses neural embeddings to find semantically similar documents in high-dimensional space.",
                    retrieved_docs=[
                        {
                            'text': "Vector search converts text to embeddings and uses similarity measures like cosine similarity.",
                            'title': "Vector Search Fundamentals",
                            'taxonomy_path': ["AI", "Information Retrieval", "Vector Search"],
                            'score': 0.92
                        }
                    ],
                    confidence=0.91,
                    metadata={'search_type': 'vector', 'model': 'test'}
                ),
                RAGResponse(
                    answer="Hybrid search combines keyword-based and semantic search for comprehensive retrieval coverage.",
                    retrieved_docs=[
                        {
                            'text': "Hybrid search systems combine BM25 and vector search using fusion techniques like RRF.",
                            'title': "Hybrid Search Systems",
                            'taxonomy_path': ["AI", "Information Retrieval", "Hybrid"],
                            'score': 0.87
                        }
                    ],
                    confidence=0.85,
                    metadata={'search_type': 'hybrid', 'model': 'test'}
                )
            ]

            ground_truths = [
                "RAG is a framework that combines information retrieval with text generation for accurate responses.",
                "Vector search uses neural embeddings to find semantically similar content.",
                "Hybrid search combines lexical and semantic search methods for comprehensive retrieval."
            ]

            # Run evaluation
            start_time = time.time()
            result = await self.ragas_engine.evaluate_rag_system(
                test_queries=test_queries,
                rag_responses=test_responses,
                ground_truths=ground_truths
            )
            evaluation_time = time.time() - start_time

            # Validate results
            assert hasattr(result, 'metrics'), "Result should have metrics"
            assert hasattr(result, 'quality_gates_passed'), "Result should have quality gates status"
            assert hasattr(result, 'recommendations'), "Result should have recommendations"

            # Check key metrics are present
            required_metrics = ['faithfulness', 'answer_relevancy']
            for metric in required_metrics:
                assert metric in result.metrics, f"Missing required metric: {metric}"
                assert 0.0 <= result.metrics[metric] <= 1.0, f"Invalid metric range for {metric}"

            self.test_results['ragas_engine_basic'] = {
                'status': 'passed',
                'metrics': result.metrics,
                'quality_gates_passed': result.quality_gates_passed,
                'evaluation_time_seconds': evaluation_time,
                'num_recommendations': len(result.recommendations)
            }

            logger.info(f" RAGAS engine basic test passed - Quality gates: {result.quality_gates_passed}")
            logger.info(f"   Metrics: {', '.join([f'{k}={v:.3f}' for k, v in result.metrics.items()])}")

        except Exception as e:
            logger.error(f" RAGAS engine basic test failed: {e}")
            self.test_results['ragas_engine_basic'] = {
                'status': 'failed',
                'error': str(e)
            }

    async def test_golden_dataset_operations(self):
        """Test golden dataset loading and validation"""
        logger.info("Testing golden dataset operations")

        try:
            # Test loading golden datasets from files
            dataset_files = [
                "data/golden_datasets/ai_rag_qa.json",
                "data/golden_datasets/taxonomy_qa.json",
                "data/golden_datasets/hybrid_search_qa.json"
            ]

            loaded_datasets = {}
            total_data_points = 0

            for dataset_file in dataset_files:
                file_path = project_root / dataset_file
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            dataset_data = json.load(f)

                        dataset_name = dataset_data['dataset_name']
                        data_points = dataset_data['data_points']

                        # Validate dataset structure
                        assert 'dataset_name' in dataset_data, "Missing dataset_name"
                        assert 'data_points' in dataset_data, "Missing data_points"

                        # Validate data points
                        for i, point in enumerate(data_points):
                            required_fields = ['id', 'query', 'expected_answer', 'expected_contexts', 'taxonomy_path']
                            for field in required_fields:
                                assert field in point, f"Missing field {field} in data point {i}"

                        loaded_datasets[dataset_name] = {
                            'file': dataset_file,
                            'data_points_count': len(data_points),
                            'domains': list(set(point.get('domain', 'unknown') for point in data_points))
                        }

                        total_data_points += len(data_points)

                        logger.info(f"    Loaded {dataset_name}: {len(data_points)} data points")

                    except Exception as e:
                        logger.warning(f"    Failed to load {dataset_file}: {e}")
                else:
                    logger.warning(f"    Dataset file not found: {dataset_file}")

            # Test creating data points programmatically
            sample_data_points = [
                GoldenDataPoint(
                    id="test_001",
                    query="What is the purpose of evaluation in RAG systems?",
                    expected_answer="Evaluation in RAG systems measures quality, performance, and ensures reliable outputs.",
                    expected_contexts=["RAG evaluation uses metrics like RAGAS to assess system performance."],
                    taxonomy_path=["AI", "RAG", "Evaluation"],
                    difficulty_level="medium",
                    domain="AI/RAG"
                )
            ]

            # Test dataset validation
            validation_result = await self.golden_dataset_manager.validate_dataset(sample_data_points)

            self.test_results['golden_dataset_operations'] = {
                'status': 'passed',
                'loaded_datasets': loaded_datasets,
                'total_data_points': total_data_points,
                'validation_passed': validation_result.is_valid,
                'validation_quality_score': validation_result.quality_score
            }

            logger.info(f" Golden dataset operations test passed")
            logger.info(f"   Loaded {len(loaded_datasets)} datasets with {total_data_points} total data points")

        except Exception as e:
            logger.error(f" Golden dataset operations test failed: {e}")
            self.test_results['golden_dataset_operations'] = {
                'status': 'failed',
                'error': str(e)
            }

    async def test_evaluation_pipeline(self):
        """Test complete evaluation pipeline"""
        logger.info("Testing complete evaluation pipeline")

        try:
            # Load a sample from golden dataset for testing
            ai_rag_file = project_root / "data/golden_datasets/ai_rag_qa.json"

            if not ai_rag_file.exists():
                logger.warning("Golden dataset file not found - using synthetic data")
                test_data = self.create_synthetic_test_data()
            else:
                with open(ai_rag_file, 'r', encoding='utf-8') as f:
                    dataset_data = json.load(f)
                test_data = dataset_data['data_points'][:3]  # Use first 3 data points

            # Convert to test format
            test_queries = []
            expected_answers = []
            expected_contexts = []

            for point in test_data:
                test_queries.append(point['query'])
                expected_answers.append(point['expected_answer'])
                expected_contexts.append(point['expected_contexts'])

            # Simulate RAG responses (in real system, these would come from search)
            simulated_responses = []
            for i, (query, expected_answer) in enumerate(zip(test_queries, expected_answers)):
                response = RAGResponse(
                    answer=f"Simulated answer based on: {expected_answer[:100]}...",
                    retrieved_docs=[
                        {
                            'text': context,
                            'title': f"Document {j+1}",
                            'taxonomy_path': test_data[i].get('taxonomy_path', ['AI']),
                            'score': 0.85 - j * 0.05
                        }
                        for j, context in enumerate(expected_contexts[i][:3])  # Max 3 contexts
                    ],
                    confidence=0.8 + i * 0.05,
                    metadata={'search_type': 'hybrid', 'simulation': True}
                )
                simulated_responses.append(response)

            # Run pipeline evaluation
            start_time = time.time()
            pipeline_result = await self.ragas_engine.evaluate_rag_system(
                test_queries=test_queries,
                rag_responses=simulated_responses,
                ground_truths=expected_answers,
                expected_contexts=expected_contexts
            )
            pipeline_time = time.time() - start_time

            # Validate pipeline results
            assert len(pipeline_result.metrics) > 0, "Pipeline should produce metrics"

            # Check comprehensive metrics
            expected_metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
            present_metrics = [m for m in expected_metrics if m in pipeline_result.metrics]

            self.test_results['evaluation_pipeline'] = {
                'status': 'passed',
                'queries_evaluated': len(test_queries),
                'pipeline_time_seconds': pipeline_time,
                'metrics_present': present_metrics,
                'overall_quality_score': pipeline_result.analysis.get('overall_score', 0.0),
                'quality_gates_passed': pipeline_result.quality_gates_passed,
                'num_recommendations': len(pipeline_result.recommendations)
            }

            logger.info(f" Evaluation pipeline test passed")
            logger.info(f"   Evaluated {len(test_queries)} queries in {pipeline_time:.2f}s")
            logger.info(f"   Quality gates passed: {pipeline_result.quality_gates_passed}")

        except Exception as e:
            logger.error(f" Evaluation pipeline test failed: {e}")
            self.test_results['evaluation_pipeline'] = {
                'status': 'failed',
                'error': str(e)
            }

    async def test_quality_gates(self):
        """Test quality gates and threshold monitoring"""
        logger.info("Testing quality gates and thresholds")

        try:
            # Test different quality scenarios
            scenarios = [
                {
                    'name': 'high_quality',
                    'metrics': {
                        'faithfulness': 0.92,
                        'answer_relevancy': 0.88,
                        'context_precision': 0.85,
                        'context_recall': 0.90
                    }
                },
                {
                    'name': 'medium_quality',
                    'metrics': {
                        'faithfulness': 0.78,
                        'answer_relevancy': 0.82,
                        'context_precision': 0.70,
                        'context_recall': 0.75
                    }
                },
                {
                    'name': 'low_quality',
                    'metrics': {
                        'faithfulness': 0.65,
                        'answer_relevancy': 0.68,
                        'context_precision': 0.60,
                        'context_recall': 0.55
                    }
                }
            ]

            quality_gate_results = {}

            for scenario in scenarios:
                metrics = scenario['metrics']
                gates_passed = self.ragas_engine._check_quality_gates(metrics)

                analysis = self.ragas_engine._analyze_results(metrics, [])
                recommendations = self.ragas_engine._generate_recommendations(metrics, analysis)

                quality_gate_results[scenario['name']] = {
                    'gates_passed': gates_passed,
                    'overall_score': analysis.get('overall_score', 0.0),
                    'strengths_count': len(analysis.get('strengths', [])),
                    'weaknesses_count': len(analysis.get('weaknesses', [])),
                    'recommendations_count': len(recommendations)
                }

                logger.info(f"   {scenario['name']}: Gates passed={gates_passed}, Score={analysis.get('overall_score', 0.0):.3f}")

            # Verify expected behavior
            assert quality_gate_results['high_quality']['gates_passed'] == True, "High quality should pass gates"
            assert quality_gate_results['low_quality']['gates_passed'] == False, "Low quality should fail gates"

            self.test_results['quality_gates'] = {
                'status': 'passed',
                'scenarios_tested': len(scenarios),
                'results': quality_gate_results
            }

            logger.info(f" Quality gates test passed")

        except Exception as e:
            logger.error(f" Quality gates test failed: {e}")
            self.test_results['quality_gates'] = {
                'status': 'failed',
                'error': str(e)
            }

    async def test_metrics_collection(self):
        """Test metrics collection and monitoring integration"""
        logger.info("Testing metrics collection and monitoring")

        try:
            if not hasattr(self.metrics_collector, 'ragas_extension'):
                logger.warning("RAGAS metrics extension not available - skipping detailed metrics test")
                self.test_results['metrics_collection'] = {
                    'status': 'skipped',
                    'reason': 'extension_not_available'
                }
                return

            # Test recording evaluation metrics
            test_metrics = {
                'faithfulness': 0.87,
                'answer_relevancy': 0.84,
                'context_precision': 0.78,
                'context_recall': 0.82,
                'classification_accuracy': 0.91,
                'taxonomy_consistency': 0.85
            }

            # Record metrics
            self.metrics_collector.record_evaluation_metrics(
                metrics=test_metrics,
                evaluation_type="test",
                duration_seconds=2.5,
                quality_gates_passed=True
            )

            # Test quality gates status update
            quality_gates_status = {
                'faithfulness': {
                    'threshold': 0.85,
                    'current_value': 0.87,
                    'status': 'passing',
                    'gap': -0.02
                },
                'context_precision': {
                    'threshold': 0.75,
                    'current_value': 0.78,
                    'status': 'passing',
                    'gap': -0.03
                }
            }

            self.metrics_collector.update_quality_gates_status(quality_gates_status)

            # Test batch evaluation progress
            self.metrics_collector.record_batch_evaluation_progress(
                batch_id="test_batch_001",
                total_queries=10,
                completed_queries=7,
                status="running"
            )

            # Test success rate update
            self.metrics_collector.update_evaluation_success_rate(0.85)

            # Get summary
            ragas_summary = self.metrics_collector.get_ragas_summary()

            self.test_results['metrics_collection'] = {
                'status': 'passed',
                'metrics_recorded': list(test_metrics.keys()),
                'quality_gates_updated': len(quality_gates_status),
                'summary_available': isinstance(ragas_summary, dict) and 'ragas_metrics' in ragas_summary
            }

            logger.info(f" Metrics collection test passed")
            logger.info(f"   Recorded {len(test_metrics)} metrics")

        except Exception as e:
            logger.error(f" Metrics collection test failed: {e}")
            self.test_results['metrics_collection'] = {
                'status': 'failed',
                'error': str(e)
            }

    async def test_performance_characteristics(self):
        """Test performance and scalability characteristics"""
        logger.info(" Testing performance characteristics")

        try:
            # Test with different batch sizes
            batch_sizes = [1, 5, 10]
            performance_results = {}

            for batch_size in batch_sizes:
                # Generate test data
                test_queries = [f"Test query {i} for performance evaluation" for i in range(batch_size)]
                test_responses = [
                    RAGResponse(
                        answer=f"Test answer {i} with sufficient detail for evaluation",
                        retrieved_docs=[
                            {
                                'text': f"Test document content {i} for context evaluation",
                                'title': f"Doc {i}",
                                'taxonomy_path': ["Test", "Performance"],
                                'score': 0.8
                            }
                        ],
                        confidence=0.8,
                        metadata={'test': True}
                    )
                    for i in range(batch_size)
                ]

                # Measure evaluation time
                start_time = time.time()
                result = await self.ragas_engine.evaluate_rag_system(
                    test_queries=test_queries,
                    rag_responses=test_responses
                )
                end_time = time.time()

                evaluation_time = end_time - start_time
                queries_per_second = batch_size / evaluation_time if evaluation_time > 0 else 0

                performance_results[batch_size] = {
                    'evaluation_time_seconds': evaluation_time,
                    'queries_per_second': queries_per_second,
                    'metrics_count': len(result.metrics),
                    'quality_gates_passed': result.quality_gates_passed
                }

                logger.info(f"   Batch size {batch_size}: {evaluation_time:.2f}s, {queries_per_second:.1f} queries/sec")

            # Performance assertions
            max_time_per_query = 10.0  # Should process within 10 seconds per query
            for batch_size, results in performance_results.items():
                time_per_query = results['evaluation_time_seconds'] / batch_size
                assert time_per_query < max_time_per_query, f"Performance too slow for batch size {batch_size}"

            self.test_results['performance_characteristics'] = {
                'status': 'passed',
                'batch_sizes_tested': batch_sizes,
                'performance_results': performance_results,
                'max_time_per_query_seconds': max_time_per_query
            }

            logger.info(f" Performance characteristics test passed")

        except Exception as e:
            logger.error(f" Performance characteristics test failed: {e}")
            self.test_results['performance_characteristics'] = {
                'status': 'failed',
                'error': str(e)
            }

    def create_synthetic_test_data(self):
        """Create synthetic test data when golden datasets are not available"""
        return [
            {
                'id': 'synthetic_001',
                'query': 'What is the primary purpose of RAGAS evaluation?',
                'expected_answer': 'RAGAS evaluation provides comprehensive assessment of RAG system quality through metrics like faithfulness and relevancy.',
                'expected_contexts': ['RAGAS framework measures RAG system performance', 'Evaluation metrics include faithfulness and answer relevancy'],
                'taxonomy_path': ['AI', 'RAG', 'Evaluation'],
                'difficulty_level': 'medium',
                'domain': 'AI/RAG'
            },
            {
                'id': 'synthetic_002',
                'query': 'How does quality gate monitoring work?',
                'expected_answer': 'Quality gates monitor key metrics against thresholds to ensure system performance meets requirements.',
                'expected_contexts': ['Quality gates use threshold-based monitoring', 'Automated alerts trigger when metrics fall below thresholds'],
                'taxonomy_path': ['AI', 'Quality Assurance', 'Monitoring'],
                'difficulty_level': 'medium',
                'domain': 'AI/QA'
            },
            {
                'id': 'synthetic_003',
                'query': 'What are the benefits of comprehensive evaluation?',
                'expected_answer': 'Comprehensive evaluation ensures reliable system performance, identifies weaknesses, and guides improvements.',
                'expected_contexts': ['Evaluation identifies system strengths and weaknesses', 'Regular assessment prevents quality degradation'],
                'taxonomy_path': ['AI', 'System Design', 'Evaluation'],
                'difficulty_level': 'easy',
                'domain': 'AI/Systems'
            }
        ]

    def generate_test_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'passed')
        failed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'failed')
        skipped_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'skipped')

        success_rate = passed_tests / total_tests if total_tests > 0 else 0.0

        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'skipped_tests': skipped_tests,
                'success_rate': success_rate,
                'status': 'passed' if success_rate >= 0.8 else 'failed'
            },
            'test_details': self.test_results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'recommendations': []
        }

        # Generate recommendations based on test results
        if failed_tests > 0:
            report['recommendations'].append("Some tests failed - review failed test details for troubleshooting")

        if success_rate < 0.8:
            report['recommendations'].append("Success rate below 80% - comprehensive system review recommended")

        if success_rate >= 0.9:
            report['recommendations'].append("Excellent test results - system ready for production")

        return report

async def main():
    """Main test execution function"""
    print("RAGAS Evaluation System Comprehensive Test")
    print("=" * 60)

    tester = RAGASSystemTester()
    report = await tester.run_comprehensive_test()

    # Print results
    print("\nTest Results Summary:")
    print(f"Total Tests: {report['test_summary']['total_tests']}")
    print(f"Passed: {report['test_summary']['passed_tests']}")
    print(f"Failed: {report['test_summary']['failed_tests']}")
    print(f"Skipped: {report['test_summary']['skipped_tests']}")
    print(f"Success Rate: {report['test_summary']['success_rate']:.1%}")
    print(f"Overall Status: {report['test_summary']['status'].upper()}")

    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

    # Save detailed report
    report_file = f"ragas_test_report_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed report saved to: {report_file}")

    # Exit with appropriate code
    exit_code = 0 if report['test_summary']['status'] == 'passed' else 1
    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)