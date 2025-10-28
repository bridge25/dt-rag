"""
실시간 모니터링 대시보드
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .metrics import get_metrics_collector
from .health_check import get_health_checker, HealthStatus

logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """모니터링 대시보드"""

    def __init__(self) -> None:
        self.metrics_collector = get_metrics_collector()
        self.health_checker = get_health_checker()

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 전체 데이터 조회"""
        # 병렬로 데이터 수집
        health_task = self.health_checker.get_system_health()
        metrics_task = asyncio.create_task(self._get_current_metrics())
        performance_task = asyncio.create_task(self._get_performance_summary())

        system_health, current_metrics, performance_summary = await asyncio.gather(
            health_task, metrics_task, performance_task
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": system_health.to_dict(),
            "current_metrics": current_metrics,
            "performance_summary": performance_summary,
            "alerts": await self._get_active_alerts(),
            "system_info": await self._get_system_info(),
        }

    async def _get_current_metrics(self) -> Dict[str, Any]:
        """현재 메트릭 조회"""
        summary = self.metrics_collector.get_metrics_summary()
        return {
            "performance": summary["current_performance"],
            "uptime_seconds": summary["uptime_seconds"],
            "prometheus_enabled": summary["prometheus_enabled"],
        }

    async def _get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보"""
        # 지난 1시간 성능 트렌드
        trend_data = self.metrics_collector.get_performance_trend(duration_minutes=60)

        if not trend_data:
            return {
                "trend_available": False,
                "message": "No performance data available",
            }

        # 통계 계산
        latencies = [
            data["p95_latency"] for data in trend_data if data["p95_latency"] > 0
        ]
        qps_values = [data["qps"] for data in trend_data if data["qps"] > 0]

        return {
            "trend_available": True,
            "sample_count": len(trend_data),
            "time_range_minutes": 60,
            "latency_stats": {
                "avg_p95_ms": (
                    round(sum(latencies) / len(latencies), 2) if latencies else 0
                ),
                "max_p95_ms": max(latencies) if latencies else 0,
                "min_p95_ms": min(latencies) if latencies else 0,
            },
            "throughput_stats": {
                "avg_qps": (
                    round(sum(qps_values) / len(qps_values), 2) if qps_values else 0
                ),
                "max_qps": max(qps_values) if qps_values else 0,
                "min_qps": min(qps_values) if qps_values else 0,
            },
            "recent_samples": trend_data[-10:],  # 최근 10개 샘플
        }

    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """활성 알람 조회"""
        alerts = []

        # 시스템 헬스 기반 알람
        health = await self.health_checker.get_system_health()

        if health.overall_status == HealthStatus.UNHEALTHY:
            alerts.append(
                {
                    "level": "critical",
                    "type": "system_health",
                    "message": "System is unhealthy",
                    "timestamp": health.timestamp.isoformat(),
                    "details": [
                        comp.name
                        for comp in health.components
                        if comp.status == HealthStatus.UNHEALTHY
                    ],
                }
            )
        elif health.overall_status == HealthStatus.DEGRADED:
            alerts.append(
                {
                    "level": "warning",
                    "type": "system_health",
                    "message": "System performance is degraded",
                    "timestamp": health.timestamp.isoformat(),
                    "details": [
                        comp.name
                        for comp in health.components
                        if comp.status == HealthStatus.DEGRADED
                    ],
                }
            )

        # 성능 기반 알람
        current_snapshot = self.metrics_collector.calculate_performance_snapshot()

        # P95 지연시간 체크 (목표: 1000ms)
        if current_snapshot.p95_latency > 1000:
            alerts.append(
                {
                    "level": (
                        "critical" if current_snapshot.p95_latency > 2000 else "warning"
                    ),
                    "type": "performance",
                    "message": f"High P95 latency: {current_snapshot.p95_latency:.0f}ms",
                    "timestamp": current_snapshot.timestamp.isoformat(),
                    "threshold": 1000,
                    "current_value": current_snapshot.p95_latency,
                }
            )

        # 에러율 체크 (목표: 1% 미만)
        if current_snapshot.total_requests > 0:
            error_rate = (
                current_snapshot.failed_requests / current_snapshot.total_requests
            ) * 100
            if error_rate > 1.0:
                alerts.append(
                    {
                        "level": "critical" if error_rate > 5.0 else "warning",
                        "type": "error_rate",
                        "message": f"High error rate: {error_rate:.1f}%",
                        "timestamp": current_snapshot.timestamp.isoformat(),
                        "threshold": 1.0,
                        "current_value": error_rate,
                    }
                )

        # 캐시 히트율 체크 (목표: 70% 이상)
        if current_snapshot.cache_hit_rate < 70:
            alerts.append(
                {
                    "level": "warning",
                    "type": "cache_performance",
                    "message": f"Low cache hit rate: {current_snapshot.cache_hit_rate:.1f}%",
                    "timestamp": current_snapshot.timestamp.isoformat(),
                    "threshold": 70.0,
                    "current_value": current_snapshot.cache_hit_rate,
                }
            )

        return alerts

    async def _get_system_info(self) -> Dict[str, Any]:
        """시스템 정보"""
        return {
            "version": "1.8.1",
            "environment": "testing",  # TODO: 환경변수에서 읽기
            "features": {
                "hybrid_search": True,
                "classification": True,
                "monitoring": True,
                "caching": True,
            },
        }

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """실시간 메트릭 (짧은 주기 업데이트용)"""
        snapshot = self.metrics_collector.calculate_performance_snapshot()
        health_status = self.health_checker.get_cached_health()

        return {
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "p95_latency_ms": snapshot.p95_latency,
                "qps": snapshot.qps,
                "error_rate": (
                    (snapshot.failed_requests / max(snapshot.total_requests, 1)) * 100
                ),
                "cache_hit_rate": snapshot.cache_hit_rate,
            },
            "system": {
                "cpu_percent": snapshot.cpu_usage,
                "memory_mb": snapshot.memory_usage_mb,
                "overall_health": health_status.get("overall_status", "unknown"),
            },
        }

    async def get_search_analytics(self) -> Dict[str, Any]:
        """검색 분석 데이터"""
        # 캐시에서 검색 통계 조회
        try:
            from apps.api.cache.search_cache import get_search_cache

            cache = await get_search_cache()
            cache_stats = await cache.get_cache_stats()
        except Exception as e:
            logger.warning(f"Failed to get search cache stats: {e}")
            cache_stats = {}

        return {
            "cache_performance": cache_stats,
            "search_metrics": {
                "total_searches": self.metrics_collector.counters.get(
                    "search_total", 0
                ),
                "successful_searches": self.metrics_collector.counters.get(
                    "search_success", 0
                ),
                "failed_searches": self.metrics_collector.counters.get(
                    "search_error", 0
                ),
                "avg_search_time_ms": self.metrics_collector.gauges.get(
                    "avg_search_time", 0
                ),
            },
        }

    async def export_metrics_data(self, format: str = "json") -> str:
        """메트릭 데이터 익스포트"""
        if format.lower() == "prometheus":
            return self.metrics_collector.export_prometheus_metrics()

        # JSON 형식으로 익스포트
        dashboard_data = await self.get_dashboard_data()

        def json_serializer(obj: Any) -> Any:
            """JSON 직렬화를 위한 커스텀 직렬화 함수"""
            if hasattr(obj, "isoformat"):  # datetime 객체
                return obj.isoformat()
            elif hasattr(obj, "__dict__"):  # 일반 객체
                return str(obj)
            else:
                return str(obj)

        if format.lower() == "json":
            return json.dumps(
                dashboard_data, indent=2, ensure_ascii=False, default=json_serializer
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """성능 리포트 생성"""
        # 지정된 시간 동안의 성능 데이터 수집
        trend_data = self.metrics_collector.get_performance_trend(
            duration_minutes=hours * 60
        )

        if not trend_data:
            return {
                "status": "no_data",
                "message": f"No performance data available for the last {hours} hours",
            }

        # 성능 지표 분석
        latencies = [
            data["p95_latency"] for data in trend_data if data["p95_latency"] > 0
        ]
        qps_values = [data["qps"] for data in trend_data]
        error_rates = []

        for data in trend_data:
            if data["total_requests"] > 0:
                error_rate = (data["failed_requests"] / data["total_requests"]) * 100
                error_rates.append(error_rate)

        # SLO 준수 확인
        slo_compliance = {
            "latency_p95_target_ms": 1000,
            "latency_compliance": (
                sum(1 for lat in latencies if lat <= 1000) / len(latencies) * 100
                if latencies
                else 100
            ),
            "error_rate_target_percent": 1.0,
            "error_rate_compliance": (
                sum(1 for err in error_rates if err <= 1.0) / len(error_rates) * 100
                if error_rates
                else 100
            ),
            "cache_hit_rate_target_percent": 70.0,
            "cache_hit_rate_compliance": sum(
                1 for data in trend_data if data["cache_hit_rate"] >= 70
            )
            / len(trend_data)
            * 100,
        }

        return {
            "status": "success",
            "report_period_hours": hours,
            "sample_count": len(trend_data),
            "performance_summary": {
                "latency": {
                    "avg_p95_ms": (
                        round(sum(latencies) / len(latencies), 2) if latencies else 0
                    ),
                    "max_p95_ms": max(latencies) if latencies else 0,
                    "min_p95_ms": min(latencies) if latencies else 0,
                },
                "throughput": {
                    "avg_qps": (
                        round(sum(qps_values) / len(qps_values), 2) if qps_values else 0
                    ),
                    "max_qps": max(qps_values) if qps_values else 0,
                    "peak_hour": None,  # TODO: 시간별 분석
                },
                "reliability": {
                    "avg_error_rate": (
                        round(sum(error_rates) / len(error_rates), 2)
                        if error_rates
                        else 0
                    ),
                    "max_error_rate": max(error_rates) if error_rates else 0,
                    "total_requests": sum(
                        data["total_requests"] for data in trend_data
                    ),
                    "total_errors": sum(data["failed_requests"] for data in trend_data),
                },
            },
            "slo_compliance": slo_compliance,
            "recommendations": self._generate_performance_recommendations(
                slo_compliance, trend_data
            ),
        }

    def _generate_performance_recommendations(
        self, slo_compliance: Dict[str, Any], trend_data: List[Dict[str, Any]]
    ) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []

        # 지연시간 개선
        if slo_compliance["latency_compliance"] < 95:
            recommendations.append(
                "Consider optimizing database queries or adding more caching layers"
            )

        # 에러율 개선
        if slo_compliance["error_rate_compliance"] < 99:
            recommendations.append(
                "Investigate error patterns and improve error handling"
            )

        # 캐시 성능 개선
        if slo_compliance["cache_hit_rate_compliance"] < 90:
            recommendations.append("Review cache TTL settings and warm-up strategies")

        # 자원 사용률 체크
        recent_data = trend_data[-10:] if len(trend_data) >= 10 else trend_data
        avg_cpu = sum(data["cpu_usage"] for data in recent_data) / len(recent_data)

        if avg_cpu > 80:
            recommendations.append(
                "High CPU usage detected - consider scaling or optimization"
            )

        if not recommendations:
            recommendations.append("System performance is within acceptable limits")

        return recommendations


# 전역 대시보드 인스턴스
_dashboard: Optional[MonitoringDashboard] = None


def get_monitoring_dashboard() -> MonitoringDashboard:
    """전역 모니터링 대시보드 조회"""
    global _dashboard
    if _dashboard is None:
        _dashboard = MonitoringDashboard()
    return _dashboard
