"""
성능 메트릭 수집 및 Prometheus 익스포트 시스템
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import psutil
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# Prometheus 메트릭 (선택적)
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available, using built-in metrics only")


@dataclass
class MetricValue:
    """메트릭 값과 메타데이터"""

    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


@dataclass
class PerformanceSnapshot:
    """성능 스냅샷"""

    timestamp: datetime

    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Latency metrics (milliseconds)
    avg_latency: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0

    # Throughput
    qps: float = 0.0  # Queries per second

    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0

    # System metrics
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0

    # Search-specific metrics
    search_accuracy: float = 0.0
    avg_search_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LatencyTracker:
    """지연시간 추적기"""

    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.samples = deque(maxlen=max_samples)
        self.lock = threading.Lock()

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def add_sample(self, latency_ms: float) -> None:
        """지연시간 샘플 추가"""
        with self.lock:
            self.samples.append(latency_ms)

    def get_percentiles(self) -> Dict[str, float]:
        """백분위수 계산"""
        with self.lock:
            if not self.samples:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}

            sorted_samples = sorted(self.samples)
            n = len(sorted_samples)

            return {
                "p50": sorted_samples[int(n * 0.5)] if n > 0 else 0.0,
                "p95": sorted_samples[int(n * 0.95)] if n > 0 else 0.0,
                "p99": sorted_samples[int(n * 0.99)] if n > 0 else 0.0,
                "avg": sum(sorted_samples) / n if n > 0 else 0.0,
            }


class MetricsCollector:
    """종합 메트릭 수집기"""

    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE

        # 내장 메트릭 저장소
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)

        # 지연시간 추적기
        self.latency_tracker = LatencyTracker()

        # 성능 스냅샷 히스토리
        self.performance_history = deque(maxlen=1000)

        # Prometheus 메트릭 (사용 가능한 경우)
        if self.enable_prometheus:
            self._init_prometheus_metrics()

        # 시스템 모니터링
        self.start_time = datetime.now()
        self.last_snapshot_time = self.start_time

        logger.info(
            f"MetricsCollector initialized (Prometheus: {self.enable_prometheus})"
        )

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def _init_prometheus_metrics(self) -> None:
        """Prometheus 메트릭 초기화"""
        if not self.enable_prometheus:
            return

        # 요청 메트릭
        self.request_counter = Counter(
            "dt_rag_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )

        self.request_duration = Histogram(
            "dt_rag_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
        )

        # 검색 메트릭
        self.search_requests = Counter(
            "dt_rag_search_requests_total",
            "Total search requests",
            ["search_type", "status"],
        )

        self.search_duration = Histogram(
            "dt_rag_search_duration_seconds", "Search request duration", ["search_type"]
        )

        # 캐시 메트릭
        self.cache_operations = Counter(
            "dt_rag_cache_operations_total", "Cache operations", ["operation", "result"]
        )

        # 시스템 메트릭
        self.system_cpu = Gauge(
            "dt_rag_system_cpu_percent", "System CPU usage percentage"
        )

        self.system_memory = Gauge(
            "dt_rag_system_memory_mb", "System memory usage in MB"
        )

        # 성능 지표
        self.search_accuracy = Gauge("dt_rag_search_accuracy", "Search accuracy score")

        self.qps_gauge = Gauge("dt_rag_queries_per_second", "Queries per second")

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    @asynccontextmanager
    async def track_operation(self, operation_name: str, labels: Dict[str, str] = None):  # type: ignore[misc]
        """작업 시간 추적 컨텍스트 매니저"""
        labels = labels or {}
        start_time = time.time()

        try:
            yield
            # 성공한 경우
            duration = (time.time() - start_time) * 1000  # ms
            self.record_latency(operation_name, duration, labels)
            self.increment_counter(f"{operation_name}_success", labels)

        except Exception:
            # 실패한 경우
            duration = (time.time() - start_time) * 1000  # ms
            self.record_latency(operation_name, duration, labels)
            self.increment_counter(f"{operation_name}_error", labels)
            raise

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def record_latency(
        self, operation: str, latency_ms: float, labels: Dict[str, str] = None
    ) -> None:
        """지연시간 기록"""
        self.latency_tracker.add_sample(latency_ms)

        metric_value = MetricValue(
            value=latency_ms, timestamp=datetime.now(), labels=labels or {}
        )
        self.metrics[f"{operation}_latency"].append(metric_value)

        # Prometheus 메트릭 업데이트
        if self.enable_prometheus and hasattr(self, "request_duration"):
            labels_list = [labels.get("method", ""), labels.get("endpoint", "")]
            self.request_duration.labels(*labels_list).observe(latency_ms / 1000)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def increment_counter(
        self, counter_name: str, labels: Dict[str, str] = None, value: int = 1
    ) -> None:
        """카운터 증가"""
        self.counters[counter_name] += value

        metric_value = MetricValue(
            value=value, timestamp=datetime.now(), labels=labels or {}
        )
        self.metrics[counter_name].append(metric_value)

        # Prometheus 카운터 업데이트
        if self.enable_prometheus:
            if "request" in counter_name and hasattr(self, "request_counter"):
                method = labels.get("method", "") if labels else ""
                endpoint = labels.get("endpoint", "") if labels else ""
                status = labels.get("status", "") if labels else ""
                self.request_counter.labels(method, endpoint, status).inc(value)
            elif "search" in counter_name and hasattr(self, "search_requests"):
                search_type = labels.get("search_type", "") if labels else ""
                status = labels.get("status", "") if labels else ""
                self.search_requests.labels(search_type, status).inc(value)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def set_gauge(self, gauge_name: str, value: float, labels: Dict[str, str] = None) -> None:
        """게이지 값 설정"""
        self.gauges[gauge_name] = value

        metric_value = MetricValue(
            value=value, timestamp=datetime.now(), labels=labels or {}
        )
        self.metrics[gauge_name].append(metric_value)

        # Prometheus 게이지 업데이트
        if self.enable_prometheus:
            if gauge_name == "cpu_usage" and hasattr(self, "system_cpu"):
                self.system_cpu.set(value)
            elif gauge_name == "memory_usage_mb" and hasattr(self, "system_memory"):
                self.system_memory.set(value)
            elif gauge_name == "search_accuracy" and hasattr(self, "search_accuracy"):
                self.search_accuracy.set(value)
            elif gauge_name == "qps" and hasattr(self, "qps_gauge"):
                self.qps_gauge.set(value)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def record_cache_operation(
        self, operation: str, result: str, labels: Dict[str, str] = None
    ) -> None:
        """캐시 작업 기록"""
        all_labels = {"operation": operation, "result": result}
        if labels:
            all_labels.update(labels)

        self.increment_counter("cache_operations", all_labels)

        # Prometheus 캐시 메트릭
        if self.enable_prometheus and hasattr(self, "cache_operations"):
            self.cache_operations.labels(operation, result).inc()

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def update_system_metrics(self) -> None:
        """시스템 메트릭 업데이트"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent()
            self.set_gauge("cpu_usage", cpu_percent)

            # 메모리 사용량
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            self.set_gauge("memory_usage_mb", memory_mb)

            # 네트워크 통계 (옵션)
            net_io = psutil.net_io_counters()
            self.set_gauge("network_bytes_sent", net_io.bytes_sent)
            self.set_gauge("network_bytes_recv", net_io.bytes_recv)

        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")

    def calculate_performance_snapshot(self) -> PerformanceSnapshot:
        """현재 성능 스냅샷 계산"""
        now = datetime.now()

        # 지연시간 통계
        latency_stats = self.latency_tracker.get_percentiles()

        # 요청 통계 계산
        total_requests = self.counters.get("requests_total", 0)
        successful_requests = self.counters.get("requests_success", 0)
        failed_requests = self.counters.get("requests_error", 0)

        # QPS 계산
        time_diff = (now - self.last_snapshot_time).total_seconds()
        if time_diff > 0:
            recent_requests = total_requests  # 간단한 구현
            qps = recent_requests / time_diff if time_diff > 0 else 0
        else:
            qps = 0

        # 캐시 히트율 계산
        cache_hits = self.counters.get("cache_hits", 0)
        cache_misses = self.counters.get("cache_misses", 0)
        total_cache_ops = cache_hits + cache_misses
        cache_hit_rate = (
            (cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
        )

        snapshot = PerformanceSnapshot(
            timestamp=now,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_latency=latency_stats["avg"],
            p50_latency=latency_stats["p50"],
            p95_latency=latency_stats["p95"],
            p99_latency=latency_stats["p99"],
            qps=qps,
            cache_hit_rate=cache_hit_rate,
            cache_miss_rate=100 - cache_hit_rate,
            cpu_usage=self.gauges.get("cpu_usage", 0),
            memory_usage_mb=self.gauges.get("memory_usage_mb", 0),
            search_accuracy=self.gauges.get("search_accuracy", 0),
            avg_search_time=self.gauges.get("avg_search_time", 0),
        )

        self.performance_history.append(snapshot)
        self.last_snapshot_time = now

        return snapshot

    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약 조회"""
        snapshot = self.calculate_performance_snapshot()

        return {
            "current_performance": snapshot.to_dict(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_metrics_collected": sum(
                len(values) for values in self.metrics.values()
            ),
            "prometheus_enabled": self.enable_prometheus,
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            },
        }

    def get_performance_trend(self, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """성능 트렌드 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_snapshots = [
            snapshot
            for snapshot in self.performance_history
            if snapshot.timestamp >= cutoff_time
        ]

        return [snapshot.to_dict() for snapshot in recent_snapshots]

    def export_prometheus_metrics(self) -> str:
        """Prometheus 메트릭 익스포트"""
        if not self.enable_prometheus:
            return "# Prometheus not enabled\n"

        # 시스템 메트릭 업데이트
        self.update_system_metrics()

        return generate_latest()

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def reset_metrics(self) -> None:
        """메트릭 초기화"""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.performance_history.clear()
        self.latency_tracker = LatencyTracker()
        self.start_time = datetime.now()
        self.last_snapshot_time = self.start_time

        logger.info("Metrics reset completed")


# 전역 메트릭 수집기 인스턴스
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """전역 메트릭 수집기 조회"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def initialize_metrics_collector(enable_prometheus: bool = True) -> MetricsCollector:
    """메트릭 수집기 초기화"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(enable_prometheus=enable_prometheus)
    return _metrics_collector


# 데코레이터
def track_performance(operation_name: str) -> Any:
    """성능 추적 데코레이터"""

    def decorator(func: Any) -> Any:
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            collector = get_metrics_collector()
            async with collector.track_operation(operation_name):
                return await func(*args, **kwargs)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            collector = get_metrics_collector()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                collector.record_latency(operation_name, duration)
                collector.increment_counter(f"{operation_name}_success")
                return result
            except Exception:
                duration = (time.time() - start_time) * 1000
                collector.record_latency(operation_name, duration)
                collector.increment_counter(f"{operation_name}_error")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
