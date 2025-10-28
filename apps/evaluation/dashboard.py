# @CODE:EVAL-001 | SPEC: .moai/specs/SPEC-EVAL-001/spec.md | TEST: tests/evaluation/

"""
Real-time RAGAS evaluation dashboard

Provides interactive web dashboard for:
- Real-time quality metrics visualization
- Quality trend monitoring
- Alert management
- Experiment tracking
- System performance overview
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .quality_monitor import QualityMonitor
from .experiment_tracker import ExperimentTracker
from ..api.database import db_manager

dashboard_router = APIRouter(prefix="/dashboard", tags=["Evaluation Dashboard"])

# Initialize components
quality_monitor = QualityMonitor()
experiment_tracker = ExperimentTracker()


# WebSocket connection manager
class ConnectionManager:
    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                self.active_connections.remove(connection)


manager = ConnectionManager()

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DT-RAG Evaluation Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        .alert-high { border-left: 4px solid #ef4444; }
        .alert-medium { border-left: 4px solid #f59e0b; }
        .alert-low { border-left: 4px solid #3b82f6; }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-healthy { background-color: #10b981; }
        .status-warning { background-color: #f59e0b; }
        .status-critical { background-color: #ef4444; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-4xl font-bold text-gray-800">DT-RAG Evaluation Dashboard</h1>
            <p class="text-gray-600 mt-2">Real-time RAGAS metrics and quality monitoring</p>
            <div class="flex items-center mt-4">
                <div class="status-indicator status-healthy"></div>
                <span class="text-sm text-gray-600">System Status: <span id="system-status">Healthy</span></span>
                <span class="text-xs text-gray-500 ml-4">Last Updated: <span id="last-update">--</span></span>
            </div>
        </div>

        <!-- Metrics Overview -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">Faithfulness</h3>
                <div class="text-3xl font-bold" id="faithfulness-metric">--</div>
                <div class="text-sm opacity-75" id="faithfulness-trend">-- trend</div>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">Context Precision</h3>
                <div class="text-3xl font-bold" id="precision-metric">--</div>
                <div class="text-sm opacity-75" id="precision-trend">-- trend</div>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">Context Recall</h3>
                <div class="text-3xl font-bold" id="recall-metric">--</div>
                <div class="text-sm opacity-75" id="recall-trend">-- trend</div>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">Answer Relevancy</h3>
                <div class="text-3xl font-bold" id="relevancy-metric">--</div>
                <div class="text-sm opacity-75" id="relevancy-trend">-- trend</div>
            </div>
        </div>

        <!-- Charts and Tables -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <!-- Quality Trends Chart -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-xl font-semibold mb-4">Quality Trends (24h)</h3>
                <canvas id="trendsChart" width="400" height="200"></canvas>
            </div>

            <!-- Active Alerts -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-xl font-semibold mb-4">Active Alerts</h3>
                <div id="alerts-container" class="space-y-3 max-h-80 overflow-y-auto">
                    <!-- Alerts will be populated here -->
                </div>
            </div>
        </div>

        <!-- Quality Gates and Experiments -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Quality Gates -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-xl font-semibold mb-4">Quality Gates</h3>
                <div id="quality-gates" class="space-y-3">
                    <!-- Quality gates will be populated here -->
                </div>
            </div>

            <!-- Running Experiments -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-xl font-semibold mb-4">Running Experiments</h3>
                <div id="experiments-container" class="space-y-3">
                    <!-- Experiments will be populated here -->
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="bg-white rounded-lg shadow-lg p-6 mt-8">
            <h3 class="text-xl font-semibold mb-4">System Recommendations</h3>
            <div id="recommendations-container" class="space-y-2">
                <!-- Recommendations will be populated here -->
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for real-time updates
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/evaluation/dashboard/ws`);

        // Chart setup
        const ctx = document.getElementById('trendsChart').getContext('2d');
        const trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Faithfulness',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Context Precision',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Context Recall',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Answer Relevancy',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        ticks: {
                            callback: function(value) {
                                return (value * 100).toFixed(0) + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });

        // WebSocket event handlers
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        ws.onopen = function(event) {
            console.log('WebSocket connected');
        };

        ws.onclose = function(event) {
            console.log('WebSocket disconnected');
            // Try to reconnect after 5 seconds
            setTimeout(() => {
                location.reload();
            }, 5000);
        };

        function updateDashboard(data) {
            // Update timestamp
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();

            // Update metrics
            if (data.current_metrics) {
                updateMetric('faithfulness', data.current_metrics.faithfulness);
                updateMetric('precision', data.current_metrics.context_precision);
                updateMetric('recall', data.current_metrics.context_recall);
                updateMetric('relevancy', data.current_metrics.answer_relevancy);
            }

            // Update trends chart
            if (data.trends && data.trends.trends) {
                updateTrendsChart(data.trends.trends);
            }

            // Update alerts
            if (data.active_alerts) {
                updateAlerts(data.active_alerts);
            }

            // Update quality gates
            if (data.quality_gates && data.quality_gates.gates) {
                updateQualityGates(data.quality_gates);
            }

            // Update recommendations
            if (data.recommendations) {
                updateRecommendations(data.recommendations);
            }
        }

        function updateMetric(metricName, value) {
            const metricElement = document.getElementById(`${metricName}-metric`);
            const trendElement = document.getElementById(`${metricName}-trend`);

            if (value !== null && value !== undefined) {
                metricElement.textContent = (value * 100).toFixed(1) + '%';
                // TODO: Calculate and show trend
                trendElement.textContent = 'stable';
            }
        }

        function updateTrendsChart(trendsData) {
            const labels = trendsData.map(d => new Date(d.hour).toLocaleTimeString());
            trendsChart.data.labels = labels;
            trendsChart.data.datasets[0].data = trendsData.map(d => d.faithfulness);
            trendsChart.data.datasets[1].data = trendsData.map(d => d.context_precision);
            trendsChart.data.datasets[2].data = trendsData.map(d => d.context_recall);
            trendsChart.data.datasets[3].data = trendsData.map(d => d.answer_relevancy);
            trendsChart.update();
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');

            if (alerts.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-sm">No active alerts</p>';
                return;
            }

            container.innerHTML = alerts.map(alert => `
                <div class="p-3 border-l-4 ${getSeverityClass(alert.severity)} bg-gray-50 rounded">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold text-sm">${alert.metric_name}</h4>
                            <p class="text-xs text-gray-600 mt-1">${alert.message}</p>
                        </div>
                        <span class="text-xs text-gray-500">${new Date(alert.timestamp).toLocaleTimeString()}</span>
                    </div>
                    ${alert.suggested_actions.length > 0 ? `
                        <div class="mt-2">
                            <p class="text-xs font-medium text-gray-700">Suggested Actions:</p>
                            <ul class="text-xs text-gray-600 mt-1">
                                ${alert.suggested_actions.map(action => `<li>• ${action}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }

        function updateQualityGates(qualityGates) {
            const container = document.getElementById('quality-gates');
            const gates = qualityGates.gates;

            container.innerHTML = Object.entries(gates).map(([gateName, gate]) => `
                <div class="flex justify-between items-center p-3 border rounded">
                    <div class="flex items-center">
                        <div class="status-indicator ${gate.passing ? 'status-healthy' : 'status-critical'}"></div>
                        <span class="font-medium text-sm">${gateName.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase())}</span>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-bold ${gate.passing ? 'text-green-600' : 'text-red-600'}">
                            ${gate.current_value !== null ? (gate.current_value * 100).toFixed(1) + '%' : 'N/A'}
                        </div>
                        <div class="text-xs text-gray-500">Threshold: ${(gate.threshold * 100).toFixed(1)}%</div>
                    </div>
                </div>
            `).join('');
        }

        function updateRecommendations(recommendations) {
            const container = document.getElementById('recommendations-container');

            if (recommendations.length === 0) {
                container.innerHTML = '<p class="text-green-600 text-sm">System performing well - no recommendations</p>';
                return;
            }

            container.innerHTML = recommendations.map(rec => `
                <div class="flex items-start space-x-3">
                    <div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <p class="text-sm text-gray-700">${rec}</p>
                </div>
            `).join('');
        }

        function getSeverityClass(severity) {
            switch (severity) {
                case 'high': return 'alert-high';
                case 'medium': return 'alert-medium';
                case 'low': return 'alert-low';
                default: return 'alert-medium';
            }
        }

        // Initial data load
        loadInitialData();

        async function loadInitialData() {
            try {
                const response = await fetch('/evaluation/quality/dashboard');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to load initial data:', error);
            }
        }
    </script>
</body>
</html>
"""


