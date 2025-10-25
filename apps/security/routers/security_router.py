"""
Security API Router for DT-RAG v1.8.1
Provides security management endpoints for authentication, compliance, and monitoring
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from ..auth.auth_service import Role
from ..compliance.compliance_manager import (
    ConsentType,
    DataSubjectRightType,
    LegalBasis,
    ProcessingPurpose,
)
from ..core.security_manager import SecurityManager
from ..monitoring.security_monitor import AlertType, ThreatLevel
from ..scanning.vulnerability_scanner import ScanType

logger = logging.getLogger(__name__)

# Request/Response Models


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    roles: List[Role] = [Role.VIEWER]


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    clearance_level: str
    is_active: bool
    created_at: datetime


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=12)


class DataSubjectRequest(BaseModel):
    request_type: DataSubjectRightType
    email: EmailStr
    request_details: Optional[Dict[str, Any]] = None
    regulation: str = "GDPR"


class ConsentRequest(BaseModel):
    purpose: ProcessingPurpose
    consent_type: ConsentType = ConsentType.EXPLICIT
    legal_basis: LegalBasis = LegalBasis.CONSENT
    consent_text: Optional[str] = None
    expires_at: Optional[datetime] = None


class SecurityScanRequest(BaseModel):
    target_path: str = Field(..., description="Path to scan")
    scan_types: List[ScanType] = [ScanType.STATIC_CODE_ANALYSIS]


class PIIDetectionRequest(BaseModel):
    text: str = Field(..., description="Text to scan for PII")
    field_name: Optional[str] = None


class SecurityAlertRequest(BaseModel):
    alert_type: AlertType
    threat_level: ThreatLevel
    source: str
    details: Dict[str, Any]


class ComplianceCheckRequest(BaseModel):
    regulation: str = "GDPR"


# Router setup

security_router = APIRouter(prefix="/security", tags=["Security"])
bearer_scheme = HTTPBearer()


def get_security_manager() -> SecurityManager:
    """Get security manager instance"""
    # In production, this would be injected via dependency injection
    from ..core.security_manager import SecurityManager

    return SecurityManager()


# Authentication Endpoints


@security_router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Authenticate user and return access token
    """
    try:
        # Extract client info (in real implementation, get from request)
        client_ip = "127.0.0.1"  # Placeholder
        user_agent = "DT-RAG-Client"  # Placeholder

        token, user = await security_manager.auth_service.authenticate_user(
            request.username, request.password, client_ip, user_agent
        )

        return LoginResponse(
            access_token=token,
            expires_in=24 * 3600,  # 24 hours
            user_info={
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": [role.value for role in user.roles],
                "permissions": [perm.value for perm in user.permissions],
                "clearance_level": user.clearance_level,
            },
        )

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )


@security_router.post("/auth/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Register new user account
    """
    try:
        user = await security_manager.auth_service.register_user(
            request.username, request.email, request.password, request.roles
        )

        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[role.value for role in user.roles],
            permissions=[perm.value for perm in user.permissions],
            clearance_level=user.clearance_level,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@security_router.post("/auth/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Logout user and revoke token
    """
    try:
        await security_manager.auth_service.logout_user(credentials.credentials)
        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Logout failed"
        )


