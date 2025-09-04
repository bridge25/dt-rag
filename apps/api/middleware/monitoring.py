"""
Monitoring Middleware
메트릭 수집 및 성능 모니터링 미들웨어
"""

import logging
import time
from typing import Callable
from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'dt_rag_requests_total', 
    'Total requests', 
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'dt_rag_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 4.0, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    'dt_rag_active_requests',
    'Number of active requests'
)

COST_PER_REQUEST = Histogram(
    'dt_rag_cost_per_request_krw',
    'Cost per request in KRW',
    ['endpoint'],
    buckets=[1, 5, 10, 20, 50, 100]
)

CLASSIFICATION_CONFIDENCE = Histogram(
    'dt_rag_classification_confidence',
    'Classification confidence scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

HITL_QUEUE_SIZE = Gauge(
    'dt_rag_hitl_queue_size',
    'Number of items in HITL queue'
)


class MonitoringMiddleware:
    """성능 모니터링 미들웨어"""
    
    def __init__(self, app):
        self.app = app
        self.cost_estimates = {
            "/classify": 8.5,  # KRW per request (embedding + DB)
            "/search": 5.2,    # KRW per request (embedding + search)
            "/taxonomy": 1.0   # KRW per request (DB only)
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """미들웨어 실행"""
        
        # Skip monitoring for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Start monitoring
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        
        method = request.method
        path = self._normalize_path(request.url.path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method, 
                endpoint=path, 
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Record cost estimate
            estimated_cost = self._estimate_cost(path, request)
            if estimated_cost > 0:
                COST_PER_REQUEST.labels(endpoint=path).observe(estimated_cost)
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Estimated-Cost"] = f"₩{estimated_cost:.2f}"
            
            # Log slow requests
            if duration > 4.0:  # p95 target
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.3f}s "
                    f"(target: ≤4s)"
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path, 
                status_code=500
            ).inc()
            
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            logger.error(f"Request failed: {method} {path} - {e}")
            raise
            
        finally:
            ACTIVE_REQUESTS.dec()
    
    def _normalize_path(self, path: str) -> str:
        """경로 정규화 (파라미터 제거)"""
        # Replace path parameters with placeholders
        parts = path.split('/')
        normalized_parts = []
        
        for part in parts:
            if not part:
                continue
            
            # Check if part looks like a parameter (UUID, version, etc.)
            if (len(part) == 36 and part.count('-') == 4) or \
               part.replace('.', '').replace('_', '').isalnum():
                if any(char.isdigit() for char in part):
                    normalized_parts.append('{id}')
                else:
                    normalized_parts.append(part)
            else:
                normalized_parts.append(part)
        
        return '/' + '/'.join(normalized_parts)
    
    def _estimate_cost(self, endpoint: str, request: Request) -> float:
        """요청 비용 추정"""
        base_cost = 0
        
        # Get base cost for endpoint
        for pattern, cost in self.cost_estimates.items():
            if pattern in endpoint:
                base_cost = cost
                break
        
        # Adjust cost based on request complexity
        if hasattr(request.state, 'complexity_factor'):
            base_cost *= request.state.complexity_factor
        
        return base_cost


async def get_prometheus_metrics():
    """Prometheus 메트릭 반환"""
    return generate_latest()