@dashboard_router.get("/", response_class=HTMLResponse)
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
async def get_dashboard(request: Request) -> HTMLResponse:
    """Get the evaluation dashboard HTML page"""
    return HTMLResponse(content=DASHBOARD_HTML)


@dashboard_router.websocket("/ws")
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time dashboard updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        dashboard_data = await get_dashboard_data()
        await manager.send_personal_message(json.dumps(dashboard_data), websocket)

        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds

            try:
                dashboard_data = await get_dashboard_data()
                await manager.send_personal_message(
                    json.dumps(dashboard_data), websocket
                )
            except Exception as e:
                print(f"Error sending dashboard update: {e}")
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def get_dashboard_data() -> Dict[str, Any]:
    """Get comprehensive dashboard data"""
    try:
        # Get quality status
        quality_status = await quality_monitor.get_quality_status()

        # Get quality trends
        quality_trends = await quality_monitor.get_quality_trends(hours=24)

        # Get active alerts
        active_alerts = await quality_monitor.get_quality_alerts(active_only=True)

        # Get system statistics
        system_stats = await get_system_statistics()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": quality_status.get("current_metrics", {}),
            "trends": quality_trends,
            "active_alerts": [alert.dict() for alert in active_alerts],
            "quality_gates": quality_status.get("quality_gates", {}),
            "recommendations": quality_status.get("recommendations", []),
            "system_stats": system_stats,
        }

    except Exception as e:
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


