"""
DT-RAG v1.8.1 Monitoring Application

Main application entry point for the comprehensive monitoring system.
Provides FastAPI endpoints for monitoring dashboards, health checks, and metrics.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import configure_monitoring, monitoring_config
from .core.observability_manager import ObservabilityManager, ObservabilityConfig
from .core.dashboard_generator import DashboardGenerator
from .integration import initialize_monitoring_system, RAGMonitoringIntegration

logger = logging.getLogger(__name__)

# Configure logging
configure_monitoring()

# Global monitoring components
observability_manager: Optional[ObservabilityManager] = None
monitoring_integration: Optional[RAGMonitoringIntegration] = None
dashboard_generator: Optional[DashboardGenerator] = None

# Security
security = HTTPBearer(auto_error=False)


async def get_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate authentication token if security is enabled"""
    if monitoring_config.security.metrics_auth_enabled:
        if not credentials or credentials.credentials != monitoring_config.security.metrics_auth_token:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials


# Create FastAPI app
app = FastAPI(
    title="DT-RAG Monitoring System",
    description="Comprehensive observability and monitoring for Dynamic Taxonomy RAG v1.8.1",
    version="1.8.1",
    docs_url="/docs" if monitoring_config.environment != "production" else None,
    redoc_url="/redoc" if monitoring_config.environment != "production" else None
)

# Add CORS middleware - Security: No wildcard headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=monitoring_config.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control"
    ],
)


@app.on_event("startup")
async def startup_event():
    """Initialize monitoring system on startup"""
    global observability_manager, monitoring_integration, dashboard_generator

    try:
        logger.info("Starting DT-RAG Monitoring System")

        # Initialize observability manager
        config = ObservabilityConfig(
            langfuse_enabled=monitoring_config.langfuse.enabled,
            langfuse_public_key=monitoring_config.langfuse.public_key,
            langfuse_secret_key=monitoring_config.langfuse.secret_key,
            langfuse_host=monitoring_config.langfuse.host,
            prometheus_enabled=monitoring_config.prometheus.enabled,
            prometheus_port=monitoring_config.prometheus.port,
            metrics_export_interval=monitoring_config.prometheus.export_interval_seconds,
            health_check_enabled=monitoring_config.health_check.enabled,
            health_check_interval=monitoring_config.health_check.check_interval_seconds,
            slo_p95_latency_seconds=monitoring_config.slo.p95_latency_seconds,
            slo_cost_per_query_won=monitoring_config.slo.cost_per_query_won,
            slo_faithfulness_threshold=monitoring_config.slo.faithfulness_threshold,
            slo_availability_percent=monitoring_config.slo.availability_percent,
            alerting_enabled=monitoring_config.alerting.enabled,
            alert_webhook_url=monitoring_config.alerting.webhook_url,
            trace_sampling_rate=monitoring_config.langfuse.trace_sampling_rate
        )

        observability_manager = ObservabilityManager(config)
        await observability_manager.start()

        # Initialize integration layer
        monitoring_integration = RAGMonitoringIntegration(observability_manager)

        # Initialize dashboard generator
        dashboard_generator = DashboardGenerator()

        logger.info("DT-RAG Monitoring System started successfully")

    except Exception as e:
        logger.error(f"Failed to start monitoring system: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of monitoring system"""
    global observability_manager

    try:
        logger.info("Shutting down DT-RAG Monitoring System")

        if observability_manager:
            await observability_manager.stop()

        logger.info("DT-RAG Monitoring System shutdown complete")

    except Exception as e:
        logger.error(f"Error during monitoring system shutdown: {e}")


# Health and Status Endpoints

@app.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        if not observability_manager:
            raise HTTPException(status_code=503, detail="Monitoring system not initialized")

        health_status = await observability_manager.health_checker.get_health_status()
        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.get("/status")
async def system_status():
    """Comprehensive system status"""
    try:
        if not observability_manager:
            raise HTTPException(status_code=503, detail="Monitoring system not initialized")

        status_data = {
            "service": monitoring_config.service_name,
            "version": monitoring_config.service_version,
            "environment": monitoring_config.environment,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - observability_manager.start_time).total_seconds(),
            "components": {
                "langfuse": monitoring_config.langfuse.enabled,
                "prometheus": monitoring_config.prometheus.enabled,
                "alerting": monitoring_config.alerting.enabled,
                "health_checks": monitoring_config.health_check.enabled,
                "degradation": monitoring_config.degradation.enabled
            }
        }

        # Add health status
        health_status = await observability_manager.health_checker.get_health_status()
        status_data["health"] = health_status

        # Add system metrics
        system_metrics = await observability_manager.get_system_metrics()
        status_data["metrics"] = {
            "total_requests": system_metrics.total_requests,
            "error_rate_percent": system_metrics.error_rate_percent,
            "p95_latency_seconds": system_metrics.p95_latency_seconds,
            "availability_percent": system_metrics.availability_percent
        }

        return JSONResponse(content=status_data)

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Metrics Endpoints

