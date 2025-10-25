# @CODE:MYPY-001:PHASE2:BATCH4
"""
Quality monitoring system for RAG evaluation

Provides real-time quality monitoring, alerting, and trend analysis:
- Continuous quality metrics tracking
- Threshold-based alerting
- Performance degradation detection
- Quality trend analysis and reporting
- Automated quality gate enforcement
"""

import asyncio
import json
import logging
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..api.database import db_manager
from .models import (
    EvaluationMetrics,
    EvaluationResult,
    QualityAlert,
    QualityThresholds,
    SearchLog,
)

logger = logging.getLogger(__name__)


class QualityMonitor:
    """Real-time quality monitoring and alerting system"""

    def __init__(self) -> None:
        self.thresholds = QualityThresholds(
            faithfulness_min=0.85,
            context_precision_min=0.75,
            context_recall_min=0.70,
            answer_relevancy_min=0.80,
            response_time_max=5.0,
        )

        # In-memory metric buffers for real-time monitoring
        self.metric_buffer_size = 100
        self.metric_buffers: Dict[str, deque[float]] = {
            "faithfulness": deque(maxlen=self.metric_buffer_size),
            "context_precision": deque(maxlen=self.metric_buffer_size),
            "context_recall": deque(maxlen=self.metric_buffer_size),
            "answer_relevancy": deque(maxlen=self.metric_buffer_size),
            "response_time": deque(maxlen=self.metric_buffer_size),
        }

        # Alert state tracking
        self.active_alerts: Dict[str, QualityAlert] = {}
        self.alert_cooldown = timedelta(minutes=10)  # Prevent alert spam

        # Quality trend tracking
        self.trend_window_minutes = 60
        self.quality_history: deque[Dict[str, Any]] = deque(maxlen=1440)  # 24 hours of minute-level data

    async def record_evaluation(self, evaluation: EvaluationResult) -> List[QualityAlert]:
        """Record new evaluation result and check for quality issues"""
        try:
            # Update metric buffers
            metrics = evaluation.metrics
            if metrics.faithfulness is not None:
                self.metric_buffers["faithfulness"].append(metrics.faithfulness)
            if metrics.context_precision is not None:
                self.metric_buffers["context_precision"].append(
                    metrics.context_precision
                )
            if metrics.context_recall is not None:
                self.metric_buffers["context_recall"].append(metrics.context_recall)
            if metrics.answer_relevancy is not None:
                self.metric_buffers["answer_relevancy"].append(metrics.answer_relevancy)
            if metrics.response_time is not None:
                self.metric_buffers["response_time"].append(metrics.response_time)

            # Update quality history
            self.quality_history.append(
                {
                    "timestamp": evaluation.timestamp,
                    "metrics": metrics.dict(),
                    "quality_flags": evaluation.quality_flags,
                }
            )

            # Check for quality alerts
            alerts = await self._check_quality_thresholds(metrics, evaluation.timestamp)

            # Process any new alerts
            for alert in alerts:
                await self._process_alert(alert)

            return alerts

        except Exception as e:
            logger.error(f"Failed to record evaluation: {e}")
            return []

    async def get_quality_status(self) -> Dict[str, Any]:
        """Get current quality status and metrics"""
        try:
            current_metrics = self._calculate_current_metrics()
            trend_analysis = self._analyze_quality_trends()
            alert_summary = self._get_alert_summary()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "current_metrics": current_metrics,
                "trend_analysis": trend_analysis,
                "alert_summary": alert_summary,
                "quality_gates": self._check_quality_gates(current_metrics),
                "recommendations": self._generate_quality_recommendations(
                    current_metrics, trend_analysis
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get quality status: {e}")
            return {"error": str(e)}

    async def get_quality_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get quality trends over specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            async with db_manager.async_session() as session:
                # Query search logs for trend analysis
                from sqlalchemy import text

                query = text(
                    """
                    SELECT
                        DATE_TRUNC('hour', created_at) as hour,
                        AVG(faithfulness) as avg_faithfulness,
                        AVG(context_precision) as avg_context_precision,
                        AVG(context_recall) as avg_context_recall,
                        AVG(answer_relevancy) as avg_answer_relevancy,
                        AVG(response_time) as avg_response_time,
                        COUNT(*) as evaluation_count
                    FROM search_logs
                    WHERE created_at >= :cutoff_time
                        AND is_valid_evaluation = true
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour
                """
                )

                result = await session.execute(query, {"cutoff_time": cutoff_time})
                rows = result.fetchall()

                trend_data = []
                for row in rows:
                    trend_data.append(
                        {
                            "hour": row[0].isoformat() if row[0] else None,
                            "faithfulness": float(row[1]) if row[1] else None,
                            "context_precision": float(row[2]) if row[2] else None,
                            "context_recall": float(row[3]) if row[3] else None,
                            "answer_relevancy": float(row[4]) if row[4] else None,
                            "response_time": float(row[5]) if row[5] else None,
                            "evaluation_count": int(row[6]) if row[6] else 0,
                        }
                    )

                return {
                    "period_hours": hours,
                    "data_points": len(trend_data),
                    "trends": trend_data,
                    "summary": self._summarize_trends(trend_data),
                }

        except Exception as e:
            logger.error(f"Failed to get quality trends: {e}")
            return {"error": str(e)}

    async def get_quality_alerts(self, active_only: bool = True) -> List[QualityAlert]:
        """Get quality alerts"""
        try:
            if active_only:
                return list(self.active_alerts.values())
            else:
                # TODO: Implement alert history from database
                return list(self.active_alerts.values())

        except Exception as e:
            logger.error(f"Failed to get quality alerts: {e}")
            return []

    async def update_thresholds(self, thresholds: QualityThresholds) -> None:
        """Update quality monitoring thresholds"""
        self.thresholds = thresholds
        logger.info(f"Quality thresholds updated: {thresholds.dict()}")

        # Re-evaluate current metrics against new thresholds
        current_metrics = self._calculate_current_metrics()
        if current_metrics:
            # Create dummy metrics object for threshold checking
            metrics = EvaluationMetrics(**current_metrics)
            alerts = await self._check_quality_thresholds(metrics, datetime.utcnow())

            for alert in alerts:
                await self._process_alert(alert)

    def _calculate_current_metrics(self) -> Dict[str, float]:
        """Calculate current metric averages from buffer"""
        current_metrics = {}

        for metric_name, buffer in self.metric_buffers.items():
            if buffer:
                current_metrics[metric_name] = statistics.mean(buffer)
                current_metrics[f"{metric_name}_p95"] = self._percentile(
                    list(buffer), 95
                )
                current_metrics[f"{metric_name}_trend"] = self._calculate_trend(
                    list(buffer)
                )

        return current_metrics

    def _analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends from recent history"""
        if len(self.quality_history) < 10:
            return {"insufficient_data": True}

        recent_data = list(self.quality_history)[-60:]  # Last hour

        trends = {}
        for metric in [
            "faithfulness",
            "context_precision",
            "context_recall",
            "answer_relevancy",
        ]:
            values = [
                entry["metrics"].get(metric)
                for entry in recent_data
                if entry["metrics"].get(metric) is not None
            ]

            if len(values) >= 5:
                trends[metric] = {
                    "direction": self._calculate_trend(values),
                    "volatility": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "recent_average": (
                        statistics.mean(values[-10:])
                        if len(values) >= 10
                        else statistics.mean(values)
                    ),
                }

        return trends

    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts"""
        if not self.active_alerts:
            return {"total_alerts": 0, "severity_breakdown": {}}

        severity_counts: Dict[str, int] = defaultdict(int)
        for alert in self.active_alerts.values():
            severity_counts[alert.severity] += 1

        return {
            "total_alerts": len(self.active_alerts),
            "severity_breakdown": dict(severity_counts),
            "oldest_alert": min(
                alert.timestamp for alert in self.active_alerts.values()
            ).isoformat(),
            "newest_alert": max(
                alert.timestamp for alert in self.active_alerts.values()
            ).isoformat(),
        }

    def _check_quality_gates(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Check if quality gates are passing"""
        gates: Dict[str, Any] = {}

        # Define quality gates with explicit thresholds
        gate_checks: List[Tuple[str, str, float, str]] = [
            ("faithfulness_gate", "faithfulness", self.thresholds.faithfulness_min, ">="),
            ("precision_gate", "context_precision", self.thresholds.context_precision_min, ">="),
            ("recall_gate", "context_recall", self.thresholds.context_recall_min, ">="),
            ("relevancy_gate", "answer_relevancy", self.thresholds.answer_relevancy_min, ">="),
            ("performance_gate", "response_time", self.thresholds.response_time_max, "<="),
        ]

        all_passing = True
        for gate_name, metric_key, threshold_value, operator in gate_checks:
            metric_value = current_metrics.get(metric_key)

            if metric_value is not None:
                if operator == ">=":
                    passing = metric_value >= threshold_value
                else:  # '<='
                    passing = metric_value <= threshold_value

                gates[gate_name] = {
                    "passing": passing,
                    "current_value": metric_value,
                    "threshold": threshold_value,
                    "margin": abs(metric_value - threshold_value),
                }

                if not passing:
                    all_passing = False
            else:
                gates[gate_name] = {
                    "passing": None,
                    "current_value": None,
                    "threshold": threshold_value,
                    "margin": None,
                    "status": "no_data",
                }
                all_passing = False

        return {"overall_passing": all_passing, "gates": gates}

    def _generate_quality_recommendations(
        self, current_metrics: Dict[str, float], trend_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []

        # Check individual metrics
        if current_metrics.get("faithfulness", 1.0) < self.thresholds.faithfulness_min:
            recommendations.append(
                "Improve response grounding - consider stricter fact verification"
            )

        if (
            current_metrics.get("context_precision", 1.0)
            < self.thresholds.context_precision_min
        ):
            recommendations.append(
                "Optimize retrieval relevance - improve ranking algorithms"
            )

        if (
            current_metrics.get("context_recall", 1.0)
            < self.thresholds.context_recall_min
        ):
            recommendations.append(
                "Expand retrieval scope - increase number of retrieved contexts"
            )

        if (
            current_metrics.get("answer_relevancy", 1.0)
            < self.thresholds.answer_relevancy_min
        ):
            recommendations.append(
                "Improve response targeting - better query understanding"
            )

        if (
            current_metrics.get("response_time", 0.0)
            > self.thresholds.response_time_max
        ):
            recommendations.append("Optimize performance - reduce response latency")

        # Check trends
        for metric, trend_info in trend_analysis.items():
            if (
                isinstance(trend_info, dict) and trend_info.get("direction", 0) < -0.05
            ):  # Declining
                recommendations.append(
                    f"Address declining {metric} trend - investigate recent changes"
                )

        return recommendations

    async def _check_quality_thresholds(
        self, metrics: EvaluationMetrics, timestamp: datetime
    ) -> List[QualityAlert]:
        """Check metrics against thresholds and generate alerts"""
        alerts = []

        # Check faithfulness
        if (
            metrics.faithfulness is not None
            and metrics.faithfulness < self.thresholds.faithfulness_min
        ):
            alerts.append(
                self._create_alert(
                    "faithfulness",
                    metrics.faithfulness,
                    self.thresholds.faithfulness_min,
                    "high",
                    f"Faithfulness score {metrics.faithfulness:.3f} is below threshold {self.thresholds.faithfulness_min:.3f}",
                    timestamp,
                    [
                        "Review response grounding",
                        "Check fact verification pipeline",
                        "Audit knowledge base",
                    ],
                )
            )

        # Check context precision
        if (
            metrics.context_precision is not None
            and metrics.context_precision < self.thresholds.context_precision_min
        ):
            alerts.append(
                self._create_alert(
                    "context_precision",
                    metrics.context_precision,
                    self.thresholds.context_precision_min,
                    "medium",
                    f"Context precision {metrics.context_precision:.3f} is below threshold {self.thresholds.context_precision_min:.3f}",
                    timestamp,
                    [
                        "Improve retrieval ranking",
                        "Reduce retrieval count",
                        "Optimize query processing",
                    ],
                )
            )

        # Check context recall
        if (
            metrics.context_recall is not None
            and metrics.context_recall < self.thresholds.context_recall_min
        ):
            alerts.append(
                self._create_alert(
                    "context_recall",
                    metrics.context_recall,
                    self.thresholds.context_recall_min,
                    "medium",
                    f"Context recall {metrics.context_recall:.3f} is below threshold {self.thresholds.context_recall_min:.3f}",
                    timestamp,
                    [
                        "Increase retrieval scope",
                        "Improve semantic search",
                        "Expand knowledge base coverage",
                    ],
                )
            )

        # Check answer relevancy
        if (
            metrics.answer_relevancy is not None
            and metrics.answer_relevancy < self.thresholds.answer_relevancy_min
        ):
            alerts.append(
                self._create_alert(
                    "answer_relevancy",
                    metrics.answer_relevancy,
                    self.thresholds.answer_relevancy_min,
                    "medium",
                    f"Answer relevancy {metrics.answer_relevancy:.3f} is below threshold {self.thresholds.answer_relevancy_min:.3f}",
                    timestamp,
                    [
                        "Improve query understanding",
                        "Optimize response generation",
                        "Better intent classification",
                    ],
                )
            )

        # Check response time
        if (
            metrics.response_time is not None
            and metrics.response_time > self.thresholds.response_time_max
        ):
            alerts.append(
                self._create_alert(
                    "response_time",
                    metrics.response_time,
                    self.thresholds.response_time_max,
                    "low",
                    f"Response time {metrics.response_time:.2f}s exceeds threshold {self.thresholds.response_time_max:.2f}s",
                    timestamp,
                    [
                        "Optimize retrieval performance",
                        "Cache frequent queries",
                        "Scale infrastructure",
                    ],
                )
            )

        return alerts

    def _create_alert(
        self,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        severity: str,
        message: str,
        timestamp: datetime,
        suggested_actions: List[str],
    ) -> QualityAlert:
        """Create a quality alert"""
        alert_id = f"{metric_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        return QualityAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            severity=severity,
            message=message,
            timestamp=timestamp,
            suggested_actions=suggested_actions,
        )

    async def _process_alert(self, alert: QualityAlert) -> None:
        """Process and store alert"""
        try:
            # Check if we're in cooldown for this metric
            last_alert_time = self.active_alerts.get(alert.metric_name)
            if (
                last_alert_time
                and (alert.timestamp - last_alert_time.timestamp) < self.alert_cooldown
            ):
                return  # Skip alert due to cooldown

            # Store alert
            self.active_alerts[alert.metric_name] = alert

            # Log alert
            logger.warning(f"Quality alert: {alert.message}")

            # TODO: Send notifications (email, webhook, etc.)

        except Exception as e:
            logger.error(f"Failed to process alert: {e}")

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction (-1 to 1)"""
        if len(values) < 3:
            return 0.0

        # Simple linear regression slope
        n = len(values)
        x = list(range(n))

        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] * x[i] for i in range(n))

        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Normalize to [-1, 1] range
        return max(-1.0, min(1.0, slope))

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100.0) * (len(sorted_values) - 1))
        return sorted_values[index]

    def _summarize_trends(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize trend data"""
        if not trend_data:
            return {}

        metrics = [
            "faithfulness",
            "context_precision",
            "context_recall",
            "answer_relevancy",
            "response_time",
        ]
        summary = {}

        for metric in metrics:
            values = [
                entry[metric] for entry in trend_data if entry[metric] is not None
            ]

            if values:
                summary[metric] = {
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": self._calculate_trend(values),
                    "data_points": len(values),
                }

        # Calculate overall evaluation volume
        total_evaluations = sum(entry["evaluation_count"] for entry in trend_data)
        summary["evaluation_volume"] = {
            "total": total_evaluations,
            "average_per_hour": (
                total_evaluations / len(trend_data) if trend_data else 0
            ),
        }

        return summary