async def get_system_statistics() -> Dict[str, Any]:
    """Get system statistics for dashboard"""
    try:
        async with db_manager.async_session() as session:
            from sqlalchemy import text

            # Get recent statistics
            query = text(
                """
                SELECT
                    COUNT(*) as total_evaluations,
                    COUNT(CASE WHEN faithfulness >= 0.85 THEN 1 END) as high_quality_responses,
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN is_valid_evaluation = false THEN 1 END) as failed_evaluations
                FROM search_logs
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            )

            result = await session.execute(query)
            stats = result.fetchone()

            return {
                "evaluations_24h": int(stats[0]) if stats[0] else 0,
                "high_quality_rate": (
                    float(stats[1]) / max(1, stats[0]) if stats[0] else 0
                ),
                "avg_response_time": float(stats[2]) if stats[2] else 0,
                "error_rate": float(stats[3]) / max(1, stats[0]) if stats[0] else 0,
            }

    except Exception as e:
        return {
            "evaluations_24h": 0,
            "high_quality_rate": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "error": str(e),
        }


@dashboard_router.get("/api/metrics")
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
async def get_dashboard_metrics() -> Dict[str, Any]:
    """API endpoint to get current dashboard metrics"""
    return await get_dashboard_data()


@dashboard_router.post("/api/simulate-evaluation")
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
async def simulate_evaluation() -> Dict[str, Any]:
    """Simulate an evaluation for dashboard testing"""
    from .models import EvaluationResult, EvaluationMetrics
    import random

    # Create simulated evaluation result
    simulated_metrics = EvaluationMetrics(
        faithfulness=random.uniform(0.75, 0.95),
        context_precision=random.uniform(0.70, 0.90),
        context_recall=random.uniform(0.65, 0.85),
        answer_relevancy=random.uniform(0.80, 0.95),
        response_time=random.uniform(0.5, 3.0),
    )

    simulated_result = EvaluationResult(
        evaluation_id=f"sim_{datetime.now().strftime('%H%M%S')}",
        query="What is machine learning?",
        metrics=simulated_metrics,
        quality_flags=[],
        recommendations=[],
        timestamp=datetime.utcnow(),
    )

    # Record in quality monitor
    await quality_monitor.record_evaluation(simulated_result)

    return {
        "message": "Simulated evaluation recorded",
        "metrics": simulated_metrics.dict(),
        "timestamp": datetime.utcnow().isoformat(),
    }
