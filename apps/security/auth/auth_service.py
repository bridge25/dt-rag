"""
Authentication and Authorization Service for DT-RAG v1.8.1
Implements JWT-based authentication with RBAC
OWASP A07:2021 – Identification and Authentication Failures compliance
"""

import jwt
import hashlib
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import asyncio
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions"""
    READ_DOCUMENTS = "read_documents"
    WRITE_DOCUMENTS = "write_documents"
    DELETE_DOCUMENTS = "delete_documents"
    SEARCH_DOCUMENTS = "search_documents"
    CLASSIFY_DOCUMENTS = "classify_documents"
    MANAGE_TAXONOMY = "manage_taxonomy"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_USERS = "manage_users"
    ACCESS_PII = "access_pii"
    VIEW_PII = "view_pii"
    EXPORT_DATA = "export_data"
    ADMIN_SYSTEM = "admin_system"

class Role(Enum):
    """System roles"""
    ANONYMOUS = "anonymous"
    VIEWER = "viewer"
    EDITOR = "editor"
    CLASSIFIER = "classifier"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class User:
    """User model"""
    user_id: str
    username: str
    email: str
    password_hash: str
    roles: Set[Role]
    permissions: Set[Permission]
    clearance_level: str
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_valid: bool = True
    last_activity: datetime = None

class AuthService:
    """
    Authentication service with JWT tokens and secure session management
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # JWT configuration
        self.jwt_secret = self.config.get('jwt_secret', self._generate_jwt_secret())
        self.jwt_algorithm = self.config.get('jwt_algorithm', 'HS256')
        self.jwt_expiry_hours = self.config.get('jwt_expiry_hours', 24)

        # Security settings
        self.max_login_attempts = self.config.get('max_login_attempts', 5)
        self.lockout_duration_minutes = self.config.get('lockout_duration_minutes', 30)
        self.password_min_length = self.config.get('password_min_length', 12)
        self.require_special_chars = self.config.get('require_special_chars', True)

        # In-memory stores (in production, use Redis or database)
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._revoked_tokens: Set[str] = set()

        # Initialize default users (will be called during startup)
        self._initialized = False

        logger.info("AuthService initialized with secure defaults")

    async def initialize(self):
        """Initialize default users - call this during application startup"""
        if not self._initialized:
            await self._initialize_default_users()
            self._initialized = True
            logger.info("AuthService fully initialized with default users")

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[Role] = None
    ) -> User:
        """Register a new user with secure password handling"""

        # 1. Validate input
        if len(username) < 3:
            raise AuthenticationError("Username must be at least 3 characters")

        if len(password) < self.password_min_length:
            raise AuthenticationError(f"Password must be at least {self.password_min_length} characters")

        if self.require_special_chars and not self._has_special_chars(password):
            raise AuthenticationError("Password must contain special characters")

        # 2. Check if user exists
        if any(user.username == username or user.email == email for user in self._users.values()):
            raise AuthenticationError("User already exists")

        # 3. Hash password securely
        password_hash = self._hash_password(password)

        # 4. Create user
        user_id = str(uuid.uuid4())
        user_roles = set(roles) if roles else {Role.VIEWER}
        permissions = self._get_permissions_for_roles(user_roles)

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=user_roles,
            permissions=permissions,
            clearance_level="internal",
            created_at=datetime.utcnow(),
            metadata={}
        )

        self._users[user_id] = user

        logger.info(f"User registered: {username}")
        return user

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[str, User]:
        """Authenticate user and return JWT token"""

        # 1. Find user
        user = None
        for u in self._users.values():
            if u.username == username or u.email == username:
                user = u
                break

        if not user:
            logger.warning(f"Authentication failed: user not found - {username}")
            raise AuthenticationError("Invalid credentials")

        # 2. Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AuthenticationError("Account is temporarily locked")

        # 3. Verify password
        if not self._verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
                logger.warning(f"Account locked due to failed attempts: {username}")

            raise AuthenticationError("Invalid credentials")

        # 4. Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()

        # 5. Create session
        session = await self._create_session(user, ip_address, user_agent)

        # 6. Generate JWT token
        token = self._generate_jwt_token(user, session.session_id)

        logger.info(f"User authenticated: {username}")
        return token, user

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user info"""
        try:
            # 1. Check if token is revoked
            if token in self._revoked_tokens:
                return None

            # 2. Decode JWT
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )

            # 3. Validate expiration
            if datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
                return None

            # 4. Get user and session
            user_id = payload.get('user_id')
            session_id = payload.get('session_id')

            if not user_id or not session_id:
                return None

            user = self._users.get(user_id)
            session = self._sessions.get(session_id)

            if not user or not session or not session.is_valid:
                return None

            # 5. Update session activity
            session.last_activity = datetime.utcnow()

            return {
                'user_id': user_id,
                'session_id': session_id,
                'username': user.username,
                'roles': [role.value for role in user.roles],
                'permissions': [perm.value for perm in user.permissions],
                'clearance_level': user.clearance_level,
                'metadata': user.metadata
            }

        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def revoke_token(self, token: str):
        """Revoke a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": False}  # Don't verify expiration for revocation
            )

            # Add to revoked tokens
            self._revoked_tokens.add(token)

            # Invalidate session
            session_id = payload.get('session_id')
            if session_id and session_id in self._sessions:
                self._sessions[session_id].is_valid = False

            logger.info(f"Token revoked for user: {payload.get('user_id')}")

        except jwt.InvalidTokenError:
            pass  # Token already invalid

    async def logout_user(self, token: str):
        """Logout user by revoking token and session"""
        await self.revoke_token(token)

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""

        user = self._users.get(user_id)
        if not user:
            return False

        # Verify old password
        if not self._verify_password(old_password, user.password_hash):
            return False

        # Validate new password
        if len(new_password) < self.password_min_length:
            raise AuthenticationError(f"Password must be at least {self.password_min_length} characters")

        if self.require_special_chars and not self._has_special_chars(new_password):
            raise AuthenticationError("Password must contain special characters")

        # Update password
        user.password_hash = self._hash_password(new_password)

        logger.info(f"Password changed for user: {user.username}")
        return True

    async def get_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics"""
        active_sessions = sum(1 for s in self._sessions.values() if s.is_valid)

        return {
            "total_users": len(self._users),
            "active_sessions": active_sessions,
            "revoked_tokens": len(self._revoked_tokens),
            "locked_accounts": sum(
                1 for u in self._users.values()
                if u.locked_until and u.locked_until > datetime.utcnow()
            )
        }

    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(32)

    def _generate_jwt_token(self, user: User, session_id: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.user_id,
            'session_id': session_id,
            'username': user.username,
            'roles': [role.value for role in user.roles],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours)
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _create_session(
        self,
        user: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> Session:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours),
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown",
            last_activity=datetime.utcnow()
        )

        self._sessions[session_id] = session
        return session

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def _has_special_chars(self, password: str) -> bool:
        """Check if password has special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return any(char in special_chars for char in password)

    def _get_permissions_for_roles(self, roles: Set[Role]) -> Set[Permission]:
        """Get permissions for roles"""
        role_permissions = {
            Role.ANONYMOUS: set(),
            Role.VIEWER: {
                Permission.READ_DOCUMENTS,
                Permission.SEARCH_DOCUMENTS
            },
            Role.EDITOR: {
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.SEARCH_DOCUMENTS,
                Permission.CLASSIFY_DOCUMENTS
            },
            Role.CLASSIFIER: {
                Permission.READ_DOCUMENTS,
                Permission.SEARCH_DOCUMENTS,
                Permission.CLASSIFY_DOCUMENTS
            },
            Role.REVIEWER: {
                Permission.READ_DOCUMENTS,
                Permission.SEARCH_DOCUMENTS,
                Permission.CLASSIFY_DOCUMENTS,
                Permission.MANAGE_TAXONOMY
            },
            Role.ADMIN: {
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.DELETE_DOCUMENTS,
                Permission.SEARCH_DOCUMENTS,
                Permission.CLASSIFY_DOCUMENTS,
                Permission.MANAGE_TAXONOMY,
                Permission.VIEW_AUDIT_LOGS,
                Permission.ACCESS_PII,
                Permission.EXPORT_DATA
            },
            Role.SUPER_ADMIN: set(Permission)  # All permissions
        }

        permissions = set()
        for role in roles:
            permissions.update(role_permissions.get(role, set()))

        return permissions

    async def _initialize_default_users(self):
        """Initialize default system users"""
        # Create admin user
        admin_user = User(
            user_id="admin-001",
            username="admin",
            email="admin@dt-rag.local",
            password_hash=self._hash_password("SecureAdmin123!"),
            roles={Role.SUPER_ADMIN},
            permissions=set(Permission),
            clearance_level="top_secret",
            created_at=datetime.utcnow(),
            metadata={"created_by": "system"}
        )

        # Create viewer user
        viewer_user = User(
            user_id="viewer-001",
            username="viewer",
            email="viewer@dt-rag.local",
            password_hash=self._hash_password("SecureViewer123!"),
            roles={Role.VIEWER},
            permissions=self._get_permissions_for_roles({Role.VIEWER}),
            clearance_level="public",
            created_at=datetime.utcnow(),
            metadata={"created_by": "system"}
        )

        self._users[admin_user.user_id] = admin_user
        self._users[viewer_user.user_id] = viewer_user

        logger.info("Default users initialized")

