#!/usr/bin/env python3
"""
Configuration Migration Script for DT-RAG v1.8.1

This script helps migrate from the old configuration format to the new
structured environment configuration system with proper API key management.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def print_status(status: bool, message: str):
    """Print a status message with colored indicator"""
    indicator = "✅" if status else "❌"
    print(f"{indicator} {message}")

def print_warning(message: str):
    """Print a warning message"""
    print(f"⚠️  {message}")

def print_info(message: str):
    """Print an info message"""
    print(f"ℹ️  {message}")

def backup_existing_env():
    """Backup existing .env file if it exists"""
    env_file = project_root / ".env"

    if env_file.exists():
        # Create backup with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = project_root / f".env.backup.{timestamp}"

        shutil.copy2(env_file, backup_file)
        print_status(True, f"Backed up existing .env to {backup_file.name}")
        return backup_file

    return None

def parse_existing_env() -> Dict[str, str]:
    """Parse existing .env file and return key-value pairs"""
    env_file = project_root / ".env"
    env_vars = {}

    if env_file.exists():
        content = env_file.read_text()

        for line in content.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env_vars[key] = value

    return env_vars

def detect_environment_type(env_vars: Dict[str, str]) -> str:
    """Detect the intended environment type from existing configuration"""

    # Check explicit environment setting
    if 'DT_RAG_ENV' in env_vars:
        return env_vars['DT_RAG_ENV'].lower()

    # Check DEBUG setting
    if env_vars.get('DEBUG', 'false').lower() == 'false':
        return 'production'

    # Check database type
    db_url = env_vars.get('DATABASE_URL', '')
    if 'postgresql' in db_url.lower():
        return 'production'
    elif 'sqlite' in db_url.lower():
        if env_vars.get('TEST_MODE', 'false').lower() == 'true':
            return 'testing'
        else:
            return 'development'

    # Default to development
    return 'development'

def generate_new_env_content(env_vars: Dict[str, str], target_env: str) -> str:
    """Generate new .env content based on existing configuration"""

    # Load appropriate template
    if target_env == 'production':
        template_file = project_root / ".env.production.template"
    else:
        template_file = project_root / ".env.template"

    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")

    template_content = template_file.read_text()

    # Define migration mapping
    migration_map = {
        # Environment
        'DT_RAG_ENV': 'DT_RAG_ENV',
        'DEBUG': 'DEBUG',
        'TEST_MODE': 'TEST_MODE',

        # Database
        'DATABASE_URL': 'DATABASE_URL',
        'DB_POOL_SIZE': 'DB_POOL_SIZE',
        'DB_MAX_OVERFLOW': 'DB_MAX_OVERFLOW',
        'DB_ECHO': 'DB_ECHO',

        # Security
        'SECRET_KEY': 'SECRET_KEY',
        'JWT_EXPIRATION_MINUTES': 'JWT_EXPIRATION_MINUTES',
        'JWT_REFRESH_EXPIRATION_DAYS': 'JWT_REFRESH_EXPIRATION_DAYS',
        'PASSWORD_MIN_LENGTH': 'PASSWORD_MIN_LENGTH',
        'PASSWORD_REQUIRE_SPECIAL': 'PASSWORD_REQUIRE_SPECIAL',

        # API Keys
        'OPENAI_API_KEY': 'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        'AZURE_OPENAI_API_KEY': 'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT': 'AZURE_OPENAI_ENDPOINT',

        # Redis
        'REDIS_URL': 'REDIS_URL',

        # CORS
        'CORS_ORIGINS': 'CORS_ORIGINS',
        'CORS_CREDENTIALS': 'CORS_CREDENTIALS',
        'CORS_HEADERS': 'CORS_HEADERS',

        # Monitoring
        'MONITORING_ENABLED': 'MONITORING_ENABLED',
        'LOG_LEVEL': 'LOG_LEVEL',

        # Features
        'ENABLE_SWAGGER_UI': 'ENABLE_SWAGGER_UI',
        'ENABLE_REDOC': 'ENABLE_REDOC',
        'ENABLE_METRICS': 'ENABLE_METRICS',
        'ENABLE_RATE_LIMITING': 'ENABLE_RATE_LIMITING',
    }

    # Apply migrations
    new_content = template_content
    migrated_vars = set()

    for old_key, new_key in migration_map.items():
        if old_key in env_vars:
            old_value = env_vars[old_key]

            # Replace placeholder in template
            placeholder_patterns = [
                f"{new_key}=your-",
                f"{new_key}=sk-your-",
                f"{new_key}=REPLACE-WITH-",
                f"{new_key}=false",
                f"{new_key}=true",
                f"{new_key}=development",
                f"{new_key}=localhost",
                f"{new_key}=5",
                f"{new_key}=10",
                f"{new_key}=30"
            ]

            # Find and replace the template value
            for pattern in placeholder_patterns:
                if pattern in new_content:
                    # Extract the line and replace the value
                    lines = new_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith(f"{new_key}="):
                            lines[i] = f"{new_key}={old_value}"
                            break
                    new_content = '\n'.join(lines)
                    break

            migrated_vars.add(old_key)

    # Set environment-specific values
    lines = new_content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('DT_RAG_ENV='):
            lines[i] = f"DT_RAG_ENV={target_env}"
        elif line.strip().startswith('LLM_SERVICE_MODE='):
            # Set LLM mode based on available API keys
            if env_vars.get('OPENAI_API_KEY'):
                lines[i] = "LLM_SERVICE_MODE=openai"
            elif env_vars.get('ANTHROPIC_API_KEY'):
                lines[i] = "LLM_SERVICE_MODE=anthropic"
            elif env_vars.get('AZURE_OPENAI_API_KEY'):
                lines[i] = "LLM_SERVICE_MODE=azure"
            else:
                lines[i] = "LLM_SERVICE_MODE=dummy"
        elif line.strip().startswith('EMBEDDING_SERVICE_MODE='):
            # Set embedding mode based on available API keys
            if env_vars.get('OPENAI_API_KEY') or env_vars.get('AZURE_OPENAI_API_KEY'):
                lines[i] = "EMBEDDING_SERVICE_MODE=openai"
            else:
                lines[i] = "EMBEDDING_SERVICE_MODE=dummy"

    new_content = '\n'.join(lines)

    # Add migration comment at the top
    migration_comment = f"""# =============================================================================
