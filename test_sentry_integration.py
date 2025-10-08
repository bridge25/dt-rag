"""
Test Sentry Integration for DT-RAG v1.8.1

Quick validation test for Sentry monitoring integration.
Run this to verify Sentry is properly configured.
"""

import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))


def test_sentry_import():
    """Test that Sentry module can be imported"""
    print("Testing Sentry import...")
    try:
        from monitoring.sentry_reporter import (
            init_sentry,
            report_search_failure,
            SentryReport,
            SENTRY_AVAILABLE
        )
        print(f"✅ Sentry imports successful (available: {SENTRY_AVAILABLE})")
        return True
    except ImportError as e:
        print(f"❌ Sentry import failed: {e}")
        return False


def test_sentry_report_structure():
    """Test SentryReport dataclass structure"""
    print("\nTesting SentryReport structure...")
    try:
        from monitoring.sentry_reporter import SentryReport

        report = SentryReport(
            reproduction_steps={
                "query": "test query",
                "search_type": "hybrid"
            },
            expected_behavior="Expected successful search",
            actual_behavior="Search failed",
            metrics={"total_time": 1.5},
            possible_causes=["Database error"],
            next_steps=["Check database connection"],
            error_boundary="test",
            search_type="hybrid"
        )

        assert report.reproduction_steps["query"] == "test query"
        assert report.search_type == "hybrid"
        print("✅ SentryReport structure validated")
        return True
    except Exception as e:
        print(f"❌ SentryReport test failed: {e}")
        return False


def test_sentry_initialization():
    """Test Sentry initialization (dry run)"""
    print("\nTesting Sentry initialization...")
    try:
        from monitoring.sentry_reporter import init_sentry, SENTRY_AVAILABLE

        if not SENTRY_AVAILABLE:
            print("⚠️ Sentry SDK not installed - install with: pip install sentry-sdk[fastapi]")
            return False

        # Test with empty DSN (should fail gracefully)
        result = init_sentry(dsn=None)
        assert result is False, "Should return False for empty DSN"

        print("✅ Sentry initialization test passed")
        return True
    except Exception as e:
        print(f"❌ Sentry initialization test failed: {e}")
        return False


def test_error_reporting_mock():
    """Test error reporting with mock data"""
    print("\nTesting error reporting (mock)...")
    try:
        from monitoring.sentry_reporter import (
            report_search_failure,
            SENTRY_AVAILABLE
        )

        # Test with actual exception (won't send without DSN)
        try:
            raise ValueError("Test error for Sentry reporting")
        except Exception as e:
            report_search_failure(
                error=e,
                query="test query",
                filters={"test": "filter"},
                metrics={
                    "total_time": 2.5,
                    "bm25_time": 0.8,
                    "vector_time": 1.2,
                    "cache_hit": False
                },
                search_type="hybrid",
                error_boundary="test_integration"
            )

        print(f"✅ Error reporting executed (Sentry available: {SENTRY_AVAILABLE})")
        return True
    except Exception as e:
        print(f"❌ Error reporting test failed: {e}")
        return False


def test_hybrid_search_integration():
    """Test hybrid search engine Sentry integration"""
    print("\nTesting hybrid search engine integration...")
    try:
        # Import to verify integration points exist
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "apps"))

        from search.hybrid_search_engine import SENTRY_AVAILABLE

        print(f"✅ Hybrid search engine Sentry integration loaded (available: {SENTRY_AVAILABLE})")
        return True
    except Exception as e:
        print(f"❌ Hybrid search integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DT-RAG v1.8.1 - Sentry Integration Tests")
    print("=" * 60)

    tests = [
        test_sentry_import,
        test_sentry_report_structure,
        test_sentry_initialization,
        test_error_reporting_mock,
        test_hybrid_search_integration
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check output above.")

    print("\nNext Steps:")
    print("1. Install Sentry SDK: pip install sentry-sdk[fastapi]")
    print("2. Configure SENTRY_DSN in .env file")
    print("3. Run API server and verify Sentry dashboard")
    print("4. Trigger test error and verify report in Sentry")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
