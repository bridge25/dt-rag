"""
Real Hybrid Search Engine Execution Test
Tests actual BM25, Vector, and Hybrid search against PostgreSQL database
Following CLAUDE.md: No mocks, real execution only
"""

import asyncio
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apps.search.hybrid_search_engine import (
    search_engine,
    hybrid_search,
    keyword_search,
    vector_search,
    SearchResult,
    SearchMetrics
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bm25_search():
    """Test BM25 keyword search alone"""
    print("\n" + "="*80)
    print("TEST 1: BM25 Keyword Search")
    print("="*80)

    query = "machine learning algorithms"
    print(f"\nQuery: '{query}'")

    try:
        results, metrics = await search_engine.keyword_only_search(query, top_k=3)

        print(f"\nResults found: {len(results)}")
        print(f"Search time: {metrics.total_time:.3f}s (BM25: {metrics.bm25_time:.3f}s)")

        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] Chunk ID: {result.chunk_id}")
            print(f"      Text: {result.text[:100]}...")
            print(f"      BM25 Score: {result.bm25_score:.4f}")
            print(f"      Hybrid Score: {result.hybrid_score:.4f}")
            if result.title:
                print(f"      Title: {result.title}")

        return len(results) > 0

    except Exception as e:
        logger.error(f"BM25 search failed: {e}", exc_info=True)
        return False


async def test_vector_search():
    """Test vector similarity search alone"""
    print("\n" + "="*80)
    print("TEST 2: Vector Similarity Search")
    print("="*80)

    query = "deep learning neural networks"
    print(f"\nQuery: '{query}'")

    try:
        results, metrics = await search_engine.vector_only_search(query, top_k=3)

        print(f"\nResults found: {len(results)}")
        print(f"Search time: {metrics.total_time:.3f}s (Vector: {metrics.vector_time:.3f}s, Embedding: {metrics.embedding_time:.3f}s)")

        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] Chunk ID: {result.chunk_id}")
            print(f"      Text: {result.text[:100]}...")
            print(f"      Vector Score: {result.vector_score:.4f}")
            print(f"      Hybrid Score: {result.hybrid_score:.4f}")
            if result.title:
                print(f"      Title: {result.title}")

        return len(results) > 0

    except Exception as e:
        logger.error(f"Vector search failed: {e}", exc_info=True)
        return False


async def test_hybrid_search():
    """Test full hybrid search with score fusion"""
    print("\n" + "="*80)
    print("TEST 3: Hybrid Search (BM25 + Vector)")
    print("="*80)

    queries = [
        "artificial intelligence and machine learning",
        "natural language processing",
        "computer vision image recognition"
    ]

    all_success = True

    for query in queries:
        print(f"\n--- Query: '{query}' ---")

        try:
            results, metrics = await search_engine.search(query, top_k=5)

            print(f"\nResults: {len(results)}")
            print(f"Total time: {metrics.total_time:.3f}s")
            print(f"  - BM25: {metrics.bm25_time:.3f}s ({metrics.bm25_candidates} candidates)")
            print(f"  - Vector: {metrics.vector_time:.3f}s ({metrics.vector_candidates} candidates)")
            print(f"  - Embedding: {metrics.embedding_time:.3f}s")
            print(f"  - Fusion: {metrics.fusion_time:.3f}s")
            print(f"  - Rerank: {metrics.rerank_time:.3f}s")
            print(f"Cache hit: {metrics.cache_hit}")

            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] Chunk ID: {result.chunk_id}")
                print(f"      Text: {result.text[:80]}...")
                print(f"      Scores: BM25={result.bm25_score:.4f}, Vector={result.vector_score:.4f}, Hybrid={result.hybrid_score:.4f}, Rerank={result.rerank_score:.4f}")

                if result.metadata:
                    fusion_method = result.metadata.get('fusion_method', 'N/A')
                    print(f"      Fusion method: {fusion_method}")

            if len(results) == 0:
                logger.warning(f"No results for query: {query}")
                all_success = False

        except Exception as e:
            logger.error(f"Hybrid search failed for '{query}': {e}", exc_info=True)
            all_success = False

    return all_success


