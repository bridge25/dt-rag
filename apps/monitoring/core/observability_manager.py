"""
Core Observability Manager for DT-RAG v1.8.1

Central orchestrator for all monitoring, metrics, alerting, and observability systems.
Integrates Langfuse for LLM observability with comprehensive system monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from .langfuse_integration import LangfuseManager, LangfuseRAGObserver
from .metrics_collector import MetricsCollector, RAGMetrics
from .alerting_manager import AlertingManager
from .dashboard_generator import DashboardGenerator
from ..utils.health_checker import SystemHealthChecker

logger = logging.getLogger(__name__)


@dataclass
class ObservabilityConfig:
    """Configuration for observability system"""
    # Langfuse configuration
    langfuse_enabled: bool = True
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: Optional[str] = None

    # Metrics configuration
    prometheus_enabled: bool = True
    prometheus_port: int = 8090
    metrics_export_interval: int = 30

    # Health monitoring
    health_check_interval: int = 30
    health_check_enabled: bool = True

    # Performance requirements (SLO targets)
    slo_p95_latency_seconds: float = 4.0
    slo_cost_per_query_won: float = 10.0
    slo_faithfulness_threshold: float = 0.85
    slo_availability_percent: float = 99.5

    # Alerting
    alerting_enabled: bool = True
    alert_webhook_url: Optional[str] = None

    # Sampling
    trace_sampling_rate: float = 0.1  # 10% sampling for production


@dataclass
class SystemMetrics:
    """System-wide metrics snapshot"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_seconds: float
    p95_latency_seconds: float
    p99_latency_seconds: float
    current_load: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate_percent: float
    availability_percent: float

    # RAG-specific metrics
    total_classifications: int
    avg_classification_confidence: float
    taxonomy_operations: int
    search_operations: int

    # Cost metrics
    total_cost_won: float
    avg_cost_per_query_won: float

    # Quality metrics
    avg_faithfulness_score: float
    search_quality_score: float


