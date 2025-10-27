import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    yield


@pytest.fixture(autouse=True)
def cleanup_test_files():
    yield


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
