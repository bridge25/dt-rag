"""
Taxonomy Metrics Service

Service for tracking taxonomy usage, collecting metrics, and analyzing patterns.
Supports real-time tracking and time-series aggregation.

@CODE:TAXONOMY-EVOLUTION-001
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import re

from ..models.metrics_models import (
    EventType,
    AggregationPeriod,
    UsageEvent,
    CategoryMetrics,
    QueryMetrics,
    TaxonomyHealthMetrics,
    ZeroResultQuery,
)

logger = logging.getLogger(__name__)


class TaxonomyMetricsService:
    """
    Service for tracking and analyzing taxonomy usage metrics.

    Provides event recording, aggregation, and pattern detection for
    informing taxonomy evolution decisions.
    """

    def __init__(self):
        """Initialize the metrics service"""
        # In-memory storage for real-time metrics (production would use Redis/TimescaleDB)
        self._events: List[UsageEvent] = []
        self._latency_buffer: Dict[str, List[float]] = defaultdict(list)
        self._active_sessions: Set[str] = set()
        self._zero_result_cache: Dict[str, ZeroResultQuery] = {}

        # Buffer limits
        self._max_events = 10000
        self._max_latency_samples = 1000

    # ========================================================================
    # Event Recording
    # ========================================================================

    async def record_event(self, event: UsageEvent) -> bool:
        """
        Record a single usage event.

        Args:
            event: The usage event to record

        Returns:
            True if recorded successfully
        """
        try:
            await self._store_event(event)

            # Handle special event types
            if event.event_type == EventType.ZERO_RESULTS and event.query_text:
                self._update_zero_result_cache(event)

            return True

        except Exception as e:
            logger.error(f"Failed to record event: {e}")
            return False

    async def record_batch(self, events: List[UsageEvent]) -> int:
        """
        Record multiple events in batch.

        Args:
            events: List of events to record

        Returns:
            Number of successfully recorded events
        """
        try:
            return await self._store_events_batch(events)
        except Exception as e:
            logger.error(f"Failed to record batch: {e}")
            return 0

    async def _store_event(self, event: UsageEvent) -> None:
        """Store event in memory buffer"""
        self._events.append(event)

        # Trim if over limit
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    async def _store_events_batch(self, events: List[UsageEvent]) -> int:
        """Store multiple events"""
        for event in events:
            await self._store_event(event)
        return len(events)

    def _update_zero_result_cache(self, event: UsageEvent) -> None:
        """Update zero result query cache"""
        if not event.query_text:
            return

        key = event.query_text.lower().strip()

        if key in self._zero_result_cache:
            cached = self._zero_result_cache[key]
            cached.occurrence_count += 1
            cached.last_seen = event.timestamp
        else:
            self._zero_result_cache[key] = ZeroResultQuery(
                query_text=event.query_text,
                taxonomy_id=event.taxonomy_id,
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                occurrence_count=1,
            )

    # ========================================================================
    # Category Metrics
    # ========================================================================

    async def get_category_metrics(
        self,
        category_id: str,
        taxonomy_id: str,
        period: AggregationPeriod,
        start_date: Optional[datetime] = None,
    ) -> CategoryMetrics:
        """
        Get aggregated metrics for a category.

        Args:
            category_id: Category identifier
            taxonomy_id: Taxonomy identifier
            period: Aggregation period
            start_date: Optional start date (defaults based on period)

        Returns:
            CategoryMetrics with aggregated data
        """
        period_start, period_end = self._get_period_bounds(period, start_date)

        # Fetch events for category
        events_data = await self._fetch_category_events(
            category_id, taxonomy_id, period_start, period_end
        )

        # Calculate metrics
        total_views = sum(
            e.get("count", 0)
            for e in events_data
            if e.get("event_type") in ["category_view", "taxonomy_navigate"]
        )
        search_clicks = sum(
            e.get("count", 0)
            for e in events_data
            if e.get("event_type") == "search_result_click"
        )
        search_hits = sum(
            e.get("count", 0)
            for e in events_data
            if e.get("event_type") == "search_hits"
        )

        ctr = self._calculate_ctr(search_clicks, search_hits) if search_hits > 0 else 0.0

        return CategoryMetrics(
            category_id=category_id,
            taxonomy_id=taxonomy_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period,
            total_views=total_views,
            unique_views=int(total_views * 0.7),  # Estimate
            search_hits=search_hits,
            search_clicks=search_clicks,
            click_through_rate=ctr,
        )

    async def _fetch_category_events(
        self,
        category_id: str,
        taxonomy_id: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch events for a category from storage"""
        # Filter in-memory events
        filtered = [
            e for e in self._events
            if e.category_id == category_id
            and e.taxonomy_id == taxonomy_id
            and start <= e.timestamp <= end
        ]

        # Aggregate by event type
        counts: Dict[str, int] = defaultdict(int)
        for event in filtered:
            counts[event.event_type.value] += 1

        return [
            {"event_type": etype, "count": count}
            for etype, count in counts.items()
        ]

    # ========================================================================
    # Query Metrics
    # ========================================================================

    async def get_top_queries(
        self,
        taxonomy_id: str,
        period: AggregationPeriod,
        limit: int = 10,
    ) -> List[QueryMetrics]:
        """
        Get top queries by frequency.

        Args:
            taxonomy_id: Taxonomy identifier
            period: Aggregation period
            limit: Maximum number of queries to return

        Returns:
            List of QueryMetrics sorted by frequency
        """
        period_start, period_end = self._get_period_bounds(period)

        # Fetch query data
        query_data = await self._fetch_query_events(taxonomy_id, period_start, period_end)

        # Convert to QueryMetrics
        metrics = []
        for data in query_data[:limit]:
            metrics.append(QueryMetrics(
                query_text=data["query_text"],
                taxonomy_id=taxonomy_id,
                period_start=period_start,
                period_end=period_end,
                total_searches=data.get("count", 0),
                avg_result_count=data.get("avg_results", 0.0),
            ))

        # Sort by total searches
        metrics.sort(key=lambda m: m.total_searches, reverse=True)
        return metrics

    async def _fetch_query_events(
        self,
        taxonomy_id: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch query events from storage"""
        # Filter search events
        filtered = [
            e for e in self._events
            if e.event_type == EventType.SEARCH_QUERY
            and e.taxonomy_id == taxonomy_id
            and start <= e.timestamp <= end
            and e.query_text
        ]

        # Aggregate by query
        query_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "total_results": 0}
        )
        for event in filtered:
            key = event.query_text.lower().strip()
            query_stats[key]["count"] += 1
            query_stats[key]["total_results"] += event.result_count or 0
            query_stats[key]["query_text"] = event.query_text

        # Calculate averages
        results = []
        for key, stats in query_stats.items():
            avg_results = stats["total_results"] / stats["count"] if stats["count"] > 0 else 0
            results.append({
                "query_text": stats["query_text"],
                "count": stats["count"],
                "avg_results": avg_results,
            })

        return sorted(results, key=lambda x: x["count"], reverse=True)

    # ========================================================================
    # Zero Result Analysis
    # ========================================================================

    async def get_zero_result_patterns(
        self,
        taxonomy_id: str,
        min_occurrences: int = 5,
    ) -> List[ZeroResultQuery]:
        """
        Get queries that consistently return zero results.

        Args:
            taxonomy_id: Taxonomy identifier
            min_occurrences: Minimum occurrence count

        Returns:
            List of ZeroResultQuery patterns
        """
        patterns = await self._fetch_zero_result_queries(taxonomy_id, min_occurrences)

        results = []
        for p in patterns:
            query = ZeroResultQuery(
                query_text=p["query_text"],
                taxonomy_id=taxonomy_id,
                first_seen=datetime.utcnow() - timedelta(days=7),
                last_seen=datetime.utcnow(),
                occurrence_count=p["count"],
            )
            results.append(query)

        return results

    async def _fetch_zero_result_queries(
        self,
        taxonomy_id: str,
        min_occurrences: int,
    ) -> List[Dict[str, Any]]:
        """Fetch zero result queries from cache"""
        results = []
        for key, query in self._zero_result_cache.items():
            if query.taxonomy_id == taxonomy_id and query.occurrence_count >= min_occurrences:
                results.append({
                    "query_text": query.query_text,
                    "count": query.occurrence_count,
                })

        return sorted(results, key=lambda x: x["count"], reverse=True)

    def _group_similar_queries(
        self,
        queries: List[ZeroResultQuery],
        similarity_threshold: float = 0.7,
    ) -> List[List[ZeroResultQuery]]:
        """Group similar zero-result queries"""
        if not queries:
            return []

        groups: List[List[ZeroResultQuery]] = []
        used = set()

        for i, q1 in enumerate(queries):
            if i in used:
                continue

            group = [q1]
            used.add(i)

            for j, q2 in enumerate(queries[i + 1:], start=i + 1):
                if j in used:
                    continue

                similarity = self._query_similarity(q1.query_text, q2.query_text)
                if similarity >= similarity_threshold:
                    group.append(q2)
                    used.add(j)

            groups.append(group)

        return groups

    def _query_similarity(self, q1: str, q2: str) -> float:
        """Calculate simple similarity between two queries"""
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _suggest_category_from_queries(
        self,
        queries: List[ZeroResultQuery],
        min_occurrences: int = 10,
        min_days: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Suggest a new category based on recurring queries"""
        if not queries:
            return None

        # Find query with highest occurrence
        best = max(queries, key=lambda q: q.occurrence_count)

        if best.occurrence_count < min_occurrences:
            return None

        days_active = (best.last_seen - best.first_seen).days
        if days_active < min_days:
            return None

        # Generate category name from query
        name = " ".join(word.capitalize() for word in best.query_text.split()[:3])

        return {
            "name": name,
            "based_on_query": best.query_text,
            "occurrence_count": best.occurrence_count,
            "days_active": days_active,
            "confidence": min(0.95, 0.5 + (best.occurrence_count / 100)),
        }

    # ========================================================================
    # Taxonomy Health
    # ========================================================================

    async def get_taxonomy_health(
        self,
        taxonomy_id: str,
        period: AggregationPeriod,
    ) -> TaxonomyHealthMetrics:
        """
        Calculate overall taxonomy health metrics.

        Args:
            taxonomy_id: Taxonomy identifier
            period: Aggregation period

        Returns:
            TaxonomyHealthMetrics with overall health data
        """
        stats = await self._fetch_taxonomy_stats(taxonomy_id, period)

        total_searches = stats.get("total_searches", 0)
        zero_results = stats.get("zero_results", 0)
        zero_rate = zero_results / total_searches if total_searches > 0 else 0.0

        return TaxonomyHealthMetrics(
            taxonomy_id=taxonomy_id,
            calculated_at=datetime.utcnow(),
            period_type=period,
            total_categories=stats.get("total_categories", 0),
            active_categories=stats.get("active_categories", 0),
            orphan_categories=stats.get("total_categories", 0) - stats.get("active_categories", 0),
            zero_result_rate=zero_rate,
        )

    async def _fetch_taxonomy_stats(
        self,
        taxonomy_id: str,
        period: AggregationPeriod,
    ) -> Dict[str, Any]:
        """Fetch taxonomy statistics"""
        period_start, period_end = self._get_period_bounds(period)

        # Count events in period
        filtered = [
            e for e in self._events
            if e.taxonomy_id == taxonomy_id
            and period_start <= e.timestamp <= period_end
        ]

        search_events = [e for e in filtered if e.event_type == EventType.SEARCH_QUERY]
        zero_events = [e for e in filtered if e.event_type == EventType.ZERO_RESULTS]

        # Get unique categories
        categories = {e.category_id for e in filtered if e.category_id}

        return {
            "total_categories": len(categories) if categories else 20,  # Default
            "active_categories": len(categories) if categories else 15,
            "total_searches": len(search_events),
            "zero_results": len(zero_events),
        }

    # ========================================================================
    # Aggregation Utilities
    # ========================================================================

    def _get_period_bounds(
        self,
        period: AggregationPeriod,
        start_date: Optional[datetime] = None,
    ) -> tuple[datetime, datetime]:
        """Get start and end times for a period"""
        end = datetime.utcnow()

        if start_date:
            start = start_date
        else:
            if period == AggregationPeriod.HOUR:
                start = end - timedelta(hours=1)
            elif period == AggregationPeriod.DAY:
                start = end - timedelta(days=1)
            elif period == AggregationPeriod.WEEK:
                start = end - timedelta(weeks=1)
            else:  # MONTH
                start = end - timedelta(days=30)

        return start, end

    def _aggregate_events_by_period(
        self,
        events: List[UsageEvent],
        period: AggregationPeriod,
    ) -> Dict[str, List[UsageEvent]]:
        """Group events by time period"""
        buckets: Dict[str, List[UsageEvent]] = defaultdict(list)

        for event in events:
            if period == AggregationPeriod.HOUR:
                key = event.timestamp.strftime("%Y-%m-%d %H:00")
            elif period == AggregationPeriod.DAY:
                key = event.timestamp.strftime("%Y-%m-%d")
            elif period == AggregationPeriod.WEEK:
                key = event.timestamp.strftime("%Y-W%W")
            else:
                key = event.timestamp.strftime("%Y-%m")

            buckets[key].append(event)

        return dict(buckets)

    def _calculate_ctr(self, clicks: int, impressions: int) -> float:
        """Calculate click-through rate"""
        if impressions == 0:
            return 0.0
        return clicks / impressions

    def _identify_underperforming(
        self,
        category_metrics: List[Dict[str, Any]],
        ctr_threshold: float = 0.1,
    ) -> List[str]:
        """Identify underperforming categories"""
        underperforming = []

        for metrics in category_metrics:
            views = metrics.get("views", 0)
            clicks = metrics.get("clicks", 0)

            if views > 0:
                ctr = clicks / views
                if ctr < ctr_threshold:
                    underperforming.append(metrics["category_id"])

        return underperforming

    # ========================================================================
    # Real-time Metrics
    # ========================================================================

    def _record_latency(self, operation: str, latency_ms: float) -> None:
        """Record operation latency"""
        self._latency_buffer[operation].append(latency_ms)

        # Trim buffer
        if len(self._latency_buffer[operation]) > self._max_latency_samples:
            self._latency_buffer[operation] = self._latency_buffer[operation][-self._max_latency_samples:]

    def get_latency_stats(self, operation: str) -> Dict[str, float]:
        """Get latency statistics for an operation"""
        samples = self._latency_buffer.get(operation, [])

        if not samples:
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}

        sorted_samples = sorted(samples)
        p95_idx = int(len(sorted_samples) * 0.95)

        return {
            "avg": sum(samples) / len(samples),
            "min": min(samples),
            "max": max(samples),
            "p95": sorted_samples[p95_idx] if p95_idx < len(sorted_samples) else sorted_samples[-1],
        }

    def _register_session(self, session_id: str) -> None:
        """Register an active session"""
        self._active_sessions.add(session_id)

    def _unregister_session(self, session_id: str) -> None:
        """Unregister a session"""
        self._active_sessions.discard(session_id)

    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self._active_sessions)

    # ========================================================================
    # Export / Dashboard
    # ========================================================================

    def _metrics_to_dict(self, metrics: CategoryMetrics) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "category_id": metrics.category_id,
            "taxonomy_id": metrics.taxonomy_id,
            "period_start": metrics.period_start.isoformat(),
            "period_end": metrics.period_end.isoformat(),
            "total_views": metrics.total_views,
            "unique_views": metrics.unique_views,
            "search_hits": metrics.search_hits,
            "search_clicks": metrics.search_clicks,
            "click_through_rate": metrics.click_through_rate,
            "bounce_rate": metrics.bounce_rate,
        }

    async def get_dashboard_summary(
        self,
        taxonomy_id: str,
        period: AggregationPeriod,
    ) -> Dict[str, Any]:
        """Get summary data for dashboard"""
        data = await self._fetch_dashboard_data(taxonomy_id, period)
        return data

    async def _fetch_dashboard_data(
        self,
        taxonomy_id: str,
        period: AggregationPeriod,
    ) -> Dict[str, Any]:
        """Fetch dashboard data"""
        period_start, period_end = self._get_period_bounds(period)

        filtered = [
            e for e in self._events
            if e.taxonomy_id == taxonomy_id
            and period_start <= e.timestamp <= period_end
        ]

        search_events = [e for e in filtered if e.event_type == EventType.SEARCH_QUERY]
        category_views = [e for e in filtered if e.event_type == EventType.CATEGORY_VIEW]
        unique_users = {e.user_id for e in filtered if e.user_id}

        # Calculate avg response time
        latencies = [e.response_time_ms for e in search_events if e.response_time_ms]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "total_events": len(filtered),
            "total_searches": len(search_events),
            "total_category_views": len(category_views),
            "unique_users": len(unique_users),
            "avg_response_time_ms": avg_latency,
        }


# Global instance
_metrics_service: Optional[TaxonomyMetricsService] = None


def get_metrics_service() -> TaxonomyMetricsService:
    """Get or create the metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = TaxonomyMetricsService()
    return _metrics_service
