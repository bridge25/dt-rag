"""
Security Integration for DT-RAG v1.8.1
Integrates the security framework with the main application
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from .core.security_manager import SecurityManager
from .config.security_config import SecurityConfigManager, SecurityLevel, get_security_config
from .middleware.security_middleware import SecurityMiddleware, RequestLoggingMiddleware
from .routers.security_router import security_router
from .audit.audit_logger import EventType, SeverityLevel

logger = logging.getLogger(__name__)

class SecurityIntegration:
    """
    Main security integration class that sets up all security components
    """

    def __init__(self, config_file: Optional[str] = None):
        self.config_manager = SecurityConfigManager(config_file)
        self.config = None
        self.security_manager: Optional[SecurityManager] = None
        self._initialized = False

    async def initialize(self, security_level: Optional[SecurityLevel] = None):
        """Initialize security framework"""
        try:
            # Load configuration
            self.config = self.config_manager.load_config(security_level)

            # Validate configuration
            issues = self.config_manager.validate_config(self.config)
            if issues:
                logger.warning(f"Security configuration issues: {issues}")

            # Initialize security manager
            security_config = {
                'auth': {
                    'jwt_secret': self.config.auth.jwt_secret,
                    'jwt_algorithm': self.config.auth.jwt_algorithm,
                    'jwt_expiry_hours': self.config.auth.jwt_expiry_hours,
                    'max_login_attempts': self.config.auth.max_login_attempts,
                    'lockout_duration_minutes': self.config.auth.lockout_duration_minutes,
                    'password_min_length': self.config.auth.password_min_length,
                    'require_special_chars': self.config.auth.require_special_chars
                },
                'rbac': {
                    'default_role': self.config.rbac.default_role,
                    'enable_attribute_based_access': self.config.rbac.enable_attribute_based_access,
                    'enable_time_based_access': self.config.rbac.enable_time_based_access,
                    'max_concurrent_sessions': self.config.rbac.max_concurrent_sessions
                },
                'audit': {
                    'storage_type': self.config.audit.storage_type,
                    'log_directory': self.config.audit.log_directory,
                    'max_log_file_size': self.config.audit.max_log_file_size,
                    'retention_days': self.config.audit.retention_days,
                    'enable_encryption': self.config.audit.enable_encryption,
                    'enable_signing': self.config.audit.enable_signing,
                    'compression_enabled': self.config.audit.compression_enabled,
                    'cache_size': self.config.audit.cache_size
                },
                'pii': {
                    'confidence_threshold': self.config.pii.confidence_threshold,
                    'enable_context_analysis': self.config.pii.enable_context_analysis,
                    'supported_languages': self.config.pii.supported_languages,
                    'custom_patterns': self.config.pii.custom_patterns,
                    'exclusion_patterns': self.config.pii.exclusion_patterns
                },
                'compliance': {
                    'supported_regulations': self.config.compliance.supported_regulations,
                    'storage_path': self.config.compliance.storage_path,
                    'auto_response_enabled': self.config.compliance.auto_response_enabled,
                    'breach_notification_enabled': self.config.compliance.breach_notification_enabled
                },
                'monitoring': {
                    'enable_ml_detection': self.config.monitoring.enable_ml_detection,
                    'alert_thresholds': self.config.monitoring.alert_thresholds,
                    'enable_real_time_monitoring': self.config.monitoring.enable_real_time_monitoring,
                    'alert_retention_days': self.config.monitoring.alert_retention_days
                },
                'scanning': {
                    'enable_bandit': self.config.scanning.enable_bandit,
                    'enable_safety': self.config.scanning.enable_safety,
                    'enable_semgrep': self.config.scanning.enable_semgrep,
                    'enable_custom_rules': self.config.scanning.enable_custom_rules,
                    'max_file_size': self.config.scanning.max_file_size,
                    'excluded_paths': self.config.scanning.excluded_paths
                },
                'policy': {
                    'require_authentication': self.config.middleware.enable_auth,
                    'require_authorization': True,
                    'enable_audit_logging': True,
                    'enable_pii_detection': True,
                    'enable_rate_limiting': self.config.middleware.enable_rate_limiting,
                    'max_requests_per_minute': self.config.middleware.rate_limit_requests,
                    'session_timeout_minutes': self.config.auth.session_timeout_minutes,
                    'require_encryption': self.config.encryption.enable_communication_encryption,
                    'allow_anonymous_read': not self.config.middleware.enable_auth,
                    'sensitive_operations': [
                        'delete_documents', 'access_pii', 'admin_system',
                        'manage_users', 'export_data'
                    ]
                }
            }

            self.security_manager = SecurityManager(security_config)

            # Start background security services
            if self.config.monitoring.enable_real_time_monitoring:
                await self.security_manager.security_monitor.start_monitoring()

            await self.security_manager.audit_logger.start_background_tasks()

            # Log security system startup
            await self.security_manager.audit_logger.log_event({
                'event_type': EventType.SYSTEM_STARTUP,
                'severity': SeverityLevel.INFO,
                'details': {
                    'security_level': self.config.security_level.value,
                    'components_enabled': {
                        'authentication': self.config.middleware.enable_auth,
                        'authorization': True,
                        'pii_detection': True,
                        'compliance': True,
                        'monitoring': self.config.monitoring.enable_real_time_monitoring,
                        'vulnerability_scanning': True
                    }
                },
                'user_id': 'system',
                'ip_address': '127.0.0.1',
                'timestamp': None
            })

            self._initialized = True
            logger.info(f"Security framework initialized (Level: {self.config.security_level.value})")

        except Exception as e:
            logger.error(f"Security initialization failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown security framework"""
        if self.security_manager:
            try:
                # Stop monitoring
                await self.security_manager.security_monitor.stop_monitoring()

                # Stop audit logging
                await self.security_manager.audit_logger.stop_background_tasks()

                # Log shutdown
                await self.security_manager.audit_logger.log_event({
                    'event_type': EventType.SYSTEM_SHUTDOWN,
                    'severity': SeverityLevel.INFO,
                    'details': {'reason': 'graceful_shutdown'},
                    'user_id': 'system',
                    'ip_address': '127.0.0.1',
                    'timestamp': None
                })

                logger.info("Security framework shutdown completed")

            except Exception as e:
                logger.error(f"Security shutdown error: {e}")

    def setup_fastapi_app(self, app: FastAPI):
        """Setup FastAPI application with security"""
        if not self._initialized:
            raise RuntimeError("Security framework not initialized")

        # Add security middleware
        middleware_config = {
            'enable_auth': self.config.middleware.enable_auth,
            'enable_rate_limiting': self.config.middleware.enable_rate_limiting,
            'enable_input_validation': self.config.middleware.enable_input_validation,
            'enable_output_sanitization': self.config.middleware.enable_output_sanitization,
            'enable_security_headers': self.config.middleware.enable_security_headers,
            'exempt_endpoints': self.config.middleware.exempt_endpoints,
            'rate_limit_requests': self.config.middleware.rate_limit_requests,
            'rate_limit_window': self.config.middleware.rate_limit_window,
            'max_request_size': self.config.middleware.max_request_size,
            'max_json_fields': self.config.middleware.max_json_fields,
            'blocked_ips': self.config.middleware.blocked_ips,
            'allowed_ips': self.config.middleware.allowed_ips
        }

        # Add request logging middleware first
        app.add_middleware(
            RequestLoggingMiddleware,
            security_manager=self.security_manager
        )

        # Add main security middleware
        app.add_middleware(
            SecurityMiddleware,
            security_manager=self.security_manager,
            config=middleware_config
        )

        # Update CORS middleware for security
        if any(isinstance(middleware, CORSMiddleware) for middleware in app.user_middleware):
            # CORS already configured, update with security settings
            pass
        else:
            # Add secure CORS configuration - Security: No wildcards in any environment
            production_origins = ["https://dt-rag.com", "https://app.dt-rag.com"]
            development_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ]

            app.add_middleware(
                CORSMiddleware,
                allow_origins=production_origins if self.config.security_level == SecurityLevel.PRODUCTION else development_origins,
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
                    "Cache-Control",
                    "X-Security-Version"
                ],
                expose_headers=["X-Request-ID", "X-Security-Version"]
            )

        # Add security router
        app.include_router(security_router)

        # Add startup/shutdown events
        @app.on_event("startup")
        async def security_startup():
            if self.config.monitoring.enable_real_time_monitoring and not self.security_manager.security_monitor._monitoring_task:
                await self.security_manager.security_monitor.start_monitoring()

        @app.on_event("shutdown")
        async def security_shutdown():
            await self.shutdown()

        logger.info("FastAPI security integration completed")

    def get_security_dependency(self):
        """Get security dependency for endpoints"""
        from .middleware.security_middleware import create_security_dependency
        return create_security_dependency(self.security_manager)

    def get_security_manager(self) -> SecurityManager:
        """Get security manager instance"""
        if not self._initialized:
            raise RuntimeError("Security framework not initialized")
        return self.security_manager

    async def run_security_check(self) -> Dict[str, Any]:
        """Run comprehensive security check"""
        if not self._initialized:
            return {"status": "not_initialized"}

        try:
            # Get security metrics
            metrics = await self.security_manager.get_security_metrics()

            # Run compliance check
            compliance_report = await self.security_manager.compliance_manager.run_compliance_check()

            # Get vulnerability scan results (if any recent scans)
            scan_metrics = await self.security_manager.vulnerability_scanner.get_metrics()

            # Get monitoring status
            monitoring_metrics = await self.security_manager.security_monitor.get_metrics()

            return {
                "status": "healthy",
                "security_level": self.config.security_level.value,
                "overall_metrics": metrics,
                "compliance": {
                    "status": "compliant" if compliance_report["overall_compliance"] else "non_compliant",
                    "violations": len(compliance_report.get("violations", [])),
                    "warnings": len(compliance_report.get("warnings", []))
                },
                "vulnerability_scanning": {
                    "scans_completed": scan_metrics.get("completed_scans", 0),
                    "active_scans": scan_metrics.get("active_scans", 0),
                    "vulnerabilities_found": scan_metrics.get("vulnerabilities_found", 0)
                },
                "monitoring": {
                    "active_alerts": monitoring_metrics.get("active_alerts", 0),
                    "incidents": monitoring_metrics.get("open_incidents", 0),
                    "model_trained": monitoring_metrics.get("model_trained", False)
                },
                "timestamp": None
            }

        except Exception as e:
            logger.error(f"Security check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": None
            }

