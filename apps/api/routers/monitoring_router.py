"""
Monitoring API Router for DT-RAG v1.8.1

Provides REST endpoints for system monitoring and observability including:
- Health checks and system status
- Performance metrics and analytics
- Resource utilization monitoring
- API usage statistics and trends
"""

import logging
import psutil
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Create router
monitoring_router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# Models for monitoring operations

class HealthStatus(BaseModel):
    """System health status"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="System version")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    components: Dict[str, str] = Field(..., description="Component health status")

class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_gb: float = Field(..., description="Disk usage in GB")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    network_io: Dict[str, int] = Field(..., description="Network I/O statistics")
    active_connections: int = Field(..., description="Active database connections")

class APIMetrics(BaseModel):
    """API performance metrics"""
    total_requests: int = Field(..., description="Total number of requests")
    requests_per_minute: float = Field(..., description="Average requests per minute")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    error_rate: float = Field(..., description="Error rate as percentage")
    active_users: int = Field(..., description="Number of active users")

class EndpointStats(BaseModel):
    """Individual endpoint statistics"""
    endpoint: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    request_count: int = Field(..., description="Total request count")
    avg_response_time_ms: float = Field(..., description="Average response time")
    error_count: int = Field(..., description="Total error count")
    last_accessed: datetime = Field(..., description="Last access time")

class AlertInfo(BaseModel):
    """System alert information"""
    alert_id: str = Field(..., description="Unique alert identifier")
    severity: str = Field(..., description="Alert severity level")
    component: str = Field(..., description="Affected component")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(..., description="Alert creation time")
    acknowledged: bool = Field(False, description="Whether alert is acknowledged")

# Mock monitoring service

class MonitoringService:
    """Mock monitoring service"""

    def __init__(self):
        self.start_time = datetime.utcnow()

    async def get_health_status(self) -> HealthStatus:
        """Get overall system health status"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        # Check component health (mock implementation)
        components = {
            "database": "healthy",
            "redis": "healthy",
            "search_index": "healthy",
            "classification_service": "healthy",
            "orchestration_service": "healthy",
            "taxonomy_service": "healthy"
        }

        # Determine overall status
        unhealthy_components = [k for k, v in components.items() if v != "healthy"]
        overall_status = "unhealthy" if unhealthy_components else "healthy"

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.8.1",
            uptime_seconds=int(uptime),
            components=components
        )

    async def get_system_metrics(self) -> SystemMetrics:
        """Get system performance metrics"""
        # Get actual system metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return SystemMetrics(
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory.used / (1024 * 1024),
            memory_usage_percent=memory.percent,
            disk_usage_gb=disk.used / (1024 ** 3),
            disk_usage_percent=(disk.used / disk.total) * 100,
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            active_connections=25  # Mock database connections
        )

    async def get_api_metrics(self) -> APIMetrics:
        """Get API performance metrics"""
        return APIMetrics(
            total_requests=125847,
            requests_per_minute=45.2,
            avg_response_time_ms=89.5,
            p95_response_time_ms=234.7,
            error_rate=0.8,
            active_users=156
        )

    async def get_endpoint_stats(self, limit: int = 20) -> List[EndpointStats]:
        """Get endpoint-specific statistics"""
        endpoints = [
            EndpointStats(
                endpoint="/api/v1/search",
                method="POST",
                request_count=45678,
                avg_response_time_ms=45.2,
                error_count=123,
                last_accessed=datetime.utcnow()
            ),
            EndpointStats(
                endpoint="/api/v1/classify",
                method="POST",
                request_count=23456,
                avg_response_time_ms=89.7,
                error_count=67,
                last_accessed=datetime.utcnow()
            ),
            EndpointStats(
                endpoint="/api/v1/taxonomy/{version}/tree",
                method="GET",
                request_count=12345,
                avg_response_time_ms=23.4,
                error_count=12,
                last_accessed=datetime.utcnow()
            )
        ]

        return endpoints[:limit]

    async def get_alerts(self, severity: Optional[str] = None) -> List[AlertInfo]:
        """Get system alerts"""
        alerts = [
            AlertInfo(
                alert_id=str(uuid.uuid4()),
                severity="warning",
                component="search_index",
                message="Search index size approaching limit (85% full)",
                created_at=datetime.utcnow() - timedelta(minutes=15),
                acknowledged=False
            ),
            AlertInfo(
                alert_id=str(uuid.uuid4()),
                severity="info",
                component="classification_service",
                message="HITL queue length above normal (45 pending tasks)",
                created_at=datetime.utcnow() - timedelta(minutes=30),
                acknowledged=True
            )
        ]

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return alerts

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        # Mock implementation
        return True

    async def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        # Generate mock trend data
        now = datetime.utcnow()
        timestamps = [now - timedelta(hours=i) for i in range(hours, 0, -1)]

        return {
            "period_hours": hours,
            "data_points": len(timestamps),
            "metrics": {
                "response_times": [89.5 + (i * 2.3) % 45 for i in range(len(timestamps))],
                "request_rates": [45.2 + (i * 1.7) % 20 for i in range(len(timestamps))],
                "error_rates": [0.8 + (i * 0.1) % 0.5 for i in range(len(timestamps))],
                "timestamps": [ts.isoformat() for ts in timestamps]
            }
        }

