"""
API Key Management Router

Administrative endpoints for managing API keys with comprehensive security controls.
This router provides secure API key CRUD operations with proper authentication,
authorization, and audit logging.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from ...deps import verify_api_key
from ...security.api_key_storage import (
    APIKeyManager, APIKeyCreateRequest, APIKeyInfo
)
from ...database import get_async_session

router = APIRouter(prefix="/admin/api-keys", tags=["API Key Management"])
security = HTTPBearer()

# Request/Response Models
class CreateAPIKeyRequest(BaseModel):
    """Request model for creating a new API key"""
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the API key")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    scope: str = Field("read", description="Access scope: read, write, or admin")
    permissions: Optional[List[str]] = Field(None, description="Specific permissions list")
    allowed_ips: Optional[List[str]] = Field(None, description="Allowed IP addresses or CIDR ranges")
    rate_limit: int = Field(100, ge=1, le=10000, description="Requests per hour limit")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days (optional)")
    owner_id: Optional[str] = Field(None, description="Owner user ID")

    @validator('scope')
    def validate_scope(cls, v):
        if v not in ['read', 'write', 'admin']:
            raise ValueError('Scope must be read, write, or admin')
        return v

    @validator('allowed_ips')
    def validate_ips(cls, v):
        if v is None:
            return v

        import ipaddress
        for ip_or_range in v:
            try:
                if '/' in ip_or_range:
                    ipaddress.ip_network(ip_or_range, strict=False)
                else:
                    ipaddress.ip_address(ip_or_range)
            except ValueError:
                raise ValueError(f'Invalid IP address or range: {ip_or_range}')
        return v

class APIKeyResponse(BaseModel):
    """Response model for API key operations"""
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

class CreateAPIKeyResponse(BaseModel):
    """Response for API key creation (includes plaintext key)"""
    api_key: str = Field(..., description="The generated API key (only shown once)")
    key_info: APIKeyResponse

class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    allowed_ips: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None

class APIKeyUsageStats(BaseModel):
    """API key usage statistics"""
    key_id: str
    total_requests: int
    failed_requests: int
    requests_last_24h: int
    requests_last_7d: int
    most_used_endpoints: List[Dict[str, Any]]
    last_used_at: Optional[datetime]

# Helper function to check admin permissions
async def require_admin_key(current_key: APIKeyInfo = Depends(verify_api_key)):
    """Dependency to ensure the API key has admin scope"""
    if current_key.scope != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Your API key does not have sufficient permissions."
        )
    return current_key

@router.post("/", response_model=CreateAPIKeyResponse, status_code=201)
async def create_api_key(
    request: CreateAPIKeyRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Create a new API key with comprehensive security validation

    Requires admin-level API key for access. The generated key is only shown once
    and cannot be retrieved again for security reasons.
    """
    client_ip = http_request.client.host if http_request.client else "unknown"

    try:
        key_manager = APIKeyManager(db)

        # Convert Pydantic model to storage request
        create_request = APIKeyCreateRequest(
            name=request.name,
            description=request.description,
            owner_id=request.owner_id or current_key.key_id,  # Default to current key owner
            permissions=request.permissions or [],
            scope=request.scope,
            allowed_ips=request.allowed_ips,
            rate_limit=request.rate_limit,
            expires_days=request.expires_days
        )

        # Create the API key
        plaintext_key, key_info = await key_manager.create_api_key(
            request=create_request,
            created_by=current_key.key_id,
            client_ip=client_ip
        )

        # Convert to response model
        key_response = APIKeyResponse(
            key_id=key_info.key_id,
            name=key_info.name,
            description=key_info.description,
            scope=key_info.scope,
            permissions=key_info.permissions,
            allowed_ips=key_info.allowed_ips,
            rate_limit=key_info.rate_limit,
            is_active=key_info.is_active,
            expires_at=key_info.expires_at,
            created_at=key_info.created_at,
            last_used_at=key_info.last_used_at,
            total_requests=key_info.total_requests,
            failed_requests=key_info.failed_requests
        )

        return CreateAPIKeyResponse(
            api_key=plaintext_key,
            key_info=key_response
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create API key: {str(e)}"
        )

