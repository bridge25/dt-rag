"""
Secure API Key Storage and Management

This module provides database models and management functions for secure API key storage,
including proper hashing, rate limiting, and audit logging.
"""
# @CODE:MYPY-CONSOLIDATION-002 | Phase 1: SQLAlchemy Column Type Casting

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, cast, Any
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    Index,
    select,
    delete,
    and_,
    func,
    desc,
)
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Key identification
    key_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    key_hash: Mapped[str] = mapped_column(String(256), index=True)

    # Metadata
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Ownership and permissions
    owner_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    permissions: Mapped[str] = mapped_column(Text, default="[]")
    scope: Mapped[str] = mapped_column(String(50), default="read")

    # Security settings
    allowed_ips: Mapped[Optional[str]] = mapped_column(Text)
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)

    # Status and lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Usage tracking
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Indexes for performance
    __table_args__ = (
        Index("idx_key_hash_active", key_hash, is_active),
        Index("idx_owner_active", owner_id, is_active),
        Index("idx_expires_at", expires_at),
        Index("idx_last_used", last_used_at),
    )


class APIKeyUsage(Base):
    """
    API Key usage tracking for rate limiting and analytics

    Tracks individual requests for detailed monitoring and rate limiting.
    """

    __tablename__ = "api_key_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Key reference
    key_id: Mapped[str] = mapped_column(String(32), index=True)

    # Request details
    endpoint: Mapped[str] = mapped_column(String(200))
    method: Mapped[str] = mapped_column(String(10))
    client_ip: Mapped[str] = mapped_column(String(45), index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    # Response details
    status_code: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Additional metadata
    request_metadata: Mapped[Optional[str]] = mapped_column(Text)

    # Indexes for performance
    __table_args__ = (
        Index("idx_key_timestamp", key_id, timestamp),
        Index("idx_client_ip_timestamp", client_ip, timestamp),
        Index("idx_status_timestamp", status_code, timestamp),
    )


class APIKeyAuditLog(Base):
    """
    Audit log for API key operations

    Tracks all administrative operations on API keys for compliance and security.
    """

    __tablename__ = "api_key_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Operation details
    operation: Mapped[str] = mapped_column(String(50), index=True)
    key_id: Mapped[str] = mapped_column(String(32), index=True)

    # Who performed the operation
    performed_by: Mapped[Optional[str]] = mapped_column(String(50))
    client_ip: Mapped[str] = mapped_column(String(45))

    # What changed
    old_values: Mapped[Optional[str]] = mapped_column(Text)
    new_values: Mapped[Optional[str]] = mapped_column(Text)

    # Context
    reason: Mapped[Optional[str]] = mapped_column(String(200))

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_operation_timestamp", operation, timestamp),
        Index("idx_key_operation", key_id, operation),
        Index("idx_performed_by", performed_by, timestamp),
    )


