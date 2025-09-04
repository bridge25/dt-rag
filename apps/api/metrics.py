"""
Prometheus 메트릭 및 관찰가능성 시스템
"""

import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import asynccontextmanager

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil

logger = logging.getLogger(__name__)


# =============================================================================
# Prometheus 메트릭 정의
# =============================================================================

# HTTP 요청 메트릭
http_requests_total = Counter(
    'dt_rag_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'dt_rag_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# API 엔드포인트별 메트릭
classify_requests_total = Counter(
    'dt_rag_classify_requests_total',
    'Total classification requests',
    ['status']
)

search_requests_total = Counter(
    'dt_rag_search_requests_total', 
    'Total search requests',
    ['search_type']  # hybrid, semantic, bm25
)

ingestion_jobs_total = Counter(
    'dt_rag_ingestion_jobs_total',
    'Total ingestion jobs',
    ['status', 'doc_type']  # pending/completed/failed, pdf/markdown/html
)

# 성능 메트릭
embedding_generation_duration = Histogram(
    'dt_rag_embedding_generation_seconds',
    'Time to generate embeddings',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

database_query_duration = Histogram(
    'dt_rag_database_query_seconds', 
    'Database query duration',
    ['query_type'],  # select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# 비용 추적 메트릭
api_cost_total = Counter(
    'dt_rag_api_cost_total_usd',
    'Total API costs in USD',
    ['provider', 'model']  # openai/anthropic, gpt-4/claude-3
)

token_usage_total = Counter(
    'dt_rag_token_usage_total',
    'Total token usage',
    ['provider', 'model', 'type']  # type: input/output
)

# 시스템 리소스 게이지
active_database_connections = Gauge(
    'dt_rag_active_db_connections',
    'Active database connections'
)

active_requests = Gauge(
    'dt_rag_active_requests', 
    'Currently active HTTP requests'
)

system_cpu_usage = Gauge(
    'dt_rag_system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'dt_rag_system_memory_usage_bytes',
    'System memory usage in bytes'
)

# HITL 큐 메트릭
hitl_queue_size = Gauge(
    'dt_rag_hitl_queue_size',
    'HITL queue size by status',
    ['status']  # pending, assigned, reviewing
)


# =============================================================================
# 메트릭 수집 유틸리티
# =============================================================================

class MetricsCollector:
    """메트릭 수집 및 관리 클래스"""
    
    def __init__(self):
        self.daily_cost_limit = 10.0  # $10 일일 한도
        self.current_daily_cost = 0.0
        self.cost_reset_time = time.time()
        
    def track_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """HTTP 요청 추적"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    def track_classification(self, status: str):
        """분류 요청 추적"""
        classify_requests_total.labels(status=status).inc()
    
    def track_search(self, search_type: str):
        """검색 요청 추적"""
        search_requests_total.labels(search_type=search_type).inc()
    
    def track_ingestion_job(self, status: str, doc_type: str):
        """수집 작업 추적"""
        ingestion_jobs_total.labels(
            status=status,
            doc_type=doc_type
        ).inc()
    
    def track_embedding_generation(self, duration: float):
        """임베딩 생성 시간 추적"""
        embedding_generation_duration.observe(duration)
    
    def track_database_query(self, query_type: str, duration: float):
        """데이터베이스 쿼리 추적"""
        database_query_duration.labels(query_type=query_type).observe(duration)
    
    def track_api_cost(self, provider: str, model: str, cost: float, 
                      input_tokens: int = 0, output_tokens: int = 0):
        """API 비용 및 토큰 사용량 추적"""
        api_cost_total.labels(provider=provider, model=model).inc(cost)
        
        if input_tokens > 0:
            token_usage_total.labels(
                provider=provider, 
                model=model, 
                type='input'
            ).inc(input_tokens)
        
        if output_tokens > 0:
            token_usage_total.labels(
                provider=provider,
                model=model,
                type='output'
            ).inc(output_tokens)
        
        # 일일 비용 한도 체크
        self._update_daily_cost(cost)
    
    def _update_daily_cost(self, cost: float):
        """일일 비용 업데이트 및 한도 체크"""
        current_time = time.time()
        
        # 24시간이 지났으면 비용 리셋
        if current_time - self.cost_reset_time > 86400:  # 24 hours
            self.current_daily_cost = 0.0
            self.cost_reset_time = current_time
        
        self.current_daily_cost += cost
        
        # 비용 한도 초과 경고
        if self.current_daily_cost > self.daily_cost_limit:
            logger.warning(
                f"Daily cost limit exceeded: ${self.current_daily_cost:.2f} > ${self.daily_cost_limit}"
            )
    
    def update_system_metrics(self):
        """시스템 메트릭 업데이트"""
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage.set(cpu_percent)
        
        # 메모리 사용량
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.used)
    
    def update_database_metrics(self, active_connections: int):
        """데이터베이스 메트릭 업데이트"""
        active_database_connections.set(active_connections)
    
    def update_hitl_metrics(self, queue_stats: Dict[str, int]):
        """HITL 큐 메트릭 업데이트"""
        for status, count in queue_stats.items():
            hitl_queue_size.labels(status=status).set(count)
    
    def get_cost_guard_status(self) -> Dict[str, Any]:
        """비용 가드 상태 조회"""
        return {
            "daily_limit": self.daily_cost_limit,
            "current_daily_cost": self.current_daily_cost,
            "remaining_budget": max(0, self.daily_cost_limit - self.current_daily_cost),
            "cost_reset_time": self.cost_reset_time,
            "is_over_budget": self.current_daily_cost > self.daily_cost_limit
        }


# 전역 메트릭 수집기
metrics_collector = MetricsCollector()


# =============================================================================
# 데코레이터 및 컨텍스트 매니저
# =============================================================================

def track_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """실행 시간 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == 'embedding':
                    metrics_collector.track_embedding_generation(duration)
                elif metric_name == 'database':
                    query_type = labels.get('query_type', 'unknown') if labels else 'unknown'
                    metrics_collector.track_database_query(query_type, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == 'embedding':
                    metrics_collector.track_embedding_generation(duration)
                elif metric_name == 'database':
                    query_type = labels.get('query_type', 'unknown') if labels else 'unknown'
                    metrics_collector.track_database_query(query_type, duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


@asynccontextmanager
async def track_active_requests():
    """활성 요청 수 추적"""
    active_requests.inc()
    try:
        yield
    finally:
        active_requests.dec()


def get_metrics_summary() -> Dict[str, Any]:
    """메트릭 요약 정보"""
    return {
        "http_requests": {
            "total": http_requests_total._value.sum(),
            "avg_duration": http_request_duration_seconds._sum.sum() / max(1, http_request_duration_seconds._count.sum())
        },
        "classification": {
            "total": classify_requests_total._value.sum()
        },
        "search": {
            "total": search_requests_total._value.sum()
        },
        "ingestion": {
            "total_jobs": ingestion_jobs_total._value.sum()
        },
        "cost_guard": metrics_collector.get_cost_guard_status(),
        "system": {
            "cpu_usage": system_cpu_usage._value.get(),
            "memory_usage": system_memory_usage._value.get(),
            "active_connections": active_database_connections._value.get(),
            "active_requests": active_requests._value.get()
        }
    }


async def export_prometheus_metrics() -> str:
    """Prometheus 형식으로 메트릭 내보내기"""
    # 시스템 메트릭 업데이트
    metrics_collector.update_system_metrics()
    
    return generate_latest().decode('utf-8')


# =============================================================================
# 알림 규칙
# =============================================================================

class AlertRule:
    """알림 규칙 클래스"""
    
    def __init__(self, name: str, condition_func, threshold: float, message: str):
        self.name = name
        self.condition_func = condition_func
        self.threshold = threshold
        self.message = message
        self.last_alert_time = 0
        self.cooldown_seconds = 300  # 5분 쿨다운
    
    def check(self) -> Optional[str]:
        """알림 조건 체크"""
        current_time = time.time()
        
        # 쿨다운 체크
        if current_time - self.last_alert_time < self.cooldown_seconds:
            return None
        
        if self.condition_func() > self.threshold:
            self.last_alert_time = current_time
            return self.message
        
        return None


# 알림 규칙 정의
alert_rules = [
    AlertRule(
        name="high_response_time",
        condition_func=lambda: (
            http_request_duration_seconds._sum.sum() / 
            max(1, http_request_duration_seconds._count.sum())
        ),
        threshold=2.0,
        message="평균 응답 시간이 2초를 초과했습니다"
    ),
    AlertRule(
        name="high_error_rate", 
        condition_func=lambda: (
            sum(v for k, v in http_requests_total._value.items() if k[2].startswith('5')) /
            max(1, http_requests_total._value.sum())
        ),
        threshold=0.01,
        message="에러율이 1%를 초과했습니다"
    ),
    AlertRule(
        name="daily_cost_exceeded",
        condition_func=lambda: metrics_collector.current_daily_cost,
        threshold=10.0,
        message="일일 비용 한도를 초과했습니다"
    )
]


async def check_alerts() -> list[str]:
    """모든 알림 규칙 확인"""
    alerts = []
    for rule in alert_rules:
        try:
            alert_message = rule.check()
            if alert_message:
                alerts.append(f"[{rule.name}] {alert_message}")
                logger.warning(f"Alert triggered: {rule.name}")
        except Exception as e:
            logger.error(f"Alert rule {rule.name} failed: {e}")
    
    return alerts