@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    active_only: bool = Query(True, description="Show only active keys"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of keys to return"),
    offset: int = Query(0, ge=0, description="Number of keys to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    List API keys with optional filtering

    Requires admin-level API key for access.
    """
    try:
        key_manager = APIKeyManager(db)

        # List keys with filtering
        keys = await key_manager.list_api_keys(
            owner_id=owner_id,
            active_only=active_only
        )

        # Apply pagination
        paginated_keys = keys[offset:offset + limit]

        # Convert to response models
        return [
            APIKeyResponse(
                key_id=key.key_id,
                name=key.name,
                description=key.description,
                scope=key.scope,
                permissions=key.permissions,
                allowed_ips=key.allowed_ips,
                rate_limit=key.rate_limit,
                is_active=key.is_active,
                expires_at=key.expires_at,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                total_requests=key.total_requests,
                failed_requests=key.failed_requests
            )
            for key in paginated_keys
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list API keys: {str(e)}"
        )

@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Get detailed information about a specific API key

    Requires admin-level API key for access.
    """
    try:
        key_manager = APIKeyManager(db)
        key_info = await key_manager.get_api_key_info(key_id)

        if not key_info:
            raise HTTPException(
                status_code=404,
                detail=f"API key not found: {key_id}"
            )

        return APIKeyResponse(
            key_id=key_info.key_id,
            name=key_info.name,
            description=key_info.description,
            scope=key_info.scope,
            permissions=key_info.permissions,
            allowed_ips=key_info.allowed_ips,
            rate_limit=key_info.rate_limit,
            is_active=key_info.is_active,
            expires_at=key_info.expires_at,
            created_at=key_info.created_at,
            last_used_at=key_info.last_used_at,
            total_requests=key_info.total_requests,
            failed_requests=key_info.failed_requests
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get API key: {str(e)}"
        )

@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    request: UpdateAPIKeyRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Update an existing API key

    Requires admin-level API key for access. Only specified fields will be updated.
    """
    try:
        key_manager = APIKeyManager(db)

        client_ip = http_request.client.host if http_request.client else "unknown"

        updated_key = await key_manager.update_api_key(
            key_id=key_id,
            updated_by=current_key.key_id,
            client_ip=client_ip,
            name=request.name,
            description=request.description,
            allowed_ips=request.allowed_ips,
            rate_limit=request.rate_limit,
            is_active=request.is_active
        )

        if not updated_key:
            raise HTTPException(
                status_code=404,
                detail=f"API key not found: {key_id}"
            )

        return APIKeyResponse(
            key_id=updated_key.key_id,
            name=updated_key.name,
            description=updated_key.description,
            scope=updated_key.scope,
            permissions=updated_key.permissions,
            allowed_ips=updated_key.allowed_ips,
            rate_limit=updated_key.rate_limit,
            is_active=updated_key.is_active,
            expires_at=updated_key.expires_at,
            created_at=updated_key.created_at,
            last_used_at=updated_key.last_used_at,
            total_requests=updated_key.total_requests,
            failed_requests=updated_key.failed_requests
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update API key: {str(e)}"
        )

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    reason: str = Body(..., description="Reason for revocation"),
    http_request: Request = None,
    db: AsyncSession = Depends(get_async_session),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Revoke an API key (mark as inactive)

    Requires admin-level API key for access. Revoked keys cannot be reactivated.
    """
    client_ip = http_request.client.host if http_request.client else "unknown"

    try:
        key_manager = APIKeyManager(db)

        success = await key_manager.revoke_api_key(
            key_id=key_id,
            revoked_by=current_key.key_id,
            client_ip=client_ip,
            reason=reason
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"API key not found: {key_id}"
            )

        return {"message": f"API key {key_id} has been revoked", "reason": reason}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke API key: {str(e)}"
        )

@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage(
    key_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_session),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Get usage statistics for an API key

    Requires admin-level API key for access.
    """
    try:
        key_manager = APIKeyManager(db)

        stats = await key_manager.get_api_key_usage_stats(key_id=key_id, days=days)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"API key not found: {key_id}"
            )

        return APIKeyUsageStats(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage statistics: {str(e)}"
        )

@router.post("/generate", response_model=Dict[str, str])
async def generate_sample_keys(
    key_type: str = Query("production", description="Type of key to generate"),
    count: int = Query(1, ge=1, le=10, description="Number of keys to generate"),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Generate sample API keys for testing

    Requires admin-level API key for access. These are not stored in the database.
    """
    try:
        from ...security.api_key_generator import (
            generate_production_key, generate_development_key, generate_admin_key,
            SecureAPIKeyGenerator, APIKeyConfig
        )

        generated_keys = {}

        for i in range(count):
            if key_type == "production":
                key_data = generate_production_key()
            elif key_type == "development":
                key_data = generate_development_key()
            elif key_type == "admin":
                key_data = generate_admin_key()
            else:
                # Custom generation
                config = APIKeyConfig(
                    length=32,
                    format_type="base64",
                    prefix=key_type,
                    checksum=True
                )
                key_data = SecureAPIKeyGenerator.generate_api_key(config)

            generated_keys[f"key_{i+1}"] = {
                "api_key": key_data.key,
                "format": key_data.format_type,
                "entropy_bits": key_data.entropy_bits,
                "created_at": key_data.created_at.isoformat(),
                "note": "This is a sample key - not stored in database"
            }

        return generated_keys

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate sample keys: {str(e)}"
        )

@router.post("/validate")
async def validate_api_key_format(
    api_key: str = Body(..., description="API key to validate"),
    current_key: APIKeyInfo = Depends(require_admin_key)
):
    """
    Validate the format and strength of an API key

    Requires admin-level API key for access. This only validates format, not database existence.
    """
    try:
        from ...deps import APIKeyValidator

        is_valid, errors = APIKeyValidator.comprehensive_validate(api_key)
        entropy = APIKeyValidator.calculate_entropy(api_key)
        key_format = APIKeyValidator.validate_format(api_key)

        return {
            "is_valid": is_valid,
            "errors": errors,
            "entropy_bits": entropy,
            "format": key_format,
            "length": len(api_key),
            "character_composition": APIKeyValidator.validate_character_composition(api_key),
            "weak_patterns": not APIKeyValidator.check_weak_patterns(api_key)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate API key: {str(e)}"
        )