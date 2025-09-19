"""
Metrics Collection System for DT-RAG v1.8.1

Comprehensive Prometheus-based metrics collection for RAG operations,
system health, performance tracking, and SLO/SLI monitoring.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass

try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, Info,
        CollectorRegistry, generate_latest, start_http_server,
        CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def time(self):
            return self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def labels(self, *args, **kwargs):
            return self

    class Summary:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self

    class Info:
        def __init__(self, *args, **kwargs):
            pass
        def info(self, *args, **kwargs):
            pass

    class CollectorRegistry:
        def __init__(self):
            pass

    def generate_latest(registry):
        return b"# Prometheus metrics not available"

    def start_http_server(port, registry=None):
        pass

    CONTENT_TYPE_LATEST = "text/plain"

logger = logging.getLogger(__name__)


@dataclass
class RAGMetrics:
    """RAG-specific metrics container"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_seconds: float = 0.0
    p95_latency_seconds: float = 0.0
    total_classifications: int = 0
    avg_classification_confidence: float = 0.0
    total_searches: int = 0
    avg_search_quality: float = 0.0
    taxonomy_operations: int = 0
    total_cost_won: float = 0.0
    avg_cost_per_query_won: float = 0.0
    avg_faithfulness_score: float = 0.0


class MetricsCollector:
    """
    Comprehensive Prometheus metrics collector for DT-RAG system

    Collects metrics for:
    - RAG request processing
    - Classification operations
    - Search operations
    - Taxonomy operations
    - System health and performance
    - Cost tracking
    - Quality metrics
    """

    def __init__(self, port: int = 8090, export_interval: int = 30):
        self.port = port
        self.export_interval = export_interval
        self.enabled = PROMETHEUS_AVAILABLE
        self.is_running = False

        if not self.enabled:
            logger.warning("Prometheus client not available - metrics collection disabled")
            return

        # Initialize registry
        self.registry = CollectorRegistry()

        # Initialize metrics
        self._initialize_metrics()

        # Performance tracking
        self._latency_samples = deque(maxlen=10000)
        self._cost_samples = deque(maxlen=10000)
        self._faithfulness_samples = deque(maxlen=10000)
        self._classification_confidences = deque(maxlen=10000)
        self._search_qualities = deque(maxlen=10000)

        logger.info("MetricsCollector initialized with Prometheus metrics")

    def _initialize_metrics(self):
        """Initialize all Prometheus metrics"""
        # RAG Request Metrics
        self.rag_requests_total = Counter(
            'dt_rag_requests_total',
            'Total number of RAG requests processed',
            ['query_type', 'status'],
            registry=self.registry
        )

        self.rag_request_duration_seconds = Histogram(
            'dt_rag_request_duration_seconds',
            'RAG request processing time in seconds',
            ['query_type'],
            registry=self.registry,
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 4.0, 10.0, 30.0, 60.0)  # SLO: p95 ≤ 4s
        )

        self.rag_active_requests = Gauge(
            'dt_rag_active_requests',
            'Number of active RAG requests',
            ['query_type'],
            registry=self.registry
        )

        # Classification Metrics
        self.classification_total = Counter(
            'dt_rag_classification_total',
            'Total classification operations',
            ['category', 'confidence_bucket', 'model'],
            registry=self.registry
        )

        self.classification_duration_seconds = Histogram(
            'dt_rag_classification_duration_seconds',
            'Classification processing time in seconds',
            ['model', 'stage'],
            registry=self.registry,
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )

        self.classification_confidence = Histogram(
            'dt_rag_classification_confidence',
            'Classification confidence scores',
            ['category', 'model'],
            registry=self.registry,
            buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
        )

        # Search Metrics
        self.search_operations_total = Counter(
            'dt_rag_search_operations_total',
            'Total search operations',
            ['search_type', 'status'],
            registry=self.registry
        )

        self.search_duration_seconds = Histogram(
            'dt_rag_search_duration_seconds',
            'Search operation processing time',
            ['search_type'],
            registry=self.registry,
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )

        self.search_results_count = Histogram(
            'dt_rag_search_results_count',
            'Number of search results returned',
            ['search_type'],
            registry=self.registry,
            buckets=(0, 1, 5, 10, 25, 50, 100, 250, 500)
        )

        self.search_quality_score = Histogram(
            'dt_rag_search_quality_score',
            'Search quality scores',
            ['search_type'],
            registry=self.registry,
            buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
        )

        # Taxonomy Metrics
        self.taxonomy_operations_total = Counter(
            'dt_rag_taxonomy_operations_total',
            'Total taxonomy operations',
            ['operation_type', 'status'],
            registry=self.registry
        )

        self.taxonomy_operation_duration_seconds = Histogram(
            'dt_rag_taxonomy_operation_duration_seconds',
            'Taxonomy operation processing time',
            ['operation_type'],
            registry=self.registry,
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )

        self.taxonomy_nodes_affected = Histogram(
            'dt_rag_taxonomy_nodes_affected',
            'Number of taxonomy nodes affected by operations',
            ['operation_type'],
            registry=self.registry,
            buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000)
        )

        self.taxonomy_version_current = Gauge(
            'dt_rag_taxonomy_version_current',
            'Current taxonomy version',
            registry=self.registry
        )

        # Cost Metrics (SLO: ≤ ₩10/query)
        self.cost_total_won = Counter(
            'dt_rag_cost_total_won',
            'Total cost in Korean Won',
            ['service', 'model'],
            registry=self.registry
        )

        self.cost_per_query_won = Histogram(
            'dt_rag_cost_per_query_won',
            'Cost per query in Korean Won',
            ['service', 'model'],
            registry=self.registry,
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0)  # SLO: ≤ ₩10
        )

        # Quality Metrics (SLO: Faithfulness ≥ 0.85)
        self.faithfulness_score = Histogram(
            'dt_rag_faithfulness_score',
            'RAG faithfulness scores',
            ['model', 'query_type'],
            registry=self.registry,
            buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0)  # SLO: ≥ 0.85
        )

        self.user_satisfaction_score = Histogram(
            'dt_rag_user_satisfaction_score',
            'User satisfaction scores',
            ['query_type'],
            registry=self.registry,
            buckets=(1, 2, 3, 4, 5)
        )

        # System Health Metrics
        self.system_memory_usage_bytes = Gauge(
            'dt_rag_system_memory_usage_bytes',
            'System memory usage in bytes',
            ['memory_type'],
            registry=self.registry
        )

        self.system_cpu_usage_percent = Gauge(
            'dt_rag_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_disk_usage_bytes = Gauge(
            'dt_rag_system_disk_usage_bytes',
            'System disk usage in bytes',
            ['disk_type'],
            registry=self.registry
        )

        # Database Metrics
        self.database_connections_active = Gauge(
            'dt_rag_database_connections_active',
            'Active database connections',
            ['database_type'],
            registry=self.registry
        )

        self.database_query_duration_seconds = Histogram(
            'dt_rag_database_query_duration_seconds',
            'Database query processing time',
            ['database_type', 'operation'],
            registry=self.registry,
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
        )

        self.vector_database_size_entries = Gauge(
            'dt_rag_vector_database_size_entries',
            'Number of entries in vector database',
            ['collection'],
            registry=self.registry
        )

        # HITL (Human-in-the-Loop) Metrics
        self.hitl_queue_size = Gauge(
            'dt_rag_hitl_queue_size',
            'Current HITL queue size',
            ['queue_type'],
            registry=self.registry
        )

        self.hitl_processing_time_seconds = Histogram(
            'dt_rag_hitl_processing_time_seconds',
            'HITL processing time',
            ['queue_type', 'action'],
            registry=self.registry,
            buckets=(60, 300, 900, 1800, 3600, 7200)  # 1min to 2hrs
        )

        # System Info
        self.system_info = Info(
            'dt_rag_system_info',
            'System information',
            registry=self.registry
        )

        # Set system info
        self.system_info.info({
            'version': '1.8.1',
            'component': 'dt-rag',
            'python_version': f"{psutil.python_version()}",
            'start_time': datetime.utcnow().isoformat()
        })

    async def start(self):
        """Start metrics collection service"""
        if not self.enabled:
            logger.warning("Metrics collection disabled - Prometheus not available")
            return

        if self.is_running:
            logger.warning("MetricsCollector is already running")
            return

        try:
            self.is_running = True

            # Start HTTP server for metrics endpoint
            start_http_server(self.port, registry=self.registry)
            logger.info(f"Prometheus metrics server started on port {self.port}")

            # Start periodic system metrics collection
            asyncio.create_task(self._collect_system_metrics())

            logger.info("MetricsCollector started successfully")

        except Exception as e:
            logger.error(f"Failed to start metrics collection: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Stop metrics collection service"""
        if not self.is_running:
            return

        try:
            self.is_running = False
            logger.info("MetricsCollector stopped")

        except Exception as e:
            logger.error(f"Error stopping metrics collection: {e}")

    def record_request_start(self, query_type: str, user_id: Optional[str] = None):
        """Record start of a RAG request"""
        if not self.enabled:
            return

        self.rag_active_requests.labels(query_type=query_type).inc()

    def record_request_completion(
        self,
        duration: float,
        status: str,
        query_type: str,
        user_id: Optional[str] = None
    ):
        """Record completion of a RAG request"""
        if not self.enabled:
            return

        # Record metrics
        self.rag_requests_total.labels(
            query_type=query_type,
            status=status
        ).inc()

        self.rag_request_duration_seconds.labels(
            query_type=query_type
        ).observe(duration)

        self.rag_active_requests.labels(query_type=query_type).dec()

        # Track samples for summary statistics
        self._latency_samples.append(duration)

    def record_classification(
        self,
        category: str,
        confidence: float,
        latency_seconds: float,
        model: str,
        cost_cents: float = 0.0
    ):
        """Record classification operation metrics"""
        if not self.enabled:
            return

        # Determine confidence bucket
        confidence_bucket = self._get_confidence_bucket(confidence)

        # Record classification
        self.classification_total.labels(
            category=category.split("/")[0] if "/" in category else category,
            confidence_bucket=confidence_bucket,
            model=model
        ).inc()

        self.classification_duration_seconds.labels(
            model=model,
            stage="total"
        ).observe(latency_seconds)

        self.classification_confidence.labels(
            category=category.split("/")[0] if "/" in category else category,
            model=model
        ).observe(confidence)

        # Record cost
        if cost_cents > 0:
            cost_won = cost_cents / 100.0  # Convert cents to won (assuming 1:1 for simplicity)
            self.cost_total_won.labels(
                service="classification",
                model=model
            ).inc(cost_won)

            self.cost_per_query_won.labels(
                service="classification",
                model=model
            ).observe(cost_won)

            self._cost_samples.append(cost_won)

        # Track confidence samples
        self._classification_confidences.append(confidence)

    def record_search(
        self,
        query: str,
        results_count: int,
        search_type: str,
        latency_seconds: float,
        quality_score: Optional[float] = None
    ):
        """Record search operation metrics"""
        if not self.enabled:
            return

        self.search_operations_total.labels(
            search_type=search_type,
            status="success"
        ).inc()

        self.search_duration_seconds.labels(
            search_type=search_type
        ).observe(latency_seconds)

        self.search_results_count.labels(
            search_type=search_type
        ).observe(results_count)

        if quality_score is not None:
            self.search_quality_score.labels(
                search_type=search_type
            ).observe(quality_score)

            self._search_qualities.append(quality_score)

    def record_taxonomy_operation(
        self,
        operation_type: str,
        nodes_affected: int,
        latency_seconds: float,
        success: bool
    ):
        """Record taxonomy operation metrics"""
        if not self.enabled:
            return

        status = "success" if success else "error"

        self.taxonomy_operations_total.labels(
            operation_type=operation_type,
            status=status
        ).inc()

        self.taxonomy_operation_duration_seconds.labels(
            operation_type=operation_type
        ).observe(latency_seconds)

        self.taxonomy_nodes_affected.labels(
            operation_type=operation_type
        ).observe(nodes_affected)

    def record_faithfulness_score(
        self,
        score: float,
        model: str,
        query_type: str
    ):
        """Record faithfulness quality score"""
        if not self.enabled:
            return

        self.faithfulness_score.labels(
            model=model,
            query_type=query_type
        ).observe(score)

        self._faithfulness_samples.append(score)

    def record_user_satisfaction(
        self,
        score: int,
        query_type: str
    ):
        """Record user satisfaction score (1-5)"""
        if not self.enabled:
            return

        self.user_satisfaction_score.labels(
            query_type=query_type
        ).observe(score)

    def update_taxonomy_version(self, version: int):
        """Update current taxonomy version"""
        if not self.enabled:
            return

        self.taxonomy_version_current.set(version)

    def update_database_connections(self, database_type: str, count: int):
        """Update active database connections"""
        if not self.enabled:
            return

        self.database_connections_active.labels(
            database_type=database_type
        ).set(count)

    def update_vector_database_size(self, collection: str, size: int):
        """Update vector database size"""
        if not self.enabled:
            return

        self.vector_database_size_entries.labels(
            collection=collection
        ).set(size)

    def update_hitl_queue_size(self, queue_type: str, size: int):
        """Update HITL queue size"""
        if not self.enabled:
            return

        self.hitl_queue_size.labels(
            queue_type=queue_type
        ).set(size)

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        if not self.enabled:
            return {}

        try:
            # Calculate summary statistics
            latencies = list(self._latency_samples)
            costs = list(self._cost_samples)
            faithfulness_scores = list(self._faithfulness_samples)
            confidences = list(self._classification_confidences)
            search_qualities = list(self._search_qualities)

            summary = {
                'total_requests': len(latencies),
                'avg_latency_seconds': sum(latencies) / len(latencies) if latencies else 0.0,
                'p95_latency_seconds': self._percentile(latencies, 0.95) if latencies else 0.0,
                'p99_latency_seconds': self._percentile(latencies, 0.99) if latencies else 0.0,

                'total_classifications': len(confidences),
                'avg_classification_confidence': sum(confidences) / len(confidences) if confidences else 0.0,

                'total_cost_won': sum(costs),
                'avg_cost_per_query_won': sum(costs) / len(costs) if costs else 0.0,

                'avg_faithfulness_score': sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0,
                'avg_search_quality': sum(search_qualities) / len(search_qualities) if search_qualities else 0.0,

                'search_operations': len(search_qualities),
                'taxonomy_operations': 0  # Would be tracked separately
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}

    async def _collect_system_metrics(self):
        """Periodically collect system metrics"""
        while self.is_running:
            try:
                await asyncio.sleep(self.export_interval)

                if not self.is_running:
                    break

                # Get system metrics
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                disk = psutil.disk_usage('/')

                # Update memory metrics
                self.system_memory_usage_bytes.labels(memory_type='used').set(memory.used)
                self.system_memory_usage_bytes.labels(memory_type='available').set(memory.available)
                self.system_memory_usage_bytes.labels(memory_type='total').set(memory.total)

                # Update CPU metrics
                self.system_cpu_usage_percent.set(cpu_percent)

                # Update disk metrics
                self.system_disk_usage_bytes.labels(disk_type='used').set(disk.used)
                self.system_disk_usage_bytes.labels(disk_type='free').set(disk.free)
                self.system_disk_usage_bytes.labels(disk_type='total').set(disk.total)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

    def _get_confidence_bucket(self, confidence: float) -> str:
        """Convert confidence score to bucket for low cardinality"""
        if confidence < 0.5:
            return "low"
        elif confidence < 0.7:
            return "medium"
        elif confidence < 0.9:
            return "high"
        else:
            return "very_high"

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format"""
        if not self.enabled:
            return "# Prometheus metrics not available\n"

        return generate_latest(self.registry).decode('utf-8')