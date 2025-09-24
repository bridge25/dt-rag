"""
Secure API Key Storage and Management

This module provides database models and management functions for secure API key storage,
including proper hashing, rate limiting, and audit logging.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, Index,
    select, update, delete, and_, or_
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from dataclasses import dataclass
import json

from .api_key_generator import SecureAPIKeyGenerator

# Configure logging
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class APIKey(Base):
    """
    API Key database model with security features

    Security Features:
    - Stores hashed keys, never plaintext
    - Tracks usage and rate limiting
    - Audit logging for all operations
    - Automatic expiration support
    - IP-based access control
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)

    # Key identification
    key_id = Column(String(32), unique=True, nullable=False, index=True)  # Public identifier
    key_hash = Column(String(256), nullable=False, index=True)  # Hashed key for verification

    # Metadata
    name = Column(String(100), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)

    # Ownership and permissions
    owner_id = Column(String(50), nullable=True, index=True)  # User/service owner
    permissions = Column(Text, nullable=False, default="[]")  # JSON array of permissions
    scope = Column(String(50), nullable=False, default="read")  # read, write, admin

    # Security settings
    allowed_ips = Column(Text, nullable=True)  # JSON array of allowed IP addresses/ranges
    rate_limit = Column(Integer, nullable=False, default=100)  # Requests per hour

    # Status and lifecycle
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Usage tracking
    total_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)

    # Indexes for performance
    __table_args__ = (
        Index('idx_key_hash_active', key_hash, is_active),
        Index('idx_owner_active', owner_id, is_active),
        Index('idx_expires_at', expires_at),
        Index('idx_last_used', last_used_at),
    )

class APIKeyUsage(Base):
    """
    API Key usage tracking for rate limiting and analytics

    Tracks individual requests for detailed monitoring and rate limiting.
    """
    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True, index=True)

    # Key reference
    key_id = Column(String(32), nullable=False, index=True)

    # Request details
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    client_ip = Column(String(45), nullable=False, index=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)

    # Response details
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Additional metadata
    metadata = Column(Text, nullable=True)  # JSON for additional data

    # Indexes for performance
    __table_args__ = (
        Index('idx_key_timestamp', key_id, timestamp),
        Index('idx_client_ip_timestamp', client_ip, timestamp),
        Index('idx_status_timestamp', status_code, timestamp),
    )

class APIKeyAuditLog(Base):
    """
    Audit log for API key operations

    Tracks all administrative operations on API keys for compliance and security.
    """
    __tablename__ = "api_key_audit_log"

    id = Column(Integer, primary_key=True, index=True)

    # Operation details
    operation = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, USE, BLOCK
    key_id = Column(String(32), nullable=False, index=True)

    # Who performed the operation
    performed_by = Column(String(50), nullable=True)  # User ID or system
    client_ip = Column(String(45), nullable=False)

    # What changed
    old_values = Column(Text, nullable=True)  # JSON of previous values
    new_values = Column(Text, nullable=True)  # JSON of new values

    # Context
    reason = Column(String(200), nullable=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_operation_timestamp', operation, timestamp),
        Index('idx_key_operation', key_id, operation),
        Index('idx_performed_by', performed_by, timestamp),
    )

@dataclass
class APIKeyCreateRequest:
    """Request to create a new API key"""
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    permissions: List[str] = None
    scope: str = "read"
    allowed_ips: Optional[List[str]] = None
    rate_limit: int = 100
    expires_days: Optional[int] = None

@dataclass
class APIKeyInfo:
    """API key information (without sensitive data)"""
    key_id: str
    name: str
    description: Optional[str]
    scope: str
    permissions: List[str]
    allowed_ips: Optional[List[str]]
    rate_limit: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    total_requests: int
    failed_requests: int