# Dependency injection
async def get_monitoring_service() -> MonitoringService:
    """Get monitoring service instance"""
    return MonitoringService()

# API Endpoints

@monitoring_router.get("/health", response_model=HealthStatus)
async def get_health_status(
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Get overall system health status

    Returns comprehensive health information including:
    - Overall system status
    - Individual component health
    - System uptime and version
    - Component-specific status details
    """
    try:
        health_status = await service.get_health_status()

        # Set appropriate HTTP status based on health
        status_code = 200 if health_status.status == "healthy" else 503

        return JSONResponse(
            content=health_status.dict(),
            status_code=status_code,
            headers={
                "X-Health-Status": health_status.status,
                "X-System-Version": health_status.version
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check service unavailable"
        )

@monitoring_router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics(
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Get system performance metrics

    Returns detailed system metrics including:
    - CPU and memory utilization
    - Disk usage and I/O statistics
    - Network activity metrics
    - Database connection status
    """
    try:
        metrics = await service.get_system_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )

@monitoring_router.get("/metrics/api", response_model=APIMetrics)
async def get_api_metrics(
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Get API performance metrics

    Returns API-specific performance data including:
    - Request volume and rate statistics
    - Response time analysis
    - Error rate tracking
    - Active user counts
    """
    try:
        metrics = await service.get_api_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Failed to get API metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API metrics"
        )

@monitoring_router.get("/metrics/endpoints", response_model=List[EndpointStats])
async def get_endpoint_statistics(
    limit: int = Query(20, ge=1, le=100, description="Maximum endpoints to return"),
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Get endpoint-specific performance statistics

    Returns detailed statistics for individual API endpoints including:
    - Request counts and patterns
    - Response time analysis
    - Error tracking by endpoint
    - Usage frequency data
    """
    try:
        stats = await service.get_endpoint_stats(limit)
        return stats

    except Exception as e:
        logger.error(f"Failed to get endpoint statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve endpoint statistics"
        )

@monitoring_router.get("/alerts", response_model=List[AlertInfo])
async def get_system_alerts(
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    limit: int = Query(50, ge=1, le=200, description="Maximum alerts to return"),
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Get system alerts and notifications

    Returns active system alerts including:
    - Security alerts and warnings
    - Performance degradation notices
    - Resource utilization alerts
    - Service availability issues
    """
    try:
        alerts = await service.get_alerts(severity)

        # Apply limit
        if len(alerts) > limit:
            alerts = alerts[:limit]

        return alerts

    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system alerts"
        )

@monitoring_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Acknowledge a system alert

    Marks an alert as acknowledged to prevent repeated notifications.
    Acknowledged alerts remain visible but are marked as handled.
    """
    try:
        success = await service.acknowledge_alert(alert_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert '{alert_id}' not found"
            )

        return {
            "message": f"Alert '{alert_id}' acknowledged successfully",
            "acknowledged_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )

@monitoring_router.get("/trends")
async def get_performance_trends(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    service: MonitoringService = Depends(get_monitoring_service)
):
    """
    Get performance trends over time

    Returns historical performance data including:
    - Response time trends
    - Request rate patterns
    - Error rate evolution
    - Resource utilization over time
    """
    try:
        trends = await service.get_performance_trends(hours)
        return trends

    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance trends"
        )

@monitoring_router.get("/status")
async def get_monitoring_status():
    """
    Get monitoring system status

    Returns status of the monitoring system itself including:
    - Monitoring service health
    - Data collection status
    - Alert system functionality
    """
    try:
        status_info = {
            "monitoring_status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "data_collection": {
                "metrics_enabled": True,
                "alerts_enabled": True,
                "trend_analysis_enabled": True,
                "last_collection": datetime.utcnow().isoformat()
            },
            "storage": {
                "metrics_retention_days": 30,
                "alerts_retention_days": 90,
                "storage_usage_percent": 45.2
            },
            "features": {
                "real_time_monitoring": True,
                "automated_alerting": True,
                "performance_analysis": True,
                "custom_dashboards": True
            }
        }

        return status_info

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monitoring status"
        )

# Export router
__all__ = ["monitoring_router"]