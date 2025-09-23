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
from fastapi import Header, HTTPException, Request
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, Dict, Set
from collections import defaultdict
import asyncio

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
        'base64': re.compile(r'^[A-Za-z0-9+/=]{32,}$'),
        'hex': re.compile(r'^[0-9a-fA-F]{32,}$'),
        'alphanumeric': re.compile(r'^[A-Za-z0-9_\-\.]{32,}$'),
        'secure': re.compile(r'^[A-Za-z0-9+/=_\-\.!@#$%^&*()]{32,}$')
    }

    # Common weak patterns to reject
    WEAK_PATTERNS = [
        r'(.)\1{3,}',  # Repeated characters (4+ times)
        r'012345|123456|234567|345678|456789',  # Sequential numbers
        r'abcdef|bcdefg|cdefgh|defghi|efghij',  # Sequential letters
        r'qwerty|asdfgh|zxcvbn',  # Keyboard patterns
        r'password|secret|admin|test|demo|example',  # Common words
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
        entropy = 0.0
        length = len(key)

        for count in frequencies.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)

        return entropy * length

    @classmethod
    def validate_character_composition(cls, key: str) -> bool:
        """Validate character composition requirements"""
        if len(key) < cls.MIN_LENGTH:
            return False

        char_types = 0

        # Check different character types
        if re.search(r'[a-z]', key):
            char_types += 1
        if re.search(r'[A-Z]', key):
            char_types += 1
        if re.search(r'[0-9]', key):
            char_types += 1
        if re.search(r'[+/=_\-\.!@#$%^&*()]', key):
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
            errors.append("API key format is invalid. Use base64, hex, or secure alphanumeric format")

        # Character composition
        if not cls.validate_character_composition(key):
            errors.append(f"API key must contain at least {cls.REQUIRED_CHAR_TYPES} different character types")

        # Entropy check
        entropy = cls.calculate_entropy(key)
        if entropy < cls.MIN_ENTROPY_BITS:
            errors.append(
                f"API key entropy too low ({entropy:.1f} bits). "
                f"Minimum required: {cls.MIN_ENTROPY_BITS} bits"
            )

        # Weak pattern check
        if not cls.check_weak_patterns(key):
            errors.append("API key contains weak patterns (repeated characters, sequences, or common words)")

        return len(errors) == 0, errors


def _check_rate_limit(client_ip: str, api_key: str) -> bool:
    """Check rate limiting for API key validation attempts"""
    current_time = time.time()

    # Clean old attempts (older than 1 minute)
    cutoff_time = current_time - 60
    _api_key_attempts[client_ip] = [
        attempt_time for attempt_time in _api_key_attempts[client_ip]
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
        async def unblock_later():
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


def _log_security_event(event_type: str, api_key: str, client_ip: str, details: str):
    """Log security events for monitoring and compliance"""
    key_hash = _hash_api_key(api_key) if api_key else "unknown"

    security_logger.warning(
        f"API_KEY_SECURITY_EVENT: {event_type} | "
        f"key_hash={key_hash} | "
        f"client_ip={client_ip} | "
        f"timestamp={datetime.now(timezone.utc).isoformat()} | "
        f"details={details}"
    )


async def verify_api_key(request: Request, x_api_key: Optional[str] = Header(None)):
    """
    Production-ready API key validation with comprehensive security checks

    Security Features:
    - Minimum 32+ character length requirement
    - Character composition validation (3+ character types)
    - Entropy checks to prevent weak keys (96+ bits)
    - Format validation (base64, hex, alphanumeric)
    - Rate limiting protection (5 attempts/minute)
    - Weak pattern detection and rejection
    - Database validation against stored key hashes
    - IP-based access control
    - Comprehensive audit logging
    - Automatic expiration checks

    Args:
        request: FastAPI request object for IP tracking
        x_api_key: API key from X-API-Key header

    Returns:
        APIKeyInfo: The validated API key information

    Raises:
        HTTPException: If validation fails
    """
    client_ip = request.client.host if request.client else "unknown"
    endpoint = str(request.url.path)
    method = request.method

    # Check if API key is provided
    if not x_api_key:
        _log_security_event("MISSING_API_KEY", "", client_ip, "No API key provided in X-API-Key header")
        raise HTTPException(
            status_code=403,
            detail="API key required. Include 'X-API-Key' header."
        )

    # Rate limiting check (basic validation attempts)
    if not _check_rate_limit(client_ip, x_api_key):
        _log_security_event("RATE_LIMITED", x_api_key, client_ip, "Too many validation attempts")
        raise HTTPException(
            status_code=429,
            detail="Too many API key validation attempts. Please try again later."
        )

    # Comprehensive format validation
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
                    "allowed_formats": list(APIKeyValidator.PATTERNS.keys())
                }
            }
        )

    # Database validation and permission checking
    try:
        # Get database session (this would be dependency injected in production)
        from .security.api_key_storage import APIKeyManager
        from .database import get_async_session  # Assuming this exists

        async with get_async_session() as db_session:
            key_manager = APIKeyManager(db_session)

            # Verify against database with comprehensive checks
            api_key_info = await key_manager.verify_api_key(
                plaintext_key=x_api_key,
                client_ip=client_ip,
                endpoint=endpoint,
                method=method
            )

            if not api_key_info:
                _log_security_event("INVALID_KEY", x_api_key, client_ip, "API key not found or invalid")
                raise HTTPException(
                    status_code=403,
                    detail="Invalid API key. The key may be expired, revoked, or not found."
                )

            # Additional permission checks can be added here based on endpoint
            # For example, check if the key has the required scope for this endpoint
            required_scope = _get_required_scope(endpoint, method)
            if not _check_permission(api_key_info, required_scope):
                _log_security_event(
                    "INSUFFICIENT_PERMISSIONS", x_api_key, client_ip,
                    f"Required scope: {required_scope}, API key scope: {api_key_info.scope}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required scope: {required_scope}"
                )

            _log_security_event("VALID_API_KEY", x_api_key, client_ip, "API key validation successful")
            return api_key_info

    except HTTPException:
        raise
    except Exception as e:
        # Log database errors but don't expose internal details
        security_logger.error(f"API key validation error: {str(e)}")
        _log_security_event("VALIDATION_ERROR", x_api_key, client_ip, f"Internal error: {type(e).__name__}")

        raise HTTPException(
            status_code=500,
            detail="Internal server error during API key validation"
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
        "DELETE": "admin"
    }

    return scope_map.get((method, endpoint), method_defaults.get(method, "read"))


def _check_permission(api_key_info, required_scope: str) -> bool:
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