# Global security integration instance
_security_integration: Optional[SecurityIntegration] = None

async def get_security_integration(
    config_file: Optional[str] = None,
    security_level: Optional[SecurityLevel] = None
) -> SecurityIntegration:
    """Get or create global security integration instance"""
    global _security_integration

    if _security_integration is None:
        _security_integration = SecurityIntegration(config_file)
        await _security_integration.initialize(security_level)

    return _security_integration

def setup_security_for_app(
    app: FastAPI,
    config_file: Optional[str] = None,
    security_level: Optional[SecurityLevel] = None
) -> SecurityIntegration:
    """Setup security for FastAPI application (synchronous)"""
    global _security_integration

    # Create security integration
    security_integration = SecurityIntegration(config_file)

    # Store for async initialization
    _security_integration = security_integration

    # Setup middleware and routes
    # Note: Actual initialization happens in startup event
    async def init_security():
        await security_integration.initialize(security_level)
        security_integration.setup_fastapi_app(app)

    # Add startup event for initialization
    @app.on_event("startup")
    async def startup_security():
        await init_security()

    return security_integration

async def create_security_test_data():
    """Create test data for security demonstrations"""
    try:
        integration = await get_security_integration()
        security_manager = integration.get_security_manager()

        # Create test users
        test_users = [
            ("admin", "admin@dt-rag.local", "SecureAdmin123!", ["super_admin"]),
            ("editor", "editor@dt-rag.local", "SecureEditor123!", ["editor"]),
            ("viewer", "viewer@dt-rag.local", "SecureViewer123!", ["viewer"])
        ]

        for username, email, password, roles in test_users:
            try:
                from .auth.auth_service import Role
                user_roles = [Role(role) for role in roles]
                await security_manager.auth_service.register_user(
                    username, email, password, user_roles
                )
                logger.info(f"Created test user: {username}")
            except Exception as e:
                logger.warning(f"Failed to create test user {username}: {e}")

        # Create test processing activities
        from .compliance.compliance_manager import ProcessingPurpose, LegalBasis

        test_activities = [
            {
                "name": "Document Processing",
                "description": "Processing user-uploaded documents for classification",
                "controller": "DT-RAG System",
                "purposes": [ProcessingPurpose.SERVICE_DELIVERY],
                "legal_basis": [LegalBasis.CONSENT],
                "data_categories": ["document_content", "metadata"],
                "data_subjects": ["users"],
                "recipients": ["internal_staff"],
                "retention_period": "5 years",
                "security_measures": ["encryption", "access_controls", "audit_logging"]
            },
            {
                "name": "Security Monitoring",
                "description": "Monitoring system for security events and threats",
                "controller": "DT-RAG Security Team",
                "purposes": [ProcessingPurpose.SECURITY],
                "legal_basis": [LegalBasis.LEGITIMATE_INTERESTS],
                "data_categories": ["access_logs", "ip_addresses", "user_behavior"],
                "data_subjects": ["users", "system_administrators"],
                "recipients": ["security_team"],
                "retention_period": "1 year",
                "security_measures": ["encryption", "access_controls", "audit_logging", "anonymization"]
            }
        ]

        for activity_data in test_activities:
            try:
                await security_manager.compliance_manager.register_processing_activity(**activity_data)
                logger.info(f"Created test processing activity: {activity_data['name']}")
            except Exception as e:
                logger.warning(f"Failed to create processing activity: {e}")

        logger.info("Security test data creation completed")

    except Exception as e:
        logger.error(f"Failed to create security test data: {e}")

