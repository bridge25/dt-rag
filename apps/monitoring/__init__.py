"""
Dynamic Taxonomy RAG v1.8.1 Monitoring & Observability Package

Comprehensive monitoring system with:
- Langfuse integration for LLM observability
- Prometheus metrics collection
- Real-time alerting and dashboards
- System health monitoring
- Search quality metrics
- Taxonomy operation tracking
"""

__version__ = "1.8.1"
__author__ = "DT-RAG Observability Team"

from .core.observability_manager import ObservabilityManager
from .core.langfuse_integration import LangfuseManager, LangfuseRAGObserver
from .core.metrics_collector import MetricsCollector, RAGMetrics
from .core.alerting_manager import AlertingManager
from .core.dashboard_generator import DashboardGenerator
from .utils.health_checker import SystemHealthChecker

__all__ = [
    "ObservabilityManager",
    "LangfuseManager",
    "LangfuseRAGObserver",
    "MetricsCollector",
    "RAGMetrics",
    "AlertingManager",
    "DashboardGenerator",
    "SystemHealthChecker"
]