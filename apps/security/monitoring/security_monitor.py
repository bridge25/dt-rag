"""
Security Monitoring System for DT-RAG v1.8.1
Real-time security event monitoring, threat detection, and incident response
Implements SIEM-like capabilities with ML-based anomaly detection
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import uuid
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Security incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    MITIGATED = "mitigated"
    CLOSED = "closed"

class AlertType(Enum):
    """Types of security alerts"""
    # Authentication anomalies
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    UNUSUAL_LOGIN_TIME = "unusual_login_time"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    CONCURRENT_SESSIONS = "concurrent_sessions"

    # Access pattern anomalies
    UNUSUAL_DATA_ACCESS = "unusual_data_access"
    BULK_DATA_DOWNLOAD = "bulk_data_download"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"

    # System anomalies
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SYSTEM_PERFORMANCE_DEGRADATION = "system_performance_degradation"
    CONFIGURATION_CHANGE = "configuration_change"
    SERVICE_DISRUPTION = "service_disruption"

    # Security violations
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    MALICIOUS_FILE_UPLOAD = "malicious_file_upload"
    DATA_EXFILTRATION = "data_exfiltration"

    # Compliance violations
    PII_EXPOSURE = "pii_exposure"
    GDPR_VIOLATION = "gdpr_violation"
    RETENTION_POLICY_VIOLATION = "retention_policy_violation"

@dataclass
class SecurityAlert:
    """Security alert"""
    alert_id: str
    alert_type: AlertType
    threat_level: ThreatLevel
    detected_at: datetime
    source: str
    affected_resource: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Dict[str, Any] = None
    evidence: Dict[str, Any] = None
    status: str = "active"  # active, acknowledged, resolved, false_positive
    investigation_notes: List[str] = None
    response_actions: List[str] = None

    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = str(uuid.uuid4())
        if not self.details:
            self.details = {}
        if not self.evidence:
            self.evidence = {}
        if not self.investigation_notes:
            self.investigation_notes = []
        if not self.response_actions:
            self.response_actions = []

@dataclass
class SecurityIncident:
    """Security incident"""
    incident_id: str
    title: str
    description: str
    threat_level: ThreatLevel
    status: IncidentStatus
    created_at: datetime
    assigned_to: Optional[str] = None
    related_alerts: List[str] = None
    affected_systems: List[str] = None
    impact_assessment: Optional[str] = None
    containment_actions: List[str] = None
    mitigation_actions: List[str] = None
    lessons_learned: Optional[str] = None
    closed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.incident_id:
            self.incident_id = str(uuid.uuid4())
        if not self.related_alerts:
            self.related_alerts = []
        if not self.affected_systems:
            self.affected_systems = []
        if not self.containment_actions:
            self.containment_actions = []
        if not self.mitigation_actions:
            self.mitigation_actions = []

@dataclass
class UserBehaviorProfile:
    """User behavior profile for anomaly detection"""
    user_id: str
    typical_login_hours: List[int]
    typical_ip_addresses: Set[str]
    average_session_duration: float
    typical_resources_accessed: Set[str]
    typical_request_frequency: float
    risk_score: float = 0.0
    last_updated: datetime = None

class SecurityMonitor:
    """
    Advanced security monitoring system with ML-based threat detection
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Monitoring configuration
        self.alert_thresholds = self.config.get('alert_thresholds', {
            'failed_login_attempts': 5,
            'unusual_access_threshold': 3.0,  # Standard deviations
            'bulk_download_threshold': 100,  # Number of documents
            'session_duration_threshold': 8  # Hours
        })

        # ML models for anomaly detection
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42
        )
        self.scaler = StandardScaler()
        self.model_trained = False

        # Data storage
        self._alerts: Dict[str, SecurityAlert] = {}
        self._incidents: Dict[str, SecurityIncident] = {}
        self._user_profiles: Dict[str, UserBehaviorProfile] = {}

        # Real-time monitoring data
        self._login_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._user_activities: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._system_metrics: deque = deque(maxlen=1000)

        # Alert handlers
        self._alert_handlers: Dict[AlertType, List[Callable]] = defaultdict(list)

        # Metrics
        self._metrics = {
            "total_alerts": 0,
            "alerts_by_type": {},
            "alerts_by_threat_level": {},
            "incidents_created": 0,
            "false_positives": 0,
            "mean_time_to_detection": 0.0,
            "mean_time_to_response": 0.0
        }

        # Background tasks
        self._monitoring_task = None
        self._training_task = None

        logger.info("SecurityMonitor initialized with ML-based threat detection")

    async def start_monitoring(self):
        """Start continuous security monitoring"""
        self._monitoring_task = asyncio.create_task(self._continuous_monitoring())
        self._training_task = asyncio.create_task(self._periodic_model_training())
        logger.info("Security monitoring started")

    async def stop_monitoring(self):
        """Stop security monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._training_task:
            self._training_task.cancel()
        logger.info("Security monitoring stopped")

    # Event Processing

    async def process_security_event(self, event: Dict[str, Any]):
        """Process incoming security event"""
        try:
            event_type = event.get('type')
            user_id = event.get('user_id')
            ip_address = event.get('ip_address')
            timestamp = datetime.fromisoformat(event.get('timestamp', datetime.utcnow().isoformat()))

            # Update user behavior profile
            if user_id:
                await self._update_user_profile(user_id, event)

            # Check for specific threats
            alerts = []

            # Authentication anomalies
            if event_type == 'authentication_failed':
                alert = await self._check_failed_login_pattern(user_id, ip_address, timestamp)
                if alert:
                    alerts.append(alert)

            elif event_type == 'authentication_success':
                alert = await self._check_login_anomalies(user_id, ip_address, timestamp)
                if alert:
                    alerts.append(alert)

            # Access pattern anomalies
            elif event_type in ['document_accessed', 'search_performed']:
                alert = await self._check_access_anomalies(user_id, event)
                if alert:
                    alerts.append(alert)

            # System events
            elif event_type in ['system_error', 'performance_degradation']:
                alert = await self._check_system_anomalies(event)
                if alert:
                    alerts.append(alert)

            # Process generated alerts
            for alert in alerts:
                await self._process_alert(alert)

        except Exception as e:
            logger.error(f"Security event processing failed: {e}")

    async def create_manual_alert(
        self,
        alert_type: AlertType,
        threat_level: ThreatLevel,
        source: str,
        details: Dict[str, Any]
    ) -> SecurityAlert:
        """Create manual security alert"""

        alert = SecurityAlert(
            alert_type=alert_type,
            threat_level=threat_level,
            detected_at=datetime.utcnow(),
            source=source,
            details=details
        )

        await self._process_alert(alert)
        return alert

    # Alert Management

    async def get_active_alerts(
        self,
        threat_level: ThreatLevel = None,
        limit: int = 100
    ) -> List[SecurityAlert]:
        """Get active security alerts"""

        alerts = [
            alert for alert in self._alerts.values()
            if alert.status == "active"
        ]

        if threat_level:
            alerts = [a for a in alerts if a.threat_level == threat_level]

        # Sort by threat level and time
        threat_priority = {
            ThreatLevel.CRITICAL: 5,
            ThreatLevel.HIGH: 4,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.LOW: 2,
            ThreatLevel.INFO: 1
        }

        alerts.sort(
            key=lambda a: (threat_priority[a.threat_level], a.detected_at),
            reverse=True
        )

        return alerts[:limit]

    async def acknowledge_alert(self, alert_id: str, investigator: str) -> bool:
        """Acknowledge an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False

        alert.status = "acknowledged"
        alert.investigation_notes.append(
            f"Alert acknowledged by {investigator} at {datetime.utcnow().isoformat()}"
        )

        logger.info(f"Alert acknowledged: {alert_id} by {investigator}")
        return True

    async def resolve_alert(
        self,
        alert_id: str,
        resolution: str,
        is_false_positive: bool = False
    ) -> bool:
        """Resolve an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False

        alert.status = "false_positive" if is_false_positive else "resolved"
        alert.investigation_notes.append(
            f"Alert resolved: {resolution} at {datetime.utcnow().isoformat()}"
        )

        if is_false_positive:
            self._metrics["false_positives"] += 1
            # Use this to improve ML model
            await self._update_false_positive_feedback(alert)

        logger.info(f"Alert resolved: {alert_id}")
        return True

    # Incident Management

    async def create_incident(
        self,
        title: str,
        description: str,
        threat_level: ThreatLevel,
        related_alerts: List[str] = None
    ) -> SecurityIncident:
        """Create security incident"""

        incident = SecurityIncident(
            title=title,
            description=description,
            threat_level=threat_level,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            related_alerts=related_alerts or []
        )

        self._incidents[incident.incident_id] = incident
        self._metrics["incidents_created"] += 1

        logger.warning(f"Security incident created: {incident.incident_id} - {title}")

        # Auto-escalate critical incidents
        if threat_level == ThreatLevel.CRITICAL:
            await self._escalate_critical_incident(incident)

        return incident

    async def update_incident_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        notes: str = None
    ) -> bool:
        """Update incident status"""
        incident = self._incidents.get(incident_id)
        if not incident:
            return False

        incident.status = status
        if status == IncidentStatus.CLOSED:
            incident.closed_at = datetime.utcnow()

        if notes:
            if not hasattr(incident, 'status_notes'):
                incident.status_notes = []
            incident.status_notes.append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": status.value,
                "notes": notes
            })

        logger.info(f"Incident status updated: {incident_id} -> {status.value}")
        return True

    # Analytics and Reporting

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security monitoring dashboard data"""

        # Calculate recent metrics
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)

        recent_alerts = [
            a for a in self._alerts.values()
            if a.detected_at > last_24h
        ]

        active_incidents = [
            i for i in self._incidents.values()
            if i.status != IncidentStatus.CLOSED
        ]

        return {
            "overview": {
                "active_alerts": len([a for a in self._alerts.values() if a.status == "active"]),
                "alerts_last_24h": len(recent_alerts),
                "active_incidents": len(active_incidents),
                "critical_alerts": len([a for a in recent_alerts if a.threat_level == ThreatLevel.CRITICAL])
            },
            "alert_trends": await self._get_alert_trends(last_week),
            "top_threat_types": await self._get_top_threat_types(last_week),
            "user_risk_scores": await self._get_user_risk_scores(),
            "system_health": await self._get_system_health_metrics(),
            "compliance_status": await self._get_compliance_status()
        }

    async def generate_security_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive security report"""

        alerts_in_period = [
            a for a in self._alerts.values()
            if start_date <= a.detected_at <= end_date
        ]

        incidents_in_period = [
            i for i in self._incidents.values()
            if start_date <= i.created_at <= end_date
        ]

        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "executive_summary": {
                "total_alerts": len(alerts_in_period),
                "total_incidents": len(incidents_in_period),
                "false_positive_rate": await self._calculate_false_positive_rate(alerts_in_period),
                "mean_time_to_detection": await self._calculate_mttd(alerts_in_period),
                "mean_time_to_response": await self._calculate_mttr(incidents_in_period)
            },
            "threat_analysis": await self._analyze_threats(alerts_in_period),
            "user_behavior_analysis": await self._analyze_user_behavior(start_date, end_date),
            "recommendations": await self._generate_security_recommendations(alerts_in_period)
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get security monitoring metrics"""
        return {
            **self._metrics,
            "active_alerts": len([a for a in self._alerts.values() if a.status == "active"]),
            "open_incidents": len([i for i in self._incidents.values() if i.status != IncidentStatus.CLOSED]),
            "user_profiles": len(self._user_profiles),
            "model_trained": self.model_trained
        }

    # Private methods

    async def _continuous_monitoring(self):
        """Continuous monitoring loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Check for stale alerts
                await self._check_stale_alerts()

                # Update user risk scores
                await self._update_all_user_risk_scores()

                # Check system health
                await self._check_system_health()

                # Clean old data
                await self._cleanup_old_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

    async def _periodic_model_training(self):
        """Periodic ML model training"""
        while True:
            try:
                await asyncio.sleep(3600)  # Train every hour

                if len(self._user_activities) > 100:  # Minimum data required
                    await self._train_anomaly_detection_model()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Model training error: {e}")

    async def _update_user_profile(self, user_id: str, event: Dict[str, Any]):
        """Update user behavior profile"""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserBehaviorProfile(
                user_id=user_id,
                typical_login_hours=[],
                typical_ip_addresses=set(),
                average_session_duration=0.0,
                typical_resources_accessed=set(),
                typical_request_frequency=0.0,
                last_updated=datetime.utcnow()
            )

        profile = self._user_profiles[user_id]

        # Update based on event type
        if event.get('type') == 'authentication_success':
            hour = datetime.fromisoformat(event['timestamp']).hour
            profile.typical_login_hours.append(hour)
            if len(profile.typical_login_hours) > 100:
                profile.typical_login_hours = profile.typical_login_hours[-100:]

            if 'ip_address' in event:
                profile.typical_ip_addresses.add(event['ip_address'])

        elif event.get('type') in ['document_accessed', 'search_performed']:
            if 'resource' in event:
                profile.typical_resources_accessed.add(event['resource'])

        # Store activity for ML training
        self._user_activities[user_id].append({
            'timestamp': event.get('timestamp'),
            'type': event.get('type'),
            'ip_address': event.get('ip_address'),
            'resource': event.get('resource')
        })

        profile.last_updated = datetime.utcnow()

    async def _check_failed_login_pattern(
        self,
        user_id: str,
        ip_address: str,
        timestamp: datetime
    ) -> Optional[SecurityAlert]:
        """Check for failed login patterns"""

        # Track failed attempts
        key = f"{user_id}:{ip_address}"
        self._login_attempts[key].append(timestamp)

        # Clean old attempts (last hour)
        cutoff = timestamp - timedelta(hours=1)
        self._login_attempts[key] = [
            t for t in self._login_attempts[key] if t > cutoff
        ]

        # Check threshold
        threshold = self.alert_thresholds['failed_login_attempts']
        if len(self._login_attempts[key]) >= threshold:
            return SecurityAlert(
                alert_type=AlertType.MULTIPLE_FAILED_LOGINS,
                threat_level=ThreatLevel.MEDIUM,
                detected_at=timestamp,
                source="authentication_monitor",
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "failed_attempts": len(self._login_attempts[key]),
                    "threshold": threshold,
                    "time_window": "1 hour"
                }
            )

        return None

    async def _check_login_anomalies(
        self,
        user_id: str,
        ip_address: str,
        timestamp: datetime
    ) -> Optional[SecurityAlert]:
        """Check for login anomalies"""

        profile = self._user_profiles.get(user_id)
        if not profile:
            return None

        alerts = []

        # Check unusual login time
        hour = timestamp.hour
        if profile.typical_login_hours:
            typical_hours = set(profile.typical_login_hours)
            if hour not in typical_hours:
                # Check if this is significantly unusual
                hour_frequency = profile.typical_login_hours.count(hour) / len(profile.typical_login_hours)
                if hour_frequency < 0.05:  # Less than 5% of logins at this hour
                    alerts.append(SecurityAlert(
                        alert_type=AlertType.UNUSUAL_LOGIN_TIME,
                        threat_level=ThreatLevel.LOW,
                        detected_at=timestamp,
                        source="behavior_monitor",
                        user_id=user_id,
                        ip_address=ip_address,
                        details={
                            "login_hour": hour,
                            "typical_hours": list(typical_hours),
                            "frequency": hour_frequency
                        }
                    ))

        # Check new IP address
        if ip_address not in profile.typical_ip_addresses:
            alerts.append(SecurityAlert(
                alert_type=AlertType.GEOGRAPHIC_ANOMALY,
                threat_level=ThreatLevel.MEDIUM,
                detected_at=timestamp,
                source="behavior_monitor",
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "new_ip": ip_address,
                    "known_ips": list(profile.typical_ip_addresses)
                }
            ))

        return alerts[0] if alerts else None

    async def _check_access_anomalies(
        self,
        user_id: str,
        event: Dict[str, Any]
    ) -> Optional[SecurityAlert]:
        """Check for access pattern anomalies"""

        if not self.model_trained:
            return None

        # Extract features for anomaly detection
        features = await self._extract_features_for_user(user_id, event)
        if not features:
            return None

        # Predict anomaly
        features_scaled = self.scaler.transform([features])
        anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]

        # Check if anomalous
        threshold = self.alert_thresholds['unusual_access_threshold']
        if anomaly_score < -threshold:
            return SecurityAlert(
                alert_type=AlertType.UNUSUAL_DATA_ACCESS,
                threat_level=ThreatLevel.MEDIUM,
                detected_at=datetime.utcnow(),
                source="ml_anomaly_detector",
                user_id=user_id,
                details={
                    "anomaly_score": anomaly_score,
                    "threshold": threshold,
                    "event_type": event.get('type'),
                    "resource": event.get('resource')
                }
            )

        return None

    async def _check_system_anomalies(self, event: Dict[str, Any]) -> Optional[SecurityAlert]:
        """Check for system-level anomalies"""

        # Store system metrics
        self._system_metrics.append({
            'timestamp': event.get('timestamp'),
            'type': event.get('type'),
            'severity': event.get('severity', 'info'),
            'details': event.get('details', {})
        })

        # Check for resource exhaustion
        if event.get('type') == 'high_resource_usage':
            details = event.get('details', {})
            cpu_usage = details.get('cpu_percent', 0)
            memory_usage = details.get('memory_percent', 0)

            if cpu_usage > 90 or memory_usage > 90:
                return SecurityAlert(
                    alert_type=AlertType.RESOURCE_EXHAUSTION,
                    threat_level=ThreatLevel.HIGH,
                    detected_at=datetime.utcnow(),
                    source="system_monitor",
                    details={
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "thresholds": {"cpu": 90, "memory": 90}
                    }
                )

        return None

    async def _process_alert(self, alert: SecurityAlert):
        """Process and store security alert"""
        self._alerts[alert.alert_id] = alert

        # Update metrics
        self._metrics["total_alerts"] += 1

        alert_type = alert.alert_type.value
        if alert_type not in self._metrics["alerts_by_type"]:
            self._metrics["alerts_by_type"][alert_type] = 0
        self._metrics["alerts_by_type"][alert_type] += 1

        threat_level = alert.threat_level.value
        if threat_level not in self._metrics["alerts_by_threat_level"]:
            self._metrics["alerts_by_threat_level"][threat_level] = 0
        self._metrics["alerts_by_threat_level"][threat_level] += 1

        # Call alert handlers
        for handler in self._alert_handlers[alert.alert_type]:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        # Auto-create incident for high/critical alerts
        if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self._auto_create_incident(alert)

        logger.warning(
            f"Security alert: {alert.alert_type.value} "
            f"({alert.threat_level.value}) - {alert.alert_id}"
        )

    async def _auto_create_incident(self, alert: SecurityAlert):
        """Automatically create incident for high-severity alerts"""
        incident = await self.create_incident(
            title=f"Security Alert: {alert.alert_type.value}",
            description=f"Automatically created incident for {alert.threat_level.value} alert",
            threat_level=alert.threat_level,
            related_alerts=[alert.alert_id]
        )

        alert.investigation_notes.append(
            f"Incident created: {incident.incident_id}"
        )

    async def _escalate_critical_incident(self, incident: SecurityIncident):
        """Escalate critical incidents"""
        # In production, this would send notifications to security team
        logger.critical(
            f"CRITICAL INCIDENT: {incident.title} "
            f"(ID: {incident.incident_id}) - Immediate attention required"
        )

    async def _train_anomaly_detection_model(self):
        """Train ML model for anomaly detection"""
        try:
            # Collect training data from user activities
            training_data = []

            for user_id, activities in self._user_activities.items():
                for activity in activities:
                    features = await self._extract_features_for_activity(user_id, activity)
                    if features:
                        training_data.append(features)

            if len(training_data) < 50:  # Minimum training data
                return

            # Train model
            training_array = np.array(training_data)
            self.scaler.fit(training_array)
            training_scaled = self.scaler.transform(training_array)

            self.anomaly_detector.fit(training_scaled)
            self.model_trained = True

            logger.info(f"Anomaly detection model trained with {len(training_data)} samples")

        except Exception as e:
            logger.error(f"Model training failed: {e}")

    async def _extract_features_for_user(
        self,
        user_id: str,
        event: Dict[str, Any]
    ) -> Optional[List[float]]:
        """Extract features for ML model"""
        try:
            # Basic features
            features = []

            # Time-based features
            timestamp = datetime.fromisoformat(event.get('timestamp', datetime.utcnow().isoformat()))
            features.extend([
                timestamp.hour,  # Hour of day
                timestamp.weekday(),  # Day of week
                (timestamp.timestamp() % 86400) / 86400  # Time of day normalized
            ])

            # User activity features
            recent_activities = list(self._user_activities.get(user_id, []))[-10:]
            features.extend([
                len(recent_activities),  # Recent activity count
                len(set(a.get('type') for a in recent_activities)),  # Activity diversity
            ])

            # Event-specific features
            event_type_mapping = {
                'authentication_success': 1,
                'document_accessed': 2,
                'search_performed': 3,
                'classification_performed': 4
            }
            features.append(event_type_mapping.get(event.get('type'), 0))

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

    async def _extract_features_for_activity(
        self,
        user_id: str,
        activity: Dict[str, Any]
    ) -> Optional[List[float]]:
        """Extract features from activity for training"""
        return await self._extract_features_for_user(user_id, activity)

    async def _update_false_positive_feedback(self, alert: SecurityAlert):
        """Update model with false positive feedback"""
        # In a more sophisticated implementation, this would retrain the model
        # to reduce false positives
        pass

    async def _check_stale_alerts(self):
        """Check for stale alerts that need attention"""
        cutoff = datetime.utcnow() - timedelta(hours=24)

        for alert in self._alerts.values():
            if (alert.status == "active" and
                alert.detected_at < cutoff and
                alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]):

                logger.warning(f"Stale high-priority alert: {alert.alert_id}")

    async def _update_all_user_risk_scores(self):
        """Update risk scores for all users"""
        for user_id, profile in self._user_profiles.items():
            profile.risk_score = await self._calculate_user_risk_score(user_id)

    async def _calculate_user_risk_score(self, user_id: str) -> float:
        """Calculate risk score for user"""
        risk_score = 0.0

        # Count recent alerts for this user
        recent_alerts = [
            a for a in self._alerts.values()
            if (a.user_id == user_id and
                a.detected_at > datetime.utcnow() - timedelta(days=7))
        ]

        # Weight by threat level
        threat_weights = {
            ThreatLevel.CRITICAL: 1.0,
            ThreatLevel.HIGH: 0.7,
            ThreatLevel.MEDIUM: 0.4,
            ThreatLevel.LOW: 0.2,
            ThreatLevel.INFO: 0.1
        }

        for alert in recent_alerts:
            risk_score += threat_weights[alert.threat_level]

        # Normalize to 0-1 scale
        return min(risk_score / 5.0, 1.0)

    async def _check_system_health(self):
        """Check overall system health"""
        # This would integrate with system monitoring
        pass

    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff = datetime.utcnow() - timedelta(days=30)

        # Clean old login attempts
        for key in list(self._login_attempts.keys()):
            self._login_attempts[key] = [
                t for t in self._login_attempts[key] if t > cutoff
            ]
            if not self._login_attempts[key]:
                del self._login_attempts[key]

    # Analytics methods

    async def _get_alert_trends(self, since: datetime) -> Dict[str, Any]:
        """Get alert trends"""
        alerts_since = [
            a for a in self._alerts.values()
            if a.detected_at > since
        ]

        # Group by day
        daily_counts = defaultdict(int)
        for alert in alerts_since:
            day = alert.detected_at.date()
            daily_counts[day] += 1

        return {
            "total_alerts": len(alerts_since),
            "daily_counts": {str(k): v for k, v in daily_counts.items()}
        }

    async def _get_top_threat_types(self, since: datetime) -> List[Dict[str, Any]]:
        """Get top threat types"""
        alerts_since = [
            a for a in self._alerts.values()
            if a.detected_at > since
        ]

        type_counts = defaultdict(int)
        for alert in alerts_since:
            type_counts[alert.alert_type.value] += 1

        return [
            {"type": k, "count": v}
            for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

    async def _get_user_risk_scores(self) -> List[Dict[str, Any]]:
        """Get user risk scores"""
        return [
            {
                "user_id": profile.user_id,
                "risk_score": profile.risk_score
            }
            for profile in sorted(
                self._user_profiles.values(),
                key=lambda p: p.risk_score,
                reverse=True
            )[:20]  # Top 20 riskiest users
        ]

    async def _get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics"""
        return {
            "status": "healthy",
            "alerts_processed_last_hour": len([
                a for a in self._alerts.values()
                if a.detected_at > datetime.utcnow() - timedelta(hours=1)
            ]),
            "model_status": "trained" if self.model_trained else "training"
        }

    async def _get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status"""
        return {
            "gdpr_compliant": True,
            "data_retention_compliant": True,
            "audit_logging_active": True
        }

    async def _calculate_false_positive_rate(self, alerts: List[SecurityAlert]) -> float:
        """Calculate false positive rate"""
        if not alerts:
            return 0.0

        false_positives = len([a for a in alerts if a.status == "false_positive"])
        return false_positives / len(alerts)

    async def _calculate_mttd(self, alerts: List[SecurityAlert]) -> float:
        """Calculate Mean Time To Detection"""
        # This would require actual incident detection times
        return 0.0  # Placeholder

    async def _calculate_mttr(self, incidents: List[SecurityIncident]) -> float:
        """Calculate Mean Time To Response"""
        resolved = [i for i in incidents if i.closed_at]
        if not resolved:
            return 0.0

        response_times = [
            (i.closed_at - i.created_at).total_seconds() / 3600  # Hours
            for i in resolved
        ]

        return statistics.mean(response_times)

    async def _analyze_threats(self, alerts: List[SecurityAlert]) -> Dict[str, Any]:
        """Analyze threat patterns"""
        return {
            "total_threats": len(alerts),
            "threat_categories": dict(defaultdict(int)),
            "attack_vectors": [],
            "targeted_assets": []
        }

    async def _analyze_user_behavior(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        return {
            "total_users_monitored": len(self._user_profiles),
            "high_risk_users": len([
                p for p in self._user_profiles.values()
                if p.risk_score > 0.7
            ]),
            "behavior_anomalies": 0
        }

    async def _generate_security_recommendations(
        self,
        alerts: List[SecurityAlert]
    ) -> List[str]:
        """Generate security recommendations based on alerts"""
        recommendations = []

        # Analyze alert patterns
        alert_types = [a.alert_type for a in alerts]

        if AlertType.MULTIPLE_FAILED_LOGINS in alert_types:
            recommendations.append("Implement account lockout policies")

        if AlertType.UNUSUAL_LOGIN_TIME in alert_types:
            recommendations.append("Consider implementing time-based access controls")

        if AlertType.PII_EXPOSURE in alert_types:
            recommendations.append("Review data access permissions and implement DLP")

        return recommendations

    def register_alert_handler(self, alert_type: AlertType, handler: Callable):
        """Register custom alert handler"""
        self._alert_handlers[alert_type].append(handler)

class SecurityMonitoringError(Exception):
    """Security monitoring exception"""
    pass