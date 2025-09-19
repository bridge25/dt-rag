"""
Pytest configuration and fixtures for security framework tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
import os
from unittest.mock import AsyncMock, MagicMock

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_security.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-testing-only"
os.environ["SECURITY_LEVEL"] = "testing"

from apps.security.config.security_config import SecurityLevel, SecurityConfig
from apps.security.auth.auth_service import AuthService, RBACManager
from apps.security.audit.audit_logger import AuditLogger
from apps.security.compliance.compliance_manager import ComplianceManager
from apps.security.compliance.pii_detector import PIIDetector
from apps.security.monitoring.security_monitor import SecurityMonitor
from apps.security.scanning.vulnerability_scanner import VulnerabilityScanner
from apps.security.crypto.crypto_service import CryptoService
from apps.security.integration import SecurityFramework


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def security_config():
    """Test security configuration"""
    return SecurityConfig(
        security_level=SecurityLevel.TESTING,
        enable_debug=True,
        enable_metrics=False
    )


@pytest.fixture
async def auth_service():
    """Initialize auth service for testing"""
    service = AuthService()
    await service._init_tables()
    yield service
    await service._cleanup_test_data()


@pytest.fixture
async def rbac_manager():
    """Initialize RBAC manager for testing"""
    manager = RBACManager()
    await manager._init_tables()

    # Create test roles and permissions
    await manager.create_role(
        name="test_admin",
        description="Test admin role",
        permissions=["system:admin", "documents:read", "documents:write"]
    )
    await manager.create_role(
        name="test_user",
        description="Test user role",
        permissions=["documents:read"]
    )

    yield manager
    await manager._cleanup_test_data()


@pytest.fixture
async def audit_logger():
    """Initialize audit logger for testing"""
    logger = AuditLogger()
    await logger._init_tables()
    yield logger
    await logger._cleanup_test_data()


@pytest.fixture
async def compliance_manager():
    """Initialize compliance manager for testing"""
    manager = ComplianceManager()
    await manager._init_tables()
    yield manager
    await manager._cleanup_test_data()


@pytest.fixture
async def pii_detector():
    """Initialize PII detector for testing"""
    detector = PIIDetector()
    yield detector


@pytest.fixture
async def security_monitor():
    """Initialize security monitor for testing"""
    monitor = SecurityMonitor()
    await monitor._init_tables()
    yield monitor
    await monitor._cleanup_test_data()


@pytest.fixture
async def vulnerability_scanner(temp_dir):
    """Initialize vulnerability scanner for testing"""
    scanner = VulnerabilityScanner()
    scanner.config.results_storage_path = str(temp_dir)
    yield scanner


@pytest.fixture
async def crypto_service():
    """Initialize crypto service for testing"""
    service = CryptoService()
    yield service


@pytest.fixture
async def security_framework():
    """Initialize complete security framework for testing"""
    framework = SecurityFramework()
    await framework.initialize(SecurityLevel.TESTING)
    yield framework
    await framework.shutdown()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser@example.com",
        "password": "TestPassword123!",
        "email": "testuser@example.com",
        "roles": ["test_user"]
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin data for testing"""
    return {
        "username": "admin@example.com",
        "password": "AdminPassword123!",
        "email": "admin@example.com",
        "roles": ["test_admin"]
    }


@pytest.fixture
def sample_pii_text():
    """Sample text containing PII for testing"""
    return {
        "email_text": "Please contact John Doe at john.doe@example.com for more information.",
        "phone_text": "Call me at 010-1234-5678 or 02-123-4567.",
        "ssn_text": "His SSN is 123456-1234567 and needs verification.",
        "mixed_text": "John's email is john@test.com, phone is 010-9876-5432, and SSN is 987654-1234567.",
        "clean_text": "This text contains no personal information."
    }


