"""
Alerting Manager for DT-RAG v1.8.1

Intelligent alerting system with SLO monitoring, anomaly detection,
and automated degradation strategies for maintaining system reliability.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(Enum):
    """Alert categories"""
    SLO_VIOLATION = "slo_violation"
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE = "performance"
    COST = "cost"
    QUALITY = "quality"
    SECURITY = "security"
    DEGRADATION = "degradation"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    category: AlertCategory
    title: str
    description: str
    source: str
    metrics: Dict[str, Any]
    threshold: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None
    auto_resolution: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class SLOThreshold:
    """SLO threshold configuration"""
    name: str
    target_value: float
    warning_threshold: float
    critical_threshold: float
    measurement_window_minutes: int = 5
    evaluation_frequency_seconds: int = 60


@dataclass
class DegradationStrategy:
    """System degradation strategy"""
    name: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    recovery_conditions: Dict[str, Any]
    max_duration_minutes: int = 60
    enabled: bool = True


class AlertingManager:
    """
    Comprehensive alerting and SLO monitoring system

    Features:
    - SLO/SLI violation detection
    - Intelligent alert routing and escalation
    - Automated degradation strategies
    - Anomaly detection
    - Alert suppression and grouping
    - Integration with external alerting systems
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        slo_config: Optional[Dict[str, float]] = None,
        degradation_enabled: bool = True
    ):
        self.webhook_url = webhook_url
        self.degradation_enabled = degradation_enabled
        self.is_running = False

        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history = deque(maxlen=10000)

        # Metrics tracking for SLO evaluation
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.last_evaluation = {}

        # SLO configuration
        self._initialize_slo_thresholds(slo_config or {})

        # Degradation strategies
        self._initialize_degradation_strategies()

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Suppression rules
        self.suppression_rules = {}
        self.grouped_alerts = defaultdict(list)

        logger.info("AlertingManager initialized with comprehensive monitoring")

    def _initialize_slo_thresholds(self, config: Dict[str, float]):
        """Initialize SLO thresholds from configuration"""
        self.slo_thresholds = {
            'p95_latency_seconds': SLOThreshold(
                name='P95 Latency',
                target_value=config.get('p95_latency_seconds', 4.0),
                warning_threshold=config.get('p95_latency_seconds', 4.0) * 0.9,  # 90% of SLO
                critical_threshold=config.get('p95_latency_seconds', 4.0),
                measurement_window_minutes=5
            ),
            'cost_per_query_won': SLOThreshold(
                name='Cost per Query',
                target_value=config.get('cost_per_query_won', 10.0),
                warning_threshold=config.get('cost_per_query_won', 10.0) * 0.8,  # 80% of SLO
                critical_threshold=config.get('cost_per_query_won', 10.0),
                measurement_window_minutes=10
            ),
            'faithfulness_threshold': SLOThreshold(
                name='Faithfulness Score',
                target_value=config.get('faithfulness_threshold', 0.85),
                warning_threshold=config.get('faithfulness_threshold', 0.85) - 0.05,  # 5% below
                critical_threshold=config.get('faithfulness_threshold', 0.85) - 0.10,  # 10% below
                measurement_window_minutes=15
            ),
            'availability_percent': SLOThreshold(
                name='System Availability',
                target_value=config.get('availability_percent', 99.5),
                warning_threshold=config.get('availability_percent', 99.5) - 1.0,  # 98.5%
                critical_threshold=config.get('availability_percent', 99.5) - 2.0,  # 97.5%
                measurement_window_minutes=5
            ),
            'error_rate_percent': SLOThreshold(
                name='Error Rate',
                target_value=1.0,  # Max 1% error rate
                warning_threshold=0.5,  # 0.5% warning
                critical_threshold=1.0,  # 1% critical
                measurement_window_minutes=5
            )
        }

    def _initialize_degradation_strategies(self):
        """Initialize automated degradation strategies"""
        self.degradation_strategies = {
            'high_latency': DegradationStrategy(
                name='High Latency Mitigation',
                trigger_conditions={
                    'p95_latency_seconds': {'operator': '>', 'value': 4.0},
                    'duration_minutes': 2
                },
                actions=[
                    {'type': 'reduce_search_complexity', 'params': {'max_results': 10}},
                    {'type': 'disable_reranking', 'params': {}},
                    {'type': 'increase_caching', 'params': {'cache_duration': 1800}}
                ],
                recovery_conditions={
                    'p95_latency_seconds': {'operator': '<', 'value': 3.0},
                    'duration_minutes': 5
                }
            ),
            'high_cost': DegradationStrategy(
                name='Cost Optimization',
                trigger_conditions={
                    'cost_per_query_won': {'operator': '>', 'value': 10.0},
                    'duration_minutes': 5
                },
                actions=[
                    {'type': 'switch_to_cheaper_model', 'params': {'model': 'gpt-3.5-turbo'}},
                    {'type': 'reduce_context_length', 'params': {'max_tokens': 500}},
                    {'type': 'increase_caching', 'params': {'cache_duration': 3600}}
                ],
                recovery_conditions={
                    'cost_per_query_won': {'operator': '<', 'value': 8.0},
                    'duration_minutes': 10
                }
            ),
            'low_quality': DegradationStrategy(
                name='Quality Enhancement',
                trigger_conditions={
                    'faithfulness_threshold': {'operator': '<', 'value': 0.75},
                    'duration_minutes': 10
                },
                actions=[
                    {'type': 'enable_verification', 'params': {'verification_model': 'gpt-4'}},
                    {'type': 'reduce_response_speed', 'params': {}},
                    {'type': 'increase_search_depth', 'params': {'max_results': 50}}
                ],
                recovery_conditions={
                    'faithfulness_threshold': {'operator': '>', 'value': 0.85},
                    'duration_minutes': 15
                }
            ),
            'high_error_rate': DegradationStrategy(
                name='Error Rate Mitigation',
                trigger_conditions={
                    'error_rate_percent': {'operator': '>', 'value': 5.0},
                    'duration_minutes': 1
                },
                actions=[
                    {'type': 'enable_circuit_breaker', 'params': {'failure_threshold': 3}},
                    {'type': 'fallback_to_cached_responses', 'params': {}},
                    {'type': 'reduce_concurrent_requests', 'params': {'max_concurrent': 10}}
                ],
                recovery_conditions={
                    'error_rate_percent': {'operator': '<', 'value': 1.0},
                    'duration_minutes': 5
                }
            )
        }

    async def start(self):
        """Start alerting service"""
        if self.is_running:
            logger.warning("AlertingManager is already running")
            return

        try:
            self.is_running = True

            # Start SLO monitoring
            asyncio.create_task(self._slo_monitoring_loop())

            # Start alert processing
            asyncio.create_task(self._alert_processing_loop())

            # Start degradation monitoring
            if self.degradation_enabled:
                asyncio.create_task(self._degradation_monitoring_loop())

            logger.info("AlertingManager started successfully")

        except Exception as e:
            logger.error(f"Failed to start AlertingManager: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Stop alerting service"""
        if not self.is_running:
            return

        try:
            self.is_running = False
            logger.info("AlertingManager stopped")

        except Exception as e:
            logger.error(f"Error stopping AlertingManager: {e}")

    async def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record metric value for SLO evaluation"""
        timestamp = timestamp or datetime.utcnow()

        self.metrics_buffer[metric_name].append({
            'value': value,
            'timestamp': timestamp
        })

    async def trigger_alert(
        self,
        severity: AlertSeverity,
        category: AlertCategory,
        title: str,
        description: str,
        source: str,
        metrics: Dict[str, Any],
        threshold: Optional[Dict[str, Any]] = None,
        recommended_action: Optional[str] = None,
        auto_resolution: bool = False
    ) -> Alert:
        """Trigger a new alert"""
        alert_id = f"{category.value}_{int(time.time() * 1000)}"

        alert = Alert(
            id=alert_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            category=category,
            title=title,
            description=description,
            source=source,
            metrics=metrics,
            threshold=threshold,
            recommended_action=recommended_action,
            auto_resolution=auto_resolution
        )

        # Check suppression rules
        if not self._should_suppress_alert(alert):
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Notify callbacks
            await self._notify_alert_callbacks(alert)

            # Send external notification
            await self._send_alert_notification(alert)

            logger.warning(f"Alert triggered: {title} [{severity.value}]")

        return alert

    async def resolve_alert(self, alert_id: str, resolution_note: Optional[str] = None):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.utcnow()

            del self.active_alerts[alert_id]

            logger.info(f"Alert resolved: {alert.title}")

    async def trigger_slo_violation_alert(self, compliance_status: Dict[str, Any]):
        """Trigger SLO violation alert"""
        violations = compliance_status.get('violations', [])

        for violation in violations:
            slo_name = violation['slo']
            severity = AlertSeverity.CRITICAL if violation['severity'] == 'critical' else AlertSeverity.WARNING

            await self.trigger_alert(
                severity=severity,
                category=AlertCategory.SLO_VIOLATION,
                title=f"SLO Violation: {slo_name}",
                description=f"SLO {slo_name} violated. Target: {violation['target']}, Actual: {violation['actual']}",
                source="slo_monitor",
                metrics={
                    'slo': slo_name,
                    'target': violation['target'],
                    'actual': violation['actual'],
                    'deviation_percent': ((violation['actual'] - violation['target']) / violation['target']) * 100
                },
                threshold=violation,
                recommended_action=self._get_slo_recommendation(slo_name, violation),
                auto_resolution=False
            )

    async def check_anomaly(
        self,
        metric_name: str,
        current_value: float,
        historical_window_minutes: int = 60
    ) -> bool:
        """Check if current value is anomalous compared to historical data"""
        try:
            # Get historical data
            cutoff_time = datetime.utcnow() - timedelta(minutes=historical_window_minutes)
            historical_values = [
                point['value'] for point in self.metrics_buffer[metric_name]
                if point['timestamp'] >= cutoff_time
            ]

            if len(historical_values) < 10:  # Need sufficient data
                return False

            # Simple anomaly detection using standard deviation
            mean_value = sum(historical_values) / len(historical_values)
            variance = sum((x - mean_value) ** 2 for x in historical_values) / len(historical_values)
            std_dev = variance ** 0.5

            # Anomaly if value is more than 3 standard deviations from mean
            threshold = 3.0
            is_anomaly = abs(current_value - mean_value) > (threshold * std_dev)

            if is_anomaly:
                await self.trigger_alert(
                    severity=AlertSeverity.WARNING,
                    category=AlertCategory.PERFORMANCE,
                    title=f"Anomaly Detected: {metric_name}",
                    description=f"Metric {metric_name} value {current_value} is anomalous (mean: {mean_value:.3f}, std: {std_dev:.3f})",
                    source="anomaly_detector",
                    metrics={
                        'metric_name': metric_name,
                        'current_value': current_value,
                        'historical_mean': mean_value,
                        'historical_std': std_dev,
                        'threshold': threshold
                    },
                    recommended_action="Investigate metric spike and check system health"
                )

            return is_anomaly

        except Exception as e:
            logger.error(f"Error in anomaly detection for {metric_name}: {e}")
            return False

    async def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)

    async def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())

    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        active_alerts = list(self.active_alerts.values())
        recent_alerts = [
            alert for alert in self.alert_history
            if (datetime.utcnow() - alert.timestamp).total_seconds() < 3600  # Last hour
        ]

        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)

        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
            category_counts[alert.category.value] += 1

        return {
            'active_alerts_count': len(active_alerts),
            'recent_alerts_count': len(recent_alerts),
            'severity_distribution': dict(severity_counts),
            'category_distribution': dict(category_counts),
            'oldest_active_alert': min(
                (alert.timestamp for alert in active_alerts),
                default=None
            ),
            'degradation_active': any(
                strategy_name in [alert.source for alert in active_alerts]
                for strategy_name in self.degradation_strategies.keys()
            )
        }

    async def _slo_monitoring_loop(self):
        """Main SLO monitoring loop"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                if not self.is_running:
                    break

                await self._evaluate_slos()

            except Exception as e:
                logger.error(f"Error in SLO monitoring: {e}")

    async def _evaluate_slos(self):
        """Evaluate all SLO thresholds"""
        for slo_name, threshold in self.slo_thresholds.items():
            try:
                await self._evaluate_slo_threshold(slo_name, threshold)

            except Exception as e:
                logger.error(f"Error evaluating SLO {slo_name}: {e}")

    async def _evaluate_slo_threshold(self, slo_name: str, threshold: SLOThreshold):
        """Evaluate a specific SLO threshold"""
        # Get recent metric values
        cutoff_time = datetime.utcnow() - timedelta(minutes=threshold.measurement_window_minutes)
        recent_values = [
            point['value'] for point in self.metrics_buffer[slo_name]
            if point['timestamp'] >= cutoff_time
        ]

        if not recent_values:
            return

        # Calculate current metric value (different aggregations for different metrics)
        if slo_name in ['p95_latency_seconds']:
            current_value = self._percentile(recent_values, 0.95)
        elif slo_name in ['cost_per_query_won', 'faithfulness_threshold']:
            current_value = sum(recent_values) / len(recent_values)
        elif slo_name == 'availability_percent':
            # Availability calculated as success rate
            current_value = (sum(1 for v in recent_values if v > 0) / len(recent_values)) * 100
        elif slo_name == 'error_rate_percent':
            # Error rate as percentage
            current_value = (sum(recent_values) / len(recent_values)) * 100
        else:
            current_value = sum(recent_values) / len(recent_values)

        # Check thresholds
        violation_severity = None
        if slo_name in ['p95_latency_seconds', 'cost_per_query_won', 'error_rate_percent']:
            # Higher is worse
            if current_value >= threshold.critical_threshold:
                violation_severity = AlertSeverity.CRITICAL
            elif current_value >= threshold.warning_threshold:
                violation_severity = AlertSeverity.WARNING
        else:
            # Lower is worse (faithfulness, availability)
            if current_value <= threshold.critical_threshold:
                violation_severity = AlertSeverity.CRITICAL
            elif current_value <= threshold.warning_threshold:
                violation_severity = AlertSeverity.WARNING

        # Trigger alert if threshold violated
        if violation_severity:
            await self.trigger_alert(
                severity=violation_severity,
                category=AlertCategory.SLO_VIOLATION,
                title=f"SLO Threshold Exceeded: {threshold.name}",
                description=f"{threshold.name} SLO violation detected. Current: {current_value:.3f}, Target: {threshold.target_value}",
                source="slo_evaluator",
                metrics={
                    'slo_name': slo_name,
                    'current_value': current_value,
                    'target_value': threshold.target_value,
                    'threshold_type': violation_severity.value,
                    'measurement_window_minutes': threshold.measurement_window_minutes
                },
                recommended_action=self._get_slo_recommendation(slo_name, {
                    'target': threshold.target_value,
                    'actual': current_value
                })
            )

    async def _alert_processing_loop(self):
        """Process and manage alerts"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Process every minute

                if not self.is_running:
                    break

                # Auto-resolve expired alerts
                await self._auto_resolve_alerts()

                # Process alert grouping
                await self._process_alert_grouping()

            except Exception as e:
                logger.error(f"Error in alert processing: {e}")

    async def _degradation_monitoring_loop(self):
        """Monitor for degradation triggers and recovery"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                if not self.is_running:
                    break

                await self._check_degradation_triggers()
                await self._check_degradation_recovery()

            except Exception as e:
                logger.error(f"Error in degradation monitoring: {e}")

    async def _check_degradation_triggers(self):
        """Check if degradation strategies should be triggered"""
        for strategy_name, strategy in self.degradation_strategies.items():
            if not strategy.enabled:
                continue

            # Check if already active
            if any(alert.source == f"degradation_{strategy_name}" for alert in self.active_alerts.values()):
                continue

            # Evaluate trigger conditions
            should_trigger = await self._evaluate_degradation_conditions(
                strategy.trigger_conditions
            )

            if should_trigger:
                await self._trigger_degradation_strategy(strategy_name, strategy)

    async def _check_degradation_recovery(self):
        """Check if degradation strategies can be recovered"""
        for strategy_name, strategy in self.degradation_strategies.items():
            # Check if strategy is currently active
            active_alert = None
            for alert in self.active_alerts.values():
                if alert.source == f"degradation_{strategy_name}":
                    active_alert = alert
                    break

            if not active_alert:
                continue

            # Check recovery conditions
            should_recover = await self._evaluate_degradation_conditions(
                strategy.recovery_conditions
            )

            if should_recover:
                await self._recover_degradation_strategy(strategy_name, strategy, active_alert.id)

    async def _trigger_degradation_strategy(self, strategy_name: str, strategy: DegradationStrategy):
        """Trigger a degradation strategy"""
        try:
            # Execute degradation actions
            for action in strategy.actions:
                await self._execute_degradation_action(action)

            # Create degradation alert
            await self.trigger_alert(
                severity=AlertSeverity.WARNING,
                category=AlertCategory.DEGRADATION,
                title=f"Degradation Strategy Activated: {strategy.name}",
                description=f"System degradation strategy '{strategy.name}' has been activated due to performance issues",
                source=f"degradation_{strategy_name}",
                metrics={
                    'strategy_name': strategy_name,
                    'actions_count': len(strategy.actions),
                    'max_duration_minutes': strategy.max_duration_minutes
                },
                recommended_action="Monitor system performance and wait for automatic recovery",
                auto_resolution=True
            )

            logger.warning(f"Degradation strategy activated: {strategy_name}")

        except Exception as e:
            logger.error(f"Failed to trigger degradation strategy {strategy_name}: {e}")

    async def _recover_degradation_strategy(self, strategy_name: str, strategy: DegradationStrategy, alert_id: str):
        """Recover from a degradation strategy"""
        try:
            # Execute recovery actions (reverse of degradation actions)
            await self._execute_recovery_actions(strategy.actions)

            # Resolve degradation alert
            await self.resolve_alert(alert_id, f"Degradation strategy {strategy_name} recovered")

            logger.info(f"Degradation strategy recovered: {strategy_name}")

        except Exception as e:
            logger.error(f"Failed to recover degradation strategy {strategy_name}: {e}")

    async def _execute_degradation_action(self, action: Dict[str, Any]):
        """Execute a degradation action"""
        action_type = action.get('type')
        params = action.get('params', {})

        logger.info(f"Executing degradation action: {action_type} with params: {params}")

        # These would integrate with the actual system components
        # For now, just log the actions that would be taken
        action_implementations = {
            'reduce_search_complexity': self._reduce_search_complexity,
            'disable_reranking': self._disable_reranking,
            'increase_caching': self._increase_caching,
            'switch_to_cheaper_model': self._switch_to_cheaper_model,
            'reduce_context_length': self._reduce_context_length,
            'enable_verification': self._enable_verification,
            'enable_circuit_breaker': self._enable_circuit_breaker,
            'fallback_to_cached_responses': self._fallback_to_cached_responses,
            'reduce_concurrent_requests': self._reduce_concurrent_requests
        }

        implementation = action_implementations.get(action_type)
        if implementation:
            await implementation(params)
        else:
            logger.warning(f"Unknown degradation action type: {action_type}")

    async def _execute_recovery_actions(self, actions: List[Dict[str, Any]]):
        """Execute recovery actions (reverse degradation actions)"""
        for action in actions:
            action_type = action.get('type')
            logger.info(f"Recovering from degradation action: {action_type}")
            # Implementation would restore original system settings

    # Degradation action implementations (would integrate with actual components)
    async def _reduce_search_complexity(self, params: Dict[str, Any]):
        """Reduce search complexity to improve performance"""
        max_results = params.get('max_results', 10)
        logger.info(f"Reducing search complexity: max_results={max_results}")

    async def _disable_reranking(self, params: Dict[str, Any]):
        """Disable expensive reranking to improve latency"""
        logger.info("Disabling search result reranking")

    async def _increase_caching(self, params: Dict[str, Any]):
        """Increase caching duration to reduce load"""
        cache_duration = params.get('cache_duration', 1800)
        logger.info(f"Increasing cache duration to {cache_duration} seconds")

    async def _switch_to_cheaper_model(self, params: Dict[str, Any]):
        """Switch to cheaper LLM model to reduce costs"""
        model = params.get('model', 'gpt-3.5-turbo')
        logger.info(f"Switching to cheaper model: {model}")

    async def _reduce_context_length(self, params: Dict[str, Any]):
        """Reduce context length to reduce costs"""
        max_tokens = params.get('max_tokens', 500)
        logger.info(f"Reducing context length to {max_tokens} tokens")

    async def _enable_verification(self, params: Dict[str, Any]):
        """Enable additional verification to improve quality"""
        verification_model = params.get('verification_model', 'gpt-4')
        logger.info(f"Enabling verification with model: {verification_model}")

    async def _enable_circuit_breaker(self, params: Dict[str, Any]):
        """Enable circuit breaker to prevent cascading failures"""
        failure_threshold = params.get('failure_threshold', 3)
        logger.info(f"Enabling circuit breaker with threshold: {failure_threshold}")

    async def _fallback_to_cached_responses(self, params: Dict[str, Any]):
        """Fallback to cached responses during high error rates"""
        logger.info("Enabling fallback to cached responses")

    async def _reduce_concurrent_requests(self, params: Dict[str, Any]):
        """Reduce concurrent requests to prevent overload"""
        max_concurrent = params.get('max_concurrent', 10)
        logger.info(f"Reducing concurrent requests to {max_concurrent}")

    async def _evaluate_degradation_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Evaluate degradation trigger/recovery conditions"""
        try:
            duration_minutes = conditions.get('duration_minutes', 1)
            cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)

            for metric_name, condition in conditions.items():
                if metric_name == 'duration_minutes':
                    continue

                # Get recent values
                recent_values = [
                    point['value'] for point in self.metrics_buffer[metric_name]
                    if point['timestamp'] >= cutoff_time
                ]

                if not recent_values:
                    return False

                current_value = sum(recent_values) / len(recent_values)
                operator = condition.get('operator', '>')
                threshold = condition.get('value', 0)

                condition_met = False
                if operator == '>':
                    condition_met = current_value > threshold
                elif operator == '<':
                    condition_met = current_value < threshold
                elif operator == '>=':
                    condition_met = current_value >= threshold
                elif operator == '<=':
                    condition_met = current_value <= threshold

                if not condition_met:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error evaluating degradation conditions: {e}")
            return False

    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification to external systems"""
        if not self.webhook_url:
            return

        try:
            payload = {
                'alert_id': alert.id,
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity.value,
                'category': alert.category.value,
                'title': alert.title,
                'description': alert.description,
                'source': alert.source,
                'metrics': alert.metrics,
                'recommended_action': alert.recommended_action
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Alert notification sent: {alert.id}")
                    else:
                        logger.error(f"Failed to send alert notification: {response.status}")

        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")

    async def _notify_alert_callbacks(self, alert: Alert):
        """Notify registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed based on rules"""
        # Simple suppression: don't repeat same alert within 5 minutes
        suppression_key = f"{alert.category.value}_{alert.title}"
        now = datetime.utcnow()

        if suppression_key in self.suppression_rules:
            last_alert_time = self.suppression_rules[suppression_key]
            if (now - last_alert_time).total_seconds() < 300:  # 5 minutes
                return True

        self.suppression_rules[suppression_key] = now
        return False

    async def _auto_resolve_alerts(self):
        """Auto-resolve alerts that should be resolved"""
        current_time = datetime.utcnow()

        alerts_to_resolve = []
        for alert_id, alert in self.active_alerts.items():
            # Auto-resolve degradation alerts after max duration
            if (alert.category == AlertCategory.DEGRADATION and
                (current_time - alert.timestamp).total_seconds() > 3600):  # 1 hour max
                alerts_to_resolve.append(alert_id)

        for alert_id in alerts_to_resolve:
            await self.resolve_alert(alert_id, "Auto-resolved after maximum duration")

    async def _process_alert_grouping(self):
        """Group related alerts to reduce noise"""
        # Implementation would group alerts by category/source
        pass

    def _get_slo_recommendation(self, slo_name: str, violation: Dict[str, Any]) -> str:
        """Get recommendation for SLO violation"""
        recommendations = {
            'p95_latency_seconds': "Consider reducing search complexity, enabling caching, or scaling compute resources",
            'cost_per_query_won': "Switch to more efficient models, implement better caching, or optimize prompt length",
            'faithfulness_threshold': "Review classification rules, retrain models, or implement additional verification",
            'availability_percent': "Check system health, investigate error rates, and ensure redundancy",
            'error_rate_percent': "Investigate recent changes, check dependencies, and review error logs"
        }
        return recommendations.get(slo_name, "Review system metrics and investigate root cause")

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]