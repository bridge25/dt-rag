"""
Security Configuration for DT-RAG v1.8.1
Centralized security configuration management
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class SecurityLevel(Enum):
    """Security deployment levels"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    password_min_length: int = 12
    require_special_chars: bool = True
    enable_mfa: bool = False
    session_timeout_minutes: int = 480  # 8 hours

@dataclass
class RBACConfig:
    """Role-Based Access Control configuration"""
    default_role: str = "viewer"
    enable_attribute_based_access: bool = True
    enable_time_based_access: bool = True
    enable_location_based_access: bool = False
    max_concurrent_sessions: int = 5

@dataclass
class AuditConfig:
    """Audit logging configuration"""
    storage_type: str = "sqlite"  # sqlite, postgresql, file
    log_directory: str = "./audit_logs"
    max_log_file_size: int = 100 * 1024 * 1024  # 100MB
    retention_days: int = 2555  # 7 years
    enable_encryption: bool = True
    enable_signing: bool = True
    compression_enabled: bool = True
    cache_size: int = 1000

@dataclass
class PIIConfig:
    """PII detection configuration"""
    confidence_threshold: float = 0.8
    enable_context_analysis: bool = True
    supported_languages: List[str] = None
    custom_patterns: Dict[str, List[str]] = None
    exclusion_patterns: List[str] = None
    enable_presidio: bool = True

    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = ['en', 'ko']
        if self.custom_patterns is None:
            self.custom_patterns = {}
        if self.exclusion_patterns is None:
            self.exclusion_patterns = []

@dataclass
class ComplianceConfig:
    """Compliance management configuration"""
    supported_regulations: List[str] = None
    storage_path: str = "./compliance_data"
    auto_response_enabled: bool = True
    breach_notification_enabled: bool = True
    data_retention_checks: bool = True

    def __post_init__(self):
        if self.supported_regulations is None:
            self.supported_regulations = ['GDPR', 'CCPA', 'PIPA', 'SOX', 'HIPAA']

@dataclass
class MonitoringConfig:
    """Security monitoring configuration"""
    enable_ml_detection: bool = True
    alert_thresholds: Dict[str, Any] = None
    enable_real_time_monitoring: bool = True
    alert_retention_days: int = 90
    incident_auto_creation: bool = True

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'failed_login_attempts': 5,
                'unusual_access_threshold': 3.0,
                'bulk_download_threshold': 100,
                'session_duration_threshold': 8
            }

@dataclass
class ScanningConfig:
    """Vulnerability scanning configuration"""
    enable_bandit: bool = True
    enable_safety: bool = True
    enable_semgrep: bool = True
    enable_custom_rules: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    excluded_paths: List[str] = None
    scan_schedule_cron: str = "0 2 * * *"  # Daily at 2 AM

    def __post_init__(self):
        if self.excluded_paths is None:
            self.excluded_paths = [
                '*/node_modules/*', '*/venv/*', '*/.git/*',
                '*/tests/*', '*/test/*', '*/__pycache__/*'
            ]

@dataclass
class MiddlewareConfig:
    """Security middleware configuration"""
    enable_auth: bool = True
    enable_rate_limiting: bool = True
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    enable_security_headers: bool = True
    enable_csrf_protection: bool = True
    exempt_endpoints: List[str] = None
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_fields: int = 1000
    blocked_ips: List[str] = None
    allowed_ips: List[str] = None

    def __post_init__(self):
        if self.exempt_endpoints is None:
            self.exempt_endpoints = [
                "/", "/health", "/healthz", "/docs", "/redoc",
                "/openapi.json", "/security/auth/login", "/security/auth/register"
            ]
        if self.blocked_ips is None:
            self.blocked_ips = []
        if self.allowed_ips is None:
            self.allowed_ips = []

@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    key_iterations: int = 100000
    enable_database_encryption: bool = True
    enable_log_encryption: bool = True
    enable_communication_encryption: bool = True
    key_rotation_days: int = 90

@dataclass
class SecurityConfig:
    """Master security configuration"""
    security_level: SecurityLevel
    auth: AuthConfig
    rbac: RBACConfig
    audit: AuditConfig
    pii: PIIConfig
    compliance: ComplianceConfig
    monitoring: MonitoringConfig
    scanning: ScanningConfig
    middleware: MiddlewareConfig
    encryption: EncryptionConfig

    # Global settings
    enable_debug: bool = False
    enable_metrics: bool = True
    metrics_endpoint: str = "/security/metrics"
    health_endpoint: str = "/security/status"

