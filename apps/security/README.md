# Dynamic Taxonomy RAG Security Framework v1.8.1

A comprehensive enterprise-grade security and compliance system implementing OWASP Top 10 protections, GDPR/CCPA/PIPA compliance, and advanced threat detection for the Dynamic Taxonomy RAG system.

## 🔒 Security Features

### Core Security Components
- **Authentication & Authorization**: JWT-based authentication with RBAC
- **PII Detection & Protection**: Advanced PII scanning with Presidio integration
- **Audit Logging**: Immutable audit trails with integrity verification
- **Vulnerability Scanning**: OWASP Top 10 compliance with automated scanning
- **Security Monitoring**: Real-time threat detection with ML-based anomaly detection
- **Compliance Management**: GDPR/CCPA/PIPA data subject rights management
- **Data Encryption**: AES-256-GCM encryption at rest and in transit
- **Security Middleware**: Comprehensive request/response security controls

### Regulatory Compliance
- **GDPR**: Article 30 processing activities, data subject rights, consent management
- **CCPA**: Consumer privacy rights, data sales restrictions, opt-out mechanisms
- **Korean PIPA**: Personal information protection, consent requirements, breach notification

## 🚀 Quick Start

### 1. Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Initialize security database tables
python -m apps.security.auth.auth_service --init-db
python -m apps.security.audit.audit_logger --init-db
python -m apps.security.compliance.compliance_manager --init-db
```

### 2. Configuration

```python
from apps.security.config.security_config import SecurityLevel, load_security_config

# Load production configuration
config = load_security_config(security_level=SecurityLevel.PRODUCTION)

# Or create custom configuration
config = SecurityConfig(
    security_level=SecurityLevel.PRODUCTION,
    auth=AuthConfig(jwt_secret="your-secret-key"),
    enable_mfa=True,
    enable_encryption=True
)
```

### 3. FastAPI Integration

```python
from fastapi import FastAPI
from apps.security.integration import SecurityFramework

app = FastAPI()
security = SecurityFramework()

# Initialize security framework
await security.initialize(SecurityLevel.PRODUCTION)

# Setup FastAPI app with security
security.setup_fastapi_app(app)

# Your API endpoints are now protected
@app.get("/api/documents")
async def get_documents():
    return {"documents": []}
```

## 📊 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Framework                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Auth     │  │    Audit    │  │ Compliance  │        │
│  │  Service    │  │   Logger    │  │  Manager    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Monitoring  │  │  Scanning   │  │    Crypto   │        │
│  │   System    │  │   Engine    │  │   Service   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Security Middleware                    │   │
│  │  Rate Limiting | Input Validation | Output Encoding │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Authentication & Authorization

### User Authentication

```python
from apps.security.auth.auth_service import AuthService

auth_service = AuthService()

# Register new user
user = await auth_service.register_user(
    username="user@example.com",
    password="SecurePassword123!",
    roles=["viewer"]
)

# Authenticate user
token, user = await auth_service.authenticate_user(
    username="user@example.com",
    password="SecurePassword123!"
)
```

### Role-Based Access Control

```python
from apps.security.auth.auth_service import RBACManager

rbac = RBACManager()

# Check permissions
has_access = await rbac.check_permission(
    user_id=user.id,
    permission="documents:read",
    resource="sensitive_documents"
)
```

## 🕵️ PII Detection & Privacy

### Automatic PII Detection

```python
from apps.security.compliance.pii_detector import PIIDetector

pii_detector = PIIDetector()

# Scan text for PII
findings = await pii_detector.scan_text(
    "John Doe's SSN is 123-45-6789 and email is john@example.com"
)

# Automatically mask PII
masked_data = await pii_detector.mask_pii_data({
    "user_info": "Contact John at john@example.com",
    "sensitive": "SSN: 123-45-6789"
})
```

### GDPR Data Subject Rights

```python
from apps.security.compliance.compliance_manager import ComplianceManager

compliance = ComplianceManager()

# Handle data subject access request
request = await compliance.submit_data_subject_request(
    request_type=DataSubjectRightType.ACCESS,
    data_subject_id="user123",
    email="user@example.com"
)

# Process the request
response = await compliance.process_data_subject_request(request.id)
```

## 📋 Audit Logging

### Security Event Logging

```python
from apps.security.audit.audit_logger import AuditLogger, SecurityEvent

audit_logger = AuditLogger()

# Log security event
await audit_logger.log_event(SecurityEvent(
    event_type="user_authentication",
    user_id="user123",
    ip_address="192.168.1.100",
    details={"status": "success", "method": "jwt"},
    risk_level=RiskLevel.LOW
))

# Verify audit trail integrity
integrity_report = await audit_logger.verify_integrity()
```

## 🔍 Vulnerability Scanning

### Automated Security Scanning

```python
from apps.security.scanning.vulnerability_scanner import VulnerabilityScanner

scanner = VulnerabilityScanner()

# Scan codebase for vulnerabilities
result = await scanner.scan_codebase(
    target_path="/path/to/code",
    scan_types=[ScanType.BANDIT, ScanType.SAFETY, ScanType.SEMGREP]
)

