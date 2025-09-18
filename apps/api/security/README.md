# API Key Security Implementation

## Overview

This module provides production-ready API key security with comprehensive validation, secure storage, and audit logging. It replaces the previous weak validation (length >= 3) with enterprise-grade security controls.

## 🔒 Security Features

### Key Validation
- **Minimum Length**: 32+ characters required
- **Character Composition**: At least 3 different character types (uppercase, lowercase, numbers, special)
- **Entropy Validation**: Minimum 96 bits of Shannon entropy
- **Format Validation**: Support for base64, hex, alphanumeric, and secure mixed formats
- **Weak Pattern Detection**: Rejects repeated characters, sequences, keyboard patterns, and common words

### Rate Limiting & Abuse Protection
- **Request Rate Limiting**: 5 validation attempts per minute per IP
- **Temporary Blocking**: Invalid keys blocked for 5 minutes
- **Per-Key Rate Limits**: Configurable requests per hour per API key
- **IP-based Access Control**: Optional IP whitelist/CIDR range restrictions

### Secure Storage
- **Hash-Only Storage**: API keys are hashed with PBKDF2-SHA256, never stored in plaintext
- **Salt Generation**: Unique salt per key for rainbow table protection
- **Key Metadata**: Scope, permissions, expiration, and usage tracking
- **Secure Key IDs**: Public identifiers that don't expose key contents

### Audit & Compliance
- **Comprehensive Logging**: All security events logged with context
- **Audit Trail**: Complete record of key creation, usage, and revocation
- **Usage Analytics**: Request tracking for rate limiting and analytics
- **GDPR Compliance**: Secure key hashing and data retention policies

## 🚀 Quick Start

### 1. Generate API Keys

```python
from apps.api.security import generate_production_key, generate_custom_key

# Generate production key
prod_key = generate_production_key()
print(f"API Key: {prod_key.key}")
print(f"Entropy: {prod_key.entropy_bits} bits")

# Generate custom key
custom_key = generate_custom_key(
    length=40,
    format_type="base64",
    prefix="myapp",
    checksum=True
)
```

### 2. Validate API Keys

```python
from apps.api.deps import APIKeyValidator

# Validate format and strength
is_valid, errors = APIKeyValidator.comprehensive_validate(api_key)

if not is_valid:
    print(f"Validation errors: {errors}")
else:
    print("API key is valid!")
```

### 3. Database Integration

```python
from apps.api.security import APIKeyManager, APIKeyCreateRequest

async with get_async_session() as db:
    manager = APIKeyManager(db)

    # Create new API key
    request = APIKeyCreateRequest(
        name="My Application",
        scope="read",
        rate_limit=1000,
        expires_days=365
    )

    plaintext_key, key_info = await manager.create_api_key(
        request=request,
        created_by="admin",
        client_ip="192.168.1.100"
    )

    # Verify API key
    api_key_info = await manager.verify_api_key(
        plaintext_key=plaintext_key,
        client_ip="192.168.1.101",
        endpoint="/api/search",
        method="GET"
    )
```

## 📊 Security Validation Results

The implementation provides comprehensive security validation:

```python
# Example validation results
{
    "is_valid": True,
    "entropy_bits": 142.3,
    "format": "base64",
    "length": 45,
    "character_composition": True,
    "weak_patterns": False,
    "requirements_met": {
        "min_length": True,
        "min_entropy": True,
        "char_types": True,
        "format_valid": True,
        "no_weak_patterns": True
    }
}
```

## 🔧 Configuration

### Environment Variables

```bash
# Security Configuration
SECRET_KEY=your-256-bit-secret-key-here
API_KEY_MIN_LENGTH=32
API_KEY_MIN_ENTROPY=96
API_KEY_RATE_LIMIT=5

# Database (for key storage)
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0
```

### Security Requirements

| Requirement | Default | Production Recommendation |
|-------------|---------|---------------------------|
| Minimum Length | 32 chars | 40+ chars |
| Minimum Entropy | 96 bits | 128+ bits |
| Character Types | 3 types | 4 types (all categories) |
| Rate Limit | 100/hour | Adjust per use case |
| Expiration | None | 1 year maximum |

## 🛡️ Security Best Practices

### Key Generation
```python
# ✅ Good: Use secure generator
from apps.api.security import generate_production_key
key = generate_production_key()

# ❌ Bad: Manual generation
key = "my-simple-api-key-123"
```

### Key Storage
```python
# ✅ Good: Store only hash
key_hash = SecureAPIKeyGenerator.generate_secure_hash(plaintext_key)
store_in_database(key_hash)

# ❌ Bad: Store plaintext
store_in_database(plaintext_key)
```