class SecurityConfigManager:
    """
    Security configuration manager with environment-based profiles
    """

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv("SECURITY_CONFIG_FILE")
        self._config: Optional[SecurityConfig] = None

    def load_config(
        self,
        security_level: Optional[SecurityLevel] = None
    ) -> SecurityConfig:
        """Load security configuration"""

        if security_level is None:
            security_level = SecurityLevel(
                os.getenv("SECURITY_LEVEL", "development")
            )

        if self.config_file and Path(self.config_file).exists():
            # Load from file
            self._config = self._load_from_file(self.config_file)
        else:
            # Load default configuration
            self._config = self._get_default_config(security_level)

        # Apply environment overrides
        self._apply_env_overrides()

        return self._config

    def save_config(self, config: SecurityConfig, file_path: str):
        """Save configuration to file"""
        config_dict = asdict(config)

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

    def get_config(self) -> SecurityConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def _load_from_file(self, file_path: str) -> SecurityConfig:
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)

        return self._dict_to_config(config_dict)

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> SecurityConfig:
        """Convert dictionary to SecurityConfig"""

        # Handle security level
        security_level = SecurityLevel(config_dict.get('security_level', 'development'))

        # Create component configurations
        auth = AuthConfig(**config_dict.get('auth', {}))
        rbac = RBACConfig(**config_dict.get('rbac', {}))
        audit = AuditConfig(**config_dict.get('audit', {}))
        pii = PIIConfig(**config_dict.get('pii', {}))
        compliance = ComplianceConfig(**config_dict.get('compliance', {}))
        monitoring = MonitoringConfig(**config_dict.get('monitoring', {}))
        scanning = ScanningConfig(**config_dict.get('scanning', {}))
        middleware = MiddlewareConfig(**config_dict.get('middleware', {}))
        encryption = EncryptionConfig(**config_dict.get('encryption', {}))

        return SecurityConfig(
            security_level=security_level,
            auth=auth,
            rbac=rbac,
            audit=audit,
            pii=pii,
            compliance=compliance,
            monitoring=monitoring,
            scanning=scanning,
            middleware=middleware,
            encryption=encryption,
            enable_debug=config_dict.get('enable_debug', False),
            enable_metrics=config_dict.get('enable_metrics', True),
            metrics_endpoint=config_dict.get('metrics_endpoint', '/security/metrics'),
            health_endpoint=config_dict.get('health_endpoint', '/security/status')
        )

    def _get_default_config(self, security_level: SecurityLevel) -> SecurityConfig:
        """Get default configuration for security level"""

        # Base configuration
        config = SecurityConfig(
            security_level=security_level,
            auth=AuthConfig(
                jwt_secret=os.getenv("JWT_SECRET", self._generate_secret())
            ),
            rbac=RBACConfig(),
            audit=AuditConfig(),
            pii=PIIConfig(),
            compliance=ComplianceConfig(),
            monitoring=MonitoringConfig(),
            scanning=ScanningConfig(),
            middleware=MiddlewareConfig(),
            encryption=EncryptionConfig()
        )

        # Apply security level specific settings
        if security_level == SecurityLevel.DEVELOPMENT:
            config.enable_debug = True
            config.auth.jwt_expiry_hours = 48  # Longer sessions for dev
            config.middleware.enable_auth = False  # Disable auth for easier dev
            config.audit.enable_encryption = False
            config.scanning.enable_semgrep = False  # Faster scans

        elif security_level == SecurityLevel.TESTING:
            config.enable_debug = True
            config.auth.max_login_attempts = 10  # More lenient for testing
            config.audit.retention_days = 30  # Shorter retention
            config.monitoring.enable_ml_detection = False  # Disable ML for consistent tests

        elif security_level == SecurityLevel.STAGING:
            config.enable_debug = False
            config.auth.enable_mfa = True
            config.audit.enable_encryption = True
            config.monitoring.enable_ml_detection = True

        elif security_level == SecurityLevel.PRODUCTION:
            config.enable_debug = False
            config.auth.enable_mfa = True
            config.auth.password_min_length = 16  # Stronger passwords
            config.auth.jwt_expiry_hours = 8  # Shorter sessions
            config.rbac.enable_attribute_based_access = True
            config.rbac.enable_time_based_access = True
            config.audit.enable_encryption = True
            config.audit.enable_signing = True
            config.monitoring.enable_ml_detection = True
            config.middleware.enable_csrf_protection = True
            config.encryption.enable_database_encryption = True

        return config

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        if not self._config:
            return

        # JWT Secret override
        jwt_secret = os.getenv("JWT_SECRET")
        if jwt_secret:
            self._config.auth.jwt_secret = jwt_secret

        # Database URL for audit storage
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self._config.audit.storage_type = "postgresql"

        # Enable/disable components
        if os.getenv("DISABLE_AUTH") == "true":
            self._config.middleware.enable_auth = False

        if os.getenv("DISABLE_RATE_LIMITING") == "true":
            self._config.middleware.enable_rate_limiting = False

        # Security level override
        security_level_env = os.getenv("SECURITY_LEVEL")
        if security_level_env:
            try:
                self._config.security_level = SecurityLevel(security_level_env)
            except ValueError:
                pass  # Invalid security level, keep current

        # Rate limiting overrides
        rate_limit_requests = os.getenv("RATE_LIMIT_REQUESTS")
        if rate_limit_requests:
            try:
                self._config.middleware.rate_limit_requests = int(rate_limit_requests)
            except ValueError:
                pass

        # PII threshold override
        pii_threshold = os.getenv("PII_CONFIDENCE_THRESHOLD")
        if pii_threshold:
            try:
                self._config.pii.confidence_threshold = float(pii_threshold)
            except ValueError:
                pass

    def _generate_secret(self) -> str:
        """Generate a secure random secret"""
        import secrets
        return secrets.token_urlsafe(32)

    def validate_config(self, config: SecurityConfig) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Validate JWT secret
        if len(config.auth.jwt_secret) < 32:
            issues.append("JWT secret should be at least 32 characters")

        # Validate password requirements
        if config.auth.password_min_length < 8:
            issues.append("Minimum password length should be at least 8 characters")

        # Production-specific validations
        if config.security_level == SecurityLevel.PRODUCTION:
            if config.enable_debug:
                issues.append("Debug mode should be disabled in production")

            if not config.auth.enable_mfa:
                issues.append("MFA should be enabled in production")

            if not config.audit.enable_encryption:
                issues.append("Audit log encryption should be enabled in production")

            if not config.middleware.enable_csrf_protection:
                issues.append("CSRF protection should be enabled in production")

        # Validate file paths
        audit_dir = Path(config.audit.log_directory)
        if not audit_dir.parent.exists():
            issues.append(f"Audit log directory parent does not exist: {audit_dir.parent}")

        compliance_dir = Path(config.compliance.storage_path)
        if not compliance_dir.parent.exists():
            issues.append(f"Compliance storage directory parent does not exist: {compliance_dir.parent}")

        return issues