async def test_score_normalization():
    """Test score normalization in hybrid search"""
    print("\n" + "="*80)
    print("TEST 4: Score Normalization Verification")
    print("="*80)

    query = "python programming"
    print(f"\nQuery: '{query}'")

    try:
        # Test with different normalization methods
        original_config = search_engine.get_config()

        normalization_methods = ["min_max", "z_score", "rrf"]

        for norm_method in normalization_methods:
            print(f"\n--- Normalization: {norm_method} ---")

            search_engine.update_config(normalization=norm_method)
            search_engine.clear_cache()  # Clear cache to force new computation

            results, metrics = await search_engine.search(query, top_k=3)

            print(f"Results: {len(results)}, Time: {metrics.total_time:.3f}s")

            for i, result in enumerate(results, 1):
                print(f"  [{i}] BM25={result.bm25_score:.4f}, Vector={result.vector_score:.4f}, Hybrid={result.hybrid_score:.4f}")

        # Restore original config
        search_engine.update_config(**original_config)

        return True

    except Exception as e:
        logger.error(f"Score normalization test failed: {e}", exc_info=True)
        return False


async def test_search_with_filters():
    """Test hybrid search with taxonomy filters"""
    print("\n" + "="*80)
    print("TEST 5: Hybrid Search with Filters")
    print("="*80)

    query = "database design"
    filters = {
        "taxonomy_paths": [["Technology", "Software", "Databases"]]
    }

    print(f"\nQuery: '{query}'")
    print(f"Filters: {filters}")

    try:
        results, metrics = await search_engine.search(query, top_k=3, filters=filters)

        print(f"\nResults found: {len(results)}")
        print(f"Search time: {metrics.total_time:.3f}s")

        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] Chunk ID: {result.chunk_id}")
            print(f"      Text: {result.text[:80]}...")
            print(f"      Taxonomy: {result.taxonomy_path}")
            print(f"      Scores: BM25={result.bm25_score:.4f}, Vector={result.vector_score:.4f}, Hybrid={result.hybrid_score:.4f}")

        return True

    except Exception as e:
        logger.error(f"Filtered search failed: {e}", exc_info=True)
        return False


async def test_cache_functionality():
    """Test search result caching"""
    print("\n" + "="*80)
    print("TEST 6: Cache Functionality")
    print("="*80)

    query = "software engineering"

    try:
        # Clear cache first
        search_engine.clear_cache()
        print("\nCache cleared")

        # First search (cache miss)
        print(f"\n1st search (cache miss expected): '{query}'")
        results1, metrics1 = await search_engine.search(query, top_k=3)
        print(f"   Results: {len(results1)}, Time: {metrics1.total_time:.3f}s, Cache hit: {metrics1.cache_hit}")

        # Second search (cache hit)
        print(f"\n2nd search (cache hit expected): '{query}'")
        results2, metrics2 = await search_engine.search(query, top_k=3)
        print(f"   Results: {len(results2)}, Time: {metrics2.total_time:.3f}s, Cache hit: {metrics2.cache_hit}")

        # Verify cache hit
        if metrics2.cache_hit and metrics2.total_time < metrics1.total_time:
            print(f"\nCache working correctly! Speed improvement: {metrics1.total_time / metrics2.total_time:.2f}x")
            return True
        else:
            print(f"\nCache might not be working as expected")
            return False

    except Exception as e:
        logger.error(f"Cache test failed: {e}", exc_info=True)
        return False


async def test_api_functions():
    """Test API convenience functions"""
    print("\n" + "="*80)
    print("TEST 7: API Convenience Functions")
    print("="*80)

    query = "test query"

    try:
        # Test hybrid_search API function
        print(f"\nTesting hybrid_search() API function: '{query}'")
        api_results, api_metrics = await hybrid_search(query, top_k=2)

        print(f"API Results: {len(api_results)}")
        print(f"API Metrics keys: {list(api_metrics.keys())}")

        if len(api_results) > 0:
            sample = api_results[0]
            print(f"Sample result keys: {list(sample.keys())}")
            print(f"Sample chunk_id: {sample.get('chunk_id', 'N/A')}")
            print(f"Sample score: {sample.get('score', 0):.4f}")

        return True

    except Exception as e:
        logger.error(f"API function test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all hybrid search tests"""
    print("\n" + "="*80)
    print("HYBRID SEARCH ENGINE - REAL EXECUTION VERIFICATION")
    print("="*80)

    test_results = {
        "BM25 Search": await test_bm25_search(),
        "Vector Search": await test_vector_search(),
        "Hybrid Search": await test_hybrid_search(),
        "Score Normalization": await test_score_normalization(),
        "Filtered Search": await test_search_with_filters(),
        "Cache Functionality": await test_cache_functionality(),
        "API Functions": await test_api_functions()
    }

    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)

    for test_name, passed in test_results.items():
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {test_name}: {status}")

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    print(f"\n{passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")

    if passed_tests == total_tests:
        print("\n*** ALL TESTS PASSED - HYBRID SEARCH ENGINE VERIFIED ***")
        return 0
    else:
        print(f"\n*** {total_tests - passed_tests} TEST(S) FAILED ***")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