# MIGRATED CONFIGURATION - {target_env.upper()} ENVIRONMENT
# =============================================================================
# This file was automatically migrated from the previous configuration format.
# Please review all settings, especially API keys and security configurations.
#
# Migrated variables: {', '.join(sorted(migrated_vars))}
# Unmigrated variables found: {', '.join(sorted(set(env_vars.keys()) - migrated_vars))}
# =============================================================================

"""

    return migration_comment + new_content

def migrate_configuration():
    """Main configuration migration function"""
    print_header("DT-RAG Configuration Migration")

    # Check if .env exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print_warning("No existing .env file found")

        # Offer to create from template
        response = input("Would you like to create a new .env file from template? (y/n): ")
        if response.lower() == 'y':
            env_type = input("Environment type (development/testing/staging/production): ").lower()
            if env_type not in ['development', 'testing', 'staging', 'production']:
                env_type = 'development'

            template_file = project_root / f".env.{env_type}.template" if env_type == 'production' else project_root / ".env.template"

            if template_file.exists():
                shutil.copy2(template_file, env_file)
                print_status(True, f"Created .env from {template_file.name}")
                print_info("Please edit .env file with your specific configuration")
            else:
                print_status(False, f"Template file not found: {template_file}")

        return

    print_section("Analyzing Existing Configuration")

    # Parse existing configuration
    env_vars = parse_existing_env()
    print_info(f"Found {len(env_vars)} configuration variables")

    # Detect environment type
    detected_env = detect_environment_type(env_vars)
    print_info(f"Detected environment type: {detected_env}")

    # Ask for confirmation
    response = input(f"Migrate to {detected_env} environment? (y/n/custom): ").lower()

    if response == 'n':
        print_info("Migration cancelled")
        return
    elif response == 'custom':
        target_env = input("Enter target environment (development/testing/staging/production): ").lower()
        if target_env not in ['development', 'testing', 'staging', 'production']:
            print_warning("Invalid environment, using detected environment")
            target_env = detected_env
    else:
        target_env = detected_env

    print_section("Migration Process")

    # Backup existing file
    backup_file = backup_existing_env()

    try:
        # Generate new configuration
        print_info("Generating new configuration...")
        new_content = generate_new_env_content(env_vars, target_env)

        # Write new .env file
        env_file.write_text(new_content)
        print_status(True, "Created new .env file")

        print_section("Migration Summary")

        # Analyze what was migrated
        migrated_keys = []
        unmigrated_keys = []

        for key in env_vars.keys():
            if key in new_content:
                migrated_keys.append(key)
            else:
                unmigrated_keys.append(key)

        print_info(f"Migrated {len(migrated_keys)} variables")
        if migrated_keys:
            for key in sorted(migrated_keys):
                print(f"  ✓ {key}")

        if unmigrated_keys:
            print_warning(f"Could not migrate {len(unmigrated_keys)} variables:")
            for key in sorted(unmigrated_keys):
                print(f"  ⚠ {key} = {env_vars[key]}")
            print_info("You may need to manually add these variables if they are still needed")

        print_section("Next Steps")
        print_info("1. Review the new .env file and update any placeholder values")
        print_info("2. Test the configuration with: python scripts/validate_config.py")
        print_info("3. Remove backup file after confirming everything works")

        if backup_file:
            print_info(f"4. Backup saved as: {backup_file.name}")

    except Exception as e:
        print_status(False, f"Migration failed: {e}")

        # Restore backup if migration failed
        if backup_file and env_file.exists():
            shutil.copy2(backup_file, env_file)
            print_info("Restored original .env file from backup")

def main():
    """Main entry point"""
    try:
        migrate_configuration()
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()