@app.get("/metrics")
async def prometheus_metrics(
    token: Optional[HTTPAuthorizationCredentials] = Depends(get_auth_token)
):
    """Prometheus metrics endpoint"""
    try:
        if not observability_manager or not observability_manager.metrics_collector:
            return PlainTextResponse("# Metrics collection not available\n")

        metrics_text = observability_manager.metrics_collector.get_metrics_text()
        return PlainTextResponse(content=metrics_text)

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return PlainTextResponse(f"# Error: {str(e)}\n")


@app.get("/metrics/summary")
async def metrics_summary():
    """High-level metrics summary"""
    try:
        if not observability_manager:
            raise HTTPException(status_code=503, detail="Monitoring system not initialized")

        system_metrics = await observability_manager.get_system_metrics()
        return JSONResponse(content={
            "timestamp": system_metrics.timestamp.isoformat(),
            "performance": {
                "total_requests": system_metrics.total_requests,
                "successful_requests": system_metrics.successful_requests,
                "failed_requests": system_metrics.failed_requests,
                "avg_latency_seconds": system_metrics.avg_latency_seconds,
                "p95_latency_seconds": system_metrics.p95_latency_seconds,
                "p99_latency_seconds": system_metrics.p99_latency_seconds,
                "error_rate_percent": system_metrics.error_rate_percent,
                "availability_percent": system_metrics.availability_percent
            },
            "rag_metrics": {
                "total_classifications": system_metrics.total_classifications,
                "avg_classification_confidence": system_metrics.avg_classification_confidence,
                "search_operations": system_metrics.search_operations,
                "taxonomy_operations": system_metrics.taxonomy_operations,
                "avg_faithfulness_score": system_metrics.avg_faithfulness_score,
                "search_quality_score": system_metrics.search_quality_score
            },
            "cost_metrics": {
                "total_cost_won": system_metrics.total_cost_won,
                "avg_cost_per_query_won": system_metrics.avg_cost_per_query_won
            },
            "system_resources": {
                "cpu_usage_percent": system_metrics.cpu_usage_percent,
                "memory_usage_mb": system_metrics.memory_usage_mb
            }
        })

    except Exception as e:
        logger.error(f"Metrics summary failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# SLO and Alerting Endpoints

@app.get("/slo/compliance")
async def slo_compliance():
    """SLO compliance status"""
    try:
        if not observability_manager:
            raise HTTPException(status_code=503, detail="Monitoring system not initialized")

        compliance_status = await observability_manager.check_slo_compliance()
        return JSONResponse(content=compliance_status)

    except Exception as e:
        logger.error(f"SLO compliance check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/alerts")
async def active_alerts():
    """Get active alerts"""
    try:
        if not observability_manager or not observability_manager.alerting_manager:
            return JSONResponse(content={"active_alerts": [], "total": 0})

        alerts = await observability_manager.alerting_manager.get_active_alerts()
        alert_summary = await observability_manager.alerting_manager.get_alert_summary()

        return JSONResponse(content={
            "active_alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "category": alert.category.value,
                    "title": alert.title,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "source": alert.source
                }
                for alert in alerts
            ],
            "summary": alert_summary
        })

    except Exception as e:
        logger.error(f"Alerts endpoint failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an active alert"""
    try:
        if not observability_manager or not observability_manager.alerting_manager:
            raise HTTPException(status_code=503, detail="Alerting system not available")

        await observability_manager.alerting_manager.resolve_alert(alert_id, "Manually resolved via API")

        return JSONResponse(content={"message": f"Alert {alert_id} resolved"})

    except Exception as e:
        logger.error(f"Alert resolution failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Dashboard Endpoints

@app.get("/dashboard")
async def monitoring_dashboard():
    """Real-time monitoring dashboard"""
    try:
        if not observability_manager:
            raise HTTPException(status_code=503, detail="Monitoring system not initialized")

        dashboard_data = await observability_manager.generate_monitoring_dashboard()

        # Generate HTML dashboard
        html_content = generate_dashboard_html(dashboard_data)
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        return HTMLResponse(content=f"<html><body><h1>Dashboard Error</h1><p>{str(e)}</p></body></html>")


@app.get("/dashboard/data")
async def dashboard_data():
    """Dashboard data API endpoint"""
    try:
        if not observability_manager:
            raise HTTPException(status_code=503, detail="Monitoring system not initialized")

        dashboard_data = await observability_manager.generate_monitoring_dashboard()
        return JSONResponse(content=dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard data failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/dashboard/grafana/{dashboard_type}")
async def grafana_dashboard(dashboard_type: str):
    """Export Grafana dashboard JSON"""
    try:
        if not dashboard_generator:
            raise HTTPException(status_code=503, detail="Dashboard generator not available")

        grafana_json = dashboard_generator.export_grafana_json(dashboard_type)
        return JSONResponse(content=grafana_json)

    except Exception as e:
        logger.error(f"Grafana dashboard export failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Integration Endpoints

@app.post("/trace/rag")
async def create_rag_trace(request: Dict[str, Any]):
    """Create a new RAG trace"""
    try:
        if not monitoring_integration:
            raise HTTPException(status_code=503, detail="Monitoring integration not available")

        query = request.get("query", "")
        user_id = request.get("user_id")
        session_id = request.get("session_id")
        metadata = request.get("metadata", {})

        # This would typically be used by the RAG system
        # For now, just acknowledge the trace request
        return JSONResponse(content={
            "trace_id": f"trace_{int(datetime.utcnow().timestamp() * 1000)}",
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "status": "created"
        })

    except Exception as e:
        logger.error(f"RAG trace creation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


def generate_dashboard_html(dashboard_data: Dict[str, Any]) -> str:
    """Generate HTML dashboard"""
    status_color = {
        "healthy": "#28a745",
        "warning": "#ffc107",
        "critical": "#dc3545",
        "error": "#dc3545",
        "unknown": "#6c757d"
    }.get(dashboard_data.get("status", "unknown"), "#6c757d")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{dashboard_data.get('title', 'DT-RAG Monitoring')}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; color: white; background-color: {status_color}; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
            .metric-label {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
            .slo-section {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .compliant {{ color: #28a745; }}
            .violation {{ color: #dc3545; }}
            .component-status {{ margin: 10px 0; }}
            .component-enabled {{ color: #28a745; }}
            .component-disabled {{ color: #dc3545; }}
        </style>
        <script>
            function refreshDashboard() {{
                fetch('/dashboard/data')
                    .then(response => response.json())
                    .then(data => {{
                        // Update timestamp
                        document.getElementById('timestamp').textContent = new Date(data.timestamp).toLocaleString();

                        // Update metrics (simplified)
                        if (data.system_metrics) {{
                            const metrics = data.system_metrics;
                            if (document.getElementById('total-requests')) {{
                                document.getElementById('total-requests').textContent = metrics.total_requests || 0;
                            }}
                            if (document.getElementById('p95-latency')) {{
                                document.getElementById('p95-latency').textContent = (metrics.p95_latency_seconds || 0).toFixed(3) + 's';
                            }}
                            if (document.getElementById('error-rate')) {{
                                document.getElementById('error-rate').textContent = (metrics.error_rate_percent || 0).toFixed(2) + '%';
                            }}
                        }}
                    }})
                    .catch(error => console.error('Dashboard refresh failed:', error));
            }}

            // Refresh every 30 seconds
            setInterval(refreshDashboard, 30000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{dashboard_data.get('title', 'DT-RAG Monitoring')}</h1>
                <p>Status: <span class="status">{dashboard_data.get('status', 'unknown').upper()}</span></p>
                <p>Last Updated: <span id="timestamp">{dashboard_data.get('timestamp', '')}</span></p>
                <p>Uptime: {dashboard_data.get('uptime_seconds', 0) // 3600:.0f}h {(dashboard_data.get('uptime_seconds', 0) % 3600) // 60:.0f}m</p>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" id="total-requests">{dashboard_data.get('system_metrics', {}).get('total_requests', 0)}</div>
                    <div class="metric-label">Total Requests</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value" id="p95-latency">{dashboard_data.get('system_metrics', {}).get('p95_latency_seconds', 0):.3f}s</div>
                    <div class="metric-label">P95 Latency (SLO: ≤4s)</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value" id="error-rate">{dashboard_data.get('system_metrics', {}).get('error_rate_percent', 0):.2f}%</div>
                    <div class="metric-label">Error Rate</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{dashboard_data.get('system_metrics', {}).get('availability_percent', 0):.1f}%</div>
                    <div class="metric-label">Availability (SLO: ≥99.5%)</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">₩{dashboard_data.get('system_metrics', {}).get('avg_cost_per_query_won', 0):.2f}</div>
                    <div class="metric-label">Avg Cost per Query (SLO: ≤₩10)</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{dashboard_data.get('system_metrics', {}).get('avg_faithfulness_score', 0):.3f}</div>
                    <div class="metric-label">Faithfulness Score (SLO: ≥0.85)</div>
                </div>
            </div>

            <div class="slo-section">
                <h2>SLO Compliance</h2>
                <p class="{'compliant' if dashboard_data.get('slo_compliance', {}).get('compliant', False) else 'violation'}">
                    Status: {'COMPLIANT' if dashboard_data.get('slo_compliance', {}).get('compliant', False) else 'VIOLATIONS DETECTED'}
                </p>
            </div>

            <div class="slo-section">
                <h2>System Components</h2>
                {generate_component_status_html(dashboard_data.get('components', {}))}
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generate_component_status_html(components: Dict[str, bool]) -> str:
    """Generate HTML for component status"""
    html = ""
    for component, enabled in components.items():
        status_class = "component-enabled" if enabled else "component-disabled"
        status_text = "ENABLED" if enabled else "DISABLED"
        html += f'<div class="component-status"><span class="{status_class}">{component.upper()}: {status_text}</span></div>'
    return html


def main():
    """Main entry point for running the monitoring application"""
    logger.info(f"Starting DT-RAG Monitoring Application on port 8080")

    uvicorn.run(
        "dt_rag.apps.monitoring.app:app",
        host="0.0.0.0",
        port=8080,
        reload=monitoring_config.environment == "development",
        log_level=monitoring_config.logging.level.lower()
    )


if __name__ == "__main__":
    main()