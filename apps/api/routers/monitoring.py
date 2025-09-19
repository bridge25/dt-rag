"""
모니터링 API 라우터
"""

import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response, Request
from fastapi.responses import PlainTextResponse
import logging

from ..monitoring.metrics import get_metrics_collector, CONTENT_TYPE_LATEST
from ..monitoring.health_check import get_health_checker
from ..monitoring.dashboard import get_monitoring_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health", summary="시스템 헬스 체크")
async def get_health():
    """
    전체 시스템 헬스 상태 조회
    - 각 컴포넌트의 상태 확인
    - 전체적인 시스템 건강도 평가
    """
    try:
        health_checker = get_health_checker()
        system_health = await health_checker.get_system_health()
        return system_health.to_dict()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/health/quick", summary="빠른 헬스 체크")
async def get_quick_health():
    """
    캐시된 헬스 정보 조회 (빠른 응답)
    - 마지막 헬스 체크 결과 반환
    - 실시간 모니터링용
    """
    try:
        health_checker = get_health_checker()
        return health_checker.get_cached_health()
    except Exception as e:
        logger.error(f"Quick health check failed: {e}")
        raise HTTPException(status_code=500, detail="Quick health check failed")

@router.get("/health/{component}", summary="특정 컴포넌트 헬스 체크")
async def get_component_health(component: str):
    """
    특정 컴포넌트의 헬스 상태 조회
    - component: system, database, cache, storage 등
    """
    try:
        health_checker = get_health_checker()
        component_health = await health_checker.check_single_component(component)
        return component_health.to_dict()
    except Exception as e:
        logger.error(f"Component health check failed for {component}: {e}")
        raise HTTPException(status_code=500, detail=f"Component health check failed: {component}")