# Global configuration instance
_config_manager = SecurityConfigManager()

def get_security_config() -> SecurityConfig:
    """Get global security configuration"""
    return _config_manager.get_config()

def load_security_config(
    config_file: Optional[str] = None,
    security_level: Optional[SecurityLevel] = None
) -> SecurityConfig:
    """Load security configuration"""
    if config_file:
        _config_manager.config_file = config_file
    return _config_manager.load_config(security_level)

def create_default_config_file(
    file_path: str,
    security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
):
    """Create a default configuration file"""
    config_manager = SecurityConfigManager()
    default_config = config_manager._get_default_config(security_level)
    config_manager.save_config(default_config, file_path)

# Environment-specific configurations
def get_development_config() -> SecurityConfig:
    """Get development configuration"""
    manager = SecurityConfigManager()
    return manager._get_default_config(SecurityLevel.DEVELOPMENT)

def get_production_config() -> SecurityConfig:
    """Get production configuration"""
    manager = SecurityConfigManager()
    return manager._get_default_config(SecurityLevel.PRODUCTION)

if __name__ == "__main__":
    # CLI for creating configuration files
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "create-config":
            output_file = sys.argv[2] if len(sys.argv) > 2 else "security_config.json"
            security_level = SecurityLevel(sys.argv[3]) if len(sys.argv) > 3 else SecurityLevel.DEVELOPMENT

            create_default_config_file(output_file, security_level)
            print(f"Created configuration file: {output_file} ({security_level.value})")

        elif command == "validate":
            config_file = sys.argv[2] if len(sys.argv) > 2 else "security_config.json"

            if not Path(config_file).exists():
                print(f"Configuration file not found: {config_file}")
                sys.exit(1)

            manager = SecurityConfigManager(config_file)
            config = manager.load_config()
            issues = manager.validate_config(config)

            if issues:
                print("Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration is valid")

        else:
            print("Usage: python security_config.py [create-config|validate] [file] [level]")
    else:
        print("Usage: python security_config.py [create-config|validate] [file] [level]")