@security_router.post("/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Change user password
    """
    try:
        # Validate current token and get user info
        user_info = await security_manager.auth_service.validate_token(
            credentials.credentials
        )
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        success = await security_manager.auth_service.change_password(
            user_info["user_id"], request.current_password, request.new_password
        )

        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# PII and Privacy Endpoints


@security_router.post("/pii/detect")
async def detect_pii(
    request: PIIDetectionRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Detect PII in text
    """
    try:
        findings = await security_manager.pii_detector.scan_text(
            request.text, request.field_name
        )

        return {
            "findings": [
                {
                    "type": finding.type.value,
                    "value": finding.value,
                    "start_pos": finding.start_pos,
                    "end_pos": finding.end_pos,
                    "confidence": finding.confidence,
                    "field_name": finding.field_name,
                    "regulation_flags": finding.regulation_flags,
                }
                for finding in findings
            ],
            "summary": {
                "total_findings": len(findings),
                "types_found": list(set(f.type.value for f in findings)),
                "highest_risk": max([f.confidence for f in findings], default=0.0),
            },
        }

    except Exception as e:
        logger.error(f"PII detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PII detection failed",
        )


@security_router.post("/pii/mask")
async def mask_pii(
    request: PIIDetectionRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Mask PII in text
    """
    try:
        # Get findings first using scan_text
        findings = await security_manager.pii_detector.scan_text(
            request.text, request.field_name
        )

        # Then mask the text using the findings we already collected to avoid
        # performing an additional scan inside the masking helper.
        masked_text = await security_manager.pii_detector.mask_pii_data(
            request.text,
            findings=findings,
        )

        return {
            "original_text": request.text,
            "masked_text": masked_text,
            "findings": [
                {
                    "type": finding.type.value,
                    "confidence": finding.confidence,
                    "regulation_flags": finding.regulation_flags,
                }
                for finding in findings
            ],
        }

    except Exception as e:
        logger.error(f"PII masking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PII masking failed",
        )


# Compliance Endpoints


@security_router.post("/compliance/data-subject-request")
async def submit_data_subject_request(
    request: DataSubjectRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Submit data subject request (GDPR/CCPA/PIPA)
    """
    try:
        # Generate data subject ID from email (in production, use proper mapping)
        data_subject_id = f"subject_{hash(request.email) % 1000000}"

        data_request = (
            await security_manager.compliance_manager.submit_data_subject_request(
                request.request_type,
                data_subject_id,
                request.email,
                request.request_details,
                request.regulation,
            )
        )

        return {
            "request_id": data_request.request_id,
            "status": data_request.status,
            "request_type": data_request.request_type.value,
            "response_due_date": (
                data_request.response_due_date.isoformat()
                if data_request.response_due_date
                else None
            ),
            "message": f"Data subject request submitted. Request ID: {data_request.request_id}",
        }

    except Exception as e:
        logger.error(f"Data subject request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit data subject request",
        )


@security_router.post("/compliance/consent")
async def record_consent(
    request: ConsentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Record user consent
    """
    try:
        # Get user from token
        user_info = await security_manager.auth_service.validate_token(
            credentials.credentials
        )
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        consent = await security_manager.compliance_manager.record_consent(
            user_info["user_id"],
            request.purpose,
            request.consent_type,
            request.legal_basis,
            request.consent_text,
            request.expires_at,
        )

        return {
            "consent_id": consent.consent_id,
            "status": "recorded",
            "purpose": consent.purpose.value,
            "granted_at": consent.granted_at.isoformat(),
            "expires_at": (
                consent.expires_at.isoformat() if consent.expires_at else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consent recording failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent",
        )


@security_router.post("/compliance/check")
async def run_compliance_check(
    request: ComplianceCheckRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Run compliance check for specific regulation
    """
    try:
        compliance_report = (
            await security_manager.compliance_manager.run_compliance_check(
                request.regulation
            )
        )

        return compliance_report

    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Compliance check failed",
        )


# Security Monitoring Endpoints


@security_router.get("/monitoring/dashboard")
async def get_security_dashboard(
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Get security monitoring dashboard
    """
    try:
        dashboard_data = (
            await security_manager.security_monitor.get_security_dashboard()
        )
        return dashboard_data

    except Exception as e:
        logger.error(f"Dashboard retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


@security_router.get("/monitoring/alerts")
async def get_security_alerts(
    threat_level: Optional[ThreatLevel] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Get active security alerts
    """
    try:
        alerts = await security_manager.security_monitor.get_active_alerts(
            threat_level, limit
        )

        return {
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type.value,
                    "threat_level": alert.threat_level.value,
                    "detected_at": alert.detected_at.isoformat(),
                    "source": alert.source,
                    "user_id": alert.user_id,
                    "ip_address": alert.ip_address,
                    "details": alert.details,
                    "status": alert.status,
                }
                for alert in alerts
            ],
            "total": len(alerts),
        }

    except Exception as e:
        logger.error(f"Alert retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts",
        )


@security_router.post("/monitoring/alert")
async def create_security_alert(
    request: SecurityAlertRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Create manual security alert
    """
    try:
        alert = await security_manager.security_monitor.create_manual_alert(
            request.alert_type, request.threat_level, request.source, request.details
        )

        return {
            "alert_id": alert.alert_id,
            "message": "Security alert created",
            "status": "active",
        }

    except Exception as e:
        logger.error(f"Alert creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert",
        )


@security_router.put("/monitoring/alert/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Acknowledge security alert
    """
    try:
        # Get user from token
        user_info = await security_manager.auth_service.validate_token(
            credentials.credentials
        )
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        success = await security_manager.security_monitor.acknowledge_alert(
            alert_id, user_info["username"]
        )

        if success:
            return {"message": "Alert acknowledged", "status": "acknowledged"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert acknowledgment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert",
        )


# Vulnerability Scanning Endpoints


@security_router.post("/scanning/scan")
async def start_security_scan(
    request: SecurityScanRequest,
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Start security vulnerability scan
    """
    try:
        scan_result = await security_manager.vulnerability_scanner.scan_codebase(
            request.target_path, request.scan_types
        )

        return {
            "scan_id": scan_result.scan_id,
            "status": scan_result.status,
            "target": scan_result.target,
            "scan_types": [st.value for st in request.scan_types],
            "started_at": scan_result.started_at.isoformat(),
            "vulnerabilities_found": len(scan_result.vulnerabilities),
        }

    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start security scan",
        )


@security_router.get("/scanning/scan/{scan_id}")
async def get_scan_result(
    scan_id: str, security_manager: SecurityManager = Depends(get_security_manager)
) -> None:
    """
    Get security scan result
    """
    try:
        scan_result = await security_manager.vulnerability_scanner.get_scan_result(
            scan_id
        )

        if not scan_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Scan result not found"
            )

        return {
            "scan_id": scan_result.scan_id,
            "status": scan_result.status,
            "target": scan_result.target,
            "started_at": scan_result.started_at.isoformat(),
            "completed_at": (
                scan_result.completed_at.isoformat()
                if scan_result.completed_at
                else None
            ),
            "summary": scan_result.summary,
            "vulnerabilities": [
                {
                    "vuln_id": vuln.vuln_id,
                    "type": vuln.vuln_type.value,
                    "severity": vuln.severity.value,
                    "title": vuln.title,
                    "description": vuln.description,
                    "file_path": vuln.file_path,
                    "line_number": vuln.line_number,
                    "confidence": vuln.confidence,
                    "remediation": vuln.remediation,
                }
                for vuln in scan_result.vulnerabilities
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan result retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scan result",
        )


@security_router.get("/scanning/report/{scan_id}")
async def get_vulnerability_report(
    scan_id: str,
    include_false_positives: bool = Query(False),
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Get comprehensive vulnerability report
    """
    try:
        report = await security_manager.vulnerability_scanner.get_vulnerability_report(
            scan_id, include_false_positives
        )

        return report

    except Exception as e:
        logger.error(f"Vulnerability report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate vulnerability report",
        )


# Metrics and Status Endpoints


@security_router.get("/metrics")
async def get_security_metrics(
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Get comprehensive security metrics
    """
    try:
        metrics = await security_manager.get_security_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security metrics",
        )


@security_router.get("/status")
async def get_security_status(
    security_manager: SecurityManager = Depends(get_security_manager),
) -> None:
    """
    Get overall security system status
    """
    try:
        # Perform quick health checks
        auth_healthy = await security_manager.auth_service.get_metrics()
        compliance_healthy = await security_manager.compliance_manager.get_metrics()
        monitoring_healthy = await security_manager.security_monitor.get_metrics()
        scanning_healthy = await security_manager.vulnerability_scanner.get_metrics()

        return {
            "status": "healthy",
            "version": "1.8.1",
            "components": {
                "authentication": {"status": "healthy", "metrics": auth_healthy},
                "compliance": {"status": "healthy", "metrics": compliance_healthy},
                "monitoring": {"status": "healthy", "metrics": monitoring_healthy},
                "scanning": {"status": "healthy", "metrics": scanning_healthy},
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Export router
__all__ = ["security_router"]
