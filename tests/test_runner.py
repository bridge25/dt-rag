"""
Test runner for DT-RAG with environment-aware execution

This script provides different test execution modes based on the environment
and available services, with graceful degradation for CI environments.
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Intelligent test runner with environment awareness"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"

    def detect_environment(self) -> Dict[str, bool]:
        """Detect current environment and available services"""
        environment = {
            "is_ci": self._is_ci_environment(),
            "has_database": self._check_database_available(),
            "has_redis": self._check_redis_available(),
            "has_openai": self._check_openai_available(),
            "has_network": self._check_network_available(),
        }

        logger.info("Environment detection results:")
        for key, value in environment.items():
            logger.info(f"  {key}: {value}")

        return environment

    def _is_ci_environment(self) -> bool:
        """Check if running in CI environment"""
        ci_indicators = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS",
            "GITLAB_CI",
            "JENKINS_URL",
            "TRAVIS",
            "CIRCLECI",
        ]
        return any(os.getenv(indicator) for indicator in ci_indicators)

    def _check_database_available(self) -> bool:
        """Check if database is available"""
        try:
            import psycopg2  # type: ignore[import-untyped]
            from sqlalchemy import create_engine

            db_url = os.getenv("DATABASE_URL")
            if not db_url or "sqlite" in db_url.lower():
                return True  # SQLite is always available

            # Test PostgreSQL connection
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True

        except Exception as e:
            logger.warning(f"Database check failed: {e}")
            return False

    def _check_redis_available(self) -> bool:
        """Check if Redis is available"""
        try:
            import redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/15")
            client = redis.from_url(redis_url)
            client.ping()
            return True

        except Exception as e:
            logger.warning(f"Redis check failed: {e}")
            return False

    def _check_openai_available(self) -> bool:
        """Check if OpenAI API is available"""
        return bool(os.getenv("OPENAI_API_KEY") and os.getenv("TEST_WITH_OPENAI"))

    def _check_network_available(self) -> bool:
        """Check if network access is available"""
        if self._is_ci_environment():
            return bool(os.getenv("TEST_WITH_NETWORK"))

        try:
            import socket

            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception:
            return False

    def get_pytest_args(
        self, test_type: str = "all", environment: Optional[Dict[str, bool]] = None
    ) -> List[str]:
        """Generate pytest arguments based on test type and environment"""

        if environment is None:
            environment = self.detect_environment()

        base_args = ["python", "-m", "pytest", "--tb=short", "--strict-markers", "-v"]

        # Test type specific arguments
        if test_type == "unit":
            base_args.extend(["-m", "unit", "tests/unit/"])

        elif test_type == "integration":
            if environment["is_ci"]:
                # CI-safe integration tests
                base_args.extend(
                    ["-m", "integration and ci_safe", "tests/integration/"]
                )
            else:
                base_args.extend(["-m", "integration", "tests/integration/"])

        elif test_type == "e2e":
            if environment["is_ci"]:
                # Limited E2E tests for CI
                base_args.extend(["-m", "e2e and ci_safe", "tests/e2e/"])
            else:
                base_args.extend(["-m", "e2e", "tests/e2e/"])

        elif test_type == "ci":
            # CI-optimized test suite
            base_args.extend(["-m", "ci_safe or unit", "--maxfail=10", "--timeout=300"])

        elif test_type == "local":
            # Full local test suite
            base_args.extend(["--maxfail=5"])

        elif test_type == "quick":
            # Quick test suite (unit tests only)
            base_args.extend(["-m", "unit and not slow", "tests/unit/", "--maxfail=3"])

        elif test_type == "all":
            # Full test suite with environment awareness
            markers = []

            if environment["is_ci"]:
                markers.append("ci_safe or unit")
            else:
                # Skip only what's not available
                skip_conditions = []

                if not environment["has_database"]:
                    skip_conditions.append("not requires_db")

                if not environment["has_redis"]:
                    skip_conditions.append("not requires_redis")

                if not environment["has_openai"]:
                    skip_conditions.append("not requires_openai")

                if not environment["has_network"]:
                    skip_conditions.append("not requires_network")

                if skip_conditions:
                    markers.append(" and ".join(skip_conditions))

            if markers:
                base_args.extend(["-m", " and ".join(markers)])

        # Coverage reporting (only for comprehensive runs)
        if test_type in ["all", "local"] and not environment["is_ci"]:
            base_args.extend(
                [
                    "--cov=apps",
                    "--cov-report=html:htmlcov",
                    "--cov-report=term-missing",
                    "--cov-fail-under=70",
                ]
            )

        # Environment-specific settings
        if environment["is_ci"]:
            base_args.extend(
                ["--disable-warnings", "-x"]  # Stop on first failure in CI
            )

        return base_args

    def run_tests(
        self, test_type: str = "all", dry_run: bool = False, verbose: bool = False
    ) -> int:
        """Run tests with specified configuration"""

        environment = self.detect_environment()
        pytest_args = self.get_pytest_args(test_type, environment)

        if verbose:
            logger.info(f"Test type: {test_type}")
            logger.info(f"Environment: {environment}")
            logger.info(f"Pytest command: {' '.join(pytest_args)}")

        if dry_run:
            logger.info("Dry run - would execute:")
            logger.info(" ".join(pytest_args))
            return 0

        # Set environment variables
        env = os.environ.copy()
        env.update({"TESTING": "true", "PYTHONPATH": str(self.project_root)})

        if environment["is_ci"]:
            env.update(
                {
                    "CI_ENVIRONMENT": "true",
                    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
                    "REDIS_ENABLED": "false",
                }
            )

        # Execute tests
        try:
            result = subprocess.run(
                pytest_args, cwd=self.project_root, env=env, check=False
            )
            return result.returncode

        except KeyboardInterrupt:
            logger.info("Test execution interrupted by user")
            return 130

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return 1

    def list_test_types(self) -> Dict[str, str]:
        """List available test types and their descriptions"""
        return {
            "unit": "Fast unit tests with no external dependencies",
            "integration": "Integration tests (may require database/cache)",
            "e2e": "End-to-end tests (full system workflow)",
            "ci": "CI-optimized test suite (safe for automated environments)",
            "local": "Full local test suite with all features",
            "quick": "Quick test suite (unit tests only, no slow tests)",
            "all": "Complete test suite with environment-aware filtering",
        }

    def check_dependencies(self) -> Dict[str, bool]:
        """Check test dependencies and their availability"""
        dependencies = {}

        # Check pytest and plugins
        try:
            import pytest

            dependencies["pytest"] = True
        except ImportError:
            dependencies["pytest"] = False

        # Check coverage plugin
        try:
            import pytest_cov  # type: ignore[import-untyped]

            dependencies["pytest-cov"] = True
        except ImportError:
            dependencies["pytest-cov"] = False

        # Check async support
        try:
            import pytest_asyncio

            dependencies["pytest-asyncio"] = True
        except ImportError:
            dependencies["pytest-asyncio"] = False

        # Check mock support
        try:
            from unittest import mock

            dependencies["mock"] = True
        except ImportError:
            dependencies["mock"] = False

        # Check httpx for API testing
        try:
            import httpx

            dependencies["httpx"] = True
        except ImportError:
            dependencies["httpx"] = False

        return dependencies


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(
        description="DT-RAG Test Runner with Environment Awareness"
    )

    runner = TestRunner()

    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=list(runner.list_test_types().keys()),
        help="Type of tests to run",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running tests",
    )

    parser.add_argument(
        "--list-types", action="store_true", help="List available test types"
    )

    parser.add_argument(
        "--check-env", action="store_true", help="Check environment and dependencies"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.list_types:
        print("Available test types:")
        for test_type, description in runner.list_test_types().items():
            print(f"  {test_type:12} - {description}")
        return 0

    if args.check_env:
        print("Environment check:")
        environment = runner.detect_environment()
        for key, value in environment.items():
            status = "[OK]" if value else "[FAIL]"
            print(f"  {status} {key}")

        print("\nDependency check:")
        dependencies = runner.check_dependencies()
        for dep, available in dependencies.items():
            status = "[OK]" if available else "[FAIL]"
            print(f"  {status} {dep}")

        return 0

    # Run tests
    exit_code = runner.run_tests(
        test_type=args.test_type, dry_run=args.dry_run, verbose=args.verbose
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
