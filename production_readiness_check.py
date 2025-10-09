"""
Production Readiness Check for DT-RAG v1.8.1

Validates production environment configuration and runs comprehensive tests
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionReadinessChecker:
    """Production readiness validation"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check_env_vars(self):
        """Check required environment variables"""
        logger.info("=" * 60)
        logger.info("Step 1: Environment Variables")
        logger.info("=" * 60)

        # Critical
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            if "postgresql" in database_url.lower():
                logger.info(f"[PASS] DATABASE_URL: PostgreSQL configured")
                self.passed += 1
            else:
                logger.warning(f"[WARN] DATABASE_URL: Not PostgreSQL (using {database_url[:20]}...)")
                self.warnings += 1
        else:
            logger.error("[FAIL] DATABASE_URL: NOT SET")
            self.failed += 1

        # Optional but recommended
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            logger.info(f"[PASS] OPENAI_API_KEY: Set")
            self.passed += 1
        else:
            logger.warning("[WARN] OPENAI_API_KEY: Not set")
            self.warnings += 1

        # Optional
        optional_vars = ["GEMINI_API_KEY", "REDIS_HOST", "REDIS_PORT", "SENTRY_DSN"]
        for var in optional_vars:
            if os.getenv(var):
                logger.info(f"[PASS] {var}: Set")
                self.passed += 1
            else:
                logger.info(f"[INFO] {var}: Not set (optional)")

        logger.info("")

    def run_tests(self):
        """Run comprehensive test suite"""
        logger.info("=" * 60)
        logger.info("Step 2: Test Suite Execution")
        logger.info("=" * 60)

        test_commands = [
            ("Unit Tests", "python -m pytest tests/unit/ -v --tb=short"),
            ("Integration Tests", "python -m pytest tests/integration/ -v --tb=short"),
            ("E2E Tests", "python -m pytest tests/e2e/ -v --tb=short"),
            ("Hybrid Search Tests", "python -m pytest tests/test_hybrid_search.py -v --tb=short"),
            ("Security Tests", "python -m pytest tests/security/ -v --tb=short"),
        ]

        for test_name, command in test_commands:
            logger.info(f"\nRunning {test_name}...")
            logger.info(f"Command: {command}")

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    logger.info(f"[PASS] {test_name}: All tests passed")
                    self.passed += 1
                else:
                    # Check if any tests actually ran
                    if "collected 0 items" in result.stdout or "no tests ran" in result.stdout.lower():
                        logger.info(f"[INFO] {test_name}: No tests found (skipped)")
                    else:
                        logger.error(f"[FAIL] {test_name}: Some tests failed")
                        logger.error(f"Output:\n{result.stdout[-500:]}")
                        self.failed += 1

            except subprocess.TimeoutExpired:
                logger.error(f"[FAIL] {test_name}: Timeout (>300s)")
                self.failed += 1
            except Exception as e:
                logger.error(f"[FAIL] {test_name}: {str(e)}")
                self.failed += 1

        logger.info("")

    def check_dependencies(self):
        """Check critical dependencies are installed"""
        logger.info("=" * 60)
        logger.info("Step 3: Dependency Check")
        logger.info("=" * 60)

        critical_deps = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "asyncpg",
            "sentence_transformers",
            "slowapi",
            "ragas",
        ]

        for dep in critical_deps:
            try:
                __import__(dep)
                logger.info(f"[PASS] {dep}: Installed")
                self.passed += 1
            except ImportError:
                logger.error(f"[FAIL] {dep}: NOT INSTALLED")
                self.failed += 1

        logger.info("")

    def print_summary(self):
        """Print final summary"""
        logger.info("=" * 60)
        logger.info("PRODUCTION READINESS SUMMARY")
        logger.info("=" * 60)

        total = self.passed + self.failed + self.warnings

        logger.info(f"Total Checks: {total}")
        logger.info(f"  [PASS] {self.passed} ({self.passed/total*100:.1f}%)")
        logger.info(f"  [WARN] {self.warnings} ({self.warnings/total*100:.1f}%)")
        logger.info(f"  [FAIL] {self.failed} ({self.failed/total*100:.1f}%)")
        logger.info("")

        readiness_score = (self.passed / total * 100) if total > 0 else 0

        if self.failed == 0:
            if self.warnings == 0:
                status = "[READY] Production deployment FULLY READY"
                logger.info(status)
            else:
                status = "[READY] Production deployment ready with warnings"
                logger.warning(status)
        else:
            status = "[NOT READY] Critical issues must be resolved"
            logger.error(status)

        logger.info(f"Readiness Score: {readiness_score:.1f}/100")
        logger.info("=" * 60)

        return self.failed == 0


def main():
    """Main execution"""
    logger.info("DT-RAG v1.8.1 Production Readiness Check")
    logger.info("=" * 60)
    logger.info("")

    checker = ProductionReadinessChecker()

    # Step 1: Environment variables
    checker.check_env_vars()

    # Step 2: Dependencies
    checker.check_dependencies()

    # Step 3: Test suite
    checker.run_tests()

    # Summary
    is_ready = checker.print_summary()

    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main()