@router.get("/metrics", summary="성능 메트릭 조회")
async def get_metrics():
    """
    현재 성능 메트릭 요약 조회
    - 지연시간, 처리량, 에러율 등
    - 캐시 성능, 시스템 리소스 사용률
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_metrics_summary()
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")

@router.get("/metrics/realtime", summary="실시간 메트릭")
async def get_realtime_metrics():
    """
    실시간 메트릭 조회 (경량화된 응답)
    - 대시보드 실시간 업데이트용
    """
    try:
        dashboard = get_monitoring_dashboard()
        return await dashboard.get_real_time_metrics()
    except Exception as e:
        logger.error(f"Realtime metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Realtime metrics retrieval failed")

@router.get("/metrics/trend", summary="성능 트렌드")
async def get_performance_trend(
    duration_minutes: int = Query(60, ge=1, le=1440, description="조회 기간 (분)")
):
    """
    성능 트렌드 데이터 조회
    - duration_minutes: 조회할 기간 (1분 ~ 24시간)
    """
    try:
        metrics_collector = get_metrics_collector()
        trend_data = metrics_collector.get_performance_trend(duration_minutes)

        return {
            "duration_minutes": duration_minutes,
            "sample_count": len(trend_data),
            "data": trend_data
        }
    except Exception as e:
        logger.error(f"Performance trend retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Performance trend retrieval failed")

@router.get("/prometheus", response_class=PlainTextResponse, summary="Prometheus 메트릭")
async def get_prometheus_metrics():
    """
    Prometheus 형식의 메트릭 익스포트
    - Prometheus 서버에서 스크래핑용
    """
    try:
        metrics_collector = get_metrics_collector()
        prometheus_data = metrics_collector.export_prometheus_metrics()

        return Response(
            content=prometheus_data,
            media_type=CONTENT_TYPE_LATEST if hasattr(locals(), 'CONTENT_TYPE_LATEST') else "text/plain"
        )
    except Exception as e:
        logger.error(f"Prometheus metrics export failed: {e}")
        raise HTTPException(status_code=500, detail="Prometheus metrics export failed")

@router.get("/dashboard", summary="모니터링 대시보드 데이터")
async def get_dashboard_data():
    """
    통합 모니터링 대시보드 데이터
    - 헬스, 메트릭, 알람 등 통합 정보
    """
    try:
        dashboard = get_monitoring_dashboard()
        return await dashboard.get_dashboard_data()
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Dashboard data retrieval failed")

@router.get("/alerts", summary="활성 알람 조회")
async def get_active_alerts():
    """
    현재 활성화된 알람 목록
    - 시스템 이슈, 성능 문제 등
    """
    try:
        dashboard = get_monitoring_dashboard()
        dashboard_data = await dashboard.get_dashboard_data()
        return {
            "alerts": dashboard_data.get("alerts", []),
            "alert_count": len(dashboard_data.get("alerts", [])),
            "timestamp": dashboard_data.get("timestamp")
        }
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Alerts retrieval failed")

@router.get("/search/analytics", summary="검색 분석")
async def get_search_analytics():
    """
    검색 성능 및 사용 패턴 분석
    - 캐시 성능, 검색 정확도 등
    """
    try:
        dashboard = get_monitoring_dashboard()
        return await dashboard.get_search_analytics()
    except Exception as e:
        logger.error(f"Search analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Search analytics retrieval failed")

@router.get("/report/performance", summary="성능 리포트")
async def get_performance_report(
    hours: int = Query(24, ge=1, le=168, description="리포트 기간 (시간)")
):
    """
    성능 리포트 생성
    - SLO 준수 현황, 권장사항 등
    - hours: 분석할 기간 (1시간 ~ 7일)
    """
    try:
        dashboard = get_monitoring_dashboard()
        return await dashboard.get_performance_report(hours)
    except Exception as e:
        logger.error(f"Performance report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Performance report generation failed")

@router.post("/metrics/reset", summary="메트릭 초기화")
async def reset_metrics():
    """
    메트릭 데이터 초기화
    - 테스트나 새로운 측정 시작용
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics_collector.reset_metrics()

        return {
            "status": "success",
            "message": "Metrics reset successfully",
            "timestamp": metrics_collector.start_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics reset failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics reset failed")

@router.get("/export/{format}", summary="메트릭 데이터 익스포트")
async def export_metrics(format: str):
    """
    메트릭 데이터 익스포트
    - format: json, prometheus
    """
    if format.lower() not in ["json", "prometheus"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'prometheus'")

    try:
        dashboard = get_monitoring_dashboard()
        exported_data = await dashboard.export_metrics_data(format)

        if format.lower() == "prometheus":
            return Response(content=exported_data, media_type="text/plain")
        else:
            return Response(content=exported_data, media_type="application/json")

    except Exception as e:
        logger.error(f"Metrics export failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics export failed")

# 미들웨어용 함수들
async def track_request_metrics(request: Request, response_time_ms: float, status_code: int):
    """요청 메트릭 추적 (미들웨어에서 호출)"""
    try:
        metrics_collector = get_metrics_collector()

        # 요청 메트릭 기록
        labels = {
            "method": request.method,
            "endpoint": str(request.url.path),
            "status": str(status_code)
        }

        metrics_collector.record_latency("http_request", response_time_ms, labels)

        if 200 <= status_code < 300:
            metrics_collector.increment_counter("requests_success", labels)
        else:
            metrics_collector.increment_counter("requests_error", labels)

        metrics_collector.increment_counter("requests_total", labels)

    except Exception as e:
        logger.warning(f"Failed to track request metrics: {e}")

async def track_search_metrics(search_type: str, response_time_ms: float, success: bool, results_count: int = 0):
    """검색 메트릭 추적"""
    try:
        metrics_collector = get_metrics_collector()

        labels = {
            "search_type": search_type,
            "status": "success" if success else "error"
        }

        metrics_collector.record_latency("search_request", response_time_ms, labels)

        if success:
            metrics_collector.increment_counter("search_success", labels)
            metrics_collector.set_gauge("last_search_results_count", results_count)
        else:
            metrics_collector.increment_counter("search_error", labels)

        metrics_collector.increment_counter("search_total", labels)

    except Exception as e:
        logger.warning(f"Failed to track search metrics: {e}")

async def track_cache_metrics(operation: str, hit: bool):
    """캐시 메트릭 추적"""
    try:
        metrics_collector = get_metrics_collector()

        result = "hit" if hit else "miss"
        metrics_collector.record_cache_operation(operation, result)

        if hit:
            metrics_collector.increment_counter("cache_hits")
        else:
            metrics_collector.increment_counter("cache_misses")

    except Exception as e:
        logger.warning(f"Failed to track cache metrics: {e}")