# Utility functions for security operations

async def authenticate_user_token(token: str) -> Optional[Dict[str, Any]]:
    """Authenticate user token and return user info"""
    try:
        integration = await get_security_integration()
        security_manager = integration.get_security_manager()
        return await security_manager.auth_service.validate_token(token)
    except Exception as e:
        logger.error(f"Token authentication failed: {e}")
        return None

async def check_user_permission(
    user_id: str,
    permission: str,
    resource: str = None
) -> bool:
    """Check if user has specific permission"""
    try:
        integration = await get_security_integration()
        security_manager = integration.get_security_manager()
        return await security_manager.rbac_manager.check_permission(
            user_id, permission, resource
        )
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        return False

async def scan_text_for_pii(text: str, field_name: str = None) -> List[Dict[str, Any]]:
    """Scan text for PII and return findings"""
    try:
        integration = await get_security_integration()
        security_manager = integration.get_security_manager()
        findings = await security_manager.pii_detector.scan_text(text, field_name)

        return [
            {
                "type": finding.type.value,
                "value": finding.value,
                "confidence": finding.confidence,
                "regulation_flags": finding.regulation_flags
            }
            for finding in findings
        ]
    except Exception as e:
        logger.error(f"PII scanning failed: {e}")
        return []

async def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "info",
    user_id: str = None,
    ip_address: str = None
):
    """Log security event"""
    try:
        integration = await get_security_integration()
        security_manager = integration.get_security_manager()

        from .audit.audit_logger import EventType, SeverityLevel

        await security_manager.audit_logger.log_event({
            'event_type': EventType(event_type),
            'severity': SeverityLevel(severity),
            'details': details,
            'user_id': user_id,
            'ip_address': ip_address,
            'timestamp': None
        })

    except Exception as e:
        logger.error(f"Security event logging failed: {e}")

# Export main components
__all__ = [
    'SecurityIntegration',
    'get_security_integration',
    'setup_security_for_app',
    'create_security_test_data',
    'authenticate_user_token',
    'check_user_permission',
    'scan_text_for_pii',
    'log_security_event'
]