### Key Validation
```python
# ✅ Good: Comprehensive validation
is_valid, errors = APIKeyValidator.comprehensive_validate(key)

# ❌ Bad: Simple length check
is_valid = len(key) >= 3
```

## 🔍 Monitoring & Alerts

### Security Events
All security events are logged with structured data:

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "event_type": "INVALID_API_KEY",
    "key_hash": "a1b2c3d4e5f6g7h8",
    "client_ip": "192.168.1.100",
    "details": "API key entropy too low (45.2 bits). Minimum required: 96 bits",
    "endpoint": "/api/search",
    "method": "GET"
}
```

### Metrics
Monitor these key metrics:
- Invalid key attempts per minute
- Rate limiting triggers
- Key usage patterns
- Failed authentication rates

### Alerting
Set up alerts for:
- Unusual authentication failure patterns
- Rate limiting threshold breaches
- Expired key usage attempts
- Security policy violations

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all security tests
pytest tests/security/test_api_key_validation.py -v

# Run performance benchmarks
pytest tests/security/test_api_key_validation.py::TestProductionReadiness -v

# Run with coverage
pytest tests/security/ --cov=apps.api.security --cov-report=html
```

### Test Coverage
- ✅ Format validation (all supported formats)
- ✅ Entropy calculation and validation
- ✅ Weak pattern detection
- ✅ Rate limiting functionality
- ✅ Database integration
- ✅ Audit logging
- ✅ Permission checking
- ✅ Performance benchmarks
- ✅ Concurrent access testing

## 🚧 Migration Guide

### From Previous Implementation

1. **Install Dependencies**:
   ```bash
   pip install cryptography sqlalchemy[asyncio] redis
   ```

2. **Run Database Migration**:
   ```bash
   alembic revision --autogenerate -m "Add API key security tables"
   alembic upgrade head
   ```

3. **Update Dependencies**:
   ```python
   # Old
   from apps.api.deps import verify_api_key

   # New (compatible)
   from apps.api.deps import verify_api_key  # Now returns APIKeyInfo
   ```

4. **Generate New Keys**:
   ```python
   # Replace weak keys with secure ones
   from apps.api.security import generate_production_key

   for old_key in get_old_keys():
       new_key = generate_production_key()
       migrate_key(old_key, new_key.key)
   ```

### Breaking Changes
- API key validation now requires 32+ character minimum (was 3)
- `verify_api_key()` now returns `APIKeyInfo` object (was string)
- Database schema changes require migration
- New environment variables required for production

## 📝 API Reference

### Core Classes

#### `APIKeyValidator`
Static validation methods for API key format and strength.

```python
@classmethod
def comprehensive_validate(cls, key: str) -> tuple[bool, list[str]]
```

#### `SecureAPIKeyGenerator`
Cryptographically secure API key generation.

```python
@classmethod
def generate_api_key(cls, config: APIKeyConfig) -> GeneratedAPIKey
```

#### `APIKeyManager`
Database operations for API key management.

```python
async def verify_api_key(self, plaintext_key: str, client_ip: str,
                        endpoint: str, method: str) -> Optional[APIKeyInfo]
```

### Configuration Models

#### `APIKeyConfig`
```python
@dataclass
class APIKeyConfig:
    length: int = 32
    format_type: str = "base64"  # base64, hex, alphanumeric, mixed
    include_special_chars: bool = False
    prefix: Optional[str] = None
    checksum: bool = True
```

#### `APIKeyInfo`
```python
@dataclass
class APIKeyInfo:
    key_id: str
    name: str
    scope: str  # read, write, admin
    permissions: List[str]
    allowed_ips: Optional[List[str]]
    rate_limit: int
    is_active: bool
    expires_at: Optional[datetime]
    total_requests: int
    failed_requests: int
```

## 🤝 Contributing

### Security Guidelines
1. All changes must pass security review
2. Add tests for new validation rules
3. Update documentation for breaking changes
4. Follow secure coding practices
5. Include performance impact analysis

### Code Review Checklist
- [ ] Comprehensive test coverage
- [ ] Security implications documented
- [ ] Performance benchmarks included
- [ ] Backward compatibility considered
- [ ] Documentation updated

## 📞 Support

For security-related issues:
1. Review the test suite for examples
2. Check logs for detailed error messages
3. Validate configuration with test tools
4. Report security vulnerabilities privately

## 📋 License

This security implementation is part of the DT-RAG project and follows the same license terms.