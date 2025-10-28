"""
A팀 API 공통 의존성
- API Key 검증 (Production-Ready Security)
- Request ID 생성
- 공통 응답 필드
"""

import re
import hashlib
import time
import logging
import os
from fastapi import Header, HTTPException, Request, Depends
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, Dict, Set
from collections import defaultdict
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Configure security logging
security_logger = logging.getLogger("security")

# Rate limiting storage (in production, use Redis)
_api_key_attempts: Dict[str, list] = defaultdict(list)
_blocked_keys: Set[str] = set()


class APIKeyValidator:
    """Production-ready API key validation with comprehensive security checks"""

    # Minimum security requirements
    MIN_LENGTH = 32
    MIN_ENTROPY_BITS = 96  # Minimum entropy for secure keys

    # Rate limiting configuration
    MAX_ATTEMPTS_PER_MINUTE = 5
    BLOCK_DURATION = 300  # 5 minutes

    # Character composition requirements
    REQUIRED_CHAR_TYPES = 3  # At least 3 different character types

    # Regex patterns for validation
    PATTERNS = {
        "base64": re.compile(r"^[A-Za-z0-9+/=]{32,}$"),
        "hex": re.compile(r"^[0-9a-fA-F]{32,}$"),
        "alphanumeric": re.compile(r"^[A-Za-z0-9_\-\.]{32,}$"),
        "secure": re.compile(r"^[A-Za-z0-9+/=_\-\.!@#$%^&*()]{32,}$"),
    }

    # Common weak patterns to reject
    WEAK_PATTERNS = [
        r"(.)\1{3,}",  # Repeated characters (4+ times)
        r"012345|123456|234567|345678|456789",  # Sequential numbers
        r"abcdef|bcdefg|cdefgh|defghi|efghij",  # Sequential letters
        r"qwerty|asdfgh|zxcvbn",  # Keyboard patterns
        r"password|secret|admin|test|demo|example",  # Common words
    ]

    @classmethod
    def calculate_entropy(cls, key: str) -> float:
        """Calculate Shannon entropy of the API key"""
        if not key:
            return 0.0

        # Count character frequencies
        frequencies = {}
        for char in key:
            frequencies[char] = frequencies.get(char, 0) + 1

        # Calculate entropy
        import math

        entropy = 0.0
        length = len(key)

        for count in frequencies.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy * length

    @classmethod
    def validate_character_composition(cls, key: str) -> bool:
        """Validate character composition requirements"""
        if len(key) < cls.MIN_LENGTH:
            return False

        char_types = 0

        # Check different character types
        if re.search(r"[a-z]", key):
            char_types += 1
        if re.search(r"[A-Z]", key):
            char_types += 1
        if re.search(r"[0-9]", key):
            char_types += 1
        if re.search(r"[+/=_\-\.!@#$%^&*()]", key):
            char_types += 1

        return char_types >= cls.REQUIRED_CHAR_TYPES

    @classmethod
    def check_weak_patterns(cls, key: str) -> bool:
        """Check for weak patterns in the API key"""
        key_lower = key.lower()

        for pattern in cls.WEAK_PATTERNS:
            if re.search(pattern, key_lower):
                return False

        return True

    @classmethod
    def validate_format(cls, key: str) -> str:
        """Validate and determine API key format"""
        if not key:
            return "empty"

        # Check different format patterns
        for format_name, pattern in cls.PATTERNS.items():
            if pattern.match(key):
                return format_name

        return "invalid"

    @classmethod
    def comprehensive_validate(cls, key: str) -> tuple[bool, list[str]]:
        """Perform comprehensive API key validation"""
        errors = []

        # Basic checks
        if not key:
            errors.append("API key is required")
            return False, errors

        if len(key) < cls.MIN_LENGTH:
            errors.append(f"API key must be at least {cls.MIN_LENGTH} characters long")

        # Format validation
        key_format = cls.validate_format(key)
        if key_format == "invalid":
            errors.append(
                "API key format is invalid. Use base64, hex, or secure alphanumeric format"
            )

        # Character composition
        if not cls.validate_character_composition(key):
            errors.append(
                f"API key must contain at least {cls.REQUIRED_CHAR_TYPES} different character types"
            )

        # Entropy check
        entropy = cls.calculate_entropy(key)
        if entropy < cls.MIN_ENTROPY_BITS:
            errors.append(
                f"API key entropy too low ({entropy:.1f} bits). "
                f"Minimum required: {cls.MIN_ENTROPY_BITS} bits"
            )

        # Weak pattern check
        if not cls.check_weak_patterns(key):
            errors.append(
                "API key contains weak patterns (repeated characters, sequences, or common words)"
            )

        return len(errors) == 0, errors