class APIKeyManager:
    """
    Secure API key management with comprehensive security features
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_api_key(self, request: APIKeyCreateRequest, created_by: str, client_ip: str) -> tuple[str, APIKeyInfo]:
        """
        Create a new API key with security validation

        Args:
            request: API key creation request
            created_by: User ID creating the key
            client_ip: Client IP address

        Returns:
            tuple: (plaintext_key, api_key_info)
        """
        from .api_key_generator import generate_custom_key

        # Generate secure API key
        generated_key = generate_custom_key(
            length=40,
            format_type="base64",
            prefix=request.scope,
            checksum=True
        )

        # Calculate expiration
        expires_at = None
        if request.expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_days)

        # Generate unique key ID
        key_id = hashlib.md5(generated_key.key.encode()).hexdigest()[:16]

        # Create database record
        api_key = APIKey(
            key_id=key_id,
            key_hash=generated_key.key_hash,
            name=request.name,
            description=request.description,
            owner_id=request.owner_id,
            permissions=json.dumps(request.permissions or []),
            scope=request.scope,
            allowed_ips=json.dumps(request.allowed_ips) if request.allowed_ips else None,
            rate_limit=request.rate_limit,
            expires_at=expires_at
        )

        self.db.add(api_key)
        await self.db.flush()

        # Log creation
        await self._log_operation(
            operation="CREATE",
            key_id=key_id,
            performed_by=created_by,
            client_ip=client_ip,
            new_values=json.dumps({
                "name": request.name,
                "scope": request.scope,
                "rate_limit": request.rate_limit,
                "expires_at": expires_at.isoformat() if expires_at else None
            }),
            reason="API key created"
        )

        await self.db.commit()

        logger.info(f"Created API key: key_id={key_id}, name={request.name}, scope={request.scope}")

        # Return plaintext key and info
        api_key_info = await self.get_api_key_info(key_id)
        return generated_key.key, api_key_info

    async def verify_api_key(self, plaintext_key: str, client_ip: str, endpoint: str, method: str) -> Optional[APIKeyInfo]:
        """
        Verify an API key and check permissions

        Args:
            plaintext_key: The plaintext API key
            client_ip: Client IP address
            endpoint: API endpoint being accessed
            method: HTTP method

        Returns:
            APIKeyInfo if valid, None if invalid
        """
        # Extract key ID from plaintext key for faster lookup
        key_id = hashlib.md5(plaintext_key.encode()).hexdigest()[:16]

        # Get API key from database
        stmt = select(APIKey).where(
            and_(
                APIKey.key_id == key_id,
                APIKey.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            await self._log_usage(key_id, endpoint, method, client_ip, 401, None)
            return None

        # Verify key hash
        if not SecureAPIKeyGenerator.verify_key_hash(plaintext_key, api_key.key_hash):
            await self._log_usage(key_id, endpoint, method, client_ip, 401, None)
            api_key.failed_requests += 1
            await self.db.commit()
            return None

        # Check expiration
        if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
            await self._log_usage(key_id, endpoint, method, client_ip, 401, None, "expired")
            return None

        # Check IP restrictions
        if api_key.allowed_ips:
            allowed_ips = json.loads(api_key.allowed_ips)
            if client_ip not in allowed_ips and not self._ip_in_ranges(client_ip, allowed_ips):
                await self._log_usage(key_id, endpoint, method, client_ip, 403, None, "ip_restricted")
                return None

        # Check rate limiting
        if not await self._check_rate_limit(key_id, api_key.rate_limit):
            await self._log_usage(key_id, endpoint, method, client_ip, 429, None, "rate_limited")
            return None

        # Update usage statistics
        api_key.total_requests += 1
        api_key.last_used_at = datetime.now(timezone.utc)
        await self._log_usage(key_id, endpoint, method, client_ip, 200, None)

        await self.db.commit()

        return APIKeyInfo(
            key_id=api_key.key_id,
            name=api_key.name,
            description=api_key.description,
            scope=api_key.scope,
            permissions=json.loads(api_key.permissions),
            allowed_ips=json.loads(api_key.allowed_ips) if api_key.allowed_ips else None,
            rate_limit=api_key.rate_limit,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            total_requests=api_key.total_requests,
            failed_requests=api_key.failed_requests
        )

    async def list_api_keys(self, owner_id: Optional[str] = None, active_only: bool = True) -> List[APIKeyInfo]:
        """List API keys with optional filtering"""
        conditions = []

        if active_only:
            conditions.append(APIKey.is_active == True)

        if owner_id:
            conditions.append(APIKey.owner_id == owner_id)

        stmt = select(APIKey)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(APIKey.created_at.desc())

        result = await self.db.execute(stmt)
        api_keys = result.scalars().all()

        return [
            APIKeyInfo(
                key_id=key.key_id,
                name=key.name,
                description=key.description,
                scope=key.scope,
                permissions=json.loads(key.permissions),
                allowed_ips=json.loads(key.allowed_ips) if key.allowed_ips else None,
                rate_limit=key.rate_limit,
                is_active=key.is_active,
                expires_at=key.expires_at,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                total_requests=key.total_requests,
                failed_requests=key.failed_requests
            )
            for key in api_keys
        ]

    async def revoke_api_key(self, key_id: str, revoked_by: str, client_ip: str, reason: str = None) -> bool:
        """Revoke an API key"""
        stmt = select(APIKey).where(APIKey.key_id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        old_values = {"is_active": api_key.is_active}

        api_key.is_active = False
        api_key.updated_at = datetime.now(timezone.utc)

        await self._log_operation(
            operation="REVOKE",
            key_id=key_id,
            performed_by=revoked_by,
            client_ip=client_ip,
            old_values=json.dumps(old_values),
            new_values=json.dumps({"is_active": False}),
            reason=reason or "API key revoked"
        )

        await self.db.commit()

        logger.info(f"Revoked API key: key_id={key_id}, revoked_by={revoked_by}")
        return True

    async def get_api_key_info(self, key_id: str) -> Optional[APIKeyInfo]:
        """Get API key information by ID"""
        stmt = select(APIKey).where(APIKey.key_id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        return APIKeyInfo(
            key_id=api_key.key_id,
            name=api_key.name,
            description=api_key.description,
            scope=api_key.scope,
            permissions=json.loads(api_key.permissions),
            allowed_ips=json.loads(api_key.allowed_ips) if api_key.allowed_ips else None,
            rate_limit=api_key.rate_limit,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            total_requests=api_key.total_requests,
            failed_requests=api_key.failed_requests
        )

    async def _check_rate_limit(self, key_id: str, rate_limit: int) -> bool:
        """Check if API key is within rate limits"""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        stmt = select(APIKeyUsage).where(
            and_(
                APIKeyUsage.key_id == key_id,
                APIKeyUsage.timestamp > one_hour_ago
            )
        )
        result = await self.db.execute(stmt)
        usage_count = len(result.scalars().all())

        return usage_count < rate_limit

    async def _log_usage(self, key_id: str, endpoint: str, method: str, client_ip: str,
                        status_code: int, response_time_ms: Optional[int], metadata: str = None):
        """Log API key usage"""
        usage = APIKeyUsage(
            key_id=key_id,
            endpoint=endpoint,
            method=method,
            client_ip=client_ip,
            status_code=status_code,
            response_time_ms=response_time_ms,
            metadata=metadata
        )
        self.db.add(usage)

    async def _log_operation(self, operation: str, key_id: str, performed_by: str, client_ip: str,
                           old_values: str = None, new_values: str = None, reason: str = None):
        """Log administrative operations"""
        audit_log = APIKeyAuditLog(
            operation=operation,
            key_id=key_id,
            performed_by=performed_by,
            client_ip=client_ip,
            old_values=old_values,
            new_values=new_values,
            reason=reason
        )
        self.db.add(audit_log)

    def _ip_in_ranges(self, client_ip: str, allowed_ranges: List[str]) -> bool:
        """Check if client IP is in allowed ranges (simplified implementation)"""
        import ipaddress

        try:
            client = ipaddress.ip_address(client_ip)
            for range_str in allowed_ranges:
                try:
                    if '/' in range_str:
                        network = ipaddress.ip_network(range_str, strict=False)
                        if client in network:
                            return True
                    else:
                        allowed = ipaddress.ip_address(range_str)
                        if client == allowed:
                            return True
                except ValueError:
                    continue
        except ValueError:
            return False

        return False

    async def cleanup_expired_usage_logs(self, days_to_keep: int = 30):
        """Clean up old usage logs to prevent database bloat"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        stmt = delete(APIKeyUsage).where(APIKeyUsage.timestamp < cutoff_date)
        result = await self.db.execute(stmt)
        await self.db.commit()

        logger.info(f"Cleaned up {result.rowcount} old usage log entries")
        return result.rowcount