# Generate security report
report = await scanner.get_vulnerability_report(result.scan_id)
```

## 📊 Security Monitoring

### Real-time Threat Detection

```python
from apps.security.monitoring.security_monitor import SecurityMonitor

monitor = SecurityMonitor()

# Process security events for anomaly detection
await monitor.process_security_event({
    "timestamp": datetime.utcnow(),
    "event_type": "login_attempt",
    "user_id": "user123",
    "ip_address": "192.168.1.100",
    "features": {
        "login_hour": 14,
        "failed_attempts": 0,
        "new_device": False
    }
})
```

## ⚙️ Configuration

### Security Levels

The system supports multiple security levels with pre-configured settings:

- **DEVELOPMENT**: Relaxed security for development environments
- **TESTING**: Moderate security for testing environments
- **STAGING**: Production-like security for staging
- **PRODUCTION**: Maximum security for production deployments

### Environment Variables

```bash
# Core settings
SECURITY_LEVEL=production
JWT_SECRET=your-super-secret-jwt-key
DATABASE_URL=postgresql://user:pass@localhost/dtrag

# Feature toggles
DISABLE_AUTH=false
DISABLE_RATE_LIMITING=false
PII_CONFIDENCE_THRESHOLD=0.8
RATE_LIMIT_REQUESTS=100

# Security settings
ENABLE_MFA=true
ENABLE_AUDIT_ENCRYPTION=true
ENABLE_CSRF_PROTECTION=true
```

## 🛡️ Security Best Practices

### Input Validation
- All user inputs are validated and sanitized
- SQL injection protection through parameterized queries
- XSS prevention with output encoding
- File upload restrictions and scanning

### Authentication Security
- JWT tokens with secure expiration
- Password complexity requirements
- Account lockout after failed attempts
- Multi-factor authentication support

### Data Protection
- AES-256-GCM encryption for sensitive data
- Secure key management and rotation
- TLS 1.3 for data in transit
- PII automatic detection and masking

### Access Control
- Principle of least privilege
- Role-based access control (RBAC)
- Resource-level permissions
- Session management and timeout

## 📈 Monitoring & Alerting

### Security Metrics
- Authentication success/failure rates
- PII detection statistics
- Vulnerability scan results
- Access control violations
- Anomaly detection alerts

### Incident Response
- Automated incident creation
- Severity-based escalation
- Investigation workflow
- Forensic data collection

## 🚨 Security Alerts

The system automatically generates alerts for:
- Multiple failed login attempts
- Unusual access patterns
- PII data exposure
- Security vulnerabilities detected
- Compliance violations
- System security incidents

## 📚 API Reference

### Authentication Endpoints
- `POST /api/security/auth/login` - User authentication
- `POST /api/security/auth/register` - User registration
- `POST /api/security/auth/refresh` - Token refresh
- `POST /api/security/auth/logout` - User logout

### Compliance Endpoints
- `POST /api/security/pii/detect` - PII detection
- `POST /api/security/compliance/data-subject-request` - GDPR requests
- `GET /api/security/compliance/consent/{user_id}` - Consent status
- `POST /api/security/compliance/breach-report` - Breach reporting

### Monitoring Endpoints
- `GET /api/security/monitoring/incidents` - Security incidents
- `GET /api/security/monitoring/alerts` - Security alerts
- `GET /api/security/monitoring/metrics` - Security metrics
- `POST /api/security/monitoring/report-incident` - Report incident

### Scanning Endpoints
- `POST /api/security/scanning/scan` - Initiate vulnerability scan
- `GET /api/security/scanning/results/{scan_id}` - Scan results
- `GET /api/security/scanning/report/{scan_id}` - Security report

## 🔧 Development

### Running Tests

```bash
# Run all security tests
pytest apps/security/tests/

# Run specific test categories
pytest apps/security/tests/test_auth.py
pytest apps/security/tests/test_pii.py
pytest apps/security/tests/test_compliance.py
```

### Configuration Validation

```bash
# Validate security configuration
python -m apps.security.config.security_config validate config.json

# Create default configuration
python -m apps.security.config.security_config create-config production.json production
```

## 🆘 Troubleshooting

### Common Issues

1. **JWT Token Validation Fails**
   - Check JWT secret configuration
   - Verify token expiration settings
   - Ensure clock synchronization

2. **PII Detection False Positives**
   - Adjust confidence threshold
   - Review custom patterns
   - Check language settings

3. **Audit Log Integrity Errors**
   - Verify database connectivity
   - Check hash chain continuity
   - Review signing key configuration

4. **Compliance Report Errors**
   - Validate data subject identifiers
   - Check consent records
   - Review processing activities

## 📞 Support

For security issues or questions:
- Review the security documentation
- Check the troubleshooting guide
- Create an issue in the project repository
- Contact the security team for critical issues

---

**⚠️ Security Notice**: This security framework implements industry best practices but should be regularly reviewed and updated. Conduct regular security assessments and keep all dependencies updated.