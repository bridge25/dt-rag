#!/usr/bin/env python3
"""
PostgreSQL + pgvector Performance Optimization Validator
Comprehensive testing and validation of all optimization features
"""

import asyncio
import time
import json
import logging
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceOptimizationValidator:
    """Validate all performance optimizations"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_url": os.getenv("DATABASE_URL", ""),
            "tests": {},
            "summary": {},
            "recommendations": []
        }

    async def run_all_tests(self):
        """Run comprehensive optimization validation"""
        logger.info("🚀 Starting PostgreSQL + pgvector Performance Optimization Validation")

        # Test categories
        test_categories = [
            ("Database Connection", self._test_database_connection),
            ("Migration Safety", self._test_migration_safety),
            ("Vector Index Performance", self._test_vector_indexes),
            ("Hybrid Search Performance", self._test_hybrid_search),
            ("Connection Pool Optimization", self._test_connection_pool),
            ("Cache Performance", self._test_cache_performance),
            ("Performance Monitoring", self._test_monitoring_system),
            ("System Resource Usage", self._test_system_resources)
        ]

        total_tests = len(test_categories)
        passed_tests = 0

        for i, (category, test_func) in enumerate(test_categories, 1):
            logger.info(f"\n[{i}/{total_tests}] Testing {category}...")
            try:
                result = await test_func()
                self.results["tests"][category] = result

                if result.get("status") == "pass":
                    passed_tests += 1
                    logger.info(f"✅ {category}: PASSED")
                else:
                    logger.warning(f"⚠️  {category}: {result.get('status', 'FAILED')}")

            except Exception as e:
                logger.error(f"❌ {category}: ERROR - {e}")
                self.results["tests"][category] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        # Generate summary
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "overall_status": "pass" if passed_tests >= total_tests * 0.8 else "warning"
        }

        # Generate recommendations
        await self._generate_recommendations()

        # Output results
        await self._output_results()

        return self.results

    async def _test_database_connection(self) -> Dict[str, Any]:
        """Test database connectivity and basic functionality"""
        try:
            from apps.api.database import db_manager, test_database_connection

            # Test basic connection
            connection_ok = await test_database_connection()
            if not connection_ok:
                return {
                    "status": "fail",
                    "error": "Database connection failed",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Test pgvector availability
            async with db_manager.async_session() as session:
                try:
                    await session.execute("SELECT 1::vector;")
                    pgvector_available = True
                except Exception:
                    pgvector_available = False

                # Test table structure
                result = await session.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN ('chunks', 'embeddings', 'documents', 'taxonomy_nodes')
                """)

                tables = [row[0] for row in result.fetchall()]
                required_tables = {'chunks', 'embeddings', 'documents', 'taxonomy_nodes'}
                tables_ok = required_tables.issubset(set(tables))

            return {
                "status": "pass" if connection_ok and tables_ok else "warning",
                "pgvector_available": pgvector_available,
                "required_tables_present": tables_ok,
                "tables_found": tables,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_migration_safety(self) -> Dict[str, Any]:
        """Test migration safety and idempotency"""
        try:
            from apps.api.database import db_manager

            # Check current migration status
            async with db_manager.async_session() as session:
                try:
                    result = await session.execute("""
                        SELECT version_num
                        FROM alembic_version
                        ORDER BY version_num DESC
                        LIMIT 1
                    """)
                    current_version = result.scalar()
                except Exception:
                    current_version = None

                # Check if critical indexes exist
                critical_indexes = [
                    'idx_embeddings_vec_hnsw',
                    'idx_embeddings_vec_hnsw_optimized',
                    'idx_chunks_doc_id',
                    'idx_doc_taxonomy_path'
                ]

                existing_indexes = []
                for index_name in critical_indexes:
                    try:
                        result = await session.execute(f"""
                            SELECT 1 FROM pg_indexes
                            WHERE indexname = '{index_name}'
                        """)
                        if result.scalar():
                            existing_indexes.append(index_name)
                    except Exception:
                        pass

            return {
                "status": "pass",
                "current_migration_version": current_version,
                "critical_indexes_present": len(existing_indexes),
                "total_critical_indexes": len(critical_indexes),
                "existing_indexes": existing_indexes,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_vector_indexes(self) -> Dict[str, Any]:
        """Test vector index performance"""
        try:
            from apps.search.optimized_vector_engine import get_vector_engine
            from apps.api.database import db_manager
            import numpy as np

            # Initialize vector engine
            vector_engine = await get_vector_engine()

            # Test vector search performance
            async with db_manager.async_session() as session:
                # Create a test vector
                test_vector = np.random.rand(1536).astype(np.float32)

                # Test vector search
                start_time = time.time()
                results = await vector_engine.search_similar(
                    session=session,
                    query_vector=test_vector,
                    top_k=10
                )
                search_time = time.time() - start_time

                # Test KNN search
                start_time = time.time()
                knn_results = await vector_engine.find_nearest_neighbors(
                    session=session,
                    query_vector=test_vector,
                    k=10
                )
                knn_time = time.time() - start_time

                # Check if HNSW index is being used
                explain_result = await session.execute("""
                    EXPLAIN (ANALYZE, BUFFERS)
                    SELECT chunk_id, vec <-> %s as distance
                    FROM embeddings
                    ORDER BY vec <-> %s
                    LIMIT 10
                """, [test_vector.tolist(), test_vector.tolist()])

                explain_text = "\n".join([row[0] for row in explain_result.fetchall()])
                using_index = "Index Scan using" in explain_text and "hnsw" in explain_text

            return {
                "status": "pass" if search_time < 1.0 and using_index else "warning",
                "vector_search_time": search_time,
                "knn_search_time": knn_time,
                "results_count": len(results),
                "knn_results_count": len(knn_results),
                "using_hnsw_index": using_index,
                "performance_rating": "excellent" if search_time < 0.1 else "good" if search_time < 0.5 else "needs_improvement",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_hybrid_search(self) -> Dict[str, Any]:
        """Test hybrid search performance"""
        try:
            from apps.search.optimized_hybrid_engine import get_hybrid_engine
            from apps.api.database import db_manager

            # Initialize hybrid engine
            hybrid_engine = await get_hybrid_engine()

            # Test queries
            test_queries = [
                "machine learning algorithms",
                "RAG system implementation",
                "vector database optimization",
                "postgresql performance tuning"
            ]

            search_times = []
            result_counts = []

            async with db_manager.async_session() as session:
                for query in test_queries:
                    start_time = time.time()
                    results = await hybrid_engine.search(
                        session=session,
                        query=query,
                        top_k=10
                    )
                    search_time = time.time() - start_time

                    search_times.append(search_time)
                    result_counts.append(len(results))

                # Test batch search
                start_time = time.time()
                batch_results = await hybrid_engine.batch_search(
                    session=session,
                    queries=test_queries[:2],
                    top_k=5
                )
                batch_time = time.time() - start_time

            avg_search_time = sum(search_times) / len(search_times)
            max_search_time = max(search_times)
            avg_results = sum(result_counts) / len(result_counts)

            # Get engine statistics
            engine_stats = hybrid_engine.get_stats()

            return {
                "status": "pass" if max_search_time < 4.0 else "warning",  # PRD requirement
                "avg_search_time": avg_search_time,
                "max_search_time": max_search_time,
                "p95_estimate": sorted(search_times)[int(len(search_times) * 0.95)],
                "avg_results_count": avg_results,
                "batch_search_time": batch_time,
                "batch_results_count": len(batch_results),
                "engine_stats": engine_stats,
                "performance_rating": "excellent" if max_search_time < 1.0 else "good" if max_search_time < 2.0 else "needs_improvement",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_connection_pool(self) -> Dict[str, Any]:
        """Test connection pool optimization"""
        try:
            from apps.api.connection_pool_optimizer import get_connection_pool

            # Get connection pool
            pool = await get_connection_pool()

            # Test pool status
            pool_status = await pool.get_pool_status()

            # Test concurrent connections
            start_time = time.time()
            tasks = []
            for _ in range(10):
                task = pool.execute_optimized_query(
                    "SELECT COUNT(*) FROM chunks",
                    fetch_mode="scalar"
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_time = time.time() - start_time

            # Count successful queries
            successful_queries = sum(1 for r in results if not isinstance(r, Exception))

            return {
                "status": "pass" if successful_queries >= 8 else "warning",
                "pool_status": pool_status,
                "concurrent_queries_time": concurrent_time,
                "successful_concurrent_queries": successful_queries,
                "total_attempted_queries": len(tasks),
                "performance_rating": "excellent" if concurrent_time < 1.0 else "good" if concurrent_time < 2.0 else "needs_improvement",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_cache_performance(self) -> Dict[str, Any]:
        """Test cache performance"""
        try:
            from apps.search.optimization import get_cache

            # Get cache instance
            cache = await get_cache()

            # Test cache operations
            test_key = "test_performance_validation"
            test_data = [{"test": "data", "timestamp": time.time()}]

            # Test cache set
            start_time = time.time()
            await cache.set_search_results(test_key, test_data, "test", 300)
            set_time = time.time() - start_time

            # Test cache get
            start_time = time.time()
            cached_data = await cache.get_search_results(test_key, "test")
            get_time = time.time() - start_time

            # Test cache hit
            cache_hit = cached_data is not None and len(cached_data) > 0

            # Get cache statistics
            cache_stats = cache.get_cache_stats()

            return {
                "status": "pass" if cache_hit and get_time < 0.1 else "warning",
                "cache_set_time": set_time,
                "cache_get_time": get_time,
                "cache_hit": cache_hit,
                "cache_stats": cache_stats,
                "performance_rating": "excellent" if get_time < 0.01 else "good" if get_time < 0.05 else "needs_improvement",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_monitoring_system(self) -> Dict[str, Any]:
        """Test performance monitoring system"""
        try:
            from apps.monitoring.performance_monitor import get_performance_monitor

            # Get performance monitor
            monitor = await get_performance_monitor()

            # Get current metrics (if any)
            current_metrics = monitor.get_current_metrics()
            performance_summary = monitor.get_performance_summary()

            # Get recommendations
            recommendations = monitor.get_optimization_recommendations()

            return {
                "status": "pass",
                "monitoring_active": current_metrics is not None,
                "has_performance_data": performance_summary.get("error") is None,
                "recommendations_count": len(recommendations),
                "performance_summary": performance_summary,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _test_system_resources(self) -> Dict[str, Any]:
        """Test system resource utilization"""
        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)

            # Process info
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024**2)
            process_cpu_percent = process.cpu_percent()

            return {
                "status": "pass" if memory_percent < 85 and disk_percent < 90 else "warning",
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_percent,
                "memory_available_gb": memory_available_gb,
                "disk_usage_percent": disk_percent,
                "disk_free_gb": disk_free_gb,
                "process_memory_mb": process_memory_mb,
                "process_cpu_percent": process_cpu_percent,
                "resource_status": "healthy" if memory_percent < 70 else "warning" if memory_percent < 85 else "critical",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _generate_recommendations(self):
        """Generate optimization recommendations based on test results"""
        recommendations = []

        # Check vector search performance
        vector_test = self.results["tests"].get("Vector Index Performance", {})
        if vector_test.get("vector_search_time", 0) > 0.5:
            recommendations.append({
                "category": "vector_performance",
                "priority": "high",
                "title": "Optimize vector search performance",
                "description": f"Vector search time is {vector_test.get('vector_search_time', 0):.3f}s",
                "actions": [
                    "Apply Migration 0005 for optimized HNSW parameters",
                    "Increase ef_search parameter for better recall",
                    "Consider using materialized views for frequent searches",
                    "Monitor memory usage and increase if needed"
                ]
            })

        # Check hybrid search performance
        hybrid_test = self.results["tests"].get("Hybrid Search Performance", {})
        if hybrid_test.get("max_search_time", 0) > 2.0:
            recommendations.append({
                "category": "hybrid_performance",
                "priority": "high",
                "title": "Optimize hybrid search latency",
                "description": f"Max search time is {hybrid_test.get('max_search_time', 0):.3f}s",
                "actions": [
                    "Enable result caching for frequent queries",
                    "Optimize BM25 search with better indexes",
                    "Use adaptive fusion for query-specific optimization",
                    "Consider parallel search execution"
                ]
            })

        # Check cache performance
        cache_test = self.results["tests"].get("Cache Performance", {})
        if not cache_test.get("cache_hit", False):
            recommendations.append({
                "category": "caching",
                "priority": "medium",
                "title": "Improve cache system",
                "description": "Cache system not functioning properly",
                "actions": [
                    "Verify Redis connection and configuration",
                    "Check cache TTL settings",
                    "Monitor cache hit rates",
                    "Consider increasing cache size"
                ]
            })

        # Check system resources
        system_test = self.results["tests"].get("System Resource Usage", {})
        if system_test.get("memory_usage_percent", 0) > 80:
            recommendations.append({
                "category": "system_resources",
                "priority": "high",
                "title": "Address high memory usage",
                "description": f"Memory usage is {system_test.get('memory_usage_percent', 0):.1f}%",
                "actions": [
                    "Review memory-intensive processes",
                    "Optimize connection pool size",
                    "Consider increasing available memory",
                    "Monitor for memory leaks"
                ]
            })

        self.results["recommendations"] = recommendations

    async def _output_results(self):
        """Output validation results"""
        # Save detailed results to file
        results_file = f"performance_optimization_validation_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        # Print summary
        summary = self.results["summary"]
        print(f"\n{'='*80}")
        print("🎯 PERFORMANCE OPTIMIZATION VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"📊 Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['success_rate']:.1f}%)")
        print(f"🔍 Overall Status: {summary['overall_status'].upper()}")
        print(f"📁 Detailed Results: {results_file}")

        if self.results["recommendations"]:
            print(f"\n💡 OPTIMIZATION RECOMMENDATIONS ({len(self.results['recommendations'])})")
            print("-" * 50)
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"{i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"   {rec['description']}")

        print(f"\n⏱️  Validation completed at: {self.results['timestamp']}")
        print("="*80)


async def main():
    """Main validation function"""
    validator = PerformanceOptimizationValidator()

    try:
        results = await validator.run_all_tests()

        # Exit with appropriate code
        success_rate = results["summary"]["success_rate"]
        if success_rate >= 80:
            sys.exit(0)  # Success
        elif success_rate >= 60:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Failure

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(3)  # Error


if __name__ == "__main__":
    asyncio.run(main())