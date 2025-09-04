"""
Authentication & Authorization Middleware
RBAC/ABAC 권한 관리 미들웨어
"""

import logging
from typing import Callable, Dict, Set, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import jwt
import os

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """인증/권한 미들웨어"""
    
    def __init__(self, app):
        self.app = app
        self.secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
        self.algorithm = "HS256"
        
        # Define role-based permissions
        self.role_permissions: Dict[str, Set[str]] = {
            "admin": {
                "classify:read", "classify:write", 
                "search:read", "search:write",
                "taxonomy:read", "taxonomy:write", "taxonomy:rollback"
            },
            "operator": {
                "classify:read", "classify:write",
                "search:read", "search:write", 
                "taxonomy:read", "taxonomy:write"
            },
            "user": {
                "classify:read", "search:read", "taxonomy:read"
            },
            "readonly": {
                "search:read", "taxonomy:read"
            }
        }
        
        # Protected endpoints that require specific permissions
        self.protected_endpoints = {
            "POST /classify": "classify:write",
            "POST /search": "search:read", 
            "POST /taxonomy/{version}/rollback": "taxonomy:rollback",
            "PUT /taxonomy": "taxonomy:write",
            "DELETE /taxonomy": "taxonomy:write"
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """미들웨어 실행"""
        
        # Skip auth for public endpoints
        if self._is_public_endpoint(request):
            return await call_next(request)
        
        try:
            # Extract and validate token
            token = self._extract_token(request)
            if not token:
                return self._unauthorized_response("Missing authorization token")
            
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            roles = payload.get("roles", [])
            
            if not user_id:
                return self._unauthorized_response("Invalid token: missing user ID")
            
            # Check permissions for protected endpoints
            required_permission = self._get_required_permission(request)
            if required_permission:
                if not self._has_permission(roles, required_permission):
                    return self._forbidden_response(
                        f"Insufficient permissions for {required_permission}"
                    )
            
            # Attach user info to request
            request.state.user_id = user_id
            request.state.user_roles = roles
            request.state.user_permissions = self._get_user_permissions(roles)
            
            # Process request
            response = await call_next(request)
            return response
            
        except jwt.ExpiredSignatureError:
            return self._unauthorized_response("Token expired")
        except jwt.InvalidTokenError as e:
            return self._unauthorized_response(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "auth_error",
                        "code": 500, 
                        "message": "Authentication error occurred"
                    }
                }
            )
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """공개 엔드포인트 확인"""
        public_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
        return request.url.path in public_paths
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """요청에서 JWT 토큰 추출"""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None
    
    def _get_required_permission(self, request: Request) -> Optional[str]:
        """요청에 필요한 권한 확인"""
        method_path = f"{request.method} {request.url.path}"
        
        # Check exact matches first
        if method_path in self.protected_endpoints:
            return self.protected_endpoints[method_path]
        
        # Check pattern matches (for path parameters)
        for endpoint_pattern, permission in self.protected_endpoints.items():
            if self._matches_pattern(method_path, endpoint_pattern):
                return permission
        
        return None
    
    def _matches_pattern(self, actual_path: str, pattern: str) -> bool:
        """패턴 매칭 (간단한 구현)"""
        # Handle path parameters like {version}
        pattern_parts = pattern.split("/")
        actual_parts = actual_path.split("/")
        
        if len(pattern_parts) != len(actual_parts):
            return False
        
        for pattern_part, actual_part in zip(pattern_parts, actual_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue  # Path parameter, skip validation
            if pattern_part != actual_part:
                return False
        
        return True
    
    def _has_permission(self, user_roles: list, required_permission: str) -> bool:
        """사용자가 필요한 권한을 가지고 있는지 확인"""
        user_permissions = self._get_user_permissions(user_roles)
        return required_permission in user_permissions
    
    def _get_user_permissions(self, roles: list) -> Set[str]:
        """사용자 역할을 기반으로 권한 집합 반환"""
        permissions = set()
        for role in roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        return permissions
    
    def _unauthorized_response(self, message: str) -> JSONResponse:
        """401 Unauthorized 응답"""
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "type": "unauthorized",
                    "code": 401,
                    "message": message
                }
            }
        )
    
    def _forbidden_response(self, message: str) -> JSONResponse:
        """403 Forbidden 응답"""  
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "type": "forbidden",
                    "code": 403,
                    "message": message
                }
            }
        )