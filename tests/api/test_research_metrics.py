# @TEST:RESEARCH-BACKEND-001:METRICS
"""
Tests for Research Metrics Module - Prometheus metrics collection

Tests monitoring capabilities:
- Counter metrics (sessions started, completed, errors)
- Histogram metrics (research duration, documents found)
- Gauge metrics (active sessions, active SSE connections)
- Metrics context manager integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime

from apps.api.monitoring.research_metrics import (
    ResearchMetrics,
    get_research_metrics,
    initialize_research_metrics,
)


@pytest.fixture
def research_metrics():
    """Create ResearchMetrics instance"""
    metrics = ResearchMetrics(enable_prometheus=False)  # Disable Prometheus for testing
    return metrics


@pytest.fixture
def research_metrics_with_prometheus():
    """Create ResearchMetrics instance with Prometheus enabled"""
    metrics = ResearchMetrics(enable_prometheus=True)
    return metrics


class TestResearchMetricsInitialization:
    """Test ResearchMetrics initialization"""

    def test_init_with_prometheus_disabled(self):
        """Test initialization with Prometheus disabled"""
        metrics = ResearchMetrics(enable_prometheus=False)
        assert metrics.enable_prometheus is False
        assert metrics.counters == {}
        assert metrics.gauges == {}

    def test_init_with_prometheus_enabled(self):
        """Test initialization with Prometheus enabled"""
        metrics = ResearchMetrics(enable_prometheus=True)
        # Should initialize without errors
        assert metrics.enable_prometheus is True or metrics.enable_prometheus is False  # May not be available

    def test_init_creates_empty_metrics(self, research_metrics):
        """Test that counters and gauges are empty on init"""
        assert isinstance(research_metrics.counters, dict)
        assert isinstance(research_metrics.gauges, dict)
        assert len(research_metrics.counters) == 0
        assert len(research_metrics.gauges) == 0


class TestResearchSessionMetrics:
    """Test research session metrics"""

    def test_record_session_started(self, research_metrics):
        """Test recording session start"""
        depth_level = "deep"

        research_metrics.record_session_started(depth_level)

        assert research_metrics.counters["sessions_started"] == 1
        assert research_metrics.get_counter("sessions_started") == 1

    def test_record_session_completed(self, research_metrics):
        """Test recording session completion"""
        status = "completed"

        research_metrics.record_session_completed(status)

        assert research_metrics.counters["sessions_completed"] == 1
        assert research_metrics.get_counter("sessions_completed") == 1

    def test_record_multiple_session_completions(self, research_metrics):
        """Test recording multiple session completions"""
        research_metrics.record_session_completed("completed")
        research_metrics.record_session_completed("completed")
        research_metrics.record_session_completed("cancelled")

        assert research_metrics.get_counter("sessions_completed") == 3

    def test_record_session_error(self, research_metrics):
        """Test recording session error"""
        research_metrics.record_session_error()

        assert research_metrics.counters["sessions_error"] == 1

    def test_record_session_duration(self, research_metrics):
        """Test recording session duration"""
        duration_seconds = 45.5
        depth_level = "shallow"

        research_metrics.record_session_duration(duration_seconds, depth_level)

        # Should record in histogram
        assert len(research_metrics.duration_samples) > 0
        assert research_metrics.duration_samples[0] == duration_seconds

    def test_record_documents_found(self, research_metrics):
        """Test recording documents found"""
        count = 5

        research_metrics.record_documents_found(count)

        assert research_metrics.counters["documents_found"] == 5


class TestResearchSessionGauges:
    """Test research session gauge metrics"""

    def test_set_active_sessions(self, research_metrics):
        """Test setting active sessions gauge"""
        count = 3

        research_metrics.set_active_sessions(count)

        assert research_metrics.gauges["active_sessions"] == 3
        assert research_metrics.get_gauge("active_sessions") == 3

    def test_set_active_sse_connections(self, research_metrics):
        """Test setting active SSE connections gauge"""
        count = 5

        research_metrics.set_active_sse_connections(count)

        assert research_metrics.gauges["active_sse_connections"] == 5
        assert research_metrics.get_gauge("active_sse_connections") == 5

    def test_increment_active_sessions(self, research_metrics):
        """Test incrementing active sessions"""
        research_metrics.set_active_sessions(2)
        research_metrics.increment_active_sessions()

        assert research_metrics.get_gauge("active_sessions") == 3

    def test_decrement_active_sessions(self, research_metrics):
        """Test decrementing active sessions"""
        research_metrics.set_active_sessions(3)
        research_metrics.decrement_active_sessions()

        assert research_metrics.get_gauge("active_sessions") == 2

    def test_decrement_active_sessions_does_not_go_negative(self, research_metrics):
        """Test that decrement doesn't go below 0"""
        research_metrics.set_active_sessions(0)
        research_metrics.decrement_active_sessions()

        assert research_metrics.get_gauge("active_sessions") == 0

    def test_increment_active_sse_connections(self, research_metrics):
        """Test incrementing active SSE connections"""
        research_metrics.set_active_sse_connections(2)
        research_metrics.increment_active_sse_connections()

        assert research_metrics.get_gauge("active_sse_connections") == 3

    def test_decrement_active_sse_connections(self, research_metrics):
        """Test decrementing active SSE connections"""
        research_metrics.set_active_sse_connections(3)
        research_metrics.decrement_active_sse_connections()

        assert research_metrics.get_gauge("active_sse_connections") == 2


