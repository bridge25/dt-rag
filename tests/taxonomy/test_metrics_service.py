"""
Tests for Taxonomy Metrics Service

Tests for usage tracking, metrics aggregation, and analytics.
TDD RED phase - tests written before implementation.

@TEST:TAXONOMY-EVOLUTION-001
"""

import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.models.metrics_models import (
    EventType,
    AggregationPeriod,
    UsageEvent,
    CategoryMetrics,
    QueryMetrics,
    TaxonomyHealthMetrics,
    ZeroResultQuery,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_events() -> List[UsageEvent]:
    """Sample usage events for testing"""
    base_time = datetime.utcnow()
    return [
        UsageEvent(
            event_id="evt_1",
            event_type=EventType.SEARCH_QUERY,
            timestamp=base_time - timedelta(hours=1),
            taxonomy_id="tax_1",
            query_text="machine learning",
            result_count=10,
            response_time_ms=150.0,
        ),
        UsageEvent(
            event_id="evt_2",
            event_type=EventType.SEARCH_RESULT_CLICK,
            timestamp=base_time - timedelta(hours=1),
            taxonomy_id="tax_1",
            category_id="cat_ml",
            document_id="doc_1",
        ),
        UsageEvent(
            event_id="evt_3",
            event_type=EventType.CATEGORY_VIEW,
            timestamp=base_time - timedelta(minutes=30),
            taxonomy_id="tax_1",
            category_id="cat_ml",
        ),
        UsageEvent(
            event_id="evt_4",
            event_type=EventType.SEARCH_QUERY,
            timestamp=base_time - timedelta(minutes=20),
            taxonomy_id="tax_1",
            query_text="quantum computing",
            result_count=0,  # Zero result
            response_time_ms=50.0,
        ),
        UsageEvent(
            event_id="evt_5",
            event_type=EventType.ZERO_RESULTS,
            timestamp=base_time - timedelta(minutes=20),
            taxonomy_id="tax_1",
            query_text="quantum computing",
        ),
    ]


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    return mock


# ============================================================================
# Test: UsageEvent
# ============================================================================


class TestUsageEvent:
    """Tests for UsageEvent dataclass"""

    def test_create_event(self):
        """Should create event with required fields"""
        event = UsageEvent(
            event_id="evt_test",
            event_type=EventType.SEARCH_QUERY,
            timestamp=datetime.utcnow(),
            taxonomy_id="tax_1",
            query_text="test query",
        )

        assert event.event_id == "evt_test"
        assert event.event_type == EventType.SEARCH_QUERY
        assert event.query_text == "test query"

    def test_auto_generate_id(self):
        """Should auto-generate ID if empty"""
        event = UsageEvent(
            event_id="",
            event_type=EventType.CATEGORY_VIEW,
            timestamp=datetime.utcnow(),
            taxonomy_id="tax_1",
        )

        assert event.event_id.startswith("evt_")

    def test_optional_fields(self):
        """Should handle optional fields"""
        event = UsageEvent(
            event_id="evt_1",
            event_type=EventType.DOCUMENT_VIEW,
            timestamp=datetime.utcnow(),
            taxonomy_id="tax_1",
            category_id="cat_1",
            document_id="doc_1",
            response_time_ms=100.0,
        )

        assert event.category_id == "cat_1"
        assert event.document_id == "doc_1"
        assert event.response_time_ms == 100.0


# ============================================================================
# Test: TaxonomyMetricsService
# ============================================================================


class TestTaxonomyMetricsService:
    """Tests for TaxonomyMetricsService"""

    @pytest.mark.asyncio
    async def test_record_event(self, mock_db_session):
        """Should record a usage event"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()
        event = UsageEvent(
            event_id="evt_test",
            event_type=EventType.SEARCH_QUERY,
            timestamp=datetime.utcnow(),
            taxonomy_id="tax_1",
            query_text="test query",
        )

        with patch.object(service, "_store_event", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = True
            result = await service.record_event(event)

            assert result is True
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_batch_events(self, sample_events):
        """Should record multiple events in batch"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        with patch.object(service, "_store_events_batch", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = len(sample_events)
            result = await service.record_batch(sample_events)

            assert result == len(sample_events)

    @pytest.mark.asyncio
    async def test_get_category_metrics(self):
        """Should calculate category metrics for a period"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        with patch.object(service, "_fetch_category_events", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"event_type": "category_view", "count": 100},
                {"event_type": "search_result_click", "count": 25},
            ]

            metrics = await service.get_category_metrics(
                category_id="cat_1",
                taxonomy_id="tax_1",
                period=AggregationPeriod.DAY,
            )

            assert metrics is not None
            assert metrics.category_id == "cat_1"
            assert metrics.total_views >= 0

    @pytest.mark.asyncio
    async def test_get_query_metrics(self):
        """Should aggregate metrics for queries"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        with patch.object(service, "_fetch_query_events", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"query_text": "machine learning", "count": 50, "avg_results": 8.5},
                {"query_text": "deep learning", "count": 30, "avg_results": 12.0},
            ]

            metrics = await service.get_top_queries(
                taxonomy_id="tax_1",
                period=AggregationPeriod.WEEK,
                limit=10,
            )

            assert len(metrics) > 0
            assert metrics[0].total_searches >= metrics[-1].total_searches

    @pytest.mark.asyncio
    async def test_detect_zero_result_patterns(self, sample_events):
        """Should identify queries with zero results"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        with patch.object(service, "_fetch_zero_result_queries", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"query_text": "quantum computing", "count": 15},
                {"query_text": "blockchain", "count": 8},
            ]

            patterns = await service.get_zero_result_patterns(
                taxonomy_id="tax_1",
                min_occurrences=5,
            )

            assert len(patterns) > 0
            assert patterns[0].occurrence_count >= 5

    @pytest.mark.asyncio
    async def test_calculate_taxonomy_health(self):
        """Should calculate overall taxonomy health metrics"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        with patch.object(service, "_fetch_taxonomy_stats", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "total_categories": 20,
                "active_categories": 15,
                "total_searches": 1000,
                "zero_results": 50,
            }

            health = await service.get_taxonomy_health(
                taxonomy_id="tax_1",
                period=AggregationPeriod.WEEK,
            )

            assert health is not None
            assert health.total_categories == 20
            assert health.active_categories == 15
            assert health.zero_result_rate == 0.05


