"""
Dynamic Taxonomy RAG v1.8.1 - Enterprise Security Framework
OWASP Top 10 Compliant Security & Compliance System

Features:
- PII Detection & Data Privacy Protection
- Comprehensive Audit Logging
- Role-Based Access Control (RBAC)
- OWASP Security Controls
- GDPR/CCPA/PIPA Compliance
- Security Monitoring & Alerting
- Vulnerability Assessment
"""

from .core.security_manager import SecurityManager
from .auth.auth_service import AuthService, RBACManager
from .audit.audit_logger import AuditLogger, SecurityEvent
from .compliance.pii_detector import PIIDetector, PIIType
from .compliance.compliance_manager import ComplianceManager
from .monitoring.security_monitor import SecurityMonitor
from .scanning.vulnerability_scanner import VulnerabilityScanner

__version__ = "1.8.1"
__author__ = "DT-RAG Security Team"

# Export main security components
__all__ = [
    'SecurityManager',
    'AuthService',
    'RBACManager',
    'AuditLogger',
    'SecurityEvent',
    'PIIDetector',
    'PIIType',
    'ComplianceManager',
    'SecurityMonitor',
    'VulnerabilityScanner'
]