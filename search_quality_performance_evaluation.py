"""
Search Quality and Performance Evaluation Script

Comprehensive evaluation of DT-RAG v1.8.1 search system:
1. Test diverse query patterns
2. Measure latency and throughput
3. Evaluate search quality
4. Test edge cases
5. Validate error handling

Based on CLAUDE.md: All metrics must be actual measured values, NO assumptions.
"""

import asyncio
import time
import json
import logging
import statistics
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Import search engine components
from apps.search.hybrid_search_engine import (
    HybridSearchEngine,
    SearchResult,
    SearchMetrics,
    hybrid_search
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchQualityEvaluator:
    """Evaluate search quality and performance"""

    def __init__(self):
        self.results = {
            'query_tests': [],
            'performance_tests': [],
            'edge_case_tests': [],
            'error_handling_tests': []
        }
        self.test_start_time = datetime.now()

    async def run_full_evaluation(self) -> Dict[str, Any]:
        """Run complete evaluation suite"""
        logger.info("=" * 80)
        logger.info("Starting Search Quality and Performance Evaluation")
        logger.info("=" * 80)

        # 1. Query Pattern Tests
        logger.info("\n1. Testing Query Patterns...")
        await self.test_query_patterns()

        # 2. Performance Tests
        logger.info("\n2. Testing Performance...")
        await self.test_performance()

        # 3. Edge Case Tests
        logger.info("\n3. Testing Edge Cases...")
        await self.test_edge_cases()

        # 4. Error Handling Tests
        logger.info("\n4. Testing Error Handling...")
        await self.test_error_handling()

        # Generate report
        report = self.generate_report()

        return report

    async def test_query_patterns(self):
        """Test various query patterns and evaluate relevance"""
        test_queries = [
            # Short queries
            ("AI", "short_exact_term"),
            ("ML", "short_acronym"),

            # Medium queries
            ("machine learning algorithms", "medium_technical"),
            ("neural network architecture", "medium_technical"),
            ("natural language processing", "medium_domain"),

            # Long queries
            ("deep learning neural networks for natural language processing", "long_technical"),
            ("what are the best practices for machine learning model deployment", "long_question"),

            # Specific queries
            ("transformer architecture attention mechanism", "specific_technical"),
            ("supervised vs unsupervised learning", "comparative"),

            # Conceptual queries
            ("how does gradient descent work", "conceptual"),
            ("explain convolutional neural networks", "explanatory")
        ]

        for query, query_type in test_queries:
            result = await self.evaluate_single_query(query, query_type)
            self.results['query_tests'].append(result)

    async def evaluate_single_query(self, query: str, query_type: str) -> Dict[str, Any]:
        """Evaluate a single query with relevance assessment"""
        logger.info(f"\n  Testing query: '{query}' (Type: {query_type})")

        start_time = time.time()

        try:
            # Execute search
            results, metrics = await hybrid_search(query, top_k=5)

            latency = time.time() - start_time

            # Assess relevance (heuristic-based since we don't have ground truth)
            relevance_score = self.assess_relevance(query, results)

            # Calculate diversity
            diversity_score = self.calculate_diversity(results)

            logger.info(f"    Results: {len(results)}, Latency: {latency:.3f}s, Relevance: {relevance_score:.2f}, Diversity: {diversity_score:.2f}")

            return {
                'query': query,
                'query_type': query_type,
                'latency': latency,
                'num_results': len(results),
                'relevance_score': relevance_score,
                'diversity_score': diversity_score,
                'metrics': {
                    'total_time': metrics.get('total_time', latency),
                    'bm25_time': metrics.get('bm25_time', 0),
                    'vector_time': metrics.get('vector_time', 0),
                    'embedding_time': metrics.get('embedding_time', 0),
                    'fusion_time': metrics.get('fusion_time', 0),
                    'rerank_time': metrics.get('rerank_time', 0),
                    'cache_hit': metrics.get('cache_hit', False)
                },
                'top_result': results[0] if results else None,
                'success': True,
                'error': None
            }

        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"    ERROR: {str(e)}")

            return {
                'query': query,
                'query_type': query_type,
                'latency': latency,
                'num_results': 0,
                'relevance_score': 0.0,
                'diversity_score': 0.0,
                'metrics': {},
                'top_result': None,
                'success': False,
                'error': str(e)
            }

    def assess_relevance(self, query: str, results: List[Dict[str, Any]]) -> float:
        """Assess relevance of search results to query (heuristic-based)"""
        if not results:
            return 0.0

        query_terms = set(query.lower().split())
        relevance_scores = []

        for result in results:
            text = result.get('text', '').lower()
            text_terms = set(text.split())

            # Calculate term overlap
            overlap = len(query_terms.intersection(text_terms))
            overlap_ratio = overlap / len(query_terms) if query_terms else 0

            # Consider score
            result_score = result.get('score', 0.0)

            # Combined relevance
            relevance = (overlap_ratio * 0.6 + result_score * 0.4)
            relevance_scores.append(relevance)

        return sum(relevance_scores) / len(relevance_scores)

    def calculate_diversity(self, results: List[Dict[str, Any]]) -> float:
        """Calculate diversity of search results"""
        if len(results) < 2:
            return 1.0

        # Check text diversity
        texts = [r.get('text', '') for r in results]
        unique_texts = len(set(texts))
        text_diversity = unique_texts / len(texts)

        # Check source diversity
        sources = [r.get('source_url', '') for r in results]
        unique_sources = len(set(filter(None, sources)))
        source_diversity = unique_sources / len(results) if results else 0

        return (text_diversity * 0.6 + source_diversity * 0.4)

    async def test_performance(self):
        """Test search performance with latency and throughput measurements"""
        logger.info("\n  Performance Testing:")

        # 1. Single query latency (10 iterations)
        logger.info("\n    1. Single Query Latency Test (10 iterations)...")
        latencies = []
        test_query = "machine learning algorithms"

        # Warm-up
        await hybrid_search(test_query, top_k=5)

        for i in range(10):
            start_time = time.time()
            await hybrid_search(test_query, top_k=5)
            latency = time.time() - start_time
            latencies.append(latency)
            logger.info(f"      Iteration {i+1}: {latency:.3f}s")

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]

        logger.info(f"\n      Average Latency: {avg_latency:.3f}s")
        logger.info(f"      P95 Latency: {p95_latency:.3f}s")
        logger.info(f"      P99 Latency: {p99_latency:.3f}s")

        self.results['performance_tests'].append({
            'test_type': 'single_query_latency',
            'iterations': 10,
            'avg_latency': avg_latency,
            'p95_latency': p95_latency,
            'p99_latency': p99_latency,
            'all_latencies': latencies
        })

        # 2. Concurrent query throughput
        logger.info("\n    2. Concurrent Query Throughput Test (5 concurrent queries)...")
        queries = [
            "AI",
            "machine learning",
            "deep learning",
            "natural language processing",
            "computer vision"
        ]

        start_time = time.time()
        tasks = [hybrid_search(q, top_k=3) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        successful = sum(1 for r in results if not isinstance(r, Exception))
        throughput = len(queries) / total_time

        logger.info(f"      Total Time: {total_time:.3f}s")
        logger.info(f"      Successful Queries: {successful}/{len(queries)}")
        logger.info(f"      Throughput: {throughput:.2f} queries/second")

        self.results['performance_tests'].append({
            'test_type': 'concurrent_throughput',
            'num_queries': len(queries),
            'total_time': total_time,
            'successful_queries': successful,
            'throughput': throughput
        })

        # 3. Cache performance comparison
        logger.info("\n    3. Cache Performance Test...")

        # First execution (cache miss)
        cache_miss_start = time.time()
        await hybrid_search("neural networks", top_k=5)
        cache_miss_time = time.time() - cache_miss_start

        # Second execution (cache hit)
        cache_hit_start = time.time()
        results, metrics = await hybrid_search("neural networks", top_k=5)
        cache_hit_time = time.time() - cache_hit_start

        cache_improvement = ((cache_miss_time - cache_hit_time) / cache_miss_time * 100) if cache_miss_time > 0 else 0

        logger.info(f"      Cache Miss Time: {cache_miss_time:.3f}s")
        logger.info(f"      Cache Hit Time: {cache_hit_time:.3f}s")
        logger.info(f"      Cache Hit: {metrics.get('cache_hit', False)}")
        logger.info(f"      Improvement: {cache_improvement:.1f}%")

        self.results['performance_tests'].append({
            'test_type': 'cache_performance',
            'cache_miss_time': cache_miss_time,
            'cache_hit_time': cache_hit_time,
            'cache_hit_detected': metrics.get('cache_hit', False),
            'improvement_percent': cache_improvement
        })

    async def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        edge_cases = [
            ("", "empty_query"),
            ("   ", "whitespace_only"),
            ("AI & ML", "special_characters"),
            ("artificial intelligence" * 50, "very_long_query"),
            ("xyzabc123nonexistent", "nonexistent_terms"),
            ("a", "single_character"),
            ("123 456 789", "only_numbers"),
            ("?!@#$%", "only_special_chars")
        ]

        for query, case_type in edge_cases:
            logger.info(f"\n  Testing edge case: {case_type}")

            start_time = time.time()
            try:
                results, metrics = await hybrid_search(query, top_k=5)
                latency = time.time() - start_time

                logger.info(f"    Results: {len(results)}, Latency: {latency:.3f}s")

                self.results['edge_case_tests'].append({
                    'case_type': case_type,
                    'query': query[:100],  # Truncate for logging
                    'query_length': len(query),
                    'num_results': len(results),
                    'latency': latency,
                    'success': True,
                    'error': None
                })

            except Exception as e:
                latency = time.time() - start_time
                logger.warning(f"    ERROR: {str(e)}")

                self.results['edge_case_tests'].append({
                    'case_type': case_type,
                    'query': query[:100],
                    'query_length': len(query),
                    'num_results': 0,
                    'latency': latency,
                    'success': False,
                    'error': str(e)
                })

    async def test_error_handling(self):
        """Test error handling and recovery"""
        logger.info("\n  Testing error handling scenarios...")

        # Test 1: Invalid top_k values
        invalid_top_k_values = [0, -1, -10]

        for top_k in invalid_top_k_values:
            try:
                results, metrics = await hybrid_search("test query", top_k=top_k)
                logger.info(f"    top_k={top_k}: Handled gracefully, returned {len(results)} results")

                self.results['error_handling_tests'].append({
                    'test': f'invalid_top_k_{top_k}',
                    'handled': True,
                    'num_results': len(results),
                    'error': None
                })

            except Exception as e:
                logger.info(f"    top_k={top_k}: Exception raised: {type(e).__name__}")

                self.results['error_handling_tests'].append({
                    'test': f'invalid_top_k_{top_k}',
                    'handled': False,
                    'num_results': 0,
                    'error': str(e)
                })

        # Test 2: Timeout simulation (if applicable)
        logger.info("\n    Testing timeout handling...")
        try:
            # Note: Actual timeout testing would require modifying the search engine
            # For now, just verify normal operation doesn't timeout
            start_time = time.time()
            results, metrics = await asyncio.wait_for(
                hybrid_search("test query", top_k=5),
                timeout=30.0  # 30 second timeout
            )
            elapsed = time.time() - start_time

            logger.info(f"    Completed within timeout: {elapsed:.3f}s")

            self.results['error_handling_tests'].append({
                'test': 'timeout_handling',
                'handled': True,
                'elapsed_time': elapsed,
                'error': None
            })

        except asyncio.TimeoutError:
            logger.error("    TIMEOUT EXCEEDED")

            self.results['error_handling_tests'].append({
                'test': 'timeout_handling',
                'handled': False,
                'elapsed_time': 30.0,
                'error': 'TimeoutError'
            })

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        logger.info("\n" + "=" * 80)
        logger.info("EVALUATION REPORT")
        logger.info("=" * 80)

        # 1. Query Pattern Analysis
        logger.info("\n1. QUERY PATTERN ANALYSIS:")
        logger.info("-" * 80)

        query_tests = self.results['query_tests']
        if query_tests:
            successful_queries = [t for t in query_tests if t['success']]

            avg_latency = statistics.mean([t['latency'] for t in successful_queries]) if successful_queries else 0
            avg_relevance = statistics.mean([t['relevance_score'] for t in successful_queries]) if successful_queries else 0
            avg_diversity = statistics.mean([t['diversity_score'] for t in successful_queries]) if successful_queries else 0

            logger.info(f"\n{'Query':<42} {'Type':<20} {'Latency':<10} {'Results':<8} {'Relevance':<10} {'Diversity':<10} {'Success':<8}")
            logger.info("-" * 120)
            for test in query_tests[:10]:  # Show first 10
                logger.info(
                    f"{test['query'][:40]:<42} "
                    f"{test['query_type']:<20} "
                    f"{test['latency']:.3f}s{'':<6} "
                    f"{test['num_results']:<8} "
                    f"{test['relevance_score']:.2f}{'':<8} "
                    f"{test['diversity_score']:.2f}{'':<8} "
                    f"{'✓' if test['success'] else '✗':<8}"
                )

            logger.info(f"\nSummary:")
            logger.info(f"  Total Queries: {len(query_tests)}")
            logger.info(f"  Successful: {len(successful_queries)}")
            logger.info(f"  Average Latency: {avg_latency:.3f}s")
            logger.info(f"  Average Relevance: {avg_relevance:.2f}")
            logger.info(f"  Average Diversity: {avg_diversity:.2f}")

        # 2. Performance Metrics
        logger.info("\n2. PERFORMANCE METRICS:")
        logger.info("-" * 80)

        perf_tests = self.results['performance_tests']
        for test in perf_tests:
            if test['test_type'] == 'single_query_latency':
                logger.info(f"\nSingle Query Latency:")
                logger.info(f"  Average: {test['avg_latency']:.3f}s")
                logger.info(f"  P95: {test['p95_latency']:.3f}s")
                logger.info(f"  P99: {test['p99_latency']:.3f}s")
                logger.info(f"  Target (< 1s avg): {'✓ PASS' if test['avg_latency'] < 1.0 else '✗ FAIL'}")

            elif test['test_type'] == 'concurrent_throughput':
                logger.info(f"\nConcurrent Throughput:")
                logger.info(f"  Queries: {test['num_queries']}")
                logger.info(f"  Total Time: {test['total_time']:.3f}s")
                logger.info(f"  Throughput: {test['throughput']:.2f} queries/sec")
                logger.info(f"  Success Rate: {test['successful_queries']}/{test['num_queries']}")

            elif test['test_type'] == 'cache_performance':
                logger.info(f"\nCache Performance:")
                logger.info(f"  Cache Miss: {test['cache_miss_time']:.3f}s")
                logger.info(f"  Cache Hit: {test['cache_hit_time']:.3f}s")
                logger.info(f"  Improvement: {test['improvement_percent']:.1f}%")

        # 3. Edge Cases
        logger.info("\n3. EDGE CASE HANDLING:")
        logger.info("-" * 80)

        edge_tests = self.results['edge_case_tests']
        logger.info(f"\n{'Case Type':<30} {'Query Length':<15} {'Results':<10} {'Latency':<10} {'Success':<8}")
        logger.info("-" * 80)
        for test in edge_tests:
            logger.info(
                f"{test['case_type']:<30} "
                f"{test['query_length']:<15} "
                f"{test['num_results']:<10} "
                f"{test['latency']:.3f}s{'':<6} "
                f"{'✓' if test['success'] else '✗':<8}"
            )

        # 4. Error Handling
        logger.info("\n4. ERROR HANDLING:")
        logger.info("-" * 80)

        error_tests = self.results['error_handling_tests']
        for test in error_tests:
            logger.info(f"\n  {test['test']}:")
            logger.info(f"    Handled: {'✓' if test['handled'] else '✗'}")
            if test['error']:
                logger.info(f"    Error: {test['error']}")

        # 5. Production Readiness Score
        logger.info("\n5. PRODUCTION READINESS ASSESSMENT:")
        logger.info("-" * 80)

        score = self.calculate_production_readiness_score()
        logger.info(f"\nOverall Score: {score}/100")
        logger.info(f"Rating: {self.get_rating(score)}")

        # 6. Recommendations
        logger.info("\n6. RECOMMENDATIONS:")
        logger.info("-" * 80)

        recommendations = self.generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"\n  {i}. {rec}")

        # Prepare final report
        report = {
            'evaluation_id': f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.test_start_time).total_seconds(),
            'query_tests': self.results['query_tests'],
            'performance_tests': self.results['performance_tests'],
            'edge_case_tests': self.results['edge_case_tests'],
            'error_handling_tests': self.results['error_handling_tests'],
            'production_readiness_score': score,
            'recommendations': recommendations
        }

        # Save report
        report_file = f"search_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"\n\nReport saved to: {report_file}")

        return report

    def calculate_production_readiness_score(self) -> int:
        """Calculate production readiness score (0-100)"""
        score = 0
        max_score = 100

        # Query success rate (30 points)
        query_tests = self.results['query_tests']
        if query_tests:
            success_rate = sum(1 for t in query_tests if t['success']) / len(query_tests)
            score += int(success_rate * 30)

        # Average latency (20 points)
        perf_tests = self.results['performance_tests']
        latency_test = next((t for t in perf_tests if t['test_type'] == 'single_query_latency'), None)
        if latency_test:
            avg_latency = latency_test['avg_latency']
            if avg_latency < 0.5:
                score += 20
            elif avg_latency < 1.0:
                score += 15
            elif avg_latency < 2.0:
                score += 10
            else:
                score += 5

        # Average relevance (25 points)
        if query_tests:
            successful = [t for t in query_tests if t['success']]
            if successful:
                avg_relevance = statistics.mean([t['relevance_score'] for t in successful])
                score += int(avg_relevance * 25)

        # Edge case handling (15 points)
        edge_tests = self.results['edge_case_tests']
        if edge_tests:
            success_rate = sum(1 for t in edge_tests if t['success']) / len(edge_tests)
            score += int(success_rate * 15)

        # Error handling (10 points)
        error_tests = self.results['error_handling_tests']
        if error_tests:
            handled_rate = sum(1 for t in error_tests if t['handled']) / len(error_tests)
            score += int(handled_rate * 10)

        return min(score, max_score)

    def get_rating(self, score: int) -> str:
        """Get rating based on score"""
        if score >= 90:
            return "EXCELLENT - Production Ready"
        elif score >= 80:
            return "GOOD - Minor improvements recommended"
        elif score >= 70:
            return "FAIR - Significant improvements needed"
        else:
            return "POOR - Major issues must be addressed"

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on evaluation results"""
        recommendations = []

        # Check latency
        perf_tests = self.results['performance_tests']
        latency_test = next((t for t in perf_tests if t['test_type'] == 'single_query_latency'), None)
        if latency_test and latency_test['avg_latency'] > 1.0:
            recommendations.append(
                f"Improve search latency (current avg: {latency_test['avg_latency']:.3f}s, target: < 1s). "
                "Consider optimizing database queries or adding more caching."
            )

        # Check relevance
        query_tests = self.results['query_tests']
        if query_tests:
            successful = [t for t in query_tests if t['success']]
            if successful:
                avg_relevance = statistics.mean([t['relevance_score'] for t in successful])
                if avg_relevance < 0.7:
                    recommendations.append(
                        f"Improve search relevance (current avg: {avg_relevance:.2f}, target: > 0.7). "
                        "Consider adjusting BM25/vector weights or improving reranking."
                    )

        # Check diversity
        if query_tests and successful:
            avg_diversity = statistics.mean([t['diversity_score'] for t in successful])
            if avg_diversity < 0.6:
                recommendations.append(
                    f"Improve result diversity (current avg: {avg_diversity:.2f}, target: > 0.6). "
                    "Consider implementing diversity-based reranking."
                )

        # Check edge cases
        edge_tests = self.results['edge_case_tests']
        failed_edge_cases = [t for t in edge_tests if not t['success']]
        if failed_edge_cases:
            recommendations.append(
                f"Fix edge case handling ({len(failed_edge_cases)} failures). "
                "Add input validation and graceful degradation for edge cases."
            )

        # Check cache effectiveness
        cache_test = next((t for t in perf_tests if t['test_type'] == 'cache_performance'), None)
        if cache_test and cache_test.get('improvement_percent', 0) < 20:
            recommendations.append(
                "Improve cache effectiveness (current improvement < 20%). "
                "Review cache key generation and TTL settings."
            )

        if not recommendations:
            recommendations.append("System is performing well. Continue monitoring and gradual optimization.")

        return recommendations


async def main():
    """Main evaluation entry point"""
    evaluator = SearchQualityEvaluator()
    report = await evaluator.run_full_evaluation()

    return report


if __name__ == "__main__":
    # Run evaluation
    report = asyncio.run(main())

    print("\n" + "=" * 80)
    print("Evaluation Complete!")
    print("=" * 80)