# ============================================================================
# Test: Aggregation Functions
# ============================================================================


class TestAggregationFunctions:
    """Tests for metrics aggregation"""

    @pytest.mark.asyncio
    async def test_aggregate_by_period(self, sample_events):
        """Should aggregate events by time period"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        aggregated = service._aggregate_events_by_period(
            events=sample_events,
            period=AggregationPeriod.HOUR,
        )

        assert len(aggregated) > 0

    @pytest.mark.asyncio
    async def test_calculate_click_through_rate(self):
        """Should calculate CTR correctly"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        ctr = service._calculate_ctr(clicks=25, impressions=100)
        assert ctr == 0.25

        # Handle zero impressions
        ctr_zero = service._calculate_ctr(clicks=0, impressions=0)
        assert ctr_zero == 0.0

    @pytest.mark.asyncio
    async def test_identify_underperforming_categories(self):
        """Should identify categories below threshold"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        category_metrics = [
            {"category_id": "cat_1", "views": 100, "clicks": 50},
            {"category_id": "cat_2", "views": 100, "clicks": 5},  # Low CTR
            {"category_id": "cat_3", "views": 100, "clicks": 45},
        ]

        underperforming = service._identify_underperforming(
            category_metrics,
            ctr_threshold=0.1,
        )

        assert "cat_2" in underperforming


# ============================================================================
# Test: Zero Result Analysis
# ============================================================================


class TestZeroResultAnalysis:
    """Tests for zero result query analysis"""

    @pytest.mark.asyncio
    async def test_group_similar_queries(self):
        """Should group similar zero-result queries"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        queries = [
            ZeroResultQuery(
                query_text="quantum computing",
                taxonomy_id="tax_1",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                occurrence_count=10,
            ),
            ZeroResultQuery(
                query_text="quantum computers",
                taxonomy_id="tax_1",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                occurrence_count=5,
            ),
            ZeroResultQuery(
                query_text="blockchain",
                taxonomy_id="tax_1",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                occurrence_count=8,
            ),
        ]

        grouped = service._group_similar_queries(queries, similarity_threshold=0.7)

        # Quantum queries should be grouped together
        assert len(grouped) <= len(queries)

    @pytest.mark.asyncio
    async def test_suggest_category_from_queries(self):
        """Should suggest new category from recurring queries"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        queries = [
            ZeroResultQuery(
                query_text="quantum computing",
                taxonomy_id="tax_1",
                first_seen=datetime.utcnow() - timedelta(days=7),
                last_seen=datetime.utcnow(),
                occurrence_count=20,
            ),
        ]

        suggestion = service._suggest_category_from_queries(
            queries,
            min_occurrences=10,
            min_days=5,
        )

        assert suggestion is not None
        assert "quantum" in suggestion["name"].lower()


# ============================================================================
# Test: Real-time Metrics
# ============================================================================


class TestRealTimeMetrics:
    """Tests for real-time metrics tracking"""

    @pytest.mark.asyncio
    async def test_track_search_latency(self):
        """Should track search response times"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        # Record several searches
        latencies = [100, 150, 200, 50, 300]
        for latency in latencies:
            service._record_latency("search", latency)

        stats = service.get_latency_stats("search")

        assert stats["avg"] == 160.0
        assert stats["min"] == 50
        assert stats["max"] == 300

    @pytest.mark.asyncio
    async def test_track_active_sessions(self):
        """Should track active session count"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        # Simulate sessions
        service._register_session("session_1")
        service._register_session("session_2")
        service._register_session("session_3")
        service._unregister_session("session_1")

        assert service.get_active_session_count() == 2


# ============================================================================
# Test: Metrics Export
# ============================================================================


class TestMetricsExport:
    """Tests for metrics export functionality"""

    @pytest.mark.asyncio
    async def test_export_to_dict(self):
        """Should export metrics to dictionary format"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        metrics = CategoryMetrics(
            category_id="cat_1",
            taxonomy_id="tax_1",
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow(),
            period_type=AggregationPeriod.DAY,
            total_views=100,
            search_hits=50,
            click_through_rate=0.25,
        )

        exported = service._metrics_to_dict(metrics)

        assert exported["category_id"] == "cat_1"
        assert exported["total_views"] == 100
        assert "period_start" in exported

    @pytest.mark.asyncio
    async def test_get_summary_dashboard(self):
        """Should generate summary for dashboard"""
        from apps.api.services.taxonomy_metrics_service import TaxonomyMetricsService

        service = TaxonomyMetricsService()

        with patch.object(service, "_fetch_dashboard_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "total_events": 5000,
                "total_searches": 1000,
                "unique_users": 250,
                "avg_response_time_ms": 120.5,
            }

            summary = await service.get_dashboard_summary(
                taxonomy_id="tax_1",
                period=AggregationPeriod.WEEK,
            )

            assert summary is not None
            assert summary["total_events"] == 5000
            assert summary["unique_users"] == 250