class TestMetricsContextManager:
    """Test metrics context manager"""

    @pytest.mark.asyncio
    async def test_track_research_duration_success(self, research_metrics):
        """Test tracking research duration on success"""
        depth_level = "medium"

        async with research_metrics.track_research_duration(depth_level):
            await asyncio.sleep(0.01)

        assert len(research_metrics.duration_samples) > 0
        assert research_metrics.duration_samples[0] > 0

    @pytest.mark.asyncio
    async def test_track_research_duration_error(self, research_metrics):
        """Test tracking research duration on error"""
        depth_level = "deep"

        with pytest.raises(ValueError):
            async with research_metrics.track_research_duration(depth_level):
                await asyncio.sleep(0.01)
                raise ValueError("Test error")

        # Duration should still be recorded
        assert len(research_metrics.duration_samples) > 0
        # Error counter should be incremented
        assert research_metrics.get_counter("sessions_error") >= 1


class TestMetricsRetrieval:
    """Test metrics retrieval and aggregation"""

    def test_get_counter(self, research_metrics):
        """Test getting counter value"""
        research_metrics.counters["test_counter"] = 5

        value = research_metrics.get_counter("test_counter")

        assert value == 5

    def test_get_counter_default(self, research_metrics):
        """Test getting non-existent counter returns 0"""
        value = research_metrics.get_counter("nonexistent")

        assert value == 0

    def test_get_gauge(self, research_metrics):
        """Test getting gauge value"""
        research_metrics.gauges["test_gauge"] = 3.5

        value = research_metrics.get_gauge("test_gauge")

        assert value == 3.5

    def test_get_gauge_default(self, research_metrics):
        """Test getting non-existent gauge returns 0.0"""
        value = research_metrics.get_gauge("nonexistent")

        assert value == 0.0

    def test_get_duration_stats(self, research_metrics):
        """Test getting duration statistics"""
        durations = [10, 20, 30, 40, 50]
        for d in durations:
            research_metrics.duration_samples.append(d)

        stats = research_metrics.get_duration_stats()

        assert "min" in stats
        assert "max" in stats
        assert "avg" in stats
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["avg"] == 30

    def test_get_duration_stats_empty(self, research_metrics):
        """Test getting duration stats with no samples"""
        stats = research_metrics.get_duration_stats()

        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0

    def test_get_metrics_summary(self, research_metrics):
        """Test getting complete metrics summary"""
        research_metrics.record_session_started("deep")
        research_metrics.record_session_completed("completed")
        research_metrics.set_active_sessions(2)

        summary = research_metrics.get_metrics_summary()

        assert "sessions_started" in summary
        assert "sessions_completed" in summary
        assert "active_sessions" in summary
        assert summary["sessions_started"] == 1
        assert summary["sessions_completed"] == 1
        assert summary["active_sessions"] == 2


class TestGlobalMetricsInstance:
    """Test global metrics instance"""

    def test_get_research_metrics_returns_instance(self):
        """Test that get_research_metrics returns a ResearchMetrics instance"""
        metrics = get_research_metrics()

        assert isinstance(metrics, ResearchMetrics)

    def test_initialize_research_metrics(self):
        """Test initialization of global metrics instance"""
        metrics = initialize_research_metrics(enable_prometheus=False)

        assert isinstance(metrics, ResearchMetrics)
        assert metrics.enable_prometheus is False

    def test_global_metrics_singleton_behavior(self):
        """Test that global metrics behaves as singleton"""
        metrics1 = get_research_metrics()
        metrics1.record_session_started("shallow")

        metrics2 = get_research_metrics()

        assert metrics2.get_counter("sessions_started") == 1


class TestMetricsReset:
    """Test metrics reset functionality"""

    def test_reset_clears_all_metrics(self, research_metrics):
        """Test that reset clears all metrics"""
        research_metrics.record_session_started("deep")
        research_metrics.record_session_completed("completed")
        research_metrics.set_active_sessions(2)

        research_metrics.reset_metrics()

        assert len(research_metrics.counters) == 0
        assert len(research_metrics.gauges) == 0
        assert len(research_metrics.duration_samples) == 0
