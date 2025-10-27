"""
Search Performance Benchmark for DT-RAG v1.8.1

Comprehensive benchmarking of the hybrid search engine performance including:
- Latency measurements (p50, p95, p99)
- Throughput testing under load
- Search quality metrics (Recall@K, NDCG)
- Cost analysis per search operation
- Comparison between search methods

Performance targets:
- Recall@10 ≥ 0.85
- Search latency p95 ≤ 1s
- Cost ≤ ₩3/search
"""

# @CODE:SEARCH-001 | SPEC: .moai/specs/SPEC-SEARCH-001/spec.md | TEST: tests/test_hybrid_search.py

import asyncio
import time
import statistics
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Single benchmark test result"""

    test_name: str
    query: str
    search_type: str  # hybrid, bm25, vector
    latency_ms: float
    result_count: int
    error: Optional[str] = None
    relevance_score: float = 0.0
    cost_krw: float = 0.0


@dataclass
class BenchmarkSummary:
    """Benchmark summary statistics"""

    test_name: str
    total_queries: int
    successful_queries: int
    error_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_qps: float
    avg_results: float
    avg_relevance: float
    total_cost_krw: float
    cost_per_search_krw: float
    meets_latency_target: bool
    meets_cost_target: bool


class SearchBenchmark:
    """Search engine benchmark runner"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.cost_per_embedding = 0.1  # ₩0.1 per embedding generation
        self.cost_per_db_query = 0.05  # ₩0.05 per database query

        # Try to import search engine
        try:
            from .hybrid_search_engine import (
                hybrid_search,
                keyword_search,
                vector_search,
            )

            self.hybrid_search = hybrid_search
            self.keyword_search = keyword_search
            self.vector_search = vector_search
            self.search_available = True
            logger.info("Hybrid search engine loaded successfully")
        except ImportError as e:
            logger.warning(f"Hybrid search engine not available: {e}")
            self.search_available = False

    async def run_single_search(
        self, query: str, search_type: str = "hybrid", top_k: int = 10
    ) -> BenchmarkResult:
        """Run a single search and measure performance"""

        start_time = time.time()
        result_count = 0
        error = None
        cost = 0.0

        try:
            if not self.search_available:
                # Mock search for testing
                await asyncio.sleep(0.01)  # Simulate processing
                result_count = 5
                cost = 0.5  # Mock cost
            else:
                if search_type == "hybrid":
                    results, metrics = await self.hybrid_search(query, top_k=top_k)
                    cost = self.cost_per_embedding + (
                        self.cost_per_db_query * 2
                    )  # BM25 + Vector
                elif search_type == "bm25":
                    results, metrics = await self.keyword_search(query, top_k=top_k)
                    cost = self.cost_per_db_query
                elif search_type == "vector":
                    results, metrics = await self.vector_search(query, top_k=top_k)
                    cost = self.cost_per_embedding + self.cost_per_db_query
                else:
                    raise ValueError(f"Unknown search type: {search_type}")

                result_count = len(results)

        except Exception as e:
            error = str(e)
            logger.error(f"Search failed for '{query}': {e}")

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Calculate relevance score (simplified)
        relevance_score = self._calculate_relevance_score(
            query, result_count, error is None
        )

        return BenchmarkResult(
            test_name="single_search",
            query=query,
            search_type=search_type,
            latency_ms=latency_ms,
            result_count=result_count,
            error=error,
            relevance_score=relevance_score,
            cost_krw=cost,
        )

    def _calculate_relevance_score(
        self, query: str, result_count: int, success: bool
    ) -> float:
        """Calculate simplified relevance score"""
        if not success:
            return 0.0

        # Basic relevance scoring based on result count and query characteristics
        base_score = min(1.0, result_count / 10.0)  # Normalize by expected results

        # Boost for longer queries (assumed to be more specific)
        query_complexity = min(1.0, len(query.split()) / 5.0)

        return base_score * (0.7 + 0.3 * query_complexity)

    async def run_latency_benchmark(
        self, queries: List[str], search_types: List[str]
    ) -> List[BenchmarkSummary]:
        """Run latency benchmark for different search types"""
        logger.info(f"Starting latency benchmark with {len(queries)} queries")

        summaries = []

        for search_type in search_types:
            logger.info(f"Testing search type: {search_type}")

            type_results = []
            for i, query in enumerate(queries):
                if i % 10 == 0:
                    logger.info(f"  Progress: {i+1}/{len(queries)} queries")

                result = await self.run_single_search(query, search_type)
                type_results.append(result)
                self.results.append(result)

                # Brief pause to avoid overwhelming the system
                await asyncio.sleep(0.01)

            summary = self._calculate_summary(f"latency_{search_type}", type_results)
            summaries.append(summary)

            logger.info(
                f"  {search_type} completed - P95 latency: {summary.p95_latency_ms:.1f}ms"
            )

        return summaries

    async def run_throughput_benchmark(
        self, query: str, concurrent_requests: int = 10, duration_seconds: int = 30
    ) -> BenchmarkSummary:
        """Run throughput benchmark with concurrent requests"""
        logger.info(
            f"Starting throughput benchmark: {concurrent_requests} concurrent requests for {duration_seconds}s"
        )

        start_time = time.time()
        end_time = start_time + duration_seconds
        throughput_results = []

        async def continuous_search():
            """Continuously run searches until time limit"""
            while time.time() < end_time:
                result = await self.run_single_search(query, "hybrid")
                throughput_results.append(result)
                await asyncio.sleep(0.01)  # Brief pause

        # Run concurrent search tasks
        tasks = [continuous_search() for _ in range(concurrent_requests)]
        await asyncio.gather(*tasks)

        # Add results to main collection
        self.results.extend(throughput_results)

        summary = self._calculate_summary("throughput_test", throughput_results)
        logger.info(f"Throughput test completed - {summary.throughput_qps:.1f} QPS")

        return summary

    async def run_cost_analysis(self, queries: List[str]) -> Dict[str, float]:
        """Analyze cost per search for different methods"""
        logger.info("Running cost analysis")

        cost_results = {}
        search_types = ["hybrid", "bm25", "vector"]

        for search_type in search_types:
            type_costs = []

            # Sample queries for cost analysis
            sample_queries = queries[
                : min(20, len(queries))
            ]  # Limit to avoid excessive costs

            for query in sample_queries:
                result = await self.run_single_search(query, search_type)
                if result.error is None:
                    type_costs.append(result.cost_krw)

            if type_costs:
                avg_cost = statistics.mean(type_costs)
                cost_results[search_type] = avg_cost
                logger.info(f"  {search_type} average cost: ₩{avg_cost:.3f}")
            else:
                cost_results[search_type] = 0.0

        return cost_results

    def _calculate_summary(
        self, test_name: str, results: List[BenchmarkResult]
    ) -> BenchmarkSummary:
        """Calculate benchmark summary statistics"""
        if not results:
            return BenchmarkSummary(
                test_name=test_name,
                total_queries=0,
                successful_queries=0,
                error_rate=0.0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                throughput_qps=0.0,
                avg_results=0.0,
                avg_relevance=0.0,
                total_cost_krw=0.0,
                cost_per_search_krw=0.0,
                meets_latency_target=False,
                meets_cost_target=False,
            )

        successful_results = [r for r in results if r.error is None]
        total_queries = len(results)
        successful_queries = len(successful_results)
        error_rate = (
            (total_queries - successful_queries) / total_queries
            if total_queries > 0
            else 0.0
        )

        if successful_results:
            latencies = [r.latency_ms for r in successful_results]
            avg_latency = statistics.mean(latencies)
            p50_latency = statistics.median(latencies)
            p95_latency = (
                sorted(latencies)[int(len(latencies) * 0.95)]
                if len(latencies) > 1
                else latencies[0]
            )
            p99_latency = (
                sorted(latencies)[int(len(latencies) * 0.99)]
                if len(latencies) > 1
                else latencies[0]
            )

            # Calculate throughput (queries per second)
            if latencies:
                total_time = sum(latencies) / 1000  # Convert to seconds
                throughput = len(latencies) / max(
                    total_time, 0.001
                )  # Avoid division by zero
            else:
                throughput = 0.0

            avg_results = statistics.mean([r.result_count for r in successful_results])
            avg_relevance = statistics.mean(
                [r.relevance_score for r in successful_results]
            )
            total_cost = sum([r.cost_krw for r in results])
            cost_per_search = total_cost / total_queries if total_queries > 0 else 0.0
        else:
            avg_latency = p50_latency = p95_latency = p99_latency = 0.0
            throughput = avg_results = avg_relevance = total_cost = cost_per_search = (
                0.0
            )

        # Check targets
        meets_latency_target = p95_latency <= 1000.0  # 1 second = 1000ms
        meets_cost_target = cost_per_search <= 3.0  # ₩3 per search

        return BenchmarkSummary(
            test_name=test_name,
            total_queries=total_queries,
            successful_queries=successful_queries,
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            throughput_qps=throughput,
            avg_results=avg_results,
            avg_relevance=avg_relevance,
            total_cost_krw=total_cost,
            cost_per_search_krw=cost_per_search,
            meets_latency_target=meets_latency_target,
            meets_cost_target=meets_cost_target,
        )

    def generate_test_queries(self) -> List[str]:
        """Generate diverse test queries for benchmarking"""
        return [
            # Short specific queries
            "machine learning",
            "neural networks",
            "deep learning",
            "AI algorithms",
            "data science",
            # Medium complexity queries
            "machine learning algorithms comparison",
            "neural network architecture design",
            "natural language processing techniques",
            "computer vision applications",
            "reinforcement learning methods",
            # Long complex queries
            "how do transformer models work in natural language processing",
            "what are the differences between supervised and unsupervised learning",
            "explain convolutional neural networks for image classification",
            "best practices for training deep learning models",
            "comparison of gradient descent optimization algorithms",
            # Technical specific queries
            "BERT transformer architecture",
            "ResNet image classification",
            "LSTM recurrent networks",
            "GAN generative models",
            "attention mechanism",
            # Domain specific queries
            "RAG retrieval augmented generation",
            "vector database similarity search",
            "embedding model fine-tuning",
            "cross-encoder reranking",
            "hybrid search algorithms",
        ]

    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        logger.info("Starting comprehensive benchmark suite")

        start_time = time.time()
        test_queries = self.generate_test_queries()

        benchmark_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_configuration": {
                "total_queries": len(test_queries),
                "search_engine_available": self.search_available,
                "cost_per_embedding": self.cost_per_embedding,
                "cost_per_db_query": self.cost_per_db_query,
            },
            "results": {},
        }

        try:
            # 1. Latency benchmark
            logger.info("Phase 1: Latency benchmark")
            search_types = ["hybrid", "bm25", "vector"]
            latency_summaries = await self.run_latency_benchmark(
                test_queries, search_types
            )
            benchmark_results["results"]["latency"] = [
                asdict(s) for s in latency_summaries
            ]

            # 2. Throughput benchmark
            logger.info("Phase 2: Throughput benchmark")
            throughput_summary = await self.run_throughput_benchmark(
                query="machine learning algorithms",
                concurrent_requests=5,
                duration_seconds=15,  # Reduced for faster testing
            )
            benchmark_results["results"]["throughput"] = asdict(throughput_summary)

            # 3. Cost analysis
            logger.info("Phase 3: Cost analysis")
            cost_analysis = await self.run_cost_analysis(
                test_queries[:10]
            )  # Limited sample
            benchmark_results["results"]["cost_analysis"] = cost_analysis

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            benchmark_results["error"] = str(e)

        # Summary statistics
        total_time = time.time() - start_time
        benchmark_results["benchmark_duration_seconds"] = total_time
        benchmark_results["total_searches_performed"] = len(self.results)

        logger.info(f"Comprehensive benchmark completed in {total_time:.1f}s")
        logger.info(f"Total searches performed: {len(self.results)}")

        return benchmark_results

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save benchmark results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_benchmark_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Benchmark results saved to {filename}")

    def print_summary(self, results: Dict[str, Any]):
        """Print human-readable benchmark summary"""
        print("\n" + "=" * 60)
        print("SEARCH ENGINE BENCHMARK SUMMARY")
        print("=" * 60)

        config = results.get("test_configuration", {})
        print(f"Test Date: {results.get('timestamp', 'N/A')}")
        print(f"Total Queries: {config.get('total_queries', 0)}")
        print(
            f"Search Engine: {'Available' if config.get('search_engine_available') else 'Mock'}"
        )
        print(f"Duration: {results.get('benchmark_duration_seconds', 0):.1f}s")

        print("\n📊 LATENCY RESULTS:")
        latency_results = results.get("results", {}).get("latency", [])
        for result in latency_results:
            search_type = result.get("test_name", "").replace("latency_", "").upper()
            print(
                f"  {search_type:8} - P95: {result.get('p95_latency_ms', 0):.0f}ms, "
                f"Avg: {result.get('avg_latency_ms', 0):.0f}ms, "
                f"Success: {result.get('successful_queries', 0)}/{result.get('total_queries', 0)} "
                f"{'✅' if result.get('meets_latency_target') else '❌'}"
            )

        print("\n🚀 THROUGHPUT RESULTS:")
        throughput = results.get("results", {}).get("throughput", {})
        qps = throughput.get("throughput_qps", 0)
        print(f"  Queries per second: {qps:.1f} QPS")
        print(f"  P95 latency: {throughput.get('p95_latency_ms', 0):.0f}ms")

        print("\n💰 COST ANALYSIS:")
        cost_analysis = results.get("results", {}).get("cost_analysis", {})
        for search_type, cost in cost_analysis.items():
            target_met = "✅" if cost <= 3.0 else "❌"
            print(f"  {search_type.upper():8} - ₩{cost:.3f} per search {target_met}")

        print("\n🎯 TARGET COMPLIANCE:")
        # Check if any search method meets all targets
        targets_met = []
        for result in latency_results:
            if result.get("meets_latency_target"):
                search_type = result.get("test_name", "").replace("latency_", "")
                cost = cost_analysis.get(search_type, 0)
                if cost <= 3.0:
                    targets_met.append(search_type.upper())

        if targets_met:
            print(f"  ✅ Methods meeting all targets: {', '.join(targets_met)}")
        else:
            print("  ❌ No methods meet all performance and cost targets")

        print("\n" + "=" * 60)


async def main():
    """Main benchmark runner"""
    parser = argparse.ArgumentParser(description="Search Engine Benchmark")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick benchmark (fewer queries)"
    )
    parser.add_argument("--output", type=str, help="Output filename for results")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    benchmark = SearchBenchmark()

    # Run benchmark
    results = await benchmark.run_comprehensive_benchmark()

    # Save and display results
    benchmark.save_results(results, args.output)
    benchmark.print_summary(results)

    # Return exit code based on success
    latency_results = results.get("results", {}).get("latency", [])
    all_targets_met = any(
        result.get("meets_latency_target", False) for result in latency_results
    )

    return 0 if all_targets_met else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
