"""
Enhanced Monitoring Middleware
통합 메트릭 수집 및 성능 모니터링 미들웨어
"""

import logging
import time
from typing import Callable
from fastapi import Request

# 통합 메트릭 시스템 import
from ..metrics import (
    metrics_collector, 
    track_active_requests,
    get_metrics_summary,
    export_prometheus_metrics,
    check_alerts
)

logger = logging.getLogger(__name__)


class MonitoringMiddleware:
    """통합 성능 모니터링 미들웨어"""
    
    def __init__(self, app):
        self.app = app
        self.cost_estimates = {
            "/classify": {"base_usd": 0.003, "complexity_factor": 1.0},  # GPT-4o embedding cost
            "/search": {"base_usd": 0.001, "complexity_factor": 0.8},   # Search only
            "/taxonomy": {"base_usd": 0.0, "complexity_factor": 0.1},   # DB only
            "/ingest": {"base_usd": 0.002, "complexity_factor": 1.5}    # Document processing
        }
        self.last_alert_check = 0
        self.alert_check_interval = 30  # 30초마다 알림 체크
    
    async def __call__(self, request: Request, call_next: Callable):
        """미들웨어 실행"""
        
        # Skip monitoring for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        path = self._normalize_path(request.url.path)
        start_time = time.time()
        
        # 활성 요청 추적
        async with track_active_requests():
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate metrics
                duration = time.time() - start_time
                status_code = response.status_code
                
                # 통합 메트릭 수집기로 추적
                metrics_collector.track_request(method, path, status_code, duration)
                
                # 엔드포인트별 특수 추적
                await self._track_endpoint_specific_metrics(request, response, path)
                
                # 비용 추적
                estimated_cost = self._estimate_cost(path, request)
                if estimated_cost > 0:
                    provider, model = self._get_provider_model(path)
                    metrics_collector.track_api_cost(provider, model, estimated_cost)
                
                # 성능 헤더 추가
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
                response.headers["X-Estimated-Cost"] = f"${estimated_cost:.4f}"
                
                # NFR 가드 체크
                await self._check_nfr_violations(method, path, duration, status_code)
                
                # 주기적 알림 체크
                await self._periodic_alert_check()
                
                return response
                
            except Exception as e:
                # 오류 메트릭 기록
                duration = time.time() - start_time
                metrics_collector.track_request(method, path, 500, duration)
                
                logger.error(f"Request failed: {method} {path} - {e}")
                raise
    
    async def _track_endpoint_specific_metrics(self, request: Request, response, path: str):
        """엔드포인트별 특수 메트릭 추적"""
        try:
            if "/classify" in path and hasattr(response, 'body'):
                # 분류 요청 상태 추적
                status = "success" if response.status_code == 200 else "error"
                metrics_collector.track_classification(status)
                
            elif "/search" in path:
                # 검색 타입 추적 (요청 파라미터에서 추출)
                search_type = getattr(request.state, 'search_type', 'hybrid')
                metrics_collector.track_search(search_type)
                
            elif "/ingest" in path and response.status_code == 202:
                # 수집 작업 추적
                doc_type = getattr(request.state, 'doc_type', 'unknown')
                metrics_collector.track_ingestion_job('pending', doc_type)
                
        except Exception as e:
            logger.debug(f"Endpoint metric tracking failed: {e}")
    
    async def _check_nfr_violations(self, method: str, path: str, duration: float, status_code: int):
        """NFR(Non-Functional Requirements) 위반 체크"""
        # p95 ≤ 4s, p50 ≤ 1.5s 체크
        if duration > 4.0:
            logger.warning(
                f"NFR 위반 (응답시간): {method} {path} took {duration:.3f}s "
                f"(p95 target: ≤4s)"
            )
        elif duration > 1.5:
            logger.info(
                f"NFR 경고 (응답시간): {method} {path} took {duration:.3f}s "
                f"(p50 target: ≤1.5s)"
            )
        
        # 에러율 체크 (5xx 에러)
        if status_code >= 500:
            logger.error(f"NFR 위반 (서버 오류): {method} {path} returned {status_code}")
    
    async def _periodic_alert_check(self):
        """주기적 알림 체크"""
        current_time = time.time()
        if current_time - self.last_alert_check > self.alert_check_interval:
            self.last_alert_check = current_time
            
            alerts = await check_alerts()
            for alert in alerts:
                logger.warning(f"ALERT: {alert}")
    
    def _get_provider_model(self, path: str) -> tuple[str, str]:
        """경로별 프로바이더와 모델 추정"""
        if "/classify" in path or "/search" in path:
            return "openai", "text-embedding-3-small"
        elif "/ingest" in path:
            return "openai", "text-embedding-3-small"
        else:
            return "system", "db-only"
    
    def _normalize_path(self, path: str) -> str:
        """경로 정규화 (파라미터 제거)"""
        # Replace path parameters with placeholders
        parts = path.split('/')
        normalized_parts = []
        
        for part in parts:
            if not part:
                continue
            
            # Check if part looks like a parameter (UUID, job_id, etc.)
            if (len(part) == 36 and part.count('-') == 4) or \
               (len(part) > 8 and any(char.isdigit() for char in part)):
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        
        return '/' + '/'.join(normalized_parts)
    
    def _estimate_cost(self, endpoint: str, request: Request) -> float:
        """요청 비용 추정 (USD)"""
        base_cost = 0.0
        complexity_factor = 1.0
        
        # Get base cost for endpoint
        for pattern, cost_info in self.cost_estimates.items():
            if pattern in endpoint:
                base_cost = cost_info["base_usd"]
                complexity_factor = cost_info["complexity_factor"]
                break
        
        # Adjust cost based on request complexity
        if hasattr(request.state, 'complexity_factor'):
            complexity_factor *= request.state.complexity_factor
        
        return base_cost * complexity_factor


# 통합 메트릭 함수들
async def get_prometheus_metrics():
    """Prometheus 메트릭 반환 (통합 시스템)"""
    return await export_prometheus_metrics()


async def get_system_health():
    """시스템 건강 상태 요약"""
    summary = get_metrics_summary()
    alerts = await check_alerts()
    
    return {
        "status": "healthy" if not alerts else "warning",
        "alerts": alerts,
        "metrics_summary": summary,
        "timestamp": time.time()
    }