@pytest.fixture
def sample_security_events():
    """Sample security events for testing"""
    return [
        {
            "event_type": "user_login",
            "user_id": "user123",
            "ip_address": "192.168.1.100",
            "details": {"status": "success", "method": "jwt"},
            "risk_level": "LOW"
        },
        {
            "event_type": "failed_login",
            "user_id": "user456",
            "ip_address": "192.168.1.200",
            "details": {"status": "failed", "reason": "invalid_password"},
            "risk_level": "MEDIUM"
        },
        {
            "event_type": "data_access",
            "user_id": "user789",
            "ip_address": "192.168.1.150",
            "details": {"resource": "sensitive_document.pdf", "action": "download"},
            "risk_level": "HIGH"
        }
    ]


@pytest.fixture
def sample_vulnerable_code(temp_dir):
    """Create sample vulnerable code files for scanning"""

    # Python file with SQL injection vulnerability
    sql_injection_file = temp_dir / "vulnerable_sql.py"
    sql_injection_file.write_text("""
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()
""")

    # Python file with hardcoded secret
    hardcoded_secret_file = temp_dir / "hardcoded_secret.py"
    hardcoded_secret_file.write_text("""
import requests

# Hardcoded API key vulnerability
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "secret123"

def make_api_call():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    return requests.get("https://api.example.com/data", headers=headers)
""")

    # Python file with command injection
    command_injection_file = temp_dir / "command_injection.py"
    command_injection_file.write_text("""
import os
import subprocess

def process_file(filename):
    # Command injection vulnerability
    os.system(f"cat {filename}")
    subprocess.call(f"ls -la {filename}", shell=True)
""")

    return {
        "sql_injection": sql_injection_file,
        "hardcoded_secret": hardcoded_secret_file,
        "command_injection": command_injection_file
    }


@pytest.fixture
def mock_presidio_analyzer():
    """Mock Presidio analyzer for testing"""
    mock_analyzer = AsyncMock()

    # Mock analyze method
    async def mock_analyze(text, language="en", entities=None):
        # Return mock PII findings based on text content
        findings = []
        if "john.doe@example.com" in text:
            findings.append(MagicMock(
                entity_type="EMAIL_ADDRESS",
                start=text.find("john.doe@example.com"),
                end=text.find("john.doe@example.com") + len("john.doe@example.com"),
                score=0.95
            ))
        if "010-1234-5678" in text:
            findings.append(MagicMock(
                entity_type="PHONE_NUMBER",
                start=text.find("010-1234-5678"),
                end=text.find("010-1234-5678") + len("010-1234-5678"),
                score=0.90
            ))
        return findings

    mock_analyzer.analyze = mock_analyze
    return mock_analyzer


@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing"""
    mock_redis = MagicMock()

    # Mock redis methods
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)

    return mock_redis


@pytest.fixture
async def test_users(auth_service, rbac_manager):
    """Create test users for testing"""
    users = []

    # Create admin user
    admin_user = await auth_service.register_user(
        username="admin@test.com",
        password="AdminPass123!",
        email="admin@test.com",
        roles=["test_admin"]
    )
    users.append(admin_user)

    # Create regular user
    regular_user = await auth_service.register_user(
        username="user@test.com",
        password="UserPass123!",
        email="user@test.com",
        roles=["test_user"]
    )
    users.append(regular_user)

    return users


@pytest.fixture
def security_test_data():
    """Common test data for security tests"""
    return {
        "valid_jwt_payload": {
            "sub": "user123",
            "username": "testuser",
            "roles": ["user"],
            "permissions": ["documents:read"],
            "exp": 9999999999  # Far future
        },
        "invalid_jwt_payload": {
            "sub": "user123",
            "exp": 1  # Expired
        },
        "valid_permissions": [
            "documents:read",
            "documents:write",
            "system:admin",
            "audit:read"
        ],
        "test_ip_addresses": [
            "192.168.1.100",
            "10.0.0.50",
            "172.16.0.25"
        ]
    }


# Async test helpers
class AsyncTestCase:
    """Base class for async test cases"""

    @staticmethod
    async def async_test_wrapper(coro):
        """Wrapper for async tests"""
        return await coro


# Test database cleanup
@pytest.fixture(autouse=True)
async def cleanup_test_database():
    """Automatically clean up test database after each test"""
    yield

    # Clean up test database file
    if os.path.exists("./test_security.db"):
        os.remove("./test_security.db")