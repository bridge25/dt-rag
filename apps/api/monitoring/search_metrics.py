"""
검색 메트릭 전용 수집기

이 모듈은 검색 관련 메트릭을 수집하고 관리합니다.
MetricsCollector를 래핑하여 검색 특화 인터페이스를 제공합니다.
"""

import logging
from typing import Dict, Any, Optional
from collections import defaultdict

from .metrics import get_metrics_collector, MetricsCollector

logger = logging.getLogger(__name__)


class SearchMetrics:
    """검색 메트릭 전용 수집기

    검색 작업에 대한 메트릭을 수집하고 추적합니다.
    내부적으로 MetricsCollector를 사용하여 메트릭을 저장합니다.
    """

    def __init__(self):
        """SearchMetrics 초기화"""
        self.metrics_collector = get_metrics_collector()
        self._search_counts: Dict[str, int] = defaultdict(int)
        self._search_latencies: Dict[str, list] = defaultdict(list)
        logger.info("SearchMetrics initialized")

    def record_search(
        self,
        search_type: str,
        latency_seconds: float,
        error: bool = False
    ) -> None:
        """검색 메트릭 기록

        Args:
            search_type: 검색 유형 (예: "semantic", "hybrid", "keyword")
            latency_seconds: 검색 소요 시간 (초 단위)
            error: 에러 발생 여부 (기본값: False)
        """
        # 지연 시간을 밀리초로 변환하여 기록
        latency_ms = latency_seconds * 1000
        self.metrics_collector.record_latency(
            f"search_{search_type}",
            latency_ms
        )

        # 성공/실패 카운터 증가
        status = "error" if error else "success"
        self.metrics_collector.increment_counter(
            f"search_{status}",
            {"search_type": search_type}
        )

        # 내부 통계 업데이트
        self._search_counts[search_type] += 1
        self._search_latencies[search_type].append(latency_ms)

        logger.debug(
            f"Recorded search metric: type={search_type}, "
            f"latency={latency_ms:.2f}ms, error={error}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 조회

        Returns:
            현재까지 수집된 메트릭 요약
        """
        summary = self.metrics_collector.get_metrics_summary()

        # 검색 특화 통계 추가
        search_stats = {
            "search_counts": dict(self._search_counts),
            "search_types": list(self._search_counts.keys())
        }

        # 평균 지연 시간 계산
        avg_latencies = {}
        for search_type, latencies in self._search_latencies.items():
            if latencies:
                avg_latencies[search_type] = sum(latencies) / len(latencies)
        search_stats["avg_latencies_ms"] = avg_latencies

        summary["search_metrics"] = search_stats
        return summary

    def reset(self) -> None:
        """검색 메트릭 초기화

        주의: 이 메서드는 검색 관련 내부 통계만 초기화합니다.
        MetricsCollector의 전역 메트릭은 유지됩니다.
        """
        self._search_counts.clear()
        self._search_latencies.clear()
        logger.info("SearchMetrics reset")


# 전역 SearchMetrics 인스턴스
_search_metrics: Optional[SearchMetrics] = None


def get_search_metrics() -> SearchMetrics:
    """SearchMetrics 싱글톤 인스턴스 조회

    Returns:
        SearchMetrics 인스턴스
    """
    global _search_metrics
    if _search_metrics is None:
        _search_metrics = SearchMetrics()
    return _search_metrics
