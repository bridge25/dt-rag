"""
Security Middleware for DT-RAG v1.8.1
FastAPI middleware that implements comprehensive security controls
Integrates with the security framework for request/response processing
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse

from ..core.security_manager import SecurityManager, SecurityException, SecurityContext
# Future implementations - not yet available
from ..audit.audit_logger import EventType, SeverityLevel  # type: ignore[import-not-found]  # TODO: Implement audit logger module

logger = logging.getLogger(__name__)


class SecurityHeaders:
    """Security headers configuration"""

    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        """Get default security headers"""
        return {
            # OWASP A05:2021 – Security Misconfiguration
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            # Feature Policy / Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            # Cache control for sensitive endpoints
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware implementing OWASP controls
    """

    def __init__(
        self, app: Any, security_manager: SecurityManager, config: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(app)
        self.security_manager = security_manager
        self.config = config or {}

        # Middleware configuration
        self.enable_auth = self.config.get("enable_auth", True)
        self.enable_rate_limiting = self.config.get("enable_rate_limiting", True)
        self.enable_input_validation = self.config.get("enable_input_validation", True)
        self.enable_output_sanitization = self.config.get(
            "enable_output_sanitization", True
        )
        self.enable_security_headers = self.config.get("enable_security_headers", True)

        # Exempt endpoints (no authentication required)
        self.exempt_endpoints = set(
            self.config.get(
                "exempt_endpoints",
                [
                    "/",
                    "/health",
                    "/healthz",
                    "/docs",
                    "/redoc",
                    "/openapi.json",
                    "/auth/login",
                    "/auth/register",
                ],
            )
        )

        # Rate limiting configuration
        self.rate_limit_requests = self.config.get("rate_limit_requests", 100)
        self.rate_limit_window = self.config.get("rate_limit_window", 3600)  # 1 hour

        # Request size limits
        self.max_request_size = self.config.get(
            "max_request_size", 10 * 1024 * 1024
        )  # 10MB
        self.max_json_fields = self.config.get("max_json_fields", 1000)

        # IP filtering
        self.blocked_ips = set(self.config.get("blocked_ips", []))
        self.allowed_ips = set(self.config.get("allowed_ips", []))  # Empty = allow all

        # Request tracking
        self._request_counts: Dict[str, List[float]] = {}

        logger.info("SecurityMiddleware initialized with comprehensive OWASP controls")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Main middleware dispatch method"""

        start_time = time.time()
        request_id = f"req_{int(start_time * 1000000)}"
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        try:
            # Ensure security context state attribute is always available for downstream
            # dependencies even before authentication occurs. This prevents
            # AttributeError when dependencies expect the attribute and allows
            # them to detect unauthenticated requests via a None value.
            request.state.security_context = None

            # 1. Pre-request security checks
            await self._pre_request_checks(request, client_ip, request_id)

            # 2. Authentication and authorization (if enabled)
            security_context = None
            if self.enable_auth and not self._is_exempt_endpoint(request.url.path):
                security_context = await self._authenticate_request(
                    request, client_ip, user_agent
                )
                # Store security context on request state for downstream dependencies
                request.state.security_context = security_context

            # 3. Input validation and sanitization
            if self.enable_input_validation:
                await self._validate_and_sanitize_input(
                    request, security_context, request_id
                )

            # 4. Process request
            response = await call_next(request)

            # 5. Output sanitization
            if self.enable_output_sanitization and security_context:
                response = await self._sanitize_response(
                    response, security_context, request_id
                )

            # 6. Add security headers
            if self.enable_security_headers:
                self._add_security_headers(response)

            # 7. Log successful request
            await self._log_request_success(
                request, security_context, response, start_time, request_id
            )

            return response

        except SecurityException as e:
            # Handle security-specific exceptions
            await self._log_security_violation(request, str(e), client_ip, request_id)
            return self._create_error_response(
                status.HTTP_403_FORBIDDEN, "Access denied", request_id
            )

        except HTTPException as e:
            # Handle HTTP exceptions
            await self._log_http_error(request, e, client_ip, request_id)
            return self._create_error_response(e.status_code, e.detail, request_id)

        except Exception as e:
            # Handle unexpected exceptions
            await self._log_unexpected_error(request, str(e), client_ip, request_id)
            return self._create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal server error",
                request_id,
            )

    async def _pre_request_checks(
        self, request: Request, client_ip: str, request_id: str
    ):
        """Pre-request security checks"""

        # 1. IP filtering
        if self.blocked_ips and client_ip in self.blocked_ips:
            await self.security_manager.audit_logger.log_event(
                {
                    "event_type": EventType.SECURITY_VIOLATION,
                    "severity": SeverityLevel.HIGH,
                    "details": {"reason": "blocked_ip", "ip": client_ip},
                    "request_id": request_id,
                }
            )
            raise SecurityException("IP address blocked")

        if self.allowed_ips and client_ip not in self.allowed_ips:
            await self.security_manager.audit_logger.log_event(
                {
                    "event_type": EventType.SECURITY_VIOLATION,
                    "severity": SeverityLevel.MEDIUM,
                    "details": {"reason": "ip_not_allowed", "ip": client_ip},
                    "request_id": request_id,
                }
            )
            raise SecurityException("IP address not allowed")

        # 2. Rate limiting
        if self.enable_rate_limiting:
            if not await self._check_rate_limit(client_ip):
                await self.security_manager.audit_logger.log_event(
                    {
                        "event_type": EventType.RATE_LIMIT_EXCEEDED,
                        "severity": SeverityLevel.MEDIUM,
                        "details": {"ip": client_ip},
                        "request_id": request_id,
                    }
                )
                raise SecurityException("Rate limit exceeded")

        # 3. Request size validation
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            await self.security_manager.audit_logger.log_event(
                {
                    "event_type": EventType.SECURITY_VIOLATION,
                    "severity": SeverityLevel.HIGH,
                    "details": {
                        "reason": "request_too_large",
                        "size": content_length,
                        "max_size": self.max_request_size,
                    },
                    "request_id": request_id,
                }
            )
            raise SecurityException("Request too large")

        # 4. Suspicious user agent detection
        user_agent = request.headers.get("user-agent", "")
        if self._is_suspicious_user_agent(user_agent):
            await self.security_manager.audit_logger.log_event(
                {
                    "event_type": EventType.SECURITY_VIOLATION,
                    "severity": SeverityLevel.LOW,
                    "details": {
                        "reason": "suspicious_user_agent",
                        "user_agent": user_agent,
                    },
                    "request_id": request_id,
                }
            )

    async def _authenticate_request(
        self, request: Request, client_ip: str, user_agent: str
    ) -> SecurityContext:
        """Authenticate and authorize request"""

        # Extract token from Authorization header
        authorization = request.headers.get("authorization")
        if not authorization:
            raise SecurityException("Missing authorization header")

        # Extract bearer token
        if not authorization.startswith("Bearer "):
            raise SecurityException("Invalid authorization format")

        token = authorization[7:]  # Remove "Bearer " prefix

        # Authenticate using security manager
        operation = f"{request.method} {request.url.path}"
        security_context = await self.security_manager.authenticate_request(
            token, client_ip, user_agent, operation
        )

        # Authorization will be checked per-endpoint basis
        return security_context

    async def _validate_and_sanitize_input(
        self,
        request: Request,
        security_context: Optional[SecurityContext],
        request_id: str,
    ):
        """Validate and sanitize request input"""

        try:
            # Check content type
            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                # Get request body
                body = await request.body()
                if body:
                    try:
                        json_data = json.loads(body)

                        # Check JSON complexity
                        if self._count_json_fields(json_data) > self.max_json_fields:
                            raise SecurityException("JSON too complex")

                        # Sanitize JSON data
                        if security_context:
                            sanitized_data = (
                                await self.security_manager.sanitize_request_data(
                                    json_data, security_context
                                )
                            )
                            # Store sanitized data for use by endpoint
                            request.state.sanitized_data = sanitized_data

                    except json.JSONDecodeError:
                        raise SecurityException("Invalid JSON format")

            # Validate query parameters
            query_params = dict(request.query_params)
            if query_params and security_context:
                sanitized_params = await self.security_manager.sanitize_request_data(
                    query_params, security_context
                )
                request.state.sanitized_params = sanitized_params

        except SecurityException:
            raise
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise SecurityException("Input validation failed")

    async def _sanitize_response(
        self, response: Response, security_context: SecurityContext, request_id: str
    ) -> Response:
        """Sanitize response data"""

        try:
            # Only sanitize JSON responses
            if response.headers.get("content-type", "").startswith("application/json"):
                body = response.body
                if body:
                    try:
                        response_data = json.loads(body)
                        sanitized_data = (
                            await self.security_manager.sanitize_response_data(
                                response_data, security_context
                            )
                        )

                        # Update response body
                        sanitized_body = json.dumps(sanitized_data).encode()
                        response.body = sanitized_body
                        response.headers["content-length"] = str(len(sanitized_body))

                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If we can't parse the JSON, leave it as-is
                        pass

            return response

        except Exception as e:
            logger.error(f"Response sanitization failed: {e}")
            return response

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""

        security_headers = SecurityHeaders.get_default_headers()

        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value

        # Add custom headers
        response.headers["X-Request-ID"] = getattr(response, "request_id", "unknown")
        response.headers["X-Security-Version"] = "1.8.1"

    async def _check_rate_limit(self, identifier: str) -> bool:
        """Check rate limiting for IP or user"""

        current_time = time.time()
        window_start = current_time - self.rate_limit_window

        if identifier not in self._request_counts:
            self._request_counts[identifier] = []

        # Clean old requests
        self._request_counts[identifier] = [
            req_time
            for req_time in self._request_counts[identifier]
            if req_time > window_start
        ]

        # Check limit
        if len(self._request_counts[identifier]) >= self.rate_limit_requests:
            return False

        # Add current request
        self._request_counts[identifier].append(current_time)
        return True

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""

        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    def _is_exempt_endpoint(self, path: str) -> bool:
        """Check if endpoint is exempt from authentication"""

        # Exact match
        if path in self.exempt_endpoints:
            return True

        # Pattern matching for endpoints with parameters
        for exempt_path in self.exempt_endpoints:
            if exempt_path.endswith("*") and path.startswith(exempt_path[:-1]):
                return True

        return False

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""

        suspicious_patterns = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "zap",
            "burp",
            "w3af",
            "acunetix",
            "nessus",
            "python-requests",
            "curl",
            "wget",
            "bot",
            "crawler",
            "spider",
            "scraper",
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)

    def _count_json_fields(self, data: Any, depth: int = 0) -> int:
        """Count fields in JSON data recursively"""

        if depth > 10:  # Prevent deep recursion
            return 1000  # Return high count to trigger limit

        count = 0

        if isinstance(data, dict):
            count = len(data)
            for value in data.values():
                count += self._count_json_fields(value, depth + 1)
        elif isinstance(data, list):
            for item in data:
                count += self._count_json_fields(item, depth + 1)
        else:
            count = 1

        return count

    def _create_error_response(
        self, status_code: int, message: str, request_id: str
    ) -> JSONResponse:
        """Create standardized error response"""

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": status_code,
                    "message": message,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
            headers=SecurityHeaders.get_default_headers(),
        )

    # Logging methods

    async def _log_request_success(
        self,
        request: Request,
        security_context: Optional[SecurityContext],
        response: Response,
        start_time: float,
        request_id: str,
    ):
        """Log successful request"""

        duration = time.time() - start_time

        event_data = {
            "event_type": EventType.DOCUMENT_ACCESSED,
            "severity": SeverityLevel.INFO,
            "details": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "user_id": security_context.user_id if security_context else None,
                "ip_address": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
            },
            "request_id": request_id,
        }

        await self.security_manager.audit_logger.log_event(event_data)

    async def _log_security_violation(
        self, request: Request, error_message: str, client_ip: str, request_id: str
    ):
        """Log security violation"""

        event_data = {
            "event_type": EventType.SECURITY_VIOLATION,
            "severity": SeverityLevel.HIGH,
            "details": {
                "method": request.method,
                "path": request.url.path,
                "error": error_message,
                "ip_address": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
            },
            "request_id": request_id,
        }

        await self.security_manager.audit_logger.log_event(event_data)

    async def _log_http_error(
        self,
        request: Request,
        exception: HTTPException,
        client_ip: str,
        request_id: str,
    ):
        """Log HTTP error"""

        severity = (
            SeverityLevel.WARNING if exception.status_code < 500 else SeverityLevel.HIGH
        )

        event_data = {
            "event_type": EventType.AUTHORIZATION_FAILED,
            "severity": severity,
            "details": {
                "method": request.method,
                "path": request.url.path,
                "status_code": exception.status_code,
                "error": exception.detail,
                "ip_address": client_ip,
            },
            "request_id": request_id,
        }

        await self.security_manager.audit_logger.log_event(event_data)

    async def _log_unexpected_error(
        self, request: Request, error_message: str, client_ip: str, request_id: str
    ):
        """Log unexpected error"""

        event_data = {
            "event_type": EventType.AUTHENTICATION_ERROR,
            "severity": SeverityLevel.CRITICAL,
            "details": {
                "method": request.method,
                "path": request.url.path,
                "error": error_message,
                "ip_address": client_ip,
            },
            "request_id": request_id,
        }

        await self.security_manager.audit_logger.log_event(event_data)


class SecurityDependency:
    """
    FastAPI dependency for endpoint-level security
    """

    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager

    async def __call__(
        self, request: Request, required_permission: str = None, resource: str = None
    ) -> SecurityContext:
        """Security dependency for endpoints"""

        # Get security context from middleware
        security_context = getattr(request.state, "security_context", None)
        if not security_context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Check specific permission if required
        if required_permission:
            authorized = await self.security_manager.authorize_operation(
                security_context,
                required_permission,
                resource,
                getattr(request.state, "sanitized_data", None),
            )

            if not authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )

        return security_context


def create_security_dependency(security_manager: SecurityManager) -> SecurityDependency:
    """Create security dependency instance"""
    return SecurityDependency(security_manager)


class CSRFProtection:
    """CSRF protection middleware"""

    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key

    async def __call__(self, request: Request, call_next: Any) -> Response:
        """CSRF protection middleware"""

        # Skip CSRF for GET, HEAD, OPTIONS
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # Check CSRF token for state-changing operations
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF token missing"},
            )

        # Validate CSRF token (simplified)
        if not self._validate_csrf_token(csrf_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Invalid CSRF token"},
            )

        return await call_next(request)

    def _validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        # In production, implement proper CSRF token validation
        # This is a simplified version
        return len(token) >= 32


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware for security monitoring"""

    def __init__(self, app: Any, security_manager: SecurityManager) -> None:
        super().__init__(app)
        self.security_manager = security_manager

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Log all requests for security monitoring"""

        start_time = time.time()

        # Log request start
        await self.security_manager.security_monitor.process_security_event(
            {
                "type": "request_started",
                "method": request.method,
                "path": request.url.path,
                "ip_address": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        response = await call_next(request)

        duration = time.time() - start_time

        # Log request completion
        await self.security_manager.security_monitor.process_security_event(
            {
                "type": "request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "ip_address": self._get_client_ip(request),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return getattr(request.client, "host", "unknown")


class SecurityMiddlewareError(Exception):
    """Security middleware exception"""

    pass