class ObservabilityManager:
    """
    Central observability and monitoring system for DT-RAG v1.8.1

    Provides comprehensive monitoring including:
    - LLM call tracking via Langfuse
    - System metrics collection via Prometheus
    - Real-time alerting
    - Health monitoring
    - Performance dashboards
    - SLO/SLI tracking
    """

    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self.start_time = datetime.utcnow()
        self.is_running = False

        # Initialize core components
        self._initialize_components()

        # Performance tracking
        self._request_count = 0
        self._error_count = 0
        self._latency_samples = []
        self._cost_samples = []
        self._faithfulness_samples = []

        logger.info("ObservabilityManager initialized with comprehensive monitoring")

    def _initialize_components(self):
        """Initialize all monitoring components"""
        try:
            # Initialize Langfuse manager
            if self.config.langfuse_enabled:
                self.langfuse_manager = LangfuseManager(
                    public_key=self.config.langfuse_public_key,
                    secret_key=self.config.langfuse_secret_key,
                    host=self.config.langfuse_host
                )
                logger.info("Langfuse integration initialized")
            else:
                self.langfuse_manager = None
                logger.info("Langfuse integration disabled")

            # Initialize metrics collector
            if self.config.prometheus_enabled:
                self.metrics_collector = MetricsCollector(
                    port=self.config.prometheus_port,
                    export_interval=self.config.metrics_export_interval
                )
                logger.info("Metrics collection initialized")
            else:
                self.metrics_collector = None
                logger.info("Metrics collection disabled")

            # Initialize alerting manager
            if self.config.alerting_enabled:
                self.alerting_manager = AlertingManager(
                    webhook_url=self.config.alert_webhook_url,
                    slo_config={
                        'p95_latency_seconds': self.config.slo_p95_latency_seconds,
                        'cost_per_query_won': self.config.slo_cost_per_query_won,
                        'faithfulness_threshold': self.config.slo_faithfulness_threshold,
                        'availability_percent': self.config.slo_availability_percent
                    }
                )
                logger.info("Alerting system initialized")
            else:
                self.alerting_manager = None
                logger.info("Alerting system disabled")

            # Initialize health checker
            if self.config.health_check_enabled:
                self.health_checker = SystemHealthChecker(
                    check_interval=self.config.health_check_interval
                )
                logger.info("Health monitoring initialized")
            else:
                self.health_checker = None
                logger.info("Health monitoring disabled")

            # Initialize dashboard generator
            self.dashboard_generator = DashboardGenerator()
            logger.info("Dashboard generator initialized")

        except Exception as e:
            logger.error(f"Failed to initialize observability components: {e}")
            raise

    async def start(self):
        """Start all monitoring services"""
        if self.is_running:
            logger.warning("ObservabilityManager is already running")
            return

        try:
            self.is_running = True
            logger.info("Starting ObservabilityManager services")

            # Start health monitoring
            if self.health_checker:
                await self.health_checker.start()

            # Start metrics collection
            if self.metrics_collector:
                await self.metrics_collector.start()

            # Start alerting
            if self.alerting_manager:
                await self.alerting_manager.start()

            # Start periodic monitoring tasks
            asyncio.create_task(self._periodic_monitoring())

            logger.info("All observability services started successfully")

        except Exception as e:
            logger.error(f"Failed to start observability services: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Stop all monitoring services"""
        if not self.is_running:
            return

        try:
            logger.info("Stopping ObservabilityManager services")
            self.is_running = False

            # Stop health monitoring
            if self.health_checker:
                await self.health_checker.stop()

            # Stop metrics collection
            if self.metrics_collector:
                await self.metrics_collector.stop()

            # Stop alerting
            if self.alerting_manager:
                await self.alerting_manager.stop()

            logger.info("All observability services stopped")

        except Exception as e:
            logger.error(f"Error stopping observability services: {e}")

    @asynccontextmanager
    async def trace_rag_request(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing RAG requests with comprehensive observability

        Tracks:
        - Request lifecycle in Langfuse
        - Performance metrics
        - Error tracking
        - Cost calculation
        - Quality metrics
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"

        # Initialize tracking data
        trace_data = {
            'request_id': request_id,
            'query': query,
            'user_id': user_id,
            'session_id': session_id,
            'start_time': start_time,
            'metadata': metadata or {}
        }

        # Start Langfuse trace
        langfuse_observer = None
        if self.langfuse_manager:
            langfuse_observer = await self.langfuse_manager.create_rag_observer(
                session_id=session_id or request_id,
                user_id=user_id,
                metadata=metadata
            )
            await langfuse_observer.start_trace(query)

        # Track request start
        self._request_count += 1
        if self.metrics_collector:
            self.metrics_collector.record_request_start(
                query_type=self._classify_query_type(query),
                user_id=user_id
            )

        try:
            # Yield observer for request tracking
            yield langfuse_observer

            # Calculate metrics
            duration = time.time() - start_time
            self._latency_samples.append(duration)

            # Record successful request
            if self.metrics_collector:
                self.metrics_collector.record_request_completion(
                    duration=duration,
                    status='success',
                    query_type=self._classify_query_type(query)
                )

            logger.debug(f"RAG request {request_id} completed successfully in {duration:.3f}s")

        except Exception as e:
            # Record error
            self._error_count += 1
            duration = time.time() - start_time

            if self.metrics_collector:
                self.metrics_collector.record_request_completion(
                    duration=duration,
                    status='error',
                    query_type=self._classify_query_type(query)
                )

            # Record error in Langfuse
            if langfuse_observer:
                await langfuse_observer.record_error(str(e))

            logger.error(f"RAG request {request_id} failed after {duration:.3f}s: {e}")
            raise

        finally:
            # Finalize Langfuse trace
            if langfuse_observer:
                await langfuse_observer.end_trace()

    async def record_classification_result(
        self,
        text: str,
        category: str,
        confidence: float,
        latency_ms: float,
        model_used: str,
        cost_cents: float = 0.0,
        faithfulness_score: Optional[float] = None
    ):
        """Record classification operation results"""
        try:
            # Record in metrics
            if self.metrics_collector:
                self.metrics_collector.record_classification(
                    category=category,
                    confidence=confidence,
                    latency_seconds=latency_ms / 1000.0,
                    model=model_used,
                    cost_cents=cost_cents
                )

            # Track cost and quality
            if cost_cents > 0:
                cost_won = cost_cents / 100.0  # Convert to won
                self._cost_samples.append(cost_won)

            if faithfulness_score is not None:
                self._faithfulness_samples.append(faithfulness_score)

            # Record in Langfuse if available
            if self.langfuse_manager:
                await self.langfuse_manager.record_classification(
                    text=text,
                    category=category,
                    confidence=confidence,
                    model=model_used,
                    latency_ms=latency_ms,
                    cost_cents=cost_cents,
                    faithfulness_score=faithfulness_score
                )

        except Exception as e:
            logger.error(f"Failed to record classification result: {e}")

    async def record_search_operation(
        self,
        query: str,
        results_count: int,
        search_type: str,
        latency_ms: float,
        quality_score: Optional[float] = None
    ):
        """Record search operation metrics"""
        try:
            if self.metrics_collector:
                self.metrics_collector.record_search(
                    query=query,
                    results_count=results_count,
                    search_type=search_type,
                    latency_seconds=latency_ms / 1000.0,
                    quality_score=quality_score
                )

            # Record in Langfuse if available
            if self.langfuse_manager:
                await self.langfuse_manager.record_search(
                    query=query,
                    results_count=results_count,
                    search_type=search_type,
                    latency_ms=latency_ms,
                    quality_score=quality_score
                )

        except Exception as e:
            logger.error(f"Failed to record search operation: {e}")

    async def record_taxonomy_operation(
        self,
        operation_type: str,
        nodes_affected: int,
        latency_ms: float,
        success: bool,
        version_from: Optional[int] = None,
        version_to: Optional[int] = None
    ):
        """Record taxonomy operation metrics"""
        try:
            if self.metrics_collector:
                self.metrics_collector.record_taxonomy_operation(
                    operation_type=operation_type,
                    nodes_affected=nodes_affected,
                    latency_seconds=latency_ms / 1000.0,
                    success=success
                )

            # Record in Langfuse if available
            if self.langfuse_manager:
                await self.langfuse_manager.record_taxonomy_operation(
                    operation_type=operation_type,
                    nodes_affected=nodes_affected,
                    latency_ms=latency_ms,
                    success=success,
                    version_from=version_from,
                    version_to=version_to
                )

        except Exception as e:
            logger.error(f"Failed to record taxonomy operation: {e}")

    async def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system metrics snapshot"""
        try:
            current_time = datetime.utcnow()
            uptime_seconds = (current_time - self.start_time).total_seconds()

            # Calculate latency percentiles
            latencies = sorted(self._latency_samples[-1000:])  # Last 1000 samples
            p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
            p99_latency = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            # Calculate error rate
            total_requests = max(self._request_count, 1)
            error_rate = (self._error_count / total_requests) * 100

            # Calculate availability
            availability = max(0, 100 - error_rate)

            # Cost metrics
            avg_cost_per_query = sum(self._cost_samples) / len(self._cost_samples) if self._cost_samples else 0.0
            total_cost = sum(self._cost_samples)

            # Quality metrics
            avg_faithfulness = sum(self._faithfulness_samples) / len(self._faithfulness_samples) if self._faithfulness_samples else 0.0

            # Get system health metrics
            health_metrics = {}
            if self.health_checker:
                health_metrics = await self.health_checker.get_health_metrics()

            # Get additional metrics from collector
            collector_metrics = {}
            if self.metrics_collector:
                collector_metrics = await self.metrics_collector.get_metrics_summary()

            return SystemMetrics(
                timestamp=current_time,
                total_requests=self._request_count,
                successful_requests=self._request_count - self._error_count,
                failed_requests=self._error_count,
                avg_latency_seconds=avg_latency,
                p95_latency_seconds=p95_latency,
                p99_latency_seconds=p99_latency,
                current_load=health_metrics.get('cpu_usage_percent', 0.0),
                memory_usage_mb=health_metrics.get('memory_usage_mb', 0.0),
                cpu_usage_percent=health_metrics.get('cpu_usage_percent', 0.0),
                error_rate_percent=error_rate,
                availability_percent=availability,
                total_classifications=collector_metrics.get('total_classifications', 0),
                avg_classification_confidence=collector_metrics.get('avg_classification_confidence', 0.0),
                taxonomy_operations=collector_metrics.get('taxonomy_operations', 0),
                search_operations=collector_metrics.get('search_operations', 0),
                total_cost_won=total_cost,
                avg_cost_per_query_won=avg_cost_per_query,
                avg_faithfulness_score=avg_faithfulness,
                search_quality_score=collector_metrics.get('avg_search_quality', 0.0)
            )

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            # Return basic metrics on error
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                total_requests=self._request_count,
                successful_requests=self._request_count - self._error_count,
                failed_requests=self._error_count,
                avg_latency_seconds=0.0,
                p95_latency_seconds=0.0,
                p99_latency_seconds=0.0,
                current_load=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                error_rate_percent=0.0,
                availability_percent=100.0,
                total_classifications=0,
                avg_classification_confidence=0.0,
                taxonomy_operations=0,
                search_operations=0,
                total_cost_won=0.0,
                avg_cost_per_query_won=0.0,
                avg_faithfulness_score=0.0,
                search_quality_score=0.0
            )

    async def check_slo_compliance(self) -> Dict[str, Any]:
        """Check SLO compliance and trigger alerts if needed"""
        try:
            metrics = await self.get_system_metrics()

            compliance_status = {
                'timestamp': metrics.timestamp.isoformat(),
                'compliant': True,
                'violations': [],
                'metrics': asdict(metrics)
            }

            # Check P95 latency SLO
            if metrics.p95_latency_seconds > self.config.slo_p95_latency_seconds:
                violation = {
                    'slo': 'p95_latency',
                    'target': self.config.slo_p95_latency_seconds,
                    'actual': metrics.p95_latency_seconds,
                    'severity': 'critical' if metrics.p95_latency_seconds > self.config.slo_p95_latency_seconds * 1.5 else 'warning'
                }
                compliance_status['violations'].append(violation)
                compliance_status['compliant'] = False

            # Check cost per query SLO
            if metrics.avg_cost_per_query_won > self.config.slo_cost_per_query_won:
                violation = {
                    'slo': 'cost_per_query',
                    'target': self.config.slo_cost_per_query_won,
                    'actual': metrics.avg_cost_per_query_won,
                    'severity': 'warning'
                }
                compliance_status['violations'].append(violation)
                compliance_status['compliant'] = False

            # Check faithfulness SLO
            if metrics.avg_faithfulness_score < self.config.slo_faithfulness_threshold:
                violation = {
                    'slo': 'faithfulness',
                    'target': self.config.slo_faithfulness_threshold,
                    'actual': metrics.avg_faithfulness_score,
                    'severity': 'critical'
                }
                compliance_status['violations'].append(violation)
                compliance_status['compliant'] = False

            # Check availability SLO
            if metrics.availability_percent < self.config.slo_availability_percent:
                violation = {
                    'slo': 'availability',
                    'target': self.config.slo_availability_percent,
                    'actual': metrics.availability_percent,
                    'severity': 'critical'
                }
                compliance_status['violations'].append(violation)
                compliance_status['compliant'] = False

            # Trigger alerts for violations
            if not compliance_status['compliant'] and self.alerting_manager:
                await self.alerting_manager.trigger_slo_violation_alert(compliance_status)

            return compliance_status

        except Exception as e:
            logger.error(f"Failed to check SLO compliance: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'compliant': False,
                'violations': [{'error': str(e)}],
                'metrics': {}
            }

    async def generate_monitoring_dashboard(self) -> Dict[str, Any]:
        """Generate real-time monitoring dashboard data"""
        try:
            metrics = await self.get_system_metrics()
            slo_status = await self.check_slo_compliance()

            # Get health status
            health_status = "healthy"
            if self.health_checker:
                health_data = await self.health_checker.get_health_status()
                health_status = health_data.get('status', 'unknown')

            dashboard_data = {
                'title': 'DT-RAG v1.8.1 Observability Dashboard',
                'timestamp': datetime.utcnow().isoformat(),
                'status': health_status,
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'system_metrics': asdict(metrics),
                'slo_compliance': slo_status,
                'components': {
                    'langfuse': self.langfuse_manager is not None and self.config.langfuse_enabled,
                    'metrics_collection': self.metrics_collector is not None and self.config.prometheus_enabled,
                    'alerting': self.alerting_manager is not None and self.config.alerting_enabled,
                    'health_monitoring': self.health_checker is not None and self.config.health_check_enabled
                }
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to generate dashboard: {e}")
            return {
                'title': 'DT-RAG v1.8.1 Observability Dashboard',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': str(e)
            }

    async def _periodic_monitoring(self):
        """Run periodic monitoring tasks"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Run every minute

                if not self.is_running:
                    break

                # Check SLO compliance
                await self.check_slo_compliance()

                # Cleanup old samples (keep last 10,000)
                if len(self._latency_samples) > 10000:
                    self._latency_samples = self._latency_samples[-5000:]

                if len(self._cost_samples) > 10000:
                    self._cost_samples = self._cost_samples[-5000:]

                if len(self._faithfulness_samples) > 10000:
                    self._faithfulness_samples = self._faithfulness_samples[-5000:]

            except Exception as e:
                logger.error(f"Error in periodic monitoring: {e}")

    def _classify_query_type(self, query: str) -> str:
        """Classify query type for metrics tracking"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ['search', 'find', 'lookup']):
            return 'search'
        elif any(keyword in query_lower for keyword in ['classify', 'category', 'categorize']):
            return 'classification'
        elif any(keyword in query_lower for keyword in ['taxonomy', 'structure', 'hierarchy']):
            return 'taxonomy'
        else:
            return 'general'