@dataclass
class APIKeyCreateRequest:
    """Request to create a new API key"""

    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    permissions: Optional[List[str]] = None
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

    async def create_api_key(
        self, request: APIKeyCreateRequest, created_by: str, client_ip: str
    ) -> tuple[str, APIKeyInfo]:
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
            length=40, format_type="base64", prefix=request.scope, checksum=True
        )

        # Calculate expiration
        expires_at = None
        if request.expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=request.expires_days
            )

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
            allowed_ips=(
                json.dumps(request.allowed_ips) if request.allowed_ips else None
            ),
            rate_limit=request.rate_limit,
            expires_at=expires_at,
        )

        self.db.add(api_key)
        await self.db.flush()

        # Log creation
        await self._log_operation(
            operation="CREATE",
            key_id=key_id,
            performed_by=created_by,
            client_ip=client_ip,
            new_values=json.dumps(
                {
                    "name": request.name,
                    "scope": request.scope,
                    "rate_limit": request.rate_limit,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                }
            ),
            reason="API key created",
        )

        await self.db.commit()

        logger.info(
            f"Created API key: key_id={key_id}, name={request.name}, scope={request.scope}"
        )

        # Return plaintext key and info
        api_key_info = await self.get_api_key_info(key_id)
        if api_key_info is None:
            raise RuntimeError(f"Failed to retrieve created API key info: {key_id}")
        return generated_key.key, api_key_info

    async def verify_api_key(
        self, plaintext_key: str, client_ip: str, endpoint: str, method: str
    ) -> Optional[APIKeyInfo]:
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
        stmt = select(APIKey).where(and_(APIKey.key_id == key_id, APIKey.is_active))
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
            await self._log_usage(
                key_id, endpoint, method, client_ip, 401, None, "expired"
            )
            return None

        # Check IP restrictions
        if api_key.allowed_ips:
            allowed_ips = json.loads(api_key.allowed_ips)
            if client_ip not in allowed_ips and not self._ip_in_ranges(
                client_ip, allowed_ips
            ):
                await self._log_usage(
                    key_id, endpoint, method, client_ip, 403, None, "ip_restricted"
                )
                return None

        # Check rate limiting
        if not await self._check_rate_limit(key_id, api_key.rate_limit):
            await self._log_usage(
                key_id, endpoint, method, client_ip, 429, None, "rate_limited"
            )
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
            allowed_ips=(
                json.loads(api_key.allowed_ips) if api_key.allowed_ips else None
            ),
            rate_limit=api_key.rate_limit,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            total_requests=api_key.total_requests,
            failed_requests=api_key.failed_requests,
        )

    async def list_api_keys(
        self, owner_id: Optional[str] = None, active_only: bool = True
    ) -> List[APIKeyInfo]:
        """List API keys with optional filtering"""
        from sqlalchemy.sql.elements import ColumnElement
        conditions: List[ColumnElement[bool]] = []

        if active_only:
            conditions.append(APIKey.is_active == True)  # noqa: E712

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
                failed_requests=key.failed_requests,
            )
            for key in api_keys
        ]

    async def revoke_api_key(
        self, key_id: str, revoked_by: str, client_ip: str, reason: Optional[str] = None
    ) -> bool:
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
            reason=reason or "API key revoked",
        )

        await self.db.commit()

        logger.info(f"Revoked API key: key_id={key_id}, revoked_by={revoked_by}")
        return True

    async def update_api_key(
        self,
        key_id: str,
        updated_by: str,
        client_ip: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        allowed_ips: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[APIKeyInfo]:
        """
        Update an existing API key's metadata and settings

        Args:
            key_id: The API key ID to update
            updated_by: User ID performing the update
            client_ip: Client IP address
            name: New name (optional)
            description: New description (optional)
            allowed_ips: New allowed IPs list (optional)
            rate_limit: New rate limit (optional)
            is_active: New active status (optional)

        Returns:
            Updated APIKeyInfo if successful, None if key not found

        Note:
            Scope and permissions cannot be updated for security reasons.
            To change scope/permissions, revoke and create a new key.
        """
        stmt = select(APIKey).where(APIKey.key_id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            logger.warning(f"Update failed: API key not found: key_id={key_id}")
            return None

        # Store old values for audit log
        old_values = {
            "name": api_key.name,
            "description": api_key.description,
            "allowed_ips": api_key.allowed_ips,
            "rate_limit": api_key.rate_limit,
            "is_active": api_key.is_active,
        }

        # Update fields if provided
        updated_fields = []
        if name is not None:
            api_key.name = name
            updated_fields.append("name")

        if description is not None:
            api_key.description = description
            updated_fields.append("description")

        if allowed_ips is not None:
            api_key.allowed_ips = json.dumps(allowed_ips)
            updated_fields.append("allowed_ips")

        if rate_limit is not None:
            if rate_limit < 1 or rate_limit > 10000:
                logger.warning(f"Update failed: Invalid rate_limit={rate_limit}")
                return None
            api_key.rate_limit = rate_limit
            updated_fields.append("rate_limit")

        if is_active is not None:
            api_key.is_active = is_active
            updated_fields.append("is_active")

        # Update timestamp
        api_key.updated_at = datetime.now(timezone.utc)

        # Store new values for audit log
        new_values = {
            "name": api_key.name,
            "description": api_key.description,
            "allowed_ips": api_key.allowed_ips,
            "rate_limit": api_key.rate_limit,
            "is_active": api_key.is_active,
        }

        # Log the update operation
        await self._log_operation(
            operation="UPDATE",
            key_id=key_id,
            performed_by=updated_by,
            client_ip=client_ip,
            old_values=json.dumps(old_values),
            new_values=json.dumps(new_values),
            reason=f"API key updated: {', '.join(updated_fields)}",
        )

        await self.db.commit()

        logger.info(
            f"Updated API key: key_id={key_id}, fields={updated_fields}, updated_by={updated_by}"
        )

        # Return updated info
        return await self.get_api_key_info(key_id)

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
            allowed_ips=(
                json.loads(api_key.allowed_ips) if api_key.allowed_ips else None
            ),
            rate_limit=api_key.rate_limit,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            total_requests=api_key.total_requests,
            failed_requests=api_key.failed_requests,
        )

    async def _check_rate_limit(self, key_id: str, rate_limit: int) -> bool:
        """Check if API key is within rate limits"""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        stmt = select(APIKeyUsage).where(
            and_(APIKeyUsage.key_id == key_id, APIKeyUsage.timestamp > one_hour_ago)
        )
        result = await self.db.execute(stmt)
        usage_count = len(result.scalars().all())

        return usage_count < rate_limit

    async def _log_usage(
        self,
        key_id: str,
        endpoint: str,
        method: str,
        client_ip: str,
        status_code: int,
        response_time_ms: Optional[int],
        request_metadata: Optional[str] = None,
    ) -> None:
        """Log API key usage"""
        usage = APIKeyUsage(
            key_id=key_id,
            endpoint=endpoint,
            method=method,
            client_ip=client_ip,
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_metadata=request_metadata,
        )
        self.db.add(usage)

    async def _log_operation(
        self,
        operation: str,
        key_id: str,
        performed_by: str,
        client_ip: str,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log administrative operations"""
        audit_log = APIKeyAuditLog(
            operation=operation,
            key_id=key_id,
            performed_by=performed_by,
            client_ip=client_ip,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
        )
        self.db.add(audit_log)

    def _ip_in_ranges(self, client_ip: str, allowed_ranges: List[str]) -> bool:
        """Check if client IP is in allowed ranges (simplified implementation)"""
        import ipaddress

        try:
            client = ipaddress.ip_address(client_ip)
            for range_str in allowed_ranges:
                try:
                    if "/" in range_str:
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

    async def get_api_key_usage_stats(
        self, key_id: str, days: int = 7
    ) -> Optional[dict]:
        """
        Get usage statistics for an API key

        Args:
            key_id: API key identifier
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with usage statistics or None if key not found
        """
        key_info = await self.get_api_key_info(key_id)
        if not key_info:
            return None

        now = datetime.now(timezone.utc)

        total_stmt = select(
            func.count(APIKeyUsage.id).label("total_requests"),
            func.count(func.nullif(APIKeyUsage.status_code >= 400, False)).label(
                "failed_requests"
            ),
            func.max(APIKeyUsage.timestamp).label("last_used_at"),
        ).where(APIKeyUsage.key_id == key_id)

        total_result = await self.db.execute(total_stmt)
        total_row = total_result.first()

        total_requests = total_row.total_requests if total_row else 0
        failed_requests = (
            total_row.failed_requests if total_row and total_row.failed_requests else 0
        )
        last_used_at = total_row.last_used_at if total_row else None

        cutoff_24h = now - timedelta(hours=24)
        requests_24h_stmt = select(func.count(APIKeyUsage.id)).where(
            and_(APIKeyUsage.key_id == key_id, APIKeyUsage.timestamp >= cutoff_24h)
        )
        requests_24h_result = await self.db.execute(requests_24h_stmt)
        requests_last_24h = requests_24h_result.scalar() or 0

        cutoff_7d = now - timedelta(days=days)
        requests_7d_stmt = select(func.count(APIKeyUsage.id)).where(
            and_(APIKeyUsage.key_id == key_id, APIKeyUsage.timestamp >= cutoff_7d)
        )
        requests_7d_result = await self.db.execute(requests_7d_stmt)
        requests_last_7d = requests_7d_result.scalar() or 0

        endpoints_stmt = (
            select(
                APIKeyUsage.endpoint,
                APIKeyUsage.method,
                func.count(APIKeyUsage.id).label("request_count"),
            )
            .where(
                and_(APIKeyUsage.key_id == key_id, APIKeyUsage.timestamp >= cutoff_7d)
            )
            .group_by(APIKeyUsage.endpoint, APIKeyUsage.method)
            .order_by(desc("request_count"))
            .limit(10)
        )

        endpoints_result = await self.db.execute(endpoints_stmt)
        most_used_endpoints = [
            {"endpoint": row.endpoint, "method": row.method, "count": row.request_count}
            for row in endpoints_result
        ]

        return {
            "key_id": key_id,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "requests_last_24h": requests_last_24h,
            "requests_last_7d": requests_last_7d,
            "most_used_endpoints": most_used_endpoints,
            "last_used_at": last_used_at,
        }

    async def cleanup_expired_usage_logs(self, days_to_keep: int = 30) -> int:
        """Clean up old usage logs to prevent database bloat"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        stmt = delete(APIKeyUsage).where(APIKeyUsage.timestamp < cutoff_date)
        result: CursorResult[Any] = await self.db.execute(stmt)
        await self.db.commit()

        row_count = result.rowcount or 0
        logger.info(f"Cleaned up {row_count} old usage log entries")
        return row_count
