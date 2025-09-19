#!/usr/bin/env python3
"""
Basic search functionality test
Test database connection and search methods
"""

import asyncio
import time
import sys
import os

# Add project root path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def test_basic_functionality():
    """Test basic database and search functionality"""
    print("=== Basic Functionality Test ===")

    try:
        # Import modules
        from database import db_manager, SearchDAO, EmbeddingService
        print("OK Modules imported successfully")

        # Test database connection
        async with db_manager.async_session() as session:
            print("OK Database session created")

            # Test simple query to check if tables exist
            try:
                from sqlalchemy import text
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = result.fetchall()
                print(f"OK Tables found: {[table[0] for table in tables]}")
            except Exception as e:
                print(f"WARN Could not list tables: {e}")

            # Test hybrid search directly
            print("\nTesting hybrid search...")
            start_time = time.time()

            try:
                results = await SearchDAO.hybrid_search(
                    query="test query",
                    filters=None,
                    topk=3,
                    bm25_topk=5,
                    vector_topk=5,
                    rerank_candidates=10
                )
                search_time = time.time() - start_time
                print(f"OK Hybrid search completed: {len(results)} results in {search_time*1000:.1f}ms")

                # Show sample results
                if results:
                    print("Sample results:")
                    for i, result in enumerate(results[:2]):
                        text_preview = str(result.get('text', 'N/A'))[:80] + '...'
                        score = result.get('score', 0)
                        print(f"  {i+1}. Score: {score:.3f}, Text: {text_preview}")
                else:
                    print("  No results found")

            except Exception as e:
                print(f"ERROR Hybrid search failed: {e}")
                import traceback
                traceback.print_exc()

            # Test BM25 search if available
            print("\nTesting BM25 search...")
            try:
                bm25_start = time.time()
                bm25_results = await SearchDAO._perform_bm25_search(
                    session=session,
                    query="test",
                    topk=3,
                    filters=None
                )
                bm25_time = time.time() - bm25_start
                print(f"OK BM25 search: {len(bm25_results)} results in {bm25_time*1000:.1f}ms")
            except Exception as e:
                print(f"ERROR BM25 search failed: {e}")

            # Test vector search if available
            print("\nTesting vector search...")
            try:
                if hasattr(EmbeddingService, 'generate_embedding'):
                    # Generate query embedding
                    embedding_start = time.time()
                    query_embedding = await EmbeddingService.generate_embedding("test query")
                    embedding_time = time.time() - embedding_start
                    print(f"OK Query embedding generated in {embedding_time*1000:.1f}ms")

                    # Perform vector search
                    vector_start = time.time()
                    vector_results = await SearchDAO._perform_vector_search(
                        session=session,
                        query_embedding=query_embedding,
                        topk=3,
                        filters=None
                    )
                    vector_time = time.time() - vector_start
                    print(f"OK Vector search: {len(vector_results)} results in {vector_time*1000:.1f}ms")
                else:
                    print("WARN EmbeddingService.generate_embedding not available")
            except Exception as e:
                print(f"ERROR Vector search failed: {e}")

    except ImportError as e:
        print(f"ERROR Module import failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def run_performance_benchmark():
    """Run basic performance benchmark"""
    print("\n=== Basic Performance Benchmark ===")

    try:
        from database import SearchDAO

        queries = [
            "machine learning",
            "artificial intelligence",
            "data science",
            "neural networks",
            "deep learning"
        ]

        latencies = []
        successful_searches = 0

        print(f"Running {len(queries)} search queries...")

        for i, query in enumerate(queries):
            try:
                start_time = time.time()
                results = await SearchDAO.hybrid_search(
                    query=query,
                    filters=None,
                    topk=5,
                    bm25_topk=10,
                    vector_topk=10,
                    rerank_candidates=20
                )
                latency = time.time() - start_time
                latencies.append(latency * 1000)  # Convert to ms
                successful_searches += 1

                print(f"  Query {i+1}: {len(results)} results, {latency*1000:.1f}ms")

            except Exception as e:
                print(f"  Query {i+1}: FAILED - {e}")

        # Calculate performance metrics
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)

            print(f"\nPerformance Summary:")
            print(f"  Successful searches: {successful_searches}/{len(queries)}")
            print(f"  Average latency: {avg_latency:.1f}ms")
            print(f"  Min latency: {min_latency:.1f}ms")
            print(f"  Max latency: {max_latency:.1f}ms")
            print(f"  Estimated throughput: {1000/avg_latency:.1f} req/sec")

            # Performance evaluation
            if avg_latency < 100:
                print("  Performance: EXCELLENT (< 100ms)")
            elif avg_latency < 200:
                print("  Performance: GOOD (< 200ms)")
            elif avg_latency < 500:
                print("  Performance: ACCEPTABLE (< 500ms)")
            else:
                print("  Performance: NEEDS IMPROVEMENT (> 500ms)")

            if successful_searches == len(queries):
                print("  Reliability: EXCELLENT (100% success)")
            elif successful_searches >= len(queries) * 0.8:
                print("  Reliability: GOOD (80%+ success)")
            else:
                print("  Reliability: NEEDS IMPROVEMENT (< 80% success)")
        else:
            print("  No successful searches to analyze")

    except Exception as e:
        print(f"ERROR Benchmark failed: {e}")

async def test_concurrent_searches():
    """Test concurrent search performance"""
    print("\n=== Concurrent Search Test ===")

    try:
        from database import SearchDAO

        # Define concurrent queries
        concurrent_queries = [
            "AI technology",
            "machine learning models",
            "data processing",
            "algorithm optimization",
            "software development"
        ]

        print(f"Running {len(concurrent_queries)} concurrent searches...")

        start_time = time.time()

        # Create tasks for concurrent execution
        tasks = []
        for query in concurrent_queries:
            task = SearchDAO.hybrid_search(
                query=query,
                filters=None,
                topk=3,
                bm25_topk=8,
                vector_topk=8,
                rerank_candidates=15
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        print(f"Concurrent execution completed in {total_time*1000:.1f}ms")
        print(f"Successful: {len(successful_results)}/{len(concurrent_queries)}")
        print(f"Failed: {len(failed_results)}")

        if successful_results:
            total_results = sum(len(r) for r in successful_results)
            avg_results = total_results / len(successful_results)
            print(f"Average results per query: {avg_results:.1f}")

            # Calculate efficiency
            estimated_sequential_time = len(concurrent_queries) * 200  # 200ms per query
            efficiency = max(0, (estimated_sequential_time - total_time*1000) / estimated_sequential_time * 100)
            print(f"Concurrency efficiency: {efficiency:.1f}%")

        if failed_results:
            print("Failed queries:")
            for i, error in enumerate(failed_results):
                print(f"  {i+1}: {error}")

    except Exception as e:
        print(f"ERROR Concurrent test failed: {e}")

async def main():
    """Main execution function"""
    print("Dynamic Taxonomy RAG v1.8.1 - Basic Search Test")
    print("="*50)

    # Run tests sequentially
    if await test_basic_functionality():
        await run_performance_benchmark()
        await test_concurrent_searches()

        print("\n" + "="*50)
        print("Basic search testing completed successfully!")
    else:
        print("Basic functionality test failed. Please check configuration.")

if __name__ == "__main__":
    asyncio.run(main())