"""
Integration tests for the complete security framework
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from apps.security.integration import SecurityFramework
from apps.security.config.security_config import SecurityLevel
from apps.security.auth.auth_service import AuthService
from apps.security.audit.audit_logger import SecurityEvent, RiskLevel
from apps.security.compliance.pii_detector import PIIType


class TestSecurityFrameworkIntegration:
    """Test complete security framework integration"""

    @pytest.mark.asyncio
    async def test_framework_initialization(self, security_config):
        """Test security framework initialization"""

        framework = SecurityFramework()

        # Test initialization
        await framework.initialize(SecurityLevel.TESTING)

        # Verify components are initialized
        assert framework.auth_service is not None
        assert framework.audit_logger is not None
        assert framework.pii_detector is not None
        assert framework.compliance_manager is not None
        assert framework.security_monitor is not None
        assert framework.vulnerability_scanner is not None
        assert framework.crypto_service is not None

        # Test shutdown
        await framework.shutdown()

    @pytest.mark.asyncio
    async def test_fastapi_integration(self, security_framework):
        """Test FastAPI application integration"""

        app = FastAPI()
        security_framework.setup_fastapi_app(app)

        # Verify routes are added
        route_paths = [route.path for route in app.routes]

        # Check authentication routes
        assert "/api/security/auth/login" in route_paths
        assert "/api/security/auth/register" in route_paths
        assert "/api/security/auth/refresh" in route_paths

        # Check compliance routes
        assert "/api/security/pii/detect" in route_paths
        assert "/api/security/compliance/data-subject-request" in route_paths

        # Check monitoring routes
        assert "/api/security/monitoring/incidents" in route_paths
        assert "/api/security/monitoring/alerts" in route_paths

    @pytest.mark.asyncio
    async def test_end_to_end_authentication_flow(self, security_framework):
        """Test complete authentication flow"""

        app = FastAPI()
        security_framework.setup_fastapi_app(app)

        with TestClient(app) as client:
            # Register user
            register_response = client.post("/api/security/auth/register", json={
                "username": "testuser@example.com",
                "password": "TestPassword123!",
                "email": "testuser@example.com",
                "roles": ["viewer"]
            })
            assert register_response.status_code == 200

            # Login
            login_response = client.post("/api/security/auth/login", json={
                "username": "testuser@example.com",
                "password": "TestPassword123!"
            })
            assert login_response.status_code == 200

            login_data = login_response.json()
            assert "access_token" in login_data
            assert "token_type" in login_data

            # Test authenticated request
            token = login_data["access_token"]
            auth_response = client.get(
                "/api/security/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert auth_response.status_code == 200

    @pytest.mark.asyncio
    async def test_pii_detection_integration(self, security_framework):
        """Test PII detection integration"""

        app = FastAPI()
        security_framework.setup_fastapi_app(app)

        with TestClient(app) as client:
            # Test PII detection
            pii_response = client.post("/api/security/pii/detect", json={
                "text": "Contact John Doe at john.doe@example.com or 010-1234-5678",
                "field_name": "contact_info"
            })
            assert pii_response.status_code == 200

            pii_data = pii_response.json()
            assert "findings" in pii_data
            assert len(pii_data["findings"]) > 0

            # Check for email detection
            email_found = any(
                finding["pii_type"] == PIIType.EMAIL.value
                for finding in pii_data["findings"]
            )
            assert email_found

    @pytest.mark.asyncio
    async def test_compliance_data_subject_request(self, security_framework):
        """Test GDPR data subject request handling"""

        app = FastAPI()
        security_framework.setup_fastapi_app(app)

        with TestClient(app) as client:
            # Submit data subject request
            request_response = client.post("/api/security/compliance/data-subject-request", json={
                "request_type": "access",
                "data_subject_id": "user123",
                "email": "user@example.com",
                "description": "I want to access my personal data"
            })
            assert request_response.status_code == 200

            request_data = request_response.json()
            assert "request_id" in request_data
            assert request_data["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_security_monitoring_integration(self, security_framework):
        """Test security monitoring integration"""

        # Simulate security events
        await security_framework.process_security_event({
            "event_type": "login_attempt",
            "user_id": "user123",
            "ip_address": "192.168.1.100",
            "timestamp": datetime.utcnow(),
            "features": {
                "login_hour": 14,
                "failed_attempts": 0,
                "new_device": False
            }
        })

        # Check that event was processed
        monitor = security_framework.security_monitor
        recent_events = await monitor.get_recent_events(limit=1)
        assert len(recent_events) > 0

    @pytest.mark.asyncio
    async def test_audit_logging_integration(self, security_framework):
        """Test audit logging integration"""

        # Log a security event
        await security_framework.log_security_event(SecurityEvent(
            event_type="test_integration",
            user_id="test_user",
            ip_address="127.0.0.1",
            details={"test": True},
            risk_level=RiskLevel.LOW
        ))

        # Verify event was logged
        audit_logger = security_framework.audit_logger
        recent_logs = await audit_logger.get_recent_events(limit=1)
        assert len(recent_logs) > 0
        assert recent_logs[0]["event_type"] == "test_integration"

    @pytest.mark.asyncio
    async def test_vulnerability_scanning_integration(self, security_framework, temp_dir):
        """Test vulnerability scanning integration"""

        # Create a test file with potential vulnerability
        test_file = temp_dir / "test_vuln.py"
        test_file.write_text("""
import os
def process_input(user_input):
    os.system(f"echo {user_input}")  # Command injection vulnerability
