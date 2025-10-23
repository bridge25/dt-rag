"""
Performance test fixtures and configuration
@CODE:TEST-003:INFRA | SPEC: SPEC-TEST-003.md
"""
import pytest
import json
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    yield


@pytest.fixture(autouse=True)
def cleanup_test_files():
    yield


@pytest.fixture(scope="session")
def performance_baseline():
    """
    Load performance baseline metrics for regression detection
    @CODE:TEST-003:INFRA:BASELINE | SPEC: SPEC-TEST-003.md
    """
    baseline_file = Path("reports/performance_baseline.json")
    if baseline_file.exists():
        with open(baseline_file) as f:
            return json.load(f)
    return {}


def pytest_configure(config):
    """Configure pytest markers and benchmark settings"""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as pytest-benchmark tests"
    )
    config.addinivalue_line(
        "markers", "load: marks tests as load/stress tests"
    )