def _check_rate_limit(client_ip: str, api_key: str) -> bool:
    """Check rate limiting for API key validation attempts"""
    current_time = time.time()

    # Clean old attempts (older than 1 minute)
    cutoff_time = current_time - 60
    _api_key_attempts[client_ip] = [
        attempt_time
        for attempt_time in _api_key_attempts[client_ip]
        if attempt_time > cutoff_time
    ]

    # Check if IP is blocked
    if api_key in _blocked_keys:
        return False

    # Check attempt count
    if len(_api_key_attempts[client_ip]) >= APIKeyValidator.MAX_ATTEMPTS_PER_MINUTE:
        # Block the key temporarily
        _blocked_keys.add(api_key)

        # Schedule unblocking (in production, use Redis with TTL)
        # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
        async def unblock_later() -> None:
            await asyncio.sleep(APIKeyValidator.BLOCK_DURATION)
            _blocked_keys.discard(api_key)

        asyncio.create_task(unblock_later())
        return False

    # Record this attempt
    _api_key_attempts[client_ip].append(current_time)
    return True


def _hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage and logging"""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def _log_security_event(event_type: str, api_key: str, client_ip: str, details: str) -> None:
    """Log security events for monitoring and compliance"""
    key_hash = _hash_api_key(api_key) if api_key else "unknown"

    security_logger.warning(
        f"API_KEY_SECURITY_EVENT: {event_type} | "
        f"key_hash={key_hash} | "
        f"client_ip={client_ip} | "
        f"timestamp={datetime.now(timezone.utc).isoformat()} | "
        f"details={details}"
    )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(lambda: None),  # Will be injected by FastAPI
) -> APIKeyInfo:
    """
    Production-ready API key validation with comprehensive security checks

    Security Features:
    - Database-backed API key verification
    - Minimum 32+ character length requirement
    - Character composition validation (3+ character types)
    - Entropy checks to prevent weak keys (96+ bits)
    - Format validation (base64, hex, alphanumeric)
    - Rate limiting protection (5 attempts/minute)
    - Weak pattern detection and rejection
    - IP-based access control
    - Comprehensive audit logging
    - Automatic expiration checks

    Args:
        request: FastAPI request object for IP tracking
        x_api_key: API key from X-API-Key header
        db: Database session (injected)

    Returns:
        APIKeyInfo: The validated API key information

    Raises:
        HTTPException: If validation fails
    """
    client_ip = request.client.host if request.client else "unknown"

    # Check if API key is provided
    if not x_api_key:
        _log_security_event(
            "MISSING_API_KEY", "", client_ip, "No API key provided in X-API-Key header"
        )
        raise HTTPException(
            status_code=403, detail="API key required. Include 'X-API-Key' header."
        )

    # Development mode: Allow test API keys (env variable controlled)
    # SECURITY: Test keys are ONLY allowed in development/testing environments
    ENABLE_TEST_KEYS = os.getenv("ENABLE_TEST_API_KEYS", "false").lower() == "true"
    CURRENT_ENV = os.getenv("ENVIRONMENT", "production").lower()

    # Production safety check: NEVER allow test keys in production
    if ENABLE_TEST_KEYS and CURRENT_ENV == "production":
        security_logger.error(
            "SECURITY_VIOLATION: ENABLE_TEST_API_KEYS=true in production environment. "
            "This is a critical security misconfiguration. Test keys are DISABLED."
        )
        ENABLE_TEST_KEYS = False

    # Test keys only defined in non-production environments
    ALLOWED_TEST_KEYS = {}
    if CURRENT_ENV in ["development", "testing", "staging"]:
        ALLOWED_TEST_KEYS = {
            "7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y": {
                "scope": "write",
                "name": "Test Frontend Key",
                "key_id": "test_key_001",
            },
            "admin_X4RzsowY0qgfwqqwbo1UnP25zQjOoOxX5FUXmDHR9sPc8HT7-a570": {
                "scope": "write",
                "name": "Legacy Frontend Key",
                "key_id": "test_key_002",
            },
            "test_admin_9Kx7pLmN4qR2vW8bZhYdF3jC6tGsE5uA1nX0iO": {
                "scope": "admin",
                "name": "Test Admin Key",
                "key_id": "test_admin_001",
            },
        }

    if ENABLE_TEST_KEYS and x_api_key in ALLOWED_TEST_KEYS:
        _log_security_event(
            "VALID_API_KEY",
            x_api_key,
            client_ip,
            f"Test API key accepted ({CURRENT_ENV} mode)",
        )
        from .security.api_key_storage import APIKeyInfo

        key_info = ALLOWED_TEST_KEYS[x_api_key]
        return APIKeyInfo(
            key_id=key_info["key_id"],
            name=key_info["name"],
            description=f"Development test key ({CURRENT_ENV})",
            scope=key_info["scope"],
            permissions=["*"],
            allowed_ips=None,
            rate_limit=1000,
            is_active=True,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
            total_requests=0,
            failed_requests=0,
        )

    # Rate limiting check (basic validation attempts)
    if not _check_rate_limit(client_ip, x_api_key):
        _log_security_event(
            "RATE_LIMITED", x_api_key, client_ip, "Too many validation attempts"
        )
        raise HTTPException(
            status_code=429,
            detail="Too many API key validation attempts. Please try again later.",
        )

    # Get database session
    if db is None:
        from .database import async_session

        async with async_session() as session:
            db = session

    # Database validation
    from .security.api_key_storage import APIKeyManager, APIKeyInfo

    try:
        key_manager = APIKeyManager(db)

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: Fix attr-defined (type annotation)
        # Verify API key against database
        key_info: Optional[APIKeyInfo] = await key_manager.verify_api_key(
            plaintext_key=x_api_key,
            client_ip=client_ip,
            endpoint=request.url.path,
            method=request.method,
        )

        if key_info:
            _log_security_event(
                "VALID_API_KEY",
                x_api_key,
                client_ip,
                f"Database verification successful: {key_info.name}",
            )
            return key_info

        # If not found in database, perform comprehensive format validation for better error message
        is_valid, errors = APIKeyValidator.comprehensive_validate(x_api_key)

        if not is_valid:
            error_details = "; ".join(errors)
            _log_security_event("INVALID_FORMAT", x_api_key, client_ip, error_details)

            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Invalid API key format",
                    "details": errors,
                    "requirements": {
                        "min_length": APIKeyValidator.MIN_LENGTH,
                        "min_entropy_bits": APIKeyValidator.MIN_ENTROPY_BITS,
                        "required_char_types": APIKeyValidator.REQUIRED_CHAR_TYPES,
                        "allowed_formats": list(APIKeyValidator.PATTERNS.keys()),
                    },
                },
            )

        # Format is valid but key not found in database
        _log_security_event(
            "INVALID_KEY", x_api_key, client_ip, "API key not found in database"
        )
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. The key may be expired, revoked, or not found.",
        )

    except HTTPException:
        raise
    except Exception as e:
        _log_security_event(
            "DB_ERROR", x_api_key, client_ip, f"Database error: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="API key validation failed due to internal error"
        )


def _get_required_scope(endpoint: str, method: str) -> str:
    """Determine required scope based on endpoint and method"""
    # Define scope requirements for different endpoints
    scope_map = {
        ("GET", "/health"): "read",
        ("GET", "/taxonomy"): "read",
        ("POST", "/taxonomy"): "write",
        ("PUT", "/taxonomy"): "write",
        ("DELETE", "/taxonomy"): "admin",
        ("GET", "/search"): "read",
        ("POST", "/search"): "read",
        ("POST", "/classify"): "write",
        ("GET", "/metrics"): "admin",
    }

    # Default to write for POST/PUT/PATCH, read for GET, admin for DELETE
    method_defaults = {
        "GET": "read",
        "POST": "write",
        "PUT": "write",
        "PATCH": "write",
        "DELETE": "admin",
    }

    return scope_map.get((method, endpoint), method_defaults.get(method, "read"))


def _check_permission(api_key_info: Any, required_scope: str) -> bool:
    """Check if API key has required permissions"""
    # Define scope hierarchy: admin > write > read
    scope_hierarchy = {"read": 0, "write": 1, "admin": 2}

    key_level = scope_hierarchy.get(api_key_info.scope, 0)
    required_level = scope_hierarchy.get(required_scope, 0)

    return key_level >= required_level


def generate_request_id() -> str:
    """요청 ID 생성 (Bridge Pack 스펙 준수)"""
    return str(uuid4())


def get_current_timestamp() -> str:
    """ISO 8601 타임스탬프 생성"""
    return datetime.now(timezone.utc).isoformat()


def get_taxonomy_version() -> str:
    """현재 taxonomy 버전 (Bridge Pack 스펙)"""
    return "1.8.1"
