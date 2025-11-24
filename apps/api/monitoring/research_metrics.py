# @CODE:RESEARCH-BACKEND-001:METRICS
"""
Research Module Prometheus Metrics - Monitoring capabilities for research sessions

Provides monitoring for:
- Counters: sessions started, completed, errors, documents found
- Histograms: research duration, documents found per session
- Gauges: active sessions, active SSE connections

Supports both built-in metrics and optional Prometheus export.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dataclasses import field, dataclass
from collections import deque

logger = logging.getLogger(__name__)

# Optional Prometheus support
try:
    from prometheus_client import Counter, Histogram, Gauge

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning(
        "Prometheus client not available, using built-in metrics only"
    )


@dataclass
class ResearchMetrics:
    """Research metrics collector for monitoring session performance"""

    enable_prometheus: bool = True

    # Built-in metric storage
    counters: Dict[str, int] = field(default_factory=dict)
    gauges: Dict[str, float] = field(default_factory=dict)
    duration_samples: List[float] = field(default_factory=list)

    # Prometheus metrics (optional)
    _prometheus_initialized: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Initialize metrics after dataclass creation"""
        self.enable_prometheus = self.enable_prometheus and PROMETHEUS_AVAILABLE

        if self.enable_prometheus:
            self._init_prometheus_metrics()

        logger.info(
            f"ResearchMetrics initialized (Prometheus: {self.enable_prometheus})"
        )

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics"""
        if not self.enable_prometheus:
            return

        # Counters
        self.sessions_started_counter = Counter(
            "research_sessions_started_total",
            "Total research sessions started",
            ["depth_level"],
        )

        self.sessions_completed_counter = Counter(
            "research_sessions_completed_total",
            "Total research sessions completed",
            ["status"],
        )

        self.sessions_error_counter = Counter(
            "research_sessions_error_total",
            "Total research session errors",
        )

        self.documents_found_counter = Counter(
            "research_documents_found_total",
            "Total documents found",
        )

        # Histograms
        self.research_duration_histogram = Histogram(
            "research_session_duration_seconds",
            "Research session duration in seconds",
            ["depth_level"],
            buckets=[10, 30, 60, 120, 300, 600],
        )

        # Gauges
        self.active_sessions_gauge = Gauge(
            "research_sessions_active",
            "Currently active research sessions",
        )

        self.active_sse_connections_gauge = Gauge(
            "research_sse_connections_active",
            "Currently active SSE connections",
        )

        self._prometheus_initialized = True

    def record_session_started(self, depth_level: str = "default") -> None:
        """Record research session start"""
        self.counters["sessions_started"] = self.counters.get("sessions_started", 0) + 1

        if self.enable_prometheus and hasattr(self, "sessions_started_counter"):
            self.sessions_started_counter.labels(depth_level=depth_level).inc()

    def record_session_completed(self, status: str = "completed") -> None:
        """Record research session completion"""
        self.counters["sessions_completed"] = self.counters.get("sessions_completed", 0) + 1

        if self.enable_prometheus and hasattr(self, "sessions_completed_counter"):
            self.sessions_completed_counter.labels(status=status).inc()

    def record_session_error(self) -> None:
        """Record research session error"""
        self.counters["sessions_error"] = self.counters.get("sessions_error", 0) + 1

        if self.enable_prometheus and hasattr(self, "sessions_error_counter"):
            self.sessions_error_counter.inc()

    def record_session_duration(
        self, duration_seconds: float, depth_level: str = "default"
    ) -> None:
        """Record research session duration"""
        self.duration_samples.append(duration_seconds)

        if self.enable_prometheus and hasattr(self, "research_duration_histogram"):
            self.research_duration_histogram.labels(depth_level=depth_level).observe(
                duration_seconds
            )

    def record_documents_found(self, count: int) -> None:
        """Record documents found during research"""
        self.counters["documents_found"] = self.counters.get("documents_found", 0) + count

        if self.enable_prometheus and hasattr(self, "documents_found_counter"):
            self.documents_found_counter.inc(count)

    def set_active_sessions(self, count: int) -> None:
        """Set the current number of active sessions"""
        self.gauges["active_sessions"] = float(count)

        if self.enable_prometheus and hasattr(self, "active_sessions_gauge"):
            self.active_sessions_gauge.set(count)

    def increment_active_sessions(self) -> None:
        """Increment active sessions counter"""
        current = int(self.gauges.get("active_sessions", 0))
        self.set_active_sessions(current + 1)

    def decrement_active_sessions(self) -> None:
        """Decrement active sessions counter (does not go below 0)"""
        current = int(self.gauges.get("active_sessions", 0))
        self.set_active_sessions(max(0, current - 1))

    def set_active_sse_connections(self, count: int) -> None:
        """Set the current number of active SSE connections"""
        self.gauges["active_sse_connections"] = float(count)

        if self.enable_prometheus and hasattr(self, "active_sse_connections_gauge"):
            self.active_sse_connections_gauge.set(count)

    def increment_active_sse_connections(self) -> None:
        """Increment active SSE connections counter"""
        current = int(self.gauges.get("active_sse_connections", 0))
        self.set_active_sse_connections(current + 1)

    def decrement_active_sse_connections(self) -> None:
        """Decrement active SSE connections counter (does not go below 0)"""
        current = int(self.gauges.get("active_sse_connections", 0))
        self.set_active_sse_connections(max(0, current - 1))

    def get_counter(self, counter_name: str) -> int:
        """Get counter value"""
        return self.counters.get(counter_name, 0)

    def get_gauge(self, gauge_name: str) -> float:
        """Get gauge value"""
        return self.gauges.get(gauge_name, 0.0)

    def get_duration_stats(self) -> Dict[str, float]:
        """Get duration statistics"""
        if not self.duration_samples:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}

        return {
            "min": float(min(self.duration_samples)),
            "max": float(max(self.duration_samples)),
            "avg": float(sum(self.duration_samples) / len(self.duration_samples)),
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary"""
        return {
            "sessions_started": self.get_counter("sessions_started"),
            "sessions_completed": self.get_counter("sessions_completed"),
            "sessions_error": self.get_counter("sessions_error"),
            "documents_found": self.get_counter("documents_found"),
            "active_sessions": int(self.get_gauge("active_sessions")),
            "active_sse_connections": int(self.get_gauge("active_sse_connections")),
            "duration_stats": self.get_duration_stats(),
        }

    @asynccontextmanager
    async def track_research_duration(self, depth_level: str = "default"):
        """Context manager to track research duration with automatic error handling"""
        start_time = time.time()

        try:
            yield
            # Success case
            duration = time.time() - start_time
            self.record_session_duration(duration, depth_level)
        except Exception:
            # Error case - still record duration and increment error counter
            duration = time.time() - start_time
            self.record_session_duration(duration, depth_level)
            self.record_session_error()
            raise

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.duration_samples.clear()
        logger.info("Research metrics reset completed")


# Global metrics instance
_research_metrics: Optional[ResearchMetrics] = None


def get_research_metrics() -> ResearchMetrics:
    """Get global research metrics instance"""
    global _research_metrics
    if _research_metrics is None:
        _research_metrics = ResearchMetrics(enable_prometheus=True)
    return _research_metrics


def initialize_research_metrics(enable_prometheus: bool = True) -> ResearchMetrics:
    """Initialize global research metrics instance"""
    global _research_metrics
    _research_metrics = ResearchMetrics(enable_prometheus=enable_prometheus)
    return _research_metrics
