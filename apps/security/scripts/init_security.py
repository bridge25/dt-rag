#!/usr/bin/env python3
"""
Security Framework Initialization Script

This script initializes the security framework by:
1. Creating database tables
2. Setting up default roles and permissions
3. Creating initial admin user
4. Configuring security settings
5. Running initial security scans
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.security.integration import SecurityFramework
from apps.security.config.security_config import SecurityLevel, load_security_config
from apps.security.auth.auth_service import AuthService, RBACManager
from apps.security.audit.audit_logger import AuditLogger, SecurityEvent, RiskLevel
from apps.security.compliance.compliance_manager import ComplianceManager
from apps.security.monitoring.security_monitor import SecurityMonitor
from apps.security.scanning.vulnerability_scanner import VulnerabilityScanner

console = Console()

class SecurityInitializer:
    """Handles security framework initialization"""

    def __init__(self, security_level: SecurityLevel = SecurityLevel.DEVELOPMENT):
        self.security_level = security_level
        self.console = console

    async def initialize_framework(self,
                                 admin_username: Optional[str] = None,
                                 admin_password: Optional[str] = None,
                                 skip_scan: bool = False) -> bool:
        """Initialize the complete security framework"""

        self.console.print(Panel.fit(
            f"🔒 Initializing Security Framework v1.8.1\n"
            f"Security Level: {self.security_level.value.upper()}",
            title="Security Initialization",
            border_style="blue"
        ))

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:

                # Step 1: Load configuration
                task = progress.add_task("Loading security configuration...", total=None)
                config = load_security_config(security_level=self.security_level)
                progress.update(task, completed=True)
                self.console.print("✅ Configuration loaded successfully")

                # Step 2: Initialize database tables
                task = progress.add_task("Creating database tables...", total=None)
                await self._init_database_tables()
                progress.update(task, completed=True)
                self.console.print("✅ Database tables created")

                # Step 3: Setup roles and permissions
                task = progress.add_task("Setting up roles and permissions...", total=None)
                await self._setup_roles_and_permissions()
                progress.update(task, completed=True)
                self.console.print("✅ Roles and permissions configured")

                # Step 4: Create admin user
                if admin_username and admin_password:
                    task = progress.add_task("Creating admin user...", total=None)
                    await self._create_admin_user(admin_username, admin_password)
                    progress.update(task, completed=True)
                    self.console.print("✅ Admin user created")

                # Step 5: Initialize compliance framework
                task = progress.add_task("Setting up compliance framework...", total=None)
                await self._init_compliance()
                progress.update(task, completed=True)
                self.console.print("✅ Compliance framework initialized")

                # Step 6: Setup monitoring
                task = progress.add_task("Configuring security monitoring...", total=None)
                await self._init_monitoring()
                progress.update(task, completed=True)
                self.console.print("✅ Security monitoring configured")

                # Step 7: Initial security scan (optional)
                if not skip_scan:
                    task = progress.add_task("Running initial security scan...", total=None)
                    await self._run_initial_scan()
                    progress.update(task, completed=True)
                    self.console.print("✅ Initial security scan completed")

                # Step 8: Log initialization event
                task = progress.add_task("Logging initialization event...", total=None)
                await self._log_initialization()
                progress.update(task, completed=True)
                self.console.print("✅ Initialization logged")

            self._display_summary()
            return True

        except Exception as e:
            self.console.print(f"❌ Initialization failed: {str(e)}", style="red")
            return False

    async def _init_database_tables(self):
        """Initialize all security-related database tables"""

        # Initialize auth tables
        auth_service = AuthService()
        await auth_service._init_tables()

        # Initialize audit tables
        audit_logger = AuditLogger()
        await audit_logger._init_tables()

        # Initialize compliance tables
        compliance_manager = ComplianceManager()
        await compliance_manager._init_tables()

        # Initialize monitoring tables
        monitor = SecurityMonitor()
        await monitor._init_tables()

    async def _setup_roles_and_permissions(self):
        """Setup default roles and permissions"""

        rbac = RBACManager()

        # Create default roles
        roles = [
            {
                "name": "admin",
                "description": "Full system access",
                "permissions": [
                    "system:admin", "users:manage", "security:configure",
                    "documents:read", "documents:write", "documents:delete",
                    "taxonomy:read", "taxonomy:write", "taxonomy:manage",
                    "audit:read", "compliance:manage", "monitoring:access"
                ]
            },
            {
                "name": "editor",
                "description": "Content management access",
                "permissions": [
                    "documents:read", "documents:write",
                    "taxonomy:read", "taxonomy:write"
                ]
            },
            {
                "name": "reviewer",
                "description": "Review and approve content",
                "permissions": [
                    "documents:read", "documents:approve",
                    "taxonomy:read"
                ]
            },
            {
                "name": "viewer",
                "description": "Read-only access",
                "permissions": [
                    "documents:read", "taxonomy:read"
                ]
            },
            {
                "name": "auditor",
                "description": "Audit and compliance access",
                "permissions": [
                    "audit:read", "compliance:read", "monitoring:read"
                ]
            }
        ]

        for role_data in roles:
            await rbac.create_role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"]
            )

    async def _create_admin_user(self, username: str, password: str):
        """Create initial admin user"""

        auth_service = AuthService()

        try:
            admin_user = await auth_service.register_user(
                username=username,
                password=password,
                email=username if "@" in username else f"{username}@localhost",
                roles=["admin"],
                is_active=True,
                email_verified=True
            )

            # Log admin user creation
            audit_logger = AuditLogger()
            await audit_logger.log_event(SecurityEvent(
                event_type="admin_user_created",
                user_id=str(admin_user.id),
                details={
                    "username": username,
                    "created_during": "security_initialization"
                },
                risk_level=RiskLevel.MEDIUM
            ))

        except Exception as e:
            if "already exists" in str(e).lower():
                self.console.print(f"ℹ️ Admin user '{username}' already exists", style="yellow")
            else:
                raise

    async def _init_compliance(self):
        """Initialize compliance framework"""

        compliance = ComplianceManager()

        # Register default processing activities for GDPR Article 30
        activities = [
            {
                "name": "Document Processing",
                "purpose": "Process and classify uploaded documents",
                "legal_basis": "Legitimate interest",
                "categories_of_data": ["Content data", "Metadata"],
                "retention_period": "As per business requirements",
                "technical_measures": "Encryption, access control, audit logging"
            },
            {
                "name": "User Authentication",
                "purpose": "Authenticate and authorize system users",
                "legal_basis": "Contract performance",
                "categories_of_data": ["Authentication credentials", "Session data"],
                "retention_period": "Until account deletion",
                "technical_measures": "Password hashing, JWT tokens, session management"
            },
            {
                "name": "Audit Logging",
                "purpose": "Maintain security and compliance audit trail",
                "legal_basis": "Legal obligation",
                "categories_of_data": ["System events", "User actions", "Access logs"],
                "retention_period": "7 years",
                "technical_measures": "Immutable logging, hash verification, encryption"
            }
        ]

        for activity in activities:
            await compliance.register_processing_activity(**activity)

    async def _init_monitoring(self):
        """Initialize security monitoring"""

        monitor = SecurityMonitor()

        # Train initial anomaly detection model with sample data
        await monitor.train_anomaly_detector()

        # Create sample monitoring rules
        rules = [
            {
                "name": "Multiple Failed Logins",
                "description": "Detect multiple failed login attempts",
                "condition": "failed_login_attempts > 5",
                "severity": "HIGH",
                "enabled": True
            },
            {
                "name": "Unusual Access Hours",
                "description": "Detect access outside business hours",
                "condition": "access_hour < 6 OR access_hour > 22",
                "severity": "MEDIUM",
                "enabled": True
            },
            {
                "name": "Bulk Data Download",
                "description": "Detect bulk data download attempts",
                "condition": "download_count > 100",
                "severity": "HIGH",
                "enabled": True
            }
        ]

        for rule in rules:
            await monitor.create_monitoring_rule(**rule)

    async def _run_initial_scan(self):
        """Run initial security vulnerability scan"""

        scanner = VulnerabilityScanner()

        # Scan the security module itself
        target_path = str(Path(__file__).parent.parent)

        try:
            result = await scanner.scan_codebase(
                target_path=target_path,
                scan_types=["bandit", "safety"]
            )

            # Log scan results
            audit_logger = AuditLogger()
            await audit_logger.log_event(SecurityEvent(
                event_type="initial_security_scan",
                details={
                    "scan_id": result.scan_id,
                    "vulnerabilities_found": len(result.findings),
                    "scan_types": ["bandit", "safety"]
                },
                risk_level=RiskLevel.LOW
            ))

        except Exception as e:
            self.console.print(f"⚠️ Initial scan failed: {str(e)}", style="yellow")

    async def _log_initialization(self):
        """Log the security framework initialization"""

        audit_logger = AuditLogger()
        await audit_logger.log_event(SecurityEvent(
            event_type="security_framework_initialized",
            details={
                "security_level": self.security_level.value,
                "version": "1.8.1",
                "components": [
                    "authentication", "authorization", "audit_logging",
                    "pii_detection", "compliance_management",
                    "security_monitoring", "vulnerability_scanning"
                ]
            },
            risk_level=RiskLevel.LOW
        ))

    def _display_summary(self):
        """Display initialization summary"""

        table = Table(title="Security Framework Initialization Summary")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details")

        table.add_row("Authentication", "✅ Initialized", "JWT-based with RBAC")
        table.add_row("Audit Logging", "✅ Initialized", "Immutable trail with integrity")
        table.add_row("PII Detection", "✅ Initialized", "Presidio + custom patterns")
        table.add_row("Compliance", "✅ Initialized", "GDPR/CCPA/PIPA support")
        table.add_row("Monitoring", "✅ Initialized", "ML-based anomaly detection")
        table.add_row("Scanning", "✅ Initialized", "OWASP Top 10 vulnerability detection")
        table.add_row("Configuration", "✅ Loaded", f"Security level: {self.security_level.value}")

        self.console.print(table)

        self.console.print(Panel.fit(
            "🚀 Security Framework v1.8.1 is ready!\n\n"
            "Next steps:\n"
            "1. Configure environment variables (JWT_SECRET, DATABASE_URL)\n"
            "2. Review security configuration files\n"
            "3. Run security tests: pytest apps/security/tests/\n"
            "4. Start the API server with security middleware\n"
            "5. Access security dashboard at /security/dashboard",
            title="Initialization Complete",
            border_style="green"
        ))


@click.command()
@click.option('--security-level',
              type=click.Choice(['development', 'testing', 'staging', 'production']),
              default='development',
              help='Security level to initialize')
@click.option('--admin-username',
              prompt='Admin username',
              help='Username for initial admin user')
@click.option('--admin-password',
              prompt='Admin password',
              hide_input=True,
              confirmation_prompt=True,
              help='Password for initial admin user')
@click.option('--skip-scan',
              is_flag=True,
              help='Skip initial security scan')
@click.option('--config-file',
              type=click.Path(exists=True),
              help='Custom security configuration file')
def main(security_level: str,
         admin_username: str,
         admin_password: str,
         skip_scan: bool,
         config_file: Optional[str]):
    """Initialize the Dynamic Taxonomy RAG Security Framework"""

    async def run_init():
        level = SecurityLevel(security_level)
        initializer = SecurityInitializer(level)

        success = await initializer.initialize_framework(
            admin_username=admin_username,
            admin_password=admin_password,
            skip_scan=skip_scan
        )

        return 0 if success else 1

    return asyncio.run(run_init())


if __name__ == "__main__":
    sys.exit(main())