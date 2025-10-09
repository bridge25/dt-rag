"""
Hybrid Search Engine Demo for DT-RAG v1.8.1

This demo script shows how to use the hybrid search engine with various features:
- Basic hybrid search (BM25 + Vector)
- Individual BM25 keyword search
- Individual Vector similarity search
- Configuration management
- Performance monitoring
- Caching demonstration

Run this script to see the hybrid search engine in action.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_basic_hybrid_search():
    """Demonstrate basic hybrid search functionality"""
    print("\n🔍 HYBRID SEARCH DEMO")
    print("=" * 50)

    try:
        from apps.search.hybrid_search_engine import hybrid_search

        # Test queries with different characteristics
        test_queries = [
            "machine learning algorithms",
            "neural network architecture",
            "what is artificial intelligence?",
            "deep learning vs traditional ML"
        ]

        print("Testing hybrid search with various queries...\n")

        for i, query in enumerate(test_queries, 1):
            print(f"Query {i}: '{query}'")

            try:
                # Perform hybrid search
                results, metrics = await hybrid_search(query, top_k=3)

                print(f"  ⚡ Results: {len(results)} found in {metrics['total_time']:.3f}s")

                if results:
                    print(f"  📄 Top result: {results[0]['text'][:100]}...")
                    print(f"      Score: {results[0]['score']:.3f}")
                    print(f"      BM25: {results[0]['metadata']['bm25_score']:.3f}, "
                          f"Vector: {results[0]['metadata']['vector_score']:.3f}")
                else:
                    print("  📄 No results found")

                # Show performance breakdown
                if 'candidates_found' in metrics:
                    candidates = metrics['candidates_found']
                    print(f"  📊 Candidates: BM25={candidates.get('bm25', 0)}, "
                          f"Vector={candidates.get('vector', 0)}")

            except Exception as e:
                print(f"  ❌ Search failed: {e}")

            print()

    except ImportError:
        print("❌ Hybrid search engine not available. Using mock demo.")
        await demo_mock_search()


async def demo_individual_search_methods():
    """Demonstrate individual search methods"""
    print("\n🔎 INDIVIDUAL SEARCH METHODS DEMO")
    print("=" * 50)

    try:
        from apps.search.hybrid_search_engine import keyword_search, vector_search

        query = "machine learning neural networks"
        print(f"Comparing search methods for: '{query}'\n")

        # BM25 keyword search
        print("1. BM25 Keyword Search:")
        try:
            results, metrics = await keyword_search(query, top_k=3)
            print(f"   Found {len(results)} results in {metrics['total_time']:.3f}s")
            if results:
                print(f"   Top result score: {results[0]['score']:.3f}")
        except Exception as e:
            print(f"   Failed: {e}")

        # Vector similarity search
        print("\n2. Vector Similarity Search:")
        try:
            results, metrics = await vector_search(query, top_k=3)
            print(f"   Found {len(results)} results in {metrics['total_time']:.3f}s")
            if results:
                print(f"   Top result score: {results[0]['score']:.3f}")
        except Exception as e:
            print(f"   Failed: {e}")

    except ImportError:
        print("❌ Individual search methods not available")


async def demo_configuration_management():
    """Demonstrate search configuration management"""
    print("\n⚙️ CONFIGURATION MANAGEMENT DEMO")
    print("=" * 50)

    try:
        from apps.search.hybrid_search_engine import (
            get_search_engine_config,
            update_search_engine_config
        )

        # Get current configuration
        print("Current search engine configuration:")
        config = get_search_engine_config()
        for key, value in config.items():
            if key != "cache_stats":  # Skip complex nested data
                print(f"  {key}: {value}")

        # Update configuration
        print("\nUpdating BM25 weight to 0.7, Vector weight to 0.3...")
        update_search_engine_config(bm25_weight=0.7, vector_weight=0.3)

        # Verify update
        new_config = get_search_engine_config()
        print(f"  New BM25 weight: {new_config.get('bm25_weight', 'N/A')}")
        print(f"  New Vector weight: {new_config.get('vector_weight', 'N/A')}")

        # Reset to balanced configuration
        print("\nResetting to balanced configuration...")
        update_search_engine_config(bm25_weight=0.5, vector_weight=0.5)

    except ImportError:
        print("❌ Configuration management not available")


async def demo_performance_monitoring():
    """Demonstrate performance monitoring"""
    print("\n📊 PERFORMANCE MONITORING DEMO")
    print("=" * 50)

    try:
        from apps.search.hybrid_search_engine import get_search_statistics, hybrid_search

        # Run some searches to generate metrics
        print("Running searches to generate performance data...")
        test_queries = ["AI", "ML", "data science"]

        for query in test_queries:
            try:
                await hybrid_search(query, top_k=5)
            except:
                pass  # Ignore errors for demo

        # Get statistics
        stats = await get_search_statistics()

        print("\nSearch Engine Statistics:")
        print(f"  Engine Status: {stats.get('engine_config', {}).get('search_engine_status', 'unknown')}")

        # Database statistics
        db_stats = stats.get('database_stats', {}).get('statistics', {})
        print(f"  Total Documents: {db_stats.get('total_docs', 0)}")
        print(f"  Total Chunks: {db_stats.get('total_chunks', 0)}")
        print(f"  Embedded Chunks: {db_stats.get('embedded_chunks', 0)}")

        # Performance metrics
        perf_metrics = stats.get('performance_metrics', {})
        if perf_metrics:
            print(f"  Average Latency: {perf_metrics.get('avg_latency', 0):.3f}s")
            print(f"  Total Searches: {perf_metrics.get('total_searches', 0)}")
            print(f"  Error Rate: {perf_metrics.get('error_rate', 0):.1%}")

    except ImportError:
        print("❌ Performance monitoring not available")


async def demo_caching():
    """Demonstrate search result caching"""
    print("\n🗄️ CACHING DEMONSTRATION")
    print("=" * 50)

    try:
        from apps.search.hybrid_search_engine import hybrid_search, clear_search_cache

        query = "machine learning algorithms"
        print(f"Testing cache with query: '{query}'")

        # First search (cache miss)
        print("\n1. First search (should be cache miss):")
        results1, metrics1 = await hybrid_search(query, top_k=3)
        print(f"   Latency: {metrics1['total_time']:.3f}s")
        print(f"   Cache hit: {metrics1.get('cache_hit', False)}")

        # Second search (cache hit)
        print("\n2. Second search (should be cache hit):")
        results2, metrics2 = await hybrid_search(query, top_k=3)
        print(f"   Latency: {metrics2['total_time']:.3f}s")
        print(f"   Cache hit: {metrics2.get('cache_hit', False)}")

        # Clear cache
        print("\n3. Clearing cache and searching again:")
        clear_search_cache()
        results3, metrics3 = await hybrid_search(query, top_k=3)
        print(f"   Latency: {metrics3['total_time']:.3f}s")
        print(f"   Cache hit: {metrics3.get('cache_hit', False)}")

        # Compare results consistency
        if results1 and results2:
            consistent = results1[0]['chunk_id'] == results2[0]['chunk_id']
            print(f"\n   Cache consistency: {'✅' if consistent else '❌'}")

    except ImportError:
        print("❌ Caching demonstration not available")


async def demo_mock_search():
    """Mock search demo when real engine not available"""
    print("Running mock search demo...")

    # Simulate search results
    mock_results = [
        {
            "chunk_id": "mock_chunk_1",
            "text": "Machine learning is a method of data analysis that automates analytical model building.",
            "title": "Introduction to ML",
            "source_url": "https://example.com/ml-intro",
            "score": 0.89,
            "taxonomy_path": ["AI", "Machine Learning"],
            "metadata": {"bm25_score": 0.85, "vector_score": 0.93}
        },
        {
            "chunk_id": "mock_chunk_2",
            "text": "Neural networks are computing systems vaguely inspired by biological neural networks.",
            "title": "Neural Networks Overview",
            "source_url": "https://example.com/nn-overview",
            "score": 0.76,
            "taxonomy_path": ["AI", "Deep Learning"],
            "metadata": {"bm25_score": 0.72, "vector_score": 0.80}
        }
    ]

    mock_metrics = {
        "total_time": 0.045,
        "candidates_found": {"bm25": 15, "vector": 12},
        "cache_hit": False
    }

    print(f"Mock search completed:")
    print(f"  Results: {len(mock_results)}")
    print(f"  Latency: {mock_metrics['total_time']:.3f}s")
    print(f"  Top result: {mock_results[0]['text'][:50]}...")


async def run_comprehensive_demo():
    """Run comprehensive demo of all features"""
    print("🚀 DT-RAG HYBRID SEARCH ENGINE DEMO")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all demo sections
    await demo_basic_hybrid_search()
    await demo_individual_search_methods()
    await demo_configuration_management()
    await demo_performance_monitoring()
    await demo_caching()

    print("\n✅ Demo completed successfully!")
    print("=" * 60)


async def run_quick_benchmark():
    """Run a quick benchmark to show performance"""
    print("\n🏃‍♂️ QUICK PERFORMANCE BENCHMARK")
    print("=" * 50)

    try:
        from apps.search.search_benchmark import SearchBenchmark

        benchmark = SearchBenchmark()

        # Run a small benchmark
        queries = ["AI", "machine learning", "neural networks"]
        print(f"Running benchmark with {len(queries)} queries...")

        start_time = asyncio.get_event_loop().time()

        # Test each query
        results = []
        for query in queries:
            result = await benchmark.run_single_search(query, "hybrid", top_k=5)
            results.append(result)
            print(f"  '{query}': {result.latency_ms:.1f}ms, {result.result_count} results")

        # Calculate summary
        total_time = asyncio.get_event_loop().time() - start_time
        avg_latency = sum(r.latency_ms for r in results) / len(results)
        success_rate = sum(1 for r in results if r.error is None) / len(results)

        print(f"\nBenchmark Results:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average latency: {avg_latency:.1f}ms")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Target compliance: {'✅' if avg_latency < 1000 else '❌'} (target: <1000ms)")

    except ImportError:
        print("❌ Benchmark not available - search engine components not found")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hybrid Search Engine Demo")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    parser.add_argument("--quick", action="store_true", help="Run quick demo only")

    args = parser.parse_args()

    async def main():
        if args.benchmark:
            await run_quick_benchmark()
        elif args.quick:
            await demo_basic_hybrid_search()
        else:
            await run_comprehensive_demo()

    # Run the demo
    asyncio.run(main())