""")

        # Run vulnerability scan
        scanner = security_framework.vulnerability_scanner
        result = await scanner.scan_codebase(
            target_path=str(temp_dir),
            scan_types=["bandit"]
        )

        assert result.scan_id is not None
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_crypto_service_integration(self, security_framework):
        """Test crypto service integration"""

        crypto = security_framework.crypto_service

        # Test encryption/decryption
        plaintext = "sensitive data"
        encrypted = await crypto.encrypt(plaintext.encode())
        decrypted = await crypto.decrypt(encrypted)

        assert decrypted.decode() == plaintext

    @pytest.mark.asyncio
    async def test_permission_checking_integration(self, security_framework, test_users):
        """Test permission checking integration"""

        admin_user = test_users[0]  # Admin user
        regular_user = test_users[1]  # Regular user

        # Test admin permissions
        has_admin_access = await security_framework.check_permission(
            user_id=str(admin_user.id),
            permission="system:admin"
        )
        assert has_admin_access

        # Test regular user permissions
        has_regular_admin_access = await security_framework.check_permission(
            user_id=str(regular_user.id),
            permission="system:admin"
        )
        assert not has_regular_admin_access

        # Test regular user read access
        has_read_access = await security_framework.check_permission(
            user_id=str(regular_user.id),
            permission="documents:read"
        )
        assert has_read_access

    @pytest.mark.asyncio
    async def test_pii_scanning_and_masking_integration(self, security_framework, sample_pii_text):
        """Test integrated PII scanning and masking"""

        # Scan for PII
        findings = await security_framework.scan_for_pii(
            text=sample_pii_text["mixed_text"],
            field_name="user_input"
        )

        assert len(findings) > 0

        # Mask PII data
        masked_data = await security_framework.mask_pii_data(
            data={"content": sample_pii_text["mixed_text"]},
            findings=findings
        )

        assert masked_data["content"] != sample_pii_text["mixed_text"]
        assert "@" not in masked_data["content"] or "*" in masked_data["content"]

    @pytest.mark.asyncio
    async def test_security_middleware_integration(self, security_framework):
        """Test security middleware integration"""

        app = FastAPI()
        security_framework.setup_fastapi_app(app)

        # Add a test endpoint
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        with TestClient(app) as client:
            # Test request with security middleware
            response = client.get("/test")

            # Check security headers are added
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers

    @pytest.mark.asyncio
    async def test_token_authentication_integration(self, security_framework, test_users):
        """Test token authentication integration"""

        admin_user = test_users[0]

        # Generate token
        token = await security_framework.generate_token(
            user_id=str(admin_user.id),
            username=admin_user.username,
            permissions=["system:admin", "documents:read"]
        )

        assert token is not None

        # Authenticate with token
        context = await security_framework.authenticate_token(
            token=token,
            ip_address="127.0.0.1",
            user_agent="test-client"
        )

        assert context is not None
        assert context.user_id == str(admin_user.id)
        assert context.username == admin_user.username

    @pytest.mark.asyncio
    async def test_incident_creation_and_management(self, security_framework):
        """Test security incident creation and management"""

        # Create security incident
        incident = await security_framework.create_security_incident(
            title="Test Security Incident",
            description="This is a test incident",
            threat_level="MEDIUM",
            affected_systems=["auth_service"],
            indicators=["unusual_login_pattern"]
        )

        assert incident.id is not None
        assert incident.status == "open"
        assert incident.threat_level == "MEDIUM"

    @pytest.mark.asyncio
    async def test_compliance_reporting_integration(self, security_framework):
        """Test compliance reporting integration"""

        # Generate compliance report
        report = await security_framework.generate_compliance_report(
            regulation="GDPR",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )

        assert "gdpr_compliance" in report
        assert "data_subject_requests" in report["gdpr_compliance"]
        assert "processing_activities" in report["gdpr_compliance"]

    @pytest.mark.asyncio
    async def test_security_metrics_collection(self, security_framework):
        """Test security metrics collection"""

        # Get security metrics
        metrics = await security_framework.get_security_metrics()

        assert "authentication" in metrics
        assert "pii_detection" in metrics
        assert "audit_logging" in metrics
        assert "vulnerability_scanning" in metrics

    @pytest.mark.asyncio
    async def test_configuration_validation(self, security_framework):
        """Test security configuration validation"""

        # Validate current configuration
        issues = await security_framework.validate_configuration()

        # Should have no critical issues in test environment
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        assert len(critical_issues) == 0

    @pytest.mark.asyncio
    async def test_security_framework_stress_test(self, security_framework):
        """Test security framework under load"""

        # Simulate multiple concurrent operations
        tasks = []

        # Multiple authentication attempts
        for i in range(10):
            task = security_framework.process_security_event({
                "event_type": "login_attempt",
                "user_id": f"user{i}",
                "ip_address": f"192.168.1.{100 + i}",
                "timestamp": datetime.utcnow()
            })
            tasks.append(task)

        # Multiple PII scans
        for i in range(5):
            task = security_framework.scan_for_pii(
                text=f"Contact user{i}@example.com for details",
                field_name=f"field_{i}"
            )
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that all operations completed successfully
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, security_framework):
        """Test error handling and recovery mechanisms"""

        # Test with invalid data
        with pytest.raises(Exception):
            await security_framework.authenticate_token(
                token="invalid-token",
                ip_address="127.0.0.1",
                user_agent="test"
            )

        # Test PII detection with invalid input
        findings = await security_framework.scan_for_pii(
            text="",  # Empty text
            field_name="empty_field"
        )
        assert findings == []  # Should handle gracefully

        # Test with None values
        masked_data = await security_framework.mask_pii_data(
            data=None,
            findings=[]
        )
        assert masked_data is None  # Should handle gracefully