# @CODE:MYPY-001:PHASE2:BATCH2 | SPEC: .moai/specs/SPEC-MYPY-001/spec.md
"""
Core Security Manager for DT-RAG v1.8.1
Orchestrates all security components and provides unified security interface
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    from ..audit.audit_logger import AuditLogger, EventType, SecurityEvent, SeverityLevel
    from ..auth.auth_service import AuthService, RBACManager
    from ..compliance.compliance_manager import ComplianceManager
    from ..compliance.pii_detector import PIIDetector
    from ..monitoring.security_monitor import SecurityMonitor
    from ..scanning.vulnerability_scanner import VulnerabilityScanner
else:
    from ..audit.audit_logger import AuditLogger, EventType, SecurityEvent, SeverityLevel
    from ..auth.auth_service import AuthService, RBACManager
    from ..compliance.compliance_manager import ComplianceManager
    from ..compliance.pii_detector import PIIDetector
    from ..monitoring.security_monitor import SecurityMonitor
    from ..scanning.vulnerability_scanner import VulnerabilityScanner

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security clearance levels"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


@dataclass
class SecurityContext:
    """Security context for requests"""

    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    permissions: Set[str]
    clearance_level: SecurityLevel
    request_id: str
    timestamp: datetime
    is_authenticated: bool = False
    risk_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    require_authentication: bool = True
    require_authorization: bool = True
    enable_audit_logging: bool = True
    enable_pii_detection: bool = True
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    session_timeout_minutes: int = 30
    require_encryption: bool = True
    allow_anonymous_read: bool = False
    sensitive_operations: List[str] = field(default_factory=list)


class SecurityManager:
    """
    Central security manager that orchestrates all security components
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.policy = SecurityPolicy(**self.config.get("policy", {}))

        # Initialize security components
        self.auth_service = AuthService(self.config.get("auth", {}))
        self.rbac_manager = RBACManager(self.config.get("rbac", {}))
        self.audit_logger = AuditLogger(self.config.get("audit", {}))
        self.pii_detector = PIIDetector(self.config.get("pii", {}))
        self.compliance_manager = ComplianceManager(self.config.get("compliance", {}))
        self.security_monitor = SecurityMonitor(self.config.get("monitoring", {}))
        self.vulnerability_scanner = VulnerabilityScanner(
            self.config.get("scanning", {})
        )

        # Security state
        self._active_sessions: Dict[str, SecurityContext] = {}
        self._rate_limit_cache: Dict[str, List[datetime]] = {}
        self._security_incidents: List[Dict[str, Any]] = []

        logger.info("SecurityManager initialized with OWASP Top 10 compliance")

    async def authenticate_request(
        self, token: str, ip_address: str, user_agent: str, operation: Optional[str] = None
    ) -> SecurityContext:
        """
        Authenticate and authorize a request
        Implements OWASP A02:2021 – Cryptographic Failures & A07:2021 – Identification and Authentication Failures
        """
        request_id = str(uuid.uuid4())

        try:
            # 1. Validate token format and integrity
            if not token or len(token) < 32:
                await self._log_security_event(
                    EventType.AUTHENTICATION_FAILED,
                    {"reason": "invalid_token_format", "ip": ip_address},
                    SeverityLevel.MEDIUM,
                    request_id,
                )
                raise SecurityException("Invalid token format")

            # 2. Authenticate user
            user_info = await self.auth_service.validate_token(token)
            if not user_info:
                await self._log_security_event(
                    EventType.AUTHENTICATION_FAILED,
                    {"reason": "token_validation_failed", "ip": ip_address},
                    SeverityLevel.HIGH,
                    request_id,
                )
                raise SecurityException("Authentication failed")

            # 3. Check session validity
            session_id = user_info.get("session_id")
            if session_id in self._active_sessions:
                existing_context = self._active_sessions[session_id]
                if self._is_session_expired(existing_context):
                    await self._invalidate_session(session_id)
                    raise SecurityException("Session expired")

            # 4. Rate limiting check
            if self.policy.enable_rate_limiting:
                if not await self._check_rate_limit(ip_address):
                    await self._log_security_event(
                        EventType.RATE_LIMIT_EXCEEDED,
                        {"ip": ip_address, "user_id": user_info.get("user_id")},
                        SeverityLevel.MEDIUM,
                        request_id,
                    )
                    raise SecurityException("Rate limit exceeded")

            # 5. Risk assessment
            risk_score = await self._calculate_risk_score(
                user_info, ip_address, user_agent
            )

            # 6. Get user permissions
            permissions_enum = await self.rbac_manager.get_user_permissions(
                user_info["user_id"]
            )
            clearance_level_str = await self.rbac_manager.get_user_clearance(
                user_info["user_id"]
            )

            # Convert permissions enum to strings
            permissions_str = {p.value if hasattr(p, 'value') else str(p) for p in permissions_enum}

            # Convert clearance level string to SecurityLevel enum
            clearance_level = SecurityLevel(clearance_level_str) if isinstance(clearance_level_str, str) else clearance_level_str

            # 7. Create security context
            context = SecurityContext(
                user_id=user_info["user_id"],
                session_id=str(session_id) if session_id else "",
                ip_address=ip_address,
                user_agent=user_agent,
                permissions=permissions_str,
                clearance_level=clearance_level,
                request_id=request_id,
                timestamp=datetime.utcnow(),
                is_authenticated=True,
                risk_score=risk_score,
                metadata=user_info.get("metadata", {}),
            )

            # 8. Store active session
            if session_id:
                self._active_sessions[str(session_id)] = context

            # 9. Log successful authentication
            await self._log_security_event(
                EventType.AUTHENTICATION_SUCCESS,
                {
                    "user_id": user_info["user_id"],
                    "ip": ip_address,
                    "risk_score": risk_score,
                    "operation": operation,
                },
                SeverityLevel.INFO,
                request_id,
            )

            return context

        except SecurityException:
            raise
        except Exception as e:
            await self._log_security_event(
                EventType.AUTHENTICATION_ERROR,
                {"error": str(e), "ip": ip_address},
                SeverityLevel.HIGH,
                request_id,
            )
            raise SecurityException(f"Authentication error: {str(e)}")

    async def authorize_operation(
        self,
        context: SecurityContext,
        operation: str,
        resource: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Authorize an operation based on RBAC
        Implements OWASP A01:2021 – Broken Access Control
        """
        try:
            # 1. Check if user is authenticated
            if not context.is_authenticated:
                await self._log_security_event(
                    EventType.AUTHORIZATION_FAILED,
                    {"reason": "not_authenticated", "operation": operation},
                    SeverityLevel.HIGH,
                    context.request_id,
                )
                return False

            # 2. Check operation permissions
            if not await self.rbac_manager.check_permission(
                context.user_id, operation, resource or "", context
            ):
                await self._log_security_event(
                    EventType.AUTHORIZATION_FAILED,
                    {
                        "user_id": context.user_id,
                        "operation": operation,
                        "resource": resource,
                        "reason": "insufficient_permissions",
                    },
                    SeverityLevel.MEDIUM,
                    context.request_id,
                )
                return False

            # 3. Check resource access level if specified
            if resource:
                resource_level = await self._get_resource_security_level(resource)
                if not await self._check_clearance_access(
                    context.clearance_level, resource_level
                ):
                    await self._log_security_event(
                        EventType.AUTHORIZATION_FAILED,
                        {
                            "user_id": context.user_id,
                            "operation": operation,
                            "resource": resource,
                            "reason": "insufficient_clearance",
                            "required_level": resource_level.value,
                            "user_level": context.clearance_level.value,
                        },
                        SeverityLevel.HIGH,
                        context.request_id,
                    )
                    return False

            # 4. Risk-based authorization
            if context.risk_score > 0.8:  # High risk
                if operation in self.policy.sensitive_operations:
                    await self._log_security_event(
                        EventType.HIGH_RISK_OPERATION_BLOCKED,
                        {
                            "user_id": context.user_id,
                            "operation": operation,
                            "risk_score": context.risk_score,
                        },
                        SeverityLevel.HIGH,
                        context.request_id,
                    )
                    return False

            # 5. PII access check if data contains PII
            if data and self.policy.enable_pii_detection:
                pii_findings = await self.pii_detector.scan_data(data)
                if pii_findings:
                    if not await self.rbac_manager.check_permission(
                        context.user_id, "access_pii", resource or "", context
                    ):
                        await self._log_security_event(
                            EventType.PII_ACCESS_DENIED,
                            {
                                "user_id": context.user_id,
                                "operation": operation,
                                "pii_types": [f.type.value for f in pii_findings],
                            },
                            SeverityLevel.HIGH,
                            context.request_id,
                        )
                        return False

            # 6. Log successful authorization
            await self._log_security_event(
                EventType.AUTHORIZATION_SUCCESS,
                {
                    "user_id": context.user_id,
                    "operation": operation,
                    "resource": resource,
                },
                SeverityLevel.INFO,
                context.request_id,
            )

            return True

        except Exception as e:
            await self._log_security_event(
                EventType.AUTHORIZATION_ERROR,
                {"error": str(e), "operation": operation, "user_id": context.user_id},
                SeverityLevel.HIGH,
                context.request_id,
            )
            return False

    async def sanitize_request_data(
        self, data: Dict[str, Any], context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Sanitize request data for security
        Implements OWASP A03:2021 – Injection
        """
        try:
            sanitized_data = {}

            for key, value in data.items():
                # 1. SQL injection prevention
                if isinstance(value, str):
                    # Remove potential SQL injection patterns
                    sanitized_value = self._sanitize_sql_injection(value)

                    # 2. XSS prevention
                    sanitized_value = self._sanitize_xss(sanitized_value)

                    # 3. Command injection prevention
                    sanitized_value = self._sanitize_command_injection(sanitized_value)

                    sanitized_data[key] = sanitized_value
                else:
                    sanitized_data[key] = value

            # 4. Log data sanitization
            await self._log_security_event(
                EventType.DATA_SANITIZED,
                {"user_id": context.user_id, "keys_processed": list(data.keys())},
                SeverityLevel.DEBUG,
                context.request_id,
            )

            return sanitized_data

        except Exception as e:
            await self._log_security_event(
                EventType.DATA_SANITIZATION_ERROR,
                {"error": str(e)},
                SeverityLevel.HIGH,
                context.request_id,
            )
            raise SecurityException(f"Data sanitization failed: {str(e)}")

    async def sanitize_response_data(
        self, data: Dict[str, Any], context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Sanitize response data, including PII masking
        Implements GDPR/CCPA/PIPA compliance
        """
        try:
            # 1. Detect PII in response
            pii_findings = await self.pii_detector.scan_data(data)

            if pii_findings:
                # 2. Check if user has permission to see PII
                can_access_pii = await self.rbac_manager.check_permission(
                    context.user_id, "view_pii", "", context
                )

                if not can_access_pii:
                    # 3. Mask PII data
                    masked_data_any = await self.pii_detector.mask_pii_data(
                        data, pii_findings
                    )
                    masked_data: Dict[str, Any] = masked_data_any if isinstance(masked_data_any, dict) else {}

                    # 4. Log PII masking
                    await self._log_security_event(
                        EventType.PII_MASKED,
                        {
                            "user_id": context.user_id,
                            "pii_types": [f.type.value for f in pii_findings],
                            "masked_fields": len(pii_findings),
                        },
                        SeverityLevel.INFO,
                        context.request_id,
                    )

                    return masked_data
                else:
                    # 5. Log PII access
                    await self._log_security_event(
                        EventType.PII_ACCESSED,
                        {
                            "user_id": context.user_id,
                            "pii_types": [f.type.value for f in pii_findings],
                        },
                        SeverityLevel.WARNING,
                        context.request_id,
                    )

            return data

        except Exception as e:
            await self._log_security_event(
                EventType.DATA_SANITIZATION_ERROR,
                {"error": str(e)},
                SeverityLevel.HIGH,
                context.request_id,
            )
            raise SecurityException(f"Response sanitization failed: {str(e)}")

    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        metrics: Dict[str, Any] = {
            "authentication": await self.auth_service.get_metrics(),
            "authorization": await self.rbac_manager.get_metrics(),
            "audit": await self.audit_logger.get_metrics(),
            "pii_detection": await self.pii_detector.get_metrics(),
            "compliance": await self.compliance_manager.get_metrics(),
            "monitoring": await self.security_monitor.get_metrics(),
            "vulnerability_scanning": await self.vulnerability_scanner.get_metrics(),
            "active_sessions": len(self._active_sessions),
            "security_incidents": len(self._security_incidents),
        }
        return metrics

    async def _check_rate_limit(self, identifier: str) -> bool:
        """Check rate limiting"""
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(minutes=1)

        if identifier not in self._rate_limit_cache:
            self._rate_limit_cache[identifier] = []

        # Clean old requests
        self._rate_limit_cache[identifier] = [
            req_time
            for req_time in self._rate_limit_cache[identifier]
            if req_time > window_start
        ]

        # Check limit
        if (
            len(self._rate_limit_cache[identifier])
            >= self.policy.max_requests_per_minute
        ):
            return False

        # Add current request
        self._rate_limit_cache[identifier].append(current_time)
        return True

    async def _calculate_risk_score(
        self, user_info: Dict[str, Any], ip_address: str, user_agent: str
    ) -> float:
        """Calculate risk score for the request"""
        risk_score = 0.0

        # Check for suspicious IP patterns
        if self._is_suspicious_ip(ip_address):
            risk_score += 0.3

        # Check user agent
        if self._is_suspicious_user_agent(user_agent):
            risk_score += 0.2

        # Check time of access
        if self._is_unusual_access_time():
            risk_score += 0.1

        # Check geographic location (if available)
        # This would integrate with IP geolocation service

        return min(risk_score, 1.0)

    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        # This would integrate with threat intelligence feeds
        suspicious_patterns = ["127.0.0.1", "10.0.0.", "192.168."]
        return any(pattern in ip_address for pattern in suspicious_patterns)

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        suspicious_patterns = ["curl", "wget", "python-requests", "bot"]
        return any(
            pattern.lower() in user_agent.lower() for pattern in suspicious_patterns
        )

    def _is_unusual_access_time(self) -> bool:
        """Check if access time is unusual"""
        current_hour = datetime.utcnow().hour
        # Consider 2 AM - 6 AM as unusual hours
        return 2 <= current_hour <= 6

    def _is_session_expired(self, context: SecurityContext) -> bool:
        """Check if session is expired"""
        session_age = datetime.utcnow() - context.timestamp
        return session_age > timedelta(minutes=self.policy.session_timeout_minutes)

    async def _invalidate_session(self, session_id: str) -> None:
        """Invalidate a session"""
        if session_id in self._active_sessions:
            context = self._active_sessions[session_id]
            del self._active_sessions[session_id]

            await self._log_security_event(
                EventType.SESSION_INVALIDATED,
                {"user_id": context.user_id, "session_id": session_id},
                SeverityLevel.INFO,
                context.request_id,
            )

    async def _get_resource_security_level(self, resource: str) -> SecurityLevel:
        """Get security level for a resource"""
        # This would be configured based on resource classification
        resource_levels = {
            "pii_data": SecurityLevel.RESTRICTED,
            "financial_data": SecurityLevel.CONFIDENTIAL,
            "public_documents": SecurityLevel.PUBLIC,
            "internal_documents": SecurityLevel.INTERNAL,
        }
        return resource_levels.get(resource, SecurityLevel.INTERNAL)

    async def _check_clearance_access(
        self, user_level: SecurityLevel, resource_level: SecurityLevel
    ) -> bool:
        """Check if user clearance allows access to resource"""
        level_hierarchy = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.INTERNAL: 1,
            SecurityLevel.CONFIDENTIAL: 2,
            SecurityLevel.RESTRICTED: 3,
            SecurityLevel.TOP_SECRET: 4,
        }

        return level_hierarchy[user_level] >= level_hierarchy[resource_level]

    def _sanitize_sql_injection(self, value: str) -> str:
        """Sanitize SQL injection patterns"""
        # Remove common SQL injection patterns
        dangerous_patterns = [
            "'; DROP TABLE",
            "'; DELETE FROM",
            "'; UPDATE",
            "'; INSERT INTO",
            "UNION SELECT",
            "OR 1=1",
            "AND 1=1",
            "--",
            "/*",
            "*/",
        ]

        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, "")
            sanitized = sanitized.replace(pattern.lower(), "")

        return sanitized

    def _sanitize_xss(self, value: str) -> str:
        """Sanitize XSS patterns"""
        # Remove common XSS patterns
        dangerous_patterns = [
            "<script>",
            "</script>",
            "javascript:",
            "onload=",
            "onerror=",
            "onclick=",
            "onmouseover=",
            "<iframe>",
            "</iframe>",
        ]

        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, "")
            sanitized = sanitized.replace(pattern.upper(), "")

        return sanitized

    def _sanitize_command_injection(self, value: str) -> str:
        """Sanitize command injection patterns"""
        # Remove common command injection patterns
        dangerous_patterns = [
            ";",
            "&&",
            "||",
            "|",
            "`",
            "$(",
            "../",
            "../../",
            "/etc/passwd",
            "/bin/sh",
        ]

        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, "")

        return sanitized

    async def _log_security_event(
        self,
        event_type: EventType,
        details: Dict[str, Any],
        severity: SeverityLevel,
        request_id: str,
    ) -> None:
        """Log security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            details=details,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

        await self.audit_logger.log_event(event)

        # Add to security incidents if high severity
        if severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
            self._security_incidents.append(
                {"event": event, "timestamp": datetime.utcnow(), "resolved": False}
            )


class SecurityException(Exception):
    """Security-related exception"""

    pass
