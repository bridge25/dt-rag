"""
Configuration for DT-RAG v1.8.1 Monitoring System

Centralized configuration management for all observability components
with environment variable support and validation.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LangfuseConfig:
    """Langfuse integration configuration"""
    enabled: bool = True
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    host: str = "https://cloud.langfuse.com"
    session_timeout_minutes: int = 60
    trace_sampling_rate: float = 1.0  # 100% in dev, reduce in production

    def __post_init__(self):
        # Load from environment if not provided
        if self.public_key is None:
            self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        if self.secret_key is None:
            self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if host_env := os.getenv("LANGFUSE_HOST"):
            self.host = host_env

        # Disable if no credentials
        if not self.public_key or not self.secret_key:
            self.enabled = False
            logger.warning("Langfuse disabled: missing credentials")


@dataclass
class PrometheusConfig:
    """Prometheus metrics configuration"""
    enabled: bool = True
    port: int = 8090
    endpoint_path: str = "/metrics"
    export_interval_seconds: int = 30
    max_metrics_age_hours: int = 24
    cardinality_limit: int = 10000

    def __post_init__(self):
        if port_env := os.getenv("PROMETHEUS_PORT"):
            self.port = int(port_env)
        if interval_env := os.getenv("PROMETHEUS_EXPORT_INTERVAL"):
            self.export_interval_seconds = int(interval_env)


@dataclass
class AlertingConfig:
    """Alerting system configuration"""
    enabled: bool = True
    webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)

    # Alert suppression
    suppress_duplicate_minutes: int = 5
    suppress_flapping_count: int = 3
    suppress_flapping_window_minutes: int = 10

    def __post_init__(self):
        if webhook_env := os.getenv("ALERT_WEBHOOK_URL"):
            self.webhook_url = webhook_env
        if slack_env := os.getenv("SLACK_WEBHOOK_URL"):
            self.slack_webhook_url = slack_env
        if email_server_env := os.getenv("EMAIL_SMTP_SERVER"):
            self.email_smtp_server = email_server_env
        if email_from_env := os.getenv("EMAIL_FROM"):
            self.email_from = email_from_env
        if email_to_env := os.getenv("EMAIL_TO"):
            self.email_to = email_to_env.split(",")


@dataclass
class SLOConfig:
    """Service Level Objectives configuration"""
    # Latency SLOs
    p95_latency_seconds: float = 4.0
    p99_latency_seconds: float = 10.0

    # Cost SLOs
    cost_per_query_won: float = 10.0
    daily_cost_budget_won: float = 100000.0

    # Quality SLOs
    faithfulness_threshold: float = 0.85
    classification_confidence_threshold: float = 0.7
    search_quality_threshold: float = 0.8

    # Availability SLOs
    availability_percent: float = 99.5
    error_rate_percent: float = 1.0

    # Measurement windows
    latency_window_minutes: int = 5
    quality_window_minutes: int = 15
    availability_window_minutes: int = 5
    cost_window_minutes: int = 60

    def __post_init__(self):
        # Load SLO targets from environment
        if latency_env := os.getenv("SLO_P95_LATENCY_SECONDS"):
            self.p95_latency_seconds = float(latency_env)
        if cost_env := os.getenv("SLO_COST_PER_QUERY_WON"):
            self.cost_per_query_won = float(cost_env)
        if faithfulness_env := os.getenv("SLO_FAITHFULNESS_THRESHOLD"):
            self.faithfulness_threshold = float(faithfulness_env)
        if availability_env := os.getenv("SLO_AVAILABILITY_PERCENT"):
            self.availability_percent = float(availability_env)


@dataclass
class HealthCheckConfig:
    """Health monitoring configuration"""
    enabled: bool = True
    check_interval_seconds: int = 30
    timeout_seconds: float = 10.0
    retry_count: int = 3

    # Component-specific intervals
    system_check_interval: int = 30
    database_check_interval: int = 30
    vector_db_check_interval: int = 60
    external_service_check_interval: int = 120

    # Thresholds
    cpu_warning_percent: float = 75.0
    cpu_critical_percent: float = 90.0
    memory_warning_percent: float = 80.0
    memory_critical_percent: float = 90.0
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 90.0

    def __post_init__(self):
        if interval_env := os.getenv("HEALTH_CHECK_INTERVAL"):
            self.check_interval_seconds = int(interval_env)


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    enabled: bool = True
    grafana_url: Optional[str] = None
    grafana_api_key: Optional[str] = None
    auto_provision: bool = True
    refresh_interval: str = "30s"
    time_range: str = "1h"

    def __post_init__(self):
        if grafana_url_env := os.getenv("GRAFANA_URL"):
            self.grafana_url = grafana_url_env
        if grafana_key_env := os.getenv("GRAFANA_API_KEY"):
            self.grafana_api_key = grafana_key_env


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "/var/log/dt-rag/monitoring.log"
    file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    file_backup_count: int = 5

    # Structured logging
    structured_logging: bool = True
    json_format: bool = False

    def __post_init__(self):
        if level_env := os.getenv("LOG_LEVEL"):
            self.level = level_env.upper()
        if log_path_env := os.getenv("LOG_PATH"):
            self.file_path = log_path_env


@dataclass
class SecurityConfig:
    """Security configuration for monitoring"""
    metrics_auth_enabled: bool = False
    metrics_auth_token: Optional[str] = None
    dashboard_auth_enabled: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100

    def __post_init__(self):
        if metrics_token_env := os.getenv("METRICS_AUTH_TOKEN"):
            self.metrics_auth_token = metrics_token_env
            self.metrics_auth_enabled = True
        if origins_env := os.getenv("ALLOWED_ORIGINS"):
            self.allowed_origins = origins_env.split(",")


@dataclass
class DegradationConfig:
    """Automated degradation configuration"""
    enabled: bool = True
    max_degradation_duration_minutes: int = 60

    # Latency degradation
    latency_trigger_multiplier: float = 1.5  # Trigger at 1.5x SLO
    latency_recovery_multiplier: float = 0.8  # Recover at 0.8x SLO

    # Cost degradation
    cost_trigger_multiplier: float = 2.0  # Trigger at 2x SLO
    cost_recovery_multiplier: float = 0.8  # Recover at 0.8x SLO

    # Quality degradation
    quality_trigger_threshold: float = 0.7  # Trigger below 0.7
    quality_recovery_threshold: float = 0.85  # Recover above 0.85

    # Error rate degradation
    error_rate_trigger_percent: float = 5.0  # Trigger at 5% error rate
    error_rate_recovery_percent: float = 1.0  # Recover at 1% error rate

    def __post_init__(self):
        if enabled_env := os.getenv("DEGRADATION_ENABLED"):
            self.enabled = enabled_env.lower() == "true"


@dataclass
class MonitoringConfig:
    """Main monitoring configuration"""
    environment: str = "development"
    service_name: str = "dt-rag"
    service_version: str = "1.8.1"

    # Component configurations
    langfuse: LangfuseConfig = field(default_factory=LangfuseConfig)
    prometheus: PrometheusConfig = field(default_factory=PrometheusConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    slo: SLOConfig = field(default_factory=SLOConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    degradation: DegradationConfig = field(default_factory=DegradationConfig)

    def __post_init__(self):
        if env := os.getenv("ENVIRONMENT"):
            self.environment = env
        if service_env := os.getenv("SERVICE_NAME"):
            self.service_name = service_env
        if version_env := os.getenv("SERVICE_VERSION"):
            self.service_version = version_env


def load_config_from_file(config_path: str) -> MonitoringConfig:
    """Load configuration from YAML or JSON file"""
    import yaml
    import json

    config_file = Path(config_path)
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}")
        return MonitoringConfig()

    try:
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            elif config_file.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                logger.error(f"Unsupported config file format: {config_file.suffix}")
                return MonitoringConfig()

        # Convert dict to config objects
        config = MonitoringConfig()

        if 'langfuse' in config_data:
            config.langfuse = LangfuseConfig(**config_data['langfuse'])
        if 'prometheus' in config_data:
            config.prometheus = PrometheusConfig(**config_data['prometheus'])
        if 'alerting' in config_data:
            config.alerting = AlertingConfig(**config_data['alerting'])
        if 'slo' in config_data:
            config.slo = SLOConfig(**config_data['slo'])
        if 'health_check' in config_data:
            config.health_check = HealthCheckConfig(**config_data['health_check'])
        if 'dashboard' in config_data:
            config.dashboard = DashboardConfig(**config_data['dashboard'])
        if 'logging' in config_data:
            config.logging = LoggingConfig(**config_data['logging'])
        if 'security' in config_data:
            config.security = SecurityConfig(**config_data['security'])
        if 'degradation' in config_data:
            config.degradation = DegradationConfig(**config_data['degradation'])

        logger.info(f"Configuration loaded from {config_path}")
        return config

    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return MonitoringConfig()


def setup_logging(config: LoggingConfig):
    """Setup logging configuration"""
    import logging.handlers

    # Set log level
    logging.getLogger().setLevel(getattr(logging, config.level))

    # Create formatter
    if config.structured_logging and config.json_format:
        import json
        import datetime

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'line': record.lineno
                }

                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)

                return json.dumps(log_entry)

        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(config.format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    # File handler
    if config.file_enabled:
        try:
            # Create log directory
            log_path = Path(config.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                config.file_path,
                maxBytes=config.file_max_bytes,
                backupCount=config.file_backup_count
            )
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)

            logger.info(f"File logging enabled: {config.file_path}")
        except Exception as e:
            logger.error(f"Failed to setup file logging: {e}")


def validate_config(config: MonitoringConfig) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []

    # Validate Langfuse config
    if config.langfuse.enabled:
        if not config.langfuse.public_key:
            issues.append("Langfuse public key is required when enabled")
        if not config.langfuse.secret_key:
            issues.append("Langfuse secret key is required when enabled")

    # Validate Prometheus config
    if config.prometheus.enabled:
        if config.prometheus.port < 1024 or config.prometheus.port > 65535:
            issues.append("Prometheus port must be between 1024 and 65535")

    # Validate SLO config
    if config.slo.p95_latency_seconds <= 0:
        issues.append("P95 latency SLO must be positive")
    if config.slo.cost_per_query_won <= 0:
        issues.append("Cost per query SLO must be positive")
    if not 0 <= config.slo.faithfulness_threshold <= 1:
        issues.append("Faithfulness threshold must be between 0 and 1")
    if not 0 <= config.slo.availability_percent <= 100:
        issues.append("Availability percent must be between 0 and 100")

    # Validate health check config
    if config.health_check.check_interval_seconds <= 0:
        issues.append("Health check interval must be positive")
    if config.health_check.timeout_seconds <= 0:
        issues.append("Health check timeout must be positive")

    # Validate alerting config
    if config.alerting.enabled:
        if not any([config.alerting.webhook_url, config.alerting.slack_webhook_url, config.alerting.email_smtp_server]):
            issues.append("At least one alerting method must be configured when alerting is enabled")

    return issues


def get_environment_config() -> MonitoringConfig:
    """Get configuration with environment variable overrides"""
    config = MonitoringConfig()

    # Validate configuration
    issues = validate_config(config)
    if issues:
        logger.warning(f"Configuration issues found: {issues}")

    return config


def get_config() -> MonitoringConfig:
    """Get monitoring configuration from file or environment"""
    # Try to load from file first
    config_paths = [
        os.getenv("MONITORING_CONFIG_PATH", ""),
        "./config/monitoring.yaml",
        "./monitoring.yaml",
        "/etc/dt-rag/monitoring.yaml"
    ]

    for config_path in config_paths:
        if config_path and Path(config_path).exists():
            return load_config_from_file(config_path)

    # Fall back to environment configuration
    return get_environment_config()


# Global configuration instance
monitoring_config = get_config()


def configure_monitoring() -> MonitoringConfig:
    """Configure monitoring system with validation"""
    global monitoring_config

    # Setup logging
    setup_logging(monitoring_config.logging)

    # Validate configuration
    issues = validate_config(monitoring_config)
    if issues:
        logger.warning(f"Configuration validation issues: {issues}")

    logger.info(f"Monitoring configuration loaded for environment: {monitoring_config.environment}")
    logger.info(f"Langfuse enabled: {monitoring_config.langfuse.enabled}")
    logger.info(f"Prometheus enabled: {monitoring_config.prometheus.enabled}")
    logger.info(f"Alerting enabled: {monitoring_config.alerting.enabled}")
    logger.info(f"Health checks enabled: {monitoring_config.health_check.enabled}")
    logger.info(f"Degradation strategies enabled: {monitoring_config.degradation.enabled}")

    return monitoring_config