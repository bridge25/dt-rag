#!/usr/bin/env python3
"""
Configuration Validation Script for DT-RAG v1.8.1

This script validates the current configuration setup, checks for required
environment variables, and provides recommendations for improvement.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from apps.api.config import get_system_status, get_configuration_recommendations, validate_config, get_api_config
    from apps.api.env_manager import get_env_manager, validate_current_environment
    from apps.api.llm_config import get_llm_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

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

def validate_environment_file():
    """Validate .env file existence and basic structure"""
    print_section("Environment File Validation")

    env_file = project_root / ".env"

    if env_file.exists():
        print_status(True, ".env file exists")

        # Check if it's the template file (contains placeholder values)
        content = env_file.read_text()
        if "your-openai-api-key-here" in content:
            print_warning(".env file contains placeholder values - update with real configuration")

        if "sk-your-openai-api-key-here" in content:
            print_warning("OpenAI API key is still a placeholder")

        return True
    else:
        print_status(False, ".env file not found")

        # Check for template file
        template_file = project_root / ".env.template"
        if template_file.exists():
            print_info("Found .env.template - copy it to .env and configure")
        else:
            print_warning("No .env.template found either")

        return False

def validate_database_config():
    """Validate database configuration"""
    print_section("Database Configuration Validation")

    try:
        env_manager = get_env_manager()
        db_config = env_manager.get_database_config()

        db_url = db_config["url"]
        print_info(f"Database URL: {db_url}")

        if "sqlite" in db_url.lower():
            print_status(True, "Using SQLite database")

            # Check if SQLite file path is valid
            if ":///" in db_url:
                db_path = db_url.split("///")[1]
                db_file = Path(db_path)

                if db_file.exists():
                    print_status(True, f"SQLite database file exists: {db_path}")
                else:
                    print_info(f"SQLite database file will be created: {db_path}")

                # Check if directory is writable
                try:
                    db_file.parent.mkdir(parents=True, exist_ok=True)
                    print_status(True, "Database directory is writable")
                except Exception as e:
                    print_status(False, f"Database directory is not writable: {e}")
                    return False

        elif "postgresql" in db_url.lower():
            print_status(True, "Using PostgreSQL database")
            print_warning("Make sure PostgreSQL is running and accessible")

        else:
            print_status(False, f"Unknown database type in URL: {db_url}")
            return False

        return True

    except Exception as e:
        print_status(False, f"Database configuration error: {e}")
        return False

def validate_llm_services():
    """Validate LLM and embedding services configuration"""
    print_section("LLM Services Validation")

    try:
        llm_config = get_llm_config()
        service_status = llm_config.get_service_status()

        # LLM Service
        llm_service = service_status["llm_service"]
        print_info(f"LLM Mode: {llm_service['configured_mode']} -> {llm_service['effective_mode']}")

        if llm_service["is_dummy"]:
            print_warning("LLM service is in dummy mode - no real AI responses")
        else:
            print_status(True, f"LLM service configured: {llm_service['effective_mode']}")

        # Embedding Service
        embedding_service = service_status["embedding_service"]
        print_info(f"Embedding Mode: {embedding_service['configured_mode']} -> {embedding_service['effective_mode']}")

        if embedding_service["is_dummy"]:
            print_warning("Embedding service is in dummy mode - random vectors will be used")
        else:
            print_status(True, f"Embedding service configured: {embedding_service['effective_mode']}")

        # Show validation details
        for service_name, service_info in [("LLM", llm_service), ("Embedding", embedding_service)]:
            validation = service_info["validation"]

            if validation["errors"]:
                for error in validation["errors"]:
                    print_status(False, f"{service_name}: {error}")

            if validation["warnings"]:
                for warning in validation["warnings"]:
                    print_warning(f"{service_name}: {warning}")

        return service_status["system_operational"]

    except Exception as e:
        print_status(False, f"LLM services validation error: {e}")
        return False

def validate_security_config():
    """Validate security configuration"""
    print_section("Security Configuration Validation")

    try:
        api_config = get_api_config()

        # Check SECRET_KEY
        if api_config.security.secret_key:
            key_length = len(api_config.security.secret_key)
            if key_length >= 32:
                print_status(True, f"SECRET_KEY configured (length: {key_length})")
            else:
                print_status(False, f"SECRET_KEY too short (length: {key_length}, minimum: 32)")
        else:
            print_status(False, "SECRET_KEY not configured")

        # Check environment-specific security
        env_manager = get_env_manager()
        if env_manager.is_production():
            print_info("Production environment - applying strict security validation")

            if api_config.debug:
                print_status(False, "Debug mode should be disabled in production")

            if api_config.docs_url:
                print_status(False, "API documentation should be disabled in production")

            # Check CORS
            if "*" in api_config.cors.allow_origins:
                print_status(False, "Wildcard CORS origins not allowed in production")

            # Check HTTPS
            for origin in api_config.cors.allow_origins:
                if origin.startswith("http://") and not origin.startswith("http://localhost"):
                    print_status(False, f"HTTP origin not allowed in production: {origin}")

        return True

    except Exception as e:
        print_status(False, f"Security validation error: {e}")
        return False

def run_comprehensive_validation():
    """Run comprehensive configuration validation"""
    print_header("DT-RAG v1.8.1 Configuration Validation")

    # Check Python environment
    print_section("Python Environment")
    print_info(f"Python version: {sys.version}")
    print_info(f"Working directory: {os.getcwd()}")
    print_info(f"Project root: {project_root}")

    # Validate components
    env_file_ok = validate_environment_file()
    db_config_ok = validate_database_config()
    llm_services_ok = validate_llm_services()
    security_ok = validate_security_config()

    # Get comprehensive system status
    try:
        print_section("System Status")
        system_status = get_system_status()

        # Environment summary
        env_summary = system_status["environment"]
        print_info(f"Environment: {env_summary['environment']}")
        print_info(f"Debug mode: {env_summary['config']['debug']}")
        print_info(f"Database type: {env_summary['config']['database_type']}")

        # Validation summary
        validation = env_summary["validation"]
        print_status(validation["is_valid"], f"Environment validation: {validation['error_count']} errors, {validation['warning_count']} warnings")

        # Service status
        services = system_status["llm_services"]
        print_info(f"LLM service: {services['llm_service']['effective_mode']}")
        print_info(f"Embedding service: {services['embedding_service']['effective_mode']}")

        # System health
        health = system_status["system_health"]
        print_status(health["configuration_valid"], "Configuration validity")
        print_status(health["llm_service_available"], "LLM service availability")
        print_status(health["fallback_enabled"], "Fallback mechanisms")

    except Exception as e:
        print_status(False, f"System status check failed: {e}")

    # Get recommendations
    try:
        print_section("Configuration Recommendations")
        recommendations = get_configuration_recommendations()

        if recommendations:
            for i, recommendation in enumerate(recommendations, 1):
                print(f"{i}. {recommendation}")
        else:
            print_status(True, "No recommendations - configuration looks good!")

    except Exception as e:
        print_warning(f"Failed to get recommendations: {e}")

    # Overall status
    print_section("Overall Assessment")

    overall_ok = all([env_file_ok, db_config_ok, llm_services_ok, security_ok])

    if overall_ok:
        print_status(True, "Configuration validation passed")
        print_info("System is ready for operation")
    else:
        print_status(False, "Configuration validation failed")
        print_warning("Please address the issues above before proceeding")

    return overall_ok

def main():
    """Main entry point"""
    try:
        # Load environment variables from .env file if it exists
        env_file = project_root / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print_info("Loaded environment variables from .env file")

        # Run validation
        success = run_comprehensive_validation()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()