class RBACManager:
    """
    Role-Based Access Control Manager
    Implements fine-grained permissions and access control
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Resource-based permissions
        self._resource_permissions: Dict[str, Set[Permission]] = {
            "documents": {
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.DELETE_DOCUMENTS
            },
            "search": {Permission.SEARCH_DOCUMENTS},
            "classification": {Permission.CLASSIFY_DOCUMENTS},
            "taxonomy": {Permission.MANAGE_TAXONOMY},
            "audit": {Permission.VIEW_AUDIT_LOGS},
            "users": {Permission.MANAGE_USERS},
            "pii_data": {Permission.ACCESS_PII, Permission.VIEW_PII},
            "system": {Permission.ADMIN_SYSTEM}
        }

        logger.info("RBACManager initialized")

    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource: str = None,
        context: Any = None
    ) -> bool:
        """Check if user has permission for operation"""
        try:
            # Convert string to enum if needed
            if isinstance(permission, str):
                permission = Permission(permission)

            # Get user permissions from context or lookup
            user_permissions = context.permissions if context else await self.get_user_permissions(user_id)

            # Check basic permission
            if permission not in user_permissions:
                return False

            # Check resource-specific permissions
            if resource:
                required_perms = self._resource_permissions.get(resource, set())
                if required_perms and not any(perm in user_permissions for perm in required_perms):
                    return False

            # Additional context-based checks
            if context:
                return await self._check_context_permissions(permission, resource, context)

            return True

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False

    async def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user"""
        # This would typically query the database
        # For now, return a default set based on common roles
        return {
            Permission.READ_DOCUMENTS,
            Permission.SEARCH_DOCUMENTS
        }

    async def get_user_clearance(self, user_id: str) -> str:
        """Get user security clearance level"""
        # This would typically query the database
        return "internal"

    async def get_metrics(self) -> Dict[str, Any]:
        """Get RBAC metrics"""
        return {
            "total_permissions": len(Permission),
            "total_roles": len(Role),
            "resource_types": len(self._resource_permissions)
        }

    async def _check_context_permissions(
        self,
        permission: Permission,
        resource: str,
        context: Any
    ) -> bool:
        """Check context-specific permissions"""

        # Time-based access control
        if hasattr(context, 'timestamp'):
            current_hour = context.timestamp.hour

            # Restrict sensitive operations during off-hours
            if permission in [Permission.DELETE_DOCUMENTS, Permission.ADMIN_SYSTEM]:
                if current_hour < 8 or current_hour > 18:  # Outside business hours
                    return False

        # Risk-based access control
        if hasattr(context, 'risk_score'):
            if context.risk_score > 0.7 and permission in [
                Permission.ACCESS_PII,
                Permission.DELETE_DOCUMENTS,
                Permission.ADMIN_SYSTEM
            ]:
                return False

        # IP-based restrictions
        if hasattr(context, 'ip_address'):
            # Block certain IP ranges for sensitive operations
            if permission == Permission.ADMIN_SYSTEM:
                # This would check against allowed IP ranges
                pass

        return True

class AuthenticationError(Exception):
    """Authentication-related exception"""
    pass

class AuthorizationError(Exception):
    """Authorization-related exception"""
    pass