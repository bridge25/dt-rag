# @CODE:MYPY-001:PHASE2:BATCH5
"""
Comprehensive Performance Monitoring System
Real-time monitoring for PostgreSQL + pgvector + RAG system
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import psutil  # type: ignore[import-untyped]
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""

    timestamp: float

    # Database metrics
    db_connections_active: int = 0
    db_connections_idle: int = 0
    db_query_avg_time: float = 0.0
    db_slow_queries: int = 0

    # Search metrics
    search_requests_total: int = 0
    search_avg_latency: float = 0.0
    search_p95_latency: float = 0.0
    search_cache_hit_rate: float = 0.0

    # Vector search metrics
    vector_search_count: int = 0
    vector_avg_time: float = 0.0
    vector_index_efficiency: float = 0.0

    # BM25 search metrics
    bm25_search_count: int = 0
    bm25_avg_time: float = 0.0

    # Hybrid fusion metrics
    fusion_avg_time: float = 0.0
    fusion_method: str = "weighted_sum"

    # System metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0

    # Data metrics
    total_documents: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    embedding_coverage: float = 0.0


class RAGPerformanceMonitor:
    """Comprehensive RAG system performance monitor"""

    def __init__(self, monitoring_interval: int = 30) -> None:
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.alerts: List[Dict[str, Any]] = []

        # Performance thresholds
        self.thresholds = {
            "search_p95_latency": 4.0,  # 4 seconds max (PRD requirement)
            "db_query_avg_time": 1.0,  # 1 second max
            "memory_usage": 85.0,  # 85% memory usage
            "cpu_usage": 80.0,  # 80% CPU usage
            "cache_hit_rate_min": 30.0,  # Minimum 30% cache hit rate
            "slow_query_rate": 5.0,  # Max 5% slow queries
        }

        self.running = False
        self._monitor_task: Optional[asyncio.Task[None]] = None

    async def start_monitoring(self, session_factory: Any) -> None:
        """Start continuous performance monitoring"""
        if self.running:
            return

        self.running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop(session_factory))
        logger.info("Performance monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass  # Expected when task is cancelled
        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self, session_factory: Any) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                async with session_factory() as session:
                    metrics = await self._collect_metrics(session)
                    self.metrics_history.append(metrics)

                    # Keep only recent metrics (last 24 hours)
                    cutoff_time = time.time() - 86400
                    self.metrics_history = [
                        m for m in self.metrics_history if m.timestamp > cutoff_time
                    ]

                    # Check for performance issues
                    await self._check_alerts(metrics)

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _collect_metrics(self, session: AsyncSession) -> PerformanceMetrics:
        """Collect comprehensive performance metrics"""
        metrics = PerformanceMetrics(timestamp=time.time())

        try:
            # Database metrics
            await self._collect_db_metrics(session, metrics)

            # Search metrics
            await self._collect_search_metrics(metrics)

            # System metrics
            self._collect_system_metrics(metrics)

            # Data metrics
            await self._collect_data_metrics(session, metrics)

        except Exception as e:
            logger.error(f"Metrics collection error: {e}")

        return metrics

    async def _collect_db_metrics(
        self, session: AsyncSession, metrics: PerformanceMetrics
    ) -> None:
        """Collect database performance metrics"""
        try:
            # Connection statistics
            conn_stats = await session.execute(
                text(
                    """
                SELECT
                    state,
                    COUNT(*) as count
                FROM pg_stat_activity
                WHERE datname = current_database()
                GROUP BY state
            """
                )
            )

            for row in conn_stats:
                if row.state == "active":
                    metrics.db_connections_active = int(row[1])  # count column
                elif row.state == "idle":
                    metrics.db_connections_idle = int(row[1])  # count column

            # Query performance
            query_stats = await session.execute(
                text(
                    """
                SELECT
                    COALESCE(AVG(mean_exec_time), 0) as avg_time,
                    COALESCE(SUM(calls), 0) as total_queries
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat_statements%'
                  AND mean_exec_time > 0
            """
                )
            )

            row_result = query_stats.fetchone()
            if row_result:
                metrics.db_query_avg_time = (
                    float(row_result.avg_time) / 1000
                )  # Convert to seconds

            # Slow queries (>1 second)
            slow_queries = await session.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM pg_stat_statements
                WHERE mean_exec_time > 1000
                  AND calls > 0
            """
                )
            )
            metrics.db_slow_queries = slow_queries.scalar() or 0

        except Exception as e:
            logger.warning(f"Database metrics collection failed: {e}")

    async def _collect_search_metrics(self, metrics: PerformanceMetrics) -> None:
        """Collect search engine metrics"""
        try:
            # Import here to avoid circular imports
            from ..search.optimization import get_performance_monitor  # type: ignore[import-not-found]
            from ..search.optimized_hybrid_engine import get_hybrid_engine  # type: ignore[import-not-found]

            # Get performance monitor
            try:
                perf_monitor = get_performance_monitor()
                perf_report = perf_monitor.get_performance_report()

                metrics.search_requests_total = perf_report.get("search_count", 0)
                metrics.search_avg_latency = perf_report.get("avg_time", 0.0)
                metrics.search_p95_latency = perf_report.get("recent_p95", 0.0)

            except Exception:
                pass  # Performance monitor might not be initialized

            # Get hybrid engine stats
            try:
                hybrid_engine = await get_hybrid_engine()
                hybrid_stats = hybrid_engine.get_stats()

                engine_stats = hybrid_stats.get("hybrid_engine", {})
                metrics.search_avg_latency = engine_stats.get("avg_latency", 0.0)
                metrics.search_cache_hit_rate = (
                    engine_stats.get("cache_hit_rate", 0.0) * 100
                )
                metrics.fusion_avg_time = engine_stats.get("fusion_avg_time", 0.0)

                # BM25 and vector specific metrics
                metrics.bm25_avg_time = engine_stats.get("bm25_avg_time", 0.0)

                vector_stats = hybrid_stats.get("vector_engine", {})
                metrics.vector_avg_time = vector_stats.get("avg_latency", 0.0)
                metrics.vector_search_count = vector_stats.get("searches", 0)

            except Exception:
                pass  # Engines might not be initialized

        except Exception as e:
            logger.warning(f"Search metrics collection failed: {e}")

    def _collect_system_metrics(self, metrics: PerformanceMetrics) -> None:
        """Collect system performance metrics"""
        try:
            # CPU usage
            metrics.cpu_usage = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            metrics.memory_usage = memory.percent

            # Disk usage (root partition)
            disk = psutil.disk_usage("/")
            metrics.disk_usage = (disk.used / disk.total) * 100

        except Exception as e:
            logger.warning(f"System metrics collection failed: {e}")

    async def _collect_data_metrics(
        self, session: AsyncSession, metrics: PerformanceMetrics
    ) -> None:
        """Collect data volume and coverage metrics"""
        try:
            # Document and chunk counts
            counts = await session.execute(
                text(
                    """
                SELECT
                    (SELECT COUNT(*) FROM documents) as doc_count,
                    (SELECT COUNT(*) FROM chunks) as chunk_count,
                    (SELECT COUNT(*) FROM embeddings) as embedding_count
            """
                )
            )

            row = counts.fetchone()
            if row:
                metrics.total_documents = row.doc_count or 0
                metrics.total_chunks = row.chunk_count or 0
                metrics.total_embeddings = row.embedding_count or 0

                # Calculate embedding coverage
                if metrics.total_chunks > 0:
                    metrics.embedding_coverage = (
                        metrics.total_embeddings / metrics.total_chunks
                    ) * 100

        except Exception as e:
            logger.warning(f"Data metrics collection failed: {e}")

    async def _check_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance alerts"""
        alerts = []

        # Check search latency
        if metrics.search_p95_latency > self.thresholds["search_p95_latency"]:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "critical",
                    "message": f"Search P95 latency {metrics.search_p95_latency:.2f}s exceeds threshold {self.thresholds['search_p95_latency']}s",
                    "timestamp": metrics.timestamp,
                    "metric": "search_p95_latency",
                    "value": metrics.search_p95_latency,
                }
            )

        # Check database query performance
        if metrics.db_query_avg_time > self.thresholds["db_query_avg_time"]:
            alerts.append(
                {
                    "type": "database",
                    "severity": "warning",
                    "message": f"Average DB query time {metrics.db_query_avg_time:.2f}s exceeds threshold",
                    "timestamp": metrics.timestamp,
                    "metric": "db_query_avg_time",
                    "value": metrics.db_query_avg_time,
                }
            )

        # Check memory usage
        if metrics.memory_usage > self.thresholds["memory_usage"]:
            alerts.append(
                {
                    "type": "system",
                    "severity": "warning",
                    "message": f"Memory usage {metrics.memory_usage:.1f}% exceeds threshold",
                    "timestamp": metrics.timestamp,
                    "metric": "memory_usage",
                    "value": metrics.memory_usage,
                }
            )

        # Check cache hit rate
        if metrics.search_cache_hit_rate < self.thresholds["cache_hit_rate_min"]:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "info",
                    "message": f"Cache hit rate {metrics.search_cache_hit_rate:.1f}% below optimal",
                    "timestamp": metrics.timestamp,
                    "metric": "cache_hit_rate",
                    "value": metrics.search_cache_hit_rate,
                }
            )

        # Add new alerts
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"Performance Alert: {alert['message']}")

        # Keep only recent alerts (last 24 hours)
        cutoff_time = time.time() - 86400
        self.alerts = [a for a in self.alerts if a["timestamp"] > cutoff_time]

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, hours: int = 1) -> List[PerformanceMetrics]:
        """Get metrics history for specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics_history:
            return {"error": "No metrics available"}

        recent_metrics = self.get_metrics_history(1)  # Last hour
        if not recent_metrics:
            return {"error": "No recent metrics available"}

        # Calculate aggregated metrics
        latencies = [
            m.search_avg_latency for m in recent_metrics if m.search_avg_latency > 0
        ]
        p95_latencies = [
            m.search_p95_latency for m in recent_metrics if m.search_p95_latency > 0
        ]
        cpu_usage = [m.cpu_usage for m in recent_metrics if m.cpu_usage > 0]
        memory_usage = [m.memory_usage for m in recent_metrics if m.memory_usage > 0]

        current = self.metrics_history[-1]

        summary = {
            "timestamp": datetime.fromtimestamp(current.timestamp).isoformat(),
            "current_status": {
                "search_latency_avg": current.search_avg_latency,
                "search_latency_p95": current.search_p95_latency,
                "cache_hit_rate": current.search_cache_hit_rate,
                "active_connections": current.db_connections_active,
                "cpu_usage": current.cpu_usage,
                "memory_usage": current.memory_usage,
            },
            "last_hour_aggregates": {
                "avg_search_latency": np.mean(latencies) if latencies else 0,
                "max_search_latency": np.max(latencies) if latencies else 0,
                "avg_p95_latency": np.mean(p95_latencies) if p95_latencies else 0,
                "avg_cpu_usage": np.mean(cpu_usage) if cpu_usage else 0,
                "avg_memory_usage": np.mean(memory_usage) if memory_usage else 0,
            },
            "data_status": {
                "total_documents": current.total_documents,
                "total_chunks": current.total_chunks,
                "total_embeddings": current.total_embeddings,
                "embedding_coverage": current.embedding_coverage,
            },
            "alerts": {
                "active_alerts": len(
                    [a for a in self.alerts if time.time() - a["timestamp"] < 3600]
                ),
                "critical_alerts": len(
                    [
                        a
                        for a in self.alerts
                        if a["severity"] == "critical"
                        and time.time() - a["timestamp"] < 3600
                    ]
                ),
                "recent_alerts": self.alerts[-5:] if self.alerts else [],
            },
            "performance_status": self._get_performance_status(current),
        }

        return summary

    def _get_performance_status(self, metrics: PerformanceMetrics) -> str:
        """Determine overall performance status"""
        critical_issues = 0
        warning_issues = 0

        # Check critical thresholds
        if metrics.search_p95_latency > self.thresholds["search_p95_latency"]:
            critical_issues += 1
        if metrics.memory_usage > 90:  # Critical memory threshold
            critical_issues += 1

        # Check warning thresholds
        if metrics.db_query_avg_time > self.thresholds["db_query_avg_time"]:
            warning_issues += 1
        if metrics.memory_usage > self.thresholds["memory_usage"]:
            warning_issues += 1
        if metrics.cpu_usage > self.thresholds["cpu_usage"]:
            warning_issues += 1
        if metrics.search_cache_hit_rate < self.thresholds["cache_hit_rate_min"]:
            warning_issues += 1

        if critical_issues > 0:
            return "critical"
        elif warning_issues > 2:
            return "degraded"
        elif warning_issues > 0:
            return "warning"
        else:
            return "healthy"

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance optimization recommendations"""
        if not self.metrics_history:
            return []

        current = self.metrics_history[-1]
        recommendations = []

        # Search performance recommendations
        if current.search_p95_latency > 2.0:
            recommendations.append(
                {
                    "category": "search_performance",
                    "priority": "high",
                    "title": "Optimize search latency",
                    "description": f"P95 latency is {current.search_p95_latency:.2f}s",
                    "actions": [
                        "Increase vector index ef_search parameter",
                        "Enable result caching",
                        "Consider index optimization",
                        "Review query patterns for optimization",
                    ],
                }
            )

        # Cache optimization
        if current.search_cache_hit_rate < 50:
            recommendations.append(
                {
                    "category": "caching",
                    "priority": "medium",
                    "title": "Improve cache hit rate",
                    "description": f"Cache hit rate is {current.search_cache_hit_rate:.1f}%",
                    "actions": [
                        "Increase cache TTL for stable queries",
                        "Implement query normalization",
                        "Review cache eviction policies",
                        "Consider warming frequently accessed data",
                    ],
                }
            )

        # Database optimization
        if current.db_query_avg_time > 0.5:
            recommendations.append(
                {
                    "category": "database",
                    "priority": "medium",
                    "title": "Optimize database queries",
                    "description": f"Average query time is {current.db_query_avg_time:.2f}s",
                    "actions": [
                        "Review and optimize slow queries",
                        "Update table statistics",
                        "Consider additional indexes",
                        "Optimize connection pool settings",
                    ],
                }
            )

        # System resource optimization
        if current.memory_usage > 80:
            recommendations.append(
                {
                    "category": "system",
                    "priority": "high",
                    "title": "Memory usage optimization",
                    "description": f"Memory usage is {current.memory_usage:.1f}%",
                    "actions": [
                        "Review memory-intensive processes",
                        "Optimize connection pool size",
                        "Consider increasing available memory",
                        "Review cache sizes and settings",
                    ],
                }
            )

        return recommendations


# Global monitor instance
_performance_monitor = None


async def get_performance_monitor() -> RAGPerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = RAGPerformanceMonitor()
    return _performance_monitor
