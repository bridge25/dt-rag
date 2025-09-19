"""
Dashboard Generator for DT-RAG v1.8.1

Generates real-time monitoring dashboards with Grafana integration,
performance visualizations, and SLO compliance tracking.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DashboardPanel:
    """Dashboard panel configuration"""
    id: int
    title: str
    type: str  # graph, singlestat, table, heatmap, etc.
    targets: List[Dict[str, Any]]
    grid_pos: Dict[str, int]  # x, y, w, h
    options: Optional[Dict[str, Any]] = None


@dataclass
class Dashboard:
    """Complete dashboard configuration"""
    id: Optional[int]
    title: str
    tags: List[str]
    time_from: str
    time_to: str
    refresh: str
    panels: List[DashboardPanel]
    template_vars: Optional[List[Dict[str, Any]]] = None


class DashboardGenerator:
    """
    Generates comprehensive monitoring dashboards for DT-RAG system

    Features:
    - Real-time performance dashboards
    - SLO compliance monitoring
    - Cost tracking and optimization
    - Quality metrics visualization
    - System health overview
    - Alerting status dashboard
    """

    def __init__(self):
        self.dashboard_templates = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize dashboard templates"""
        self.dashboard_templates = {
            'system_overview': self._create_system_overview_template(),
            'rag_performance': self._create_rag_performance_template(),
            'slo_compliance': self._create_slo_compliance_template(),
            'cost_optimization': self._create_cost_optimization_template(),
            'quality_metrics': self._create_quality_metrics_template(),
            'taxonomy_operations': self._create_taxonomy_operations_template(),
            'alerting_status': self._create_alerting_status_template()
        }

    def generate_dashboard(self, dashboard_type: str, **kwargs) -> Dict[str, Any]:
        """Generate dashboard configuration"""
        if dashboard_type not in self.dashboard_templates:
            raise ValueError(f"Unknown dashboard type: {dashboard_type}")

        template = self.dashboard_templates[dashboard_type]
        dashboard_config = self._apply_template_customizations(template, **kwargs)

        return asdict(dashboard_config)

    def generate_all_dashboards(self) -> Dict[str, Dict[str, Any]]:
        """Generate all available dashboards"""
        dashboards = {}
        for dashboard_type in self.dashboard_templates.keys():
            dashboards[dashboard_type] = self.generate_dashboard(dashboard_type)

        return dashboards

    def _create_system_overview_template(self) -> Dashboard:
        """Create system overview dashboard template"""
        panels = [
            # System health indicators
            DashboardPanel(
                id=1,
                title="System Health Status",
                type="stat",
                targets=[
                    {
                        "expr": "up{job='dt-rag'}",
                        "legendFormat": "System Up",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "center",
                    "orientation": "horizontal",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                }
            ),

            # Request rate
            DashboardPanel(
                id=2,
                title="Request Rate (req/min)",
                type="stat",
                targets=[
                    {
                        "expr": "rate(dt_rag_requests_total[5m]) * 60",
                        "legendFormat": "Requests/min",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 6, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "center",
                    "orientation": "horizontal"
                }
            ),

            # P95 Latency
            DashboardPanel(
                id=3,
                title="P95 Latency (SLO: ≤4s)",
                type="stat",
                targets=[
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "P95 Latency",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "background",
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 3.0},
                            {"color": "red", "value": 4.0}
                        ]
                    },
                    "unit": "s"
                }
            ),

            # Error Rate
            DashboardPanel(
                id=4,
                title="Error Rate (%)",
                type="stat",
                targets=[
                    {
                        "expr": "rate(dt_rag_requests_total{status='error'}[5m]) / rate(dt_rag_requests_total[5m]) * 100",
                        "legendFormat": "Error Rate",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 18, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "background",
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.5},
                            {"color": "red", "value": 1.0}
                        ]
                    },
                    "unit": "percent"
                }
            ),

            # Request latency over time
            DashboardPanel(
                id=5,
                title="Request Latency Distribution",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "P50",
                        "refId": "A"
                    },
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "P95",
                        "refId": "B"
                    },
                    {
                        "expr": "histogram_quantile(0.99, rate(dt_rag_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "P99",
                        "refId": "C"
                    }
                ],
                grid_pos={"x": 0, "y": 3, "w": 12, "h": 6},
                options={
                    "legend": {"displayMode": "table", "placement": "right"},
                    "tooltip": {"mode": "multi"},
                    "yAxes": {"unit": "s"}
                }
            ),

            # System resource usage
            DashboardPanel(
                id=6,
                title="System Resources",
                type="graph",
                targets=[
                    {
                        "expr": "dt_rag_system_cpu_usage_percent",
                        "legendFormat": "CPU Usage %",
                        "refId": "A"
                    },
                    {
                        "expr": "dt_rag_system_memory_usage_bytes{memory_type='used'} / dt_rag_system_memory_usage_bytes{memory_type='total'} * 100",
                        "legendFormat": "Memory Usage %",
                        "refId": "B"
                    }
                ],
                grid_pos={"x": 12, "y": 3, "w": 12, "h": 6}
            ),

            # Request volume by type
            DashboardPanel(
                id=7,
                title="Request Volume by Type",
                type="piechart",
                targets=[
                    {
                        "expr": "sum by (query_type) (rate(dt_rag_requests_total[5m]))",
                        "legendFormat": "{{query_type}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 9, "w": 8, "h": 6}
            ),

            # Active connections
            DashboardPanel(
                id=8,
                title="Active Database Connections",
                type="graph",
                targets=[
                    {
                        "expr": "dt_rag_database_connections_active",
                        "legendFormat": "{{database_type}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 8, "y": 9, "w": 8, "h": 6}
            ),

            # Vector database size
            DashboardPanel(
                id=9,
                title="Vector Database Size",
                type="stat",
                targets=[
                    {
                        "expr": "dt_rag_vector_database_size_entries",
                        "legendFormat": "{{collection}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 16, "y": 9, "w": 8, "h": 6},
                options={
                    "colorMode": "value",
                    "unit": "short"
                }
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG System Overview",
            tags=["dt-rag", "overview", "system"],
            time_from="now-1h",
            time_to="now",
            refresh="30s",
            panels=panels
        )

    def _create_rag_performance_template(self) -> Dashboard:
        """Create RAG performance dashboard template"""
        panels = [
            # Classification performance
            DashboardPanel(
                id=1,
                title="Classification Performance",
                type="graph",
                targets=[
                    {
                        "expr": "rate(dt_rag_classification_total[5m])",
                        "legendFormat": "Classifications/sec",
                        "refId": "A"
                    },
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_classification_duration_seconds_bucket[5m]))",
                        "legendFormat": "P95 Latency",
                        "refId": "B"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 6}
            ),

            # Classification confidence distribution
            DashboardPanel(
                id=2,
                title="Classification Confidence Distribution",
                type="heatmap",
                targets=[
                    {
                        "expr": "increase(dt_rag_classification_confidence_bucket[5m])",
                        "legendFormat": "{{le}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 6}
            ),

            # Search operations
            DashboardPanel(
                id=3,
                title="Search Operations",
                type="graph",
                targets=[
                    {
                        "expr": "rate(dt_rag_search_operations_total[5m])",
                        "legendFormat": "{{search_type}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 6, "w": 12, "h": 6}
            ),

            # Search quality scores
            DashboardPanel(
                id=4,
                title="Search Quality Scores",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_search_quality_score_bucket[5m]))",
                        "legendFormat": "P50 Quality",
                        "refId": "A"
                    },
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_search_quality_score_bucket[5m]))",
                        "legendFormat": "P95 Quality",
                        "refId": "B"
                    }
                ],
                grid_pos={"x": 12, "y": 6, "w": 12, "h": 6}
            ),

            # Taxonomy operations
            DashboardPanel(
                id=5,
                title="Taxonomy Operations",
                type="graph",
                targets=[
                    {
                        "expr": "rate(dt_rag_taxonomy_operations_total[5m])",
                        "legendFormat": "{{operation_type}} - {{status}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 12, "w": 12, "h": 6}
            ),

            # Current taxonomy version
            DashboardPanel(
                id=6,
                title="Current Taxonomy Version",
                type="stat",
                targets=[
                    {
                        "expr": "dt_rag_taxonomy_version_current",
                        "legendFormat": "Version",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 12, "w": 12, "h": 6},
                options={
                    "colorMode": "background",
                    "graphMode": "none",
                    "textMode": "auto"
                }
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG Performance Metrics",
            tags=["dt-rag", "performance", "rag"],
            time_from="now-1h",
            time_to="now",
            refresh="15s",
            panels=panels
        )

    def _create_slo_compliance_template(self) -> Dashboard:
        """Create SLO compliance dashboard template"""
        panels = [
            # SLO compliance overview
            DashboardPanel(
                id=1,
                title="SLO Compliance Status",
                type="table",
                targets=[
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "P95 Latency (≤4s)",
                        "refId": "A"
                    },
                    {
                        "expr": "rate(dt_rag_requests_total{status='error'}[5m]) / rate(dt_rag_requests_total[5m]) * 100",
                        "legendFormat": "Error Rate (≤1%)",
                        "refId": "B"
                    },
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_cost_per_query_won_bucket[5m]))",
                        "legendFormat": "Cost per Query (≤₩10)",
                        "refId": "C"
                    },
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_faithfulness_score_bucket[5m]))",
                        "legendFormat": "Faithfulness (≥0.85)",
                        "refId": "D"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 24, "h": 8}
            ),

            # P95 Latency SLO
            DashboardPanel(
                id=2,
                title="P95 Latency SLO (Target: ≤4s)",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "P95 Latency",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 8, "w": 12, "h": 6},
                options={
                    "thresholds": [
                        {"colorMode": "critical", "op": "gt", "value": 4.0}
                    ]
                }
            ),

            # Cost SLO
            DashboardPanel(
                id=3,
                title="Cost per Query SLO (Target: ≤₩10)",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_cost_per_query_won_bucket[5m]))",
                        "legendFormat": "Avg Cost per Query",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 8, "w": 12, "h": 6},
                options={
                    "thresholds": [
                        {"colorMode": "critical", "op": "gt", "value": 10.0}
                    ]
                }
            ),

            # Faithfulness SLO
            DashboardPanel(
                id=4,
                title="Faithfulness SLO (Target: ≥0.85)",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_faithfulness_score_bucket[5m]))",
                        "legendFormat": "Avg Faithfulness",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 14, "w": 12, "h": 6},
                options={
                    "thresholds": [
                        {"colorMode": "critical", "op": "lt", "value": 0.85}
                    ]
                }
            ),

            # Availability SLO
            DashboardPanel(
                id=5,
                title="Availability SLO (Target: ≥99.5%)",
                type="graph",
                targets=[
                    {
                        "expr": "(rate(dt_rag_requests_total{status='success'}[5m]) / rate(dt_rag_requests_total[5m])) * 100",
                        "legendFormat": "Availability %",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 14, "w": 12, "h": 6},
                options={
                    "thresholds": [
                        {"colorMode": "critical", "op": "lt", "value": 99.5}
                    ]
                }
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG SLO Compliance",
            tags=["dt-rag", "slo", "compliance"],
            time_from="now-1h",
            time_to="now",
            refresh="30s",
            panels=panels
        )

    def _create_cost_optimization_template(self) -> Dashboard:
        """Create cost optimization dashboard template"""
        panels = [
            # Total cost trends
            DashboardPanel(
                id=1,
                title="Total Cost Trends (₩)",
                type="graph",
                targets=[
                    {
                        "expr": "rate(dt_rag_cost_total_won[5m]) * 300",  # Cost per 5 minutes
                        "legendFormat": "{{service}} - {{model}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 6}
            ),

            # Cost per query distribution
            DashboardPanel(
                id=2,
                title="Cost per Query Distribution",
                type="heatmap",
                targets=[
                    {
                        "expr": "increase(dt_rag_cost_per_query_won_bucket[5m])",
                        "legendFormat": "{{le}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 6}
            ),

            # Cost by service
            DashboardPanel(
                id=3,
                title="Cost Breakdown by Service",
                type="piechart",
                targets=[
                    {
                        "expr": "sum by (service) (rate(dt_rag_cost_total_won[5m]))",
                        "legendFormat": "{{service}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 6, "w": 8, "h": 6}
            ),

            # Cost by model
            DashboardPanel(
                id=4,
                title="Cost Breakdown by Model",
                type="piechart",
                targets=[
                    {
                        "expr": "sum by (model) (rate(dt_rag_cost_total_won[5m]))",
                        "legendFormat": "{{model}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 8, "y": 6, "w": 8, "h": 6}
            ),

            # Cost efficiency metrics
            DashboardPanel(
                id=5,
                title="Cost Efficiency",
                type="stat",
                targets=[
                    {
                        "expr": "rate(dt_rag_requests_total{status='success'}[5m]) / rate(dt_rag_cost_total_won[5m])",
                        "legendFormat": "Requests per Won",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 16, "y": 6, "w": 8, "h": 6},
                options={
                    "colorMode": "value",
                    "unit": "short"
                }
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG Cost Optimization",
            tags=["dt-rag", "cost", "optimization"],
            time_from="now-6h",
            time_to="now",
            refresh="1m",
            panels=panels
        )

    def _create_quality_metrics_template(self) -> Dashboard:
        """Create quality metrics dashboard template"""
        panels = [
            # Faithfulness scores
            DashboardPanel(
                id=1,
                title="Faithfulness Scores",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_faithfulness_score_bucket[5m]))",
                        "legendFormat": "P50 Faithfulness",
                        "refId": "A"
                    },
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_faithfulness_score_bucket[5m]))",
                        "legendFormat": "P95 Faithfulness",
                        "refId": "B"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 6}
            ),

            # User satisfaction
            DashboardPanel(
                id=2,
                title="User Satisfaction",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_user_satisfaction_score_bucket[5m]))",
                        "legendFormat": "Avg Satisfaction",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 6}
            ),

            # Classification confidence by category
            DashboardPanel(
                id=3,
                title="Classification Confidence by Category",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_classification_confidence_bucket[5m])) by (category)",
                        "legendFormat": "{{category}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 6, "w": 12, "h": 6}
            ),

            # Search quality by type
            DashboardPanel(
                id=4,
                title="Search Quality by Type",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_search_quality_score_bucket[5m])) by (search_type)",
                        "legendFormat": "{{search_type}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 6, "w": 12, "h": 6}
            ),

            # Quality trends
            DashboardPanel(
                id=5,
                title="Quality Trends Over Time",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_faithfulness_score_bucket[1h]))",
                        "legendFormat": "Faithfulness (1h avg)",
                        "refId": "A"
                    },
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_search_quality_score_bucket[1h]))",
                        "legendFormat": "Search Quality (1h avg)",
                        "refId": "B"
                    }
                ],
                grid_pos={"x": 0, "y": 12, "w": 24, "h": 6}
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG Quality Metrics",
            tags=["dt-rag", "quality", "metrics"],
            time_from="now-2h",
            time_to="now",
            refresh="1m",
            panels=panels
        )

    def _create_taxonomy_operations_template(self) -> Dashboard:
        """Create taxonomy operations dashboard template"""
        panels = [
            # Taxonomy operation rates
            DashboardPanel(
                id=1,
                title="Taxonomy Operation Rates",
                type="graph",
                targets=[
                    {
                        "expr": "rate(dt_rag_taxonomy_operations_total[5m])",
                        "legendFormat": "{{operation_type}} - {{status}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 6}
            ),

            # Operation latency
            DashboardPanel(
                id=2,
                title="Taxonomy Operation Latency",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.95, rate(dt_rag_taxonomy_operation_duration_seconds_bucket[5m]))",
                        "legendFormat": "{{operation_type}} P95",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 6}
            ),

            # Nodes affected
            DashboardPanel(
                id=3,
                title="Nodes Affected by Operations",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, rate(dt_rag_taxonomy_nodes_affected_bucket[5m]))",
                        "legendFormat": "{{operation_type}} Median",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 6, "w": 12, "h": 6}
            ),

            # Current version
            DashboardPanel(
                id=4,
                title="Current Taxonomy Version",
                type="stat",
                targets=[
                    {
                        "expr": "dt_rag_taxonomy_version_current",
                        "legendFormat": "Version",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 6, "w": 12, "h": 6}
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG Taxonomy Operations",
            tags=["dt-rag", "taxonomy", "operations"],
            time_from="now-2h",
            time_to="now",
            refresh="30s",
            panels=panels
        )

    def _create_alerting_status_template(self) -> Dashboard:
        """Create alerting status dashboard template"""
        panels = [
            # Active alerts count
            DashboardPanel(
                id=1,
                title="Active Alerts",
                type="stat",
                targets=[
                    {
                        "expr": "count(ALERTS{alertstate='firing'})",
                        "legendFormat": "Active Alerts",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "background",
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 1},
                            {"color": "red", "value": 5}
                        ]
                    }
                }
            ),

            # HITL queue size
            DashboardPanel(
                id=2,
                title="HITL Queue Size",
                type="stat",
                targets=[
                    {
                        "expr": "dt_rag_hitl_queue_size",
                        "legendFormat": "{{queue_type}}",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 6, "y": 0, "w": 6, "h": 3}
            ),

            # Alert firing rate
            DashboardPanel(
                id=3,
                title="Alert Firing Rate",
                type="graph",
                targets=[
                    {
                        "expr": "rate(prometheus_notifications_total[5m])",
                        "legendFormat": "Alerts/sec",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 0, "y": 3, "w": 12, "h": 6}
            ),

            # SLO burn rate
            DashboardPanel(
                id=4,
                title="SLO Error Budget Burn Rate",
                type="graph",
                targets=[
                    {
                        "expr": "rate(dt_rag_requests_total{status='error'}[5m]) / 0.005",  # Assuming 0.5% error budget
                        "legendFormat": "Error Budget Burn Rate",
                        "refId": "A"
                    }
                ],
                grid_pos={"x": 12, "y": 3, "w": 12, "h": 6}
            )
        ]

        return Dashboard(
            id=None,
            title="DT-RAG Alerting Status",
            tags=["dt-rag", "alerting", "status"],
            time_from="now-1h",
            time_to="now",
            refresh="15s",
            panels=panels
        )

    def _apply_template_customizations(self, template: Dashboard, **kwargs) -> Dashboard:
        """Apply customizations to dashboard template"""
        # Apply any custom time ranges, refresh rates, etc.
        if 'time_from' in kwargs:
            template.time_from = kwargs['time_from']
        if 'time_to' in kwargs:
            template.time_to = kwargs['time_to']
        if 'refresh' in kwargs:
            template.refresh = kwargs['refresh']

        return template

    def export_grafana_json(self, dashboard_type: str, **kwargs) -> str:
        """Export dashboard as Grafana JSON"""
        dashboard_config = self.generate_dashboard(dashboard_type, **kwargs)

        # Convert to Grafana format
        grafana_dashboard = {
            "dashboard": {
                "id": dashboard_config.get('id'),
                "title": dashboard_config['title'],
                "tags": dashboard_config['tags'],
                "time": {
                    "from": dashboard_config['time_from'],
                    "to": dashboard_config['time_to']
                },
                "refresh": dashboard_config['refresh'],
                "panels": [self._convert_panel_to_grafana(panel) for panel in dashboard_config['panels']],
                "templating": {
                    "list": dashboard_config.get('template_vars', [])
                },
                "version": 1,
                "editable": True,
                "graphTooltip": 1,
                "links": [],
                "annotations": {
                    "list": []
                },
                "schemaVersion": 30
            },
            "overwrite": True
        }

        return json.dumps(grafana_dashboard, indent=2)

    def _convert_panel_to_grafana(self, panel: Dict[str, Any]) -> Dict[str, Any]:
        """Convert panel configuration to Grafana format"""
        grafana_panel = {
            "id": panel['id'],
            "title": panel['title'],
            "type": panel['type'],
            "gridPos": panel['grid_pos'],
            "targets": panel['targets'],
            "options": panel.get('options', {}),
            "fieldConfig": {
                "defaults": {},
                "overrides": []
            }
        }

        return grafana_panel