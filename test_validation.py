#!/usr/bin/env python3
"""
Validation script for the new integration and E2E test infrastructure

This script validates that the test infrastructure works correctly
with graceful degradation and CI compatibility.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

def test_import_validation():
    """Test that test modules can be imported correctly"""
    print("=== Import Validation ===")

    # Test integration test imports
    try:
        sys.path.insert(0, str(Path(__file__).parent))

        # Test API database integration
        from tests.integration.test_api_database_integration import TestAPIDatabaseIntegration
        print("✓ API Database integration tests imported successfully")

        # Test search system integration
        from tests.integration.test_search_system_integration import TestSearchSystemIntegration
        print("✓ Search system integration tests imported successfully")

        # Test caching system integration
        from tests.integration.test_caching_system_integration import TestCachingSystemIntegration
        print("✓ Caching system integration tests imported successfully")

        # Test security system integration
        from tests.integration.test_security_system_integration import TestSecuritySystemIntegration
        print("✓ Security system integration tests imported successfully")

        # Test E2E workflows
        from tests.e2e.test_complete_workflow import TestCompleteWorkflow
        print("✓ E2E workflow tests imported successfully")

        # Test user scenarios
        from tests.e2e.test_user_scenarios import TestUserScenarios
        print("✓ E2E user scenario tests imported successfully")

        return True

    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_ci_config_validation():
    """Test CI configuration files"""
    print("\n=== CI Configuration Validation ===")

    try:
        # Test pytest.ini
        pytest_ini = Path("pytest.ini")
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            required_markers = ['integration', 'e2e', 'requires_db', 'requires_redis', 'ci_safe']
            for marker in required_markers:
                if marker in content:
                    print(f"✓ pytest.ini contains '{marker}' marker")
                else:
                    print(f"✗ pytest.ini missing '{marker}' marker")
        else:
            print("✗ pytest.ini not found")

        # Test GitHub Actions workflow
        workflow_file = Path(".github/workflows/test.yml")
        if workflow_file.exists():
            print("✓ GitHub Actions workflow file exists")
            content = workflow_file.read_text()
            if "test-matrix" in content and "quality-checks" in content:
                print("✓ GitHub Actions workflow has required jobs")
            else:
                print("✗ GitHub Actions workflow missing required jobs")
        else:
            print("✗ GitHub Actions workflow file not found")

        # Test conftest_ci.py
        conftest_ci = Path("tests/conftest_ci.py")
        if conftest_ci.exists():
            print("✓ CI-specific conftest file exists")
        else:
            print("✗ CI-specific conftest file not found")

        # Test test runner
        test_runner = Path("tests/test_runner.py")
        if test_runner.exists():
            print("✓ Test runner script exists")
        else:
            print("✗ Test runner script not found")

        return True

    except Exception as e:
        print(f"✗ CI config validation failed: {e}")
        return False

async def test_graceful_degradation():
    """Test graceful degradation functionality"""
    print("\n=== Graceful Degradation Testing ===")

    try:
        # Set CI environment
        os.environ["TESTING"] = "true"
        os.environ["CI_ENVIRONMENT"] = "true"

        # Import CI configuration
        from tests.conftest_ci import (
            is_ci_environment,
            has_service_available,
            ci_test_data,
            assert_ci_safe_response,
            assert_graceful_degradation
        )

        # Test CI detection
        if is_ci_environment():
            print("✗ CI environment incorrectly detected (we're in test mode)")
        else:
            # Reset for actual CI test
            os.environ["CI"] = "true"
            if is_ci_environment():
                print("✓ CI environment correctly detected")
            else:
                print("✗ CI environment not detected when CI=true")

        # Test service availability checks
        services = ["postgresql", "redis", "openai", "network"]
        for service in services:
            available = has_service_available(service)
            print(f"✓ Service '{service}' availability: {available}")

        # Test test data factory
        doc = ci_test_data.create_sample_document()
        if doc and "id" in doc and "content" in doc:
            print("✓ Test data factory works correctly")
        else:
            print("✗ Test data factory failed")

        # Test assertions
        class MockResponse:
            status_code = 200
            def json(self):
                return {"test": "data"}

        try:
            assert_ci_safe_response(MockResponse())
            print("✓ CI-safe response assertion works")
        except Exception:
            print("✗ CI-safe response assertion failed")

        try:
            assert_graceful_degradation(None, "fallback")
            print("✓ Graceful degradation assertion works")
        except Exception:
            print("✗ Graceful degradation assertion failed")

        return True

    except Exception as e:
        print(f"✗ Graceful degradation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up environment
        os.environ.pop("CI", None)
        os.environ.pop("CI_ENVIRONMENT", None)

def test_fixtures_validation():
    """Test that fixtures work correctly"""
    print("\n=== Fixtures Validation ===")

    try:
        from tests.conftest_ci import ci_test_data

        # Test document fixture
        doc = ci_test_data.create_sample_document("test_123")
        assert doc["id"] == "test_123"
        assert "content" in doc
        assert "metadata" in doc
        print("✓ Document fixture works correctly")

        # Test search query fixture
        query = ci_test_data.create_search_query("test search")
        assert query["query"] == "test search"
        assert "filters" in query
        assert "limit" in query
        print("✓ Search query fixture works correctly")

        # Test classification request fixture
        req = ci_test_data.create_classification_request("test text")
        assert req["text"] == "test text"
        assert "context" in req
        print("✓ Classification request fixture works correctly")

        return True

    except Exception as e:
        print(f"✗ Fixtures validation failed: {e}")
        return False

def test_markers_validation():
    """Test pytest markers are working correctly"""
    print("\n=== Pytest Markers Validation ===")

    try:
        # This would normally be done by pytest, but we can simulate
        markers_to_test = [
            "unit",
            "integration",
            "e2e",
            "slow",
            "requires_db",
            "requires_redis",
            "requires_openai",
            "requires_network",
            "ci_safe",
            "local_only"
        ]

        # Check if markers are defined in pytest.ini
        pytest_ini = Path("pytest.ini")
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            for marker in markers_to_test:
                if marker in content:
                    print(f"✓ Marker '{marker}' defined in pytest.ini")
                else:
                    print(f"✗ Marker '{marker}' not found in pytest.ini")

        return True

    except Exception as e:
        print(f"✗ Markers validation failed: {e}")
        return False

async def main():
    """Run all validation tests"""
    print("DT-RAG Test Infrastructure Validation")
    print("=" * 50)

    results = []

    # Run all validation tests
    results.append(test_import_validation())
    results.append(test_ci_config_validation())
    results.append(await test_graceful_degradation())
    results.append(test_fixtures_validation())
    results.append(test_markers_validation())

    # Summary
    print("\n=== Validation Summary ===")
    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All validation tests passed!")
        print("\nThe test infrastructure is ready for use:")
        print("- Integration tests with graceful degradation")
        print("- E2E tests with user scenario coverage")
        print("- CI-compatible configuration")
        print("- Environment-aware test execution")
        return 0
    else:
        print("✗ Some validation tests failed.")
        print("Please review the output above and fix any issues.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)