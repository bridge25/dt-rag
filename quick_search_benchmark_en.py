#!/usr/bin/env python3
"""
Quick Hybrid Search Performance Test
Database connection and basic search functionality validation
"""

import asyncio
import time
import sys
import os

# Add project root path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def test_database_connection():
    """Database connection test"""
    print("=== Database Connection Test ===")

    try:
        from database import db_manager, SearchDAO

        # Async session creation test
        async with db_manager.async_session() as session:
            print("OK Database session created successfully")

            # Check table existence
            chunk_count = await SearchDAO._get_chunk_count(session)
            print(f"OK Document chunks found: {chunk_count}")

            # Simple search test
            if chunk_count > 0:
                print("\nRunning simple search tests...")

                # BM25 search test
                start_time = time.time()
                bm25_results = await SearchDAO._perform_bm25_search(
                    session=session,
                    query="AI machine learning",
                    topk=5,
                    filters=None
                )
                bm25_time = time.time() - start_time
                print(f"OK BM25 search: {len(bm25_results)} results, {bm25_time*1000:.1f}ms")

                # Hybrid search test
                start_time = time.time()
                hybrid_results = await SearchDAO.hybrid_search(
                    query="AI machine learning",
                    filters=None,
                    topk=5,
                    bm25_topk=10,
                    vector_topk=10,
                    rerank_candidates=20
                )
                hybrid_time = time.time() - start_time
                print(f"OK Hybrid search: {len(hybrid_results)} results, {hybrid_time*1000:.1f}ms")

                # Performance target check
                print(f"\nPerformance evaluation:")
                if bm25_time * 1000 < 50:
                    print("OK BM25 search speed excellent (< 50ms)")
                elif bm25_time * 1000 < 100:
                    print("OK BM25 search speed good (< 100ms)")
                else:
                    print("WARN BM25 search speed needs improvement (> 100ms)")

                if hybrid_time * 1000 < 200:
                    print("OK Hybrid search speed excellent (< 200ms)")
                elif hybrid_time * 1000 < 500:
                    print("OK Hybrid search speed good (< 500ms)")
                else:
                    print("WARN Hybrid search speed needs improvement (> 500ms)")
            else:
                print("WARN No documents found in database")

    except ImportError as e:
        print(f"ERROR Database module import failed: {e}")
        print("Please check app path or install dependencies")
        return False
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    return True

async def test_search_scenarios():
    """Various search scenario tests"""
    print("\n=== Search Scenario Tests ===")

    try:
        from database import SearchDAO

        test_queries = [
            ("simple", "AI"),
            ("medium", "machine learning algorithms"),
            ("complex", "how to implement vector similarity search"),
            ("korean", "artificial intelligence"),
            ("technical", "BM25 algorithm implementation")
        ]

        results = []

        for scenario, query in test_queries:
            print(f"\n[{scenario.upper()}] Query: '{query}'")

            start_time = time.time()
            search_results = await SearchDAO.hybrid_search(
                query=query,
                filters=None,
                topk=5,
                bm25_topk=12,
                vector_topk=12,
                rerank_candidates=20
            )
            latency = time.time() - start_time

            print(f"  Results: {len(search_results)}")
            print(f"  Latency: {latency*1000:.1f}ms")

            avg_score = 0
            if search_results:
                avg_score = sum(r.get('score', 0) for r in search_results) / len(search_results)
                print(f"  Avg score: {avg_score:.3f}")

                # Top result preview
                top_result = search_results[0]
                text_preview = top_result.get('text', '')[:100] + '...' if top_result.get('text') else 'N/A'
                print(f"  Top result: {text_preview}")

            results.append({
                'scenario': scenario,
                'query': query,
                'count': len(search_results),
                'latency_ms': latency * 1000,
                'avg_score': avg_score
            })

        # Overall performance summary
        print(f"\n=== Performance Summary ===")
        total_latency = sum(r['latency_ms'] for r in results)
        avg_latency = total_latency / len(results)
        max_latency = max(r['latency_ms'] for r in results)

        print(f"Average response time: {avg_latency:.1f}ms")
        print(f"Maximum response time: {max_latency:.1f}ms")
        print(f"Estimated throughput: {1000/avg_latency:.1f} req/sec")

        # Performance target achievement
        if avg_latency < 100:
            print("OK Average response time target achieved")
        else:
            print("WARN Average response time target not met")

        if max_latency < 200:
            print("OK Maximum response time target achieved")
        else:
            print("WARN Maximum response time target not met")

        return results

    except Exception as e:
        print(f"ERROR Search scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return []

async def test_concurrent_performance():
    """Simple concurrent search performance test"""
    print("\n=== Concurrent Search Performance Test ===")

    try:
        from database import SearchDAO

        # Execute 5 concurrent queries
        queries = [
            "AI machine learning",
            "vector search",
            "document classification",
            "embedding model",
            "hybrid ranking"
        ]

        print(f"Executing {len(queries)} concurrent queries...")

        start_time = time.time()

        # Concurrent execution with asyncio.gather
        tasks = []
        for query in queries:
            task = SearchDAO.hybrid_search(
                query=query,
                filters=None,
                topk=3,
                bm25_topk=8,
                vector_topk=8,
                rerank_candidates=15
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        successful_results = [r for r in results if not isinstance(r, Exception)]
        error_results = [r for r in results if isinstance(r, Exception)]

        print(f"Total execution time: {total_time*1000:.1f}ms")
        print(f"Successful searches: {len(successful_results)}/{len(queries)}")
        print(f"Failed searches: {len(error_results)}")

        if successful_results:
            avg_result_count = sum(len(r) for r in successful_results) / len(successful_results)
            print(f"Average result count: {avg_result_count:.1f}")

            # Concurrent processing efficiency calculation
            sequential_estimate = len(queries) * 200  # 200ms per query estimate
            efficiency = (sequential_estimate - total_time*1000) / sequential_estimate * 100
            print(f"Concurrent processing efficiency: {efficiency:.1f}%")

        if error_results:
            print(f"Error details:")
            for i, error in enumerate(error_results):
                print(f"  Error {i+1}: {error}")

        return len(successful_results), total_time

    except Exception as e:
        print(f"ERROR Concurrent search test failed: {e}")
        return 0, 0

async def main():
    """Main execution function"""
    print("Dynamic Taxonomy RAG v1.8.1 Quick Search Performance Test")
    print("="*60)

    # 1. Database connection test
    if not await test_database_connection():
        print("Database connection failed.")
        return

    # 2. Search scenario tests
    scenario_results = await test_search_scenarios()

    if scenario_results:
        # 3. Concurrent search test
        concurrent_success, concurrent_time = await test_concurrent_performance()

        # Final summary
        print(f"\n{'='*60}")
        print("Final Performance Summary")
        print(f"{'='*60}")

        avg_latency = sum(r['latency_ms'] for r in scenario_results) / len(scenario_results)
        print(f"Single search avg latency: {avg_latency:.1f}ms")
        print(f"Concurrent search success rate: {concurrent_success}/5")
        print(f"Concurrent search total time: {concurrent_time*1000:.1f}ms")

        # Performance grade evaluation
        grade = "A"
        if avg_latency > 100:
            grade = "B"
        if avg_latency > 200:
            grade = "C"
        if concurrent_success < 5:
            grade = max("C", grade)

        print(f"Overall performance grade: {grade}")

        if grade == "A":
            print("OK Excellent performance - Production ready")
        elif grade == "B":
            print("OK Good performance - Some optimization recommended")
        else:
            print("WARN Performance improvement needed - Optimization required")

if __name__ == "__main__":
    asyncio.run(main())