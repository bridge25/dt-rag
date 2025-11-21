"""
Unit tests for health check module (apps.api.monitoring.health_check)

This test module provides comprehensive coverage for system health monitoring
functionality including component health checks and system status aggregation.

@TEST:API-001
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the modules under test
from apps.api.monitoring.health_check import (
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    HealthChecker,
)


class TestHealthStatus:
    """Test cases for HealthStatus enum"""

    @pytest.mark.unit
    def test_health_status_values(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"

    @pytest.mark.unit
    def test_health_status_comparison(self):
        """Test HealthStatus comparison and equality"""
        assert HealthStatus.HEALTHY == HealthStatus.HEALTHY
        assert HealthStatus.HEALTHY != HealthStatus.UNHEALTHY  # type: ignore[comparison-overlap]


class TestComponentHealth:
    """Test cases for ComponentHealth dataclass"""

    @pytest.mark.unit
    def test_component_health_creation_minimal(self):
        """Test ComponentHealth creation with minimal parameters"""
        health = ComponentHealth(name="test_component", status=HealthStatus.HEALTHY)

        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert health.response_time_ms is None
        assert health.last_check is None
        assert health.error_message is None
        assert health.metadata is None

    @pytest.mark.unit
    def test_component_health_creation_full(self):
        """Test ComponentHealth creation with all parameters"""
        timestamp = datetime.now()
        metadata = {"key": "value", "count": 42}

        health = ComponentHealth(
            name="database",
            status=HealthStatus.DEGRADED,
            response_time_ms=125.5,
            last_check=timestamp,
            error_message="Connection timeout",
            metadata=metadata,
        )

        assert health.name == "database"
        assert health.status == HealthStatus.DEGRADED
        assert health.response_time_ms == 125.5
        assert health.last_check == timestamp
        assert health.error_message == "Connection timeout"
        assert health.metadata == metadata

    @pytest.mark.unit
    def test_component_health_to_dict(self):
        """Test ComponentHealth conversion to dictionary"""
        timestamp = datetime.now()
        health = ComponentHealth(
            name="api",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
            last_check=timestamp,
            metadata={"version": "1.0"},
        )

        result = health.to_dict()

        assert result["name"] == "api"
        assert result["status"] == "healthy"
        assert result["response_time_ms"] == 50.0
        assert result["last_check"] == timestamp.isoformat()
        assert result["error_message"] is None
        assert result["metadata"] == {"version": "1.0"}

    @pytest.mark.unit
    def test_component_health_to_dict_no_timestamp(self):
        """Test ComponentHealth to_dict without timestamp"""
        health = ComponentHealth(name="cache", status=HealthStatus.UNHEALTHY)

        result = health.to_dict()

        assert result["name"] == "cache"
        assert result["status"] == "unhealthy"
        assert result["last_check"] is None


class TestSystemHealth:
    """Test cases for SystemHealth dataclass"""

    @pytest.fixture
    def sample_components(self):
        """Create sample component health objects"""
        return [
            ComponentHealth("database", HealthStatus.HEALTHY, response_time_ms=25.0),
            ComponentHealth("cache", HealthStatus.DEGRADED, response_time_ms=150.0),
            ComponentHealth("storage", HealthStatus.HEALTHY, response_time_ms=10.0),
        ]

    @pytest.mark.unit
    def test_system_health_creation(self, sample_components):
        """Test SystemHealth creation"""
        timestamp = datetime.now()
        uptime = 3600.0

        health = SystemHealth(
            overall_status=HealthStatus.DEGRADED,
            components=sample_components,
            timestamp=timestamp,
            uptime_seconds=uptime,
            version="1.8.1",
        )

        assert health.overall_status == HealthStatus.DEGRADED
        assert len(health.components) == 3
        assert health.timestamp == timestamp
        assert health.uptime_seconds == uptime
        assert health.version == "1.8.1"

    @pytest.mark.unit
    def test_system_health_to_dict(self, sample_components):
        """Test SystemHealth conversion to dictionary"""
        timestamp = datetime.now()
        health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            components=sample_components,
            timestamp=timestamp,
            uptime_seconds=1800.0,
        )

        result = health.to_dict()

        assert result["overall_status"] == "healthy"
        assert len(result["components"]) == 3
        assert result["timestamp"] == timestamp.isoformat()
        assert result["uptime_seconds"] == 1800.0
        assert result["version"] == "1.8.1"

        # Check component serialization
        assert result["components"][0]["name"] == "database"
        assert result["components"][0]["status"] == "healthy"

    @pytest.mark.unit
    def test_system_health_default_version(self, sample_components):
        """Test SystemHealth with default version"""
        health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            components=sample_components,
            timestamp=datetime.now(),
            uptime_seconds=1000.0,
        )

        assert health.version == "1.8.1"


class TestHealthChecker:
    """Test cases for HealthChecker class"""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance for testing"""
        with patch.object(HealthChecker, "_register_default_checks"):
            checker = HealthChecker()
            return checker

    @pytest.mark.unit
    def test_health_checker_init(self):
        """Test HealthChecker initialization"""
        with patch.object(HealthChecker, "_register_default_checks") as mock_register:
            start_time = datetime.now()

            checker = HealthChecker()

            assert checker.start_time is not None
            assert isinstance(checker.health_checks, dict)
            assert isinstance(checker.last_results, dict)
            assert checker.check_interval == 30
            assert checker.timeout == 5
            mock_register.assert_called_once()

    @pytest.mark.unit
    def test_register_check(self, health_checker):
        """Test registering a health check function"""

        def dummy_check():
            return ComponentHealth("dummy", HealthStatus.HEALTHY)

        health_checker.register_check("dummy", dummy_check)

        assert "dummy" in health_checker.health_checks
        assert health_checker.health_checks["dummy"] == dummy_check

    @pytest.mark.unit
    def test_register_default_checks(self):
        """Test that default health checks are registered"""
        checker = HealthChecker()

        expected_checks = ["system", "database", "cache", "storage"]
        for check_name in expected_checks:
            assert check_name in checker.health_checks
            assert callable(checker.health_checks[check_name])

    @pytest.mark.unit
    async def test_check_system_health_success(self, health_checker):
        """Test successful system health check"""
        with patch("psutil.cpu_percent", return_value=25.0):
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value.percent = 60.0
                with patch("psutil.disk_usage") as mock_disk:
                    mock_disk.return_value.percent = 45.0

                    result = await health_checker._check_system_health()

                    assert isinstance(result, ComponentHealth)
                    assert result.name == "system"
                    assert result.status == HealthStatus.HEALTHY
                    assert result.response_time_ms is not None
                    assert result.response_time_ms >= 0
                    assert result.last_check is not None
                    assert result.metadata is not None
                    assert "cpu_percent" in result.metadata
                    assert "memory_percent" in result.metadata
                    assert "disk_percent" in result.metadata

    @pytest.mark.unit
    async def test_check_system_health_degraded(self, health_checker):
        """Test system health check with degraded performance"""
        with patch("psutil.cpu_percent", return_value=85.0):  # High CPU
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value.percent = 90.0  # High memory
                with patch("psutil.disk_usage") as mock_disk:
                    mock_disk.return_value.percent = 50.0

                    result = await health_checker._check_system_health()

                    assert result.status == HealthStatus.DEGRADED

    @pytest.mark.unit
    async def test_check_system_health_unhealthy(self, health_checker):
        """Test system health check with unhealthy conditions"""
        with patch("psutil.cpu_percent", return_value=95.0):  # Very high CPU
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value.percent = 98.0  # Very high memory
                with patch("psutil.disk_usage") as mock_disk:
                    mock_disk.return_value.percent = 95.0  # Very high disk

                    result = await health_checker._check_system_health()

                    assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.unit
    async def test_check_system_health_exception(self, health_checker):
        """Test system health check with exception"""
        with patch("psutil.cpu_percent", side_effect=Exception("CPU check failed")):
            result = await health_checker._check_system_health()

            assert result.status == HealthStatus.UNKNOWN
            assert "CPU check failed" in result.error_message

    @pytest.mark.unit
    async def test_check_database_health_success(self, health_checker):
        """Test successful database health check"""
        # Mock database connection and operations
        with patch(
            "apps.api.monitoring.health_check.test_database_connection"
        ) as mock_db_test:
            mock_db_test.return_value = True

            result = await health_checker._check_database_health()

            assert isinstance(result, ComponentHealth)
            assert result.name == "database"
            # Status depends on the actual implementation

    @pytest.mark.unit
    async def test_check_database_health_failure(self, health_checker):
        """Test database health check failure"""
        with patch(
            "apps.api.monitoring.health_check.test_database_connection"
        ) as mock_db_test:
            mock_db_test.side_effect = Exception("Database connection failed")

            result = await health_checker._check_database_health()

            assert result.name == "database"
            assert result.status in [HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]

    @pytest.mark.unit
    async def test_check_cache_health_redis_available(self, health_checker):
        """Test cache health check when Redis is available"""
        mock_redis_manager = Mock()
        mock_redis_manager.health_check = AsyncMock(
            return_value={
                "status": "healthy",
                "connected": True,
                "ping_success": True,
                "response_time_ms": 15.0,
            }
        )

        with patch(
            "apps.api.monitoring.health_check.RedisManager",
            return_value=mock_redis_manager,
        ):
            result = await health_checker._check_cache_health()

            assert result.name == "cache"
            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms == 15.0

    @pytest.mark.unit
    async def test_check_cache_health_redis_unavailable(self, health_checker):
        """Test cache health check when Redis is unavailable"""
        with patch("apps.api.monitoring.health_check.REDIS_AVAILABLE", False):
            result = await health_checker._check_cache_health()

            assert result.name == "cache"
            assert result.status == HealthStatus.UNKNOWN
            assert "Redis not available" in result.error_message

    @pytest.mark.unit
    async def test_check_storage_health_success(self, health_checker):
        """Test successful storage health check"""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=True):
                with patch("psutil.disk_usage") as mock_disk_usage:
                    mock_disk_usage.return_value.free = 10 * 1024**3  # 10GB free

                    result = await health_checker._check_storage_health()

                    assert result.name == "storage"
                    assert result.status == HealthStatus.HEALTHY
                    assert result.metadata is not None
                    assert "free_space_gb" in result.metadata

    @pytest.mark.unit
    async def test_check_storage_health_low_space(self, health_checker):
        """Test storage health check with low disk space"""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=True):
                with patch("psutil.disk_usage") as mock_disk_usage:
                    mock_disk_usage.return_value.free = (
                        0.5 * 1024**3
                    )  # 0.5GB free (low)

                    result = await health_checker._check_storage_health()

                    assert result.name == "storage"
                    assert result.status in [
                        HealthStatus.DEGRADED,
                        HealthStatus.UNHEALTHY,
                    ]

    @pytest.mark.unit
    async def test_check_storage_health_no_access(self, health_checker):
        """Test storage health check without write access"""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=False):  # No write access
                result = await health_checker._check_storage_health()

                assert result.name == "storage"
                assert result.status == HealthStatus.UNHEALTHY
                assert "No write access" in result.error_message

    @pytest.mark.unit
    async def test_check_all_health_success(self, health_checker):
        """Test checking all health components successfully"""
        # Mock all health check methods to return healthy status
        mock_system = ComponentHealth("system", HealthStatus.HEALTHY)
        mock_database = ComponentHealth("database", HealthStatus.HEALTHY)
        mock_cache = ComponentHealth("cache", HealthStatus.HEALTHY)
        mock_storage = ComponentHealth("storage", HealthStatus.HEALTHY)

        health_checker._check_system_health = AsyncMock(return_value=mock_system)
        health_checker._check_database_health = AsyncMock(return_value=mock_database)
        health_checker._check_cache_health = AsyncMock(return_value=mock_cache)
        health_checker._check_storage_health = AsyncMock(return_value=mock_storage)

        system_health = await health_checker.check_all_health()

        assert isinstance(system_health, SystemHealth)
        assert system_health.overall_status == HealthStatus.HEALTHY
        assert len(system_health.components) == 4
        assert system_health.uptime_seconds > 0
        assert system_health.version == "1.8.1"

    @pytest.mark.unit
    async def test_check_all_health_mixed_status(self, health_checker):
        """Test checking all health with mixed component statuses"""
        # Mock mixed health statuses
        mock_system = ComponentHealth("system", HealthStatus.HEALTHY)
        mock_database = ComponentHealth("database", HealthStatus.DEGRADED)
        mock_cache = ComponentHealth("cache", HealthStatus.HEALTHY)
        mock_storage = ComponentHealth("storage", HealthStatus.UNHEALTHY)

        health_checker._check_system_health = AsyncMock(return_value=mock_system)
        health_checker._check_database_health = AsyncMock(return_value=mock_database)
        health_checker._check_cache_health = AsyncMock(return_value=mock_cache)
        health_checker._check_storage_health = AsyncMock(return_value=mock_storage)

        system_health = await health_checker.check_all_health()

        # Overall status should be the worst component status
        assert system_health.overall_status == HealthStatus.UNHEALTHY
        assert len(system_health.components) == 4

    @pytest.mark.unit
    async def test_check_all_health_with_timeout(self, health_checker):
        """Test health check with timeout handling"""

        # Mock one health check to timeout
        async def slow_check():
            await asyncio.sleep(10)  # Longer than timeout
            return ComponentHealth("slow", HealthStatus.HEALTHY)

        health_checker.register_check("slow", slow_check)
        health_checker.timeout = 0.1  # Very short timeout

        system_health = await health_checker.check_all_health()

        # Should still complete with timeout handling
        assert isinstance(system_health, SystemHealth)
        # Check that slow component has timeout status
        slow_component = next(
            (c for c in system_health.components if c.name == "slow"), None
        )
        if slow_component:
            assert slow_component.status in [
                HealthStatus.UNKNOWN,
                HealthStatus.UNHEALTHY,
            ]

    @pytest.mark.unit
    async def test_check_specific_component_success(self, health_checker):
        """Test checking specific component health"""
        mock_result = ComponentHealth(
            "system", HealthStatus.HEALTHY, response_time_ms=50.0
        )
        health_checker._check_system_health = AsyncMock(return_value=mock_result)

        result = await health_checker.check_component_health("system")

        assert result == mock_result
        assert result.name == "system"
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.unit
    async def test_check_specific_component_not_found(self, health_checker):
        """Test checking non-existent component health"""
        result = await health_checker.check_component_health("nonexistent")

        assert result is None

    @pytest.mark.unit
    def test_get_uptime(self, health_checker):
        """Test getting system uptime"""
        # Set a known start time
        health_checker.start_time = datetime.now() - timedelta(
            seconds=3600
        )  # 1 hour ago

        uptime = health_checker.get_uptime()

        assert uptime >= 3600.0
        assert uptime < 3700.0  # Should be close to 1 hour

    @pytest.mark.unit
    def test_determine_overall_status_all_healthy(self, health_checker):
        """Test overall status determination with all healthy components"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY),
            ComponentHealth("comp2", HealthStatus.HEALTHY),
            ComponentHealth("comp3", HealthStatus.HEALTHY),
        ]

        status = health_checker._determine_overall_status(components)

        assert status == HealthStatus.HEALTHY

    @pytest.mark.unit
    def test_determine_overall_status_mixed(self, health_checker):
        """Test overall status determination with mixed component statuses"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY),
            ComponentHealth("comp2", HealthStatus.DEGRADED),
            ComponentHealth("comp3", HealthStatus.HEALTHY),
        ]

        status = health_checker._determine_overall_status(components)

        assert status == HealthStatus.DEGRADED

    @pytest.mark.unit
    def test_determine_overall_status_worst_case(self, health_checker):
        """Test overall status determination with unhealthy components"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY),
            ComponentHealth("comp2", HealthStatus.DEGRADED),
            ComponentHealth("comp3", HealthStatus.UNHEALTHY),
        ]

        status = health_checker._determine_overall_status(components)

        assert status == HealthStatus.UNHEALTHY

    @pytest.mark.unit
    def test_determine_overall_status_empty_components(self, health_checker):
        """Test overall status determination with no components"""
        status = health_checker._determine_overall_status([])

        assert status == HealthStatus.UNKNOWN


class TestHealthCheckerIntegration:
    """Integration tests for HealthChecker functionality"""

    @pytest.mark.unit
    async def test_full_health_check_cycle(self):
        """Test complete health check cycle"""
        checker = HealthChecker()

        # Perform health check
        system_health = await checker.check_all_health()  # type: ignore[attr-defined]

        # Verify results structure
        assert isinstance(system_health, SystemHealth)
        assert isinstance(system_health.overall_status, HealthStatus)
        assert len(system_health.components) >= 4  # At least default components
        assert system_health.timestamp is not None
        assert system_health.uptime_seconds > 0
        assert system_health.version == "1.8.1"

        # Verify all components have required fields
        for component in system_health.components:
            assert isinstance(component, ComponentHealth)
            assert component.name is not None
            assert isinstance(component.status, HealthStatus)

    @pytest.mark.unit
    async def test_custom_health_check_registration(self):
        """Test registration and execution of custom health checks"""
        checker = HealthChecker()

        async def custom_health_check():
            return ComponentHealth(
                "custom", HealthStatus.HEALTHY, response_time_ms=25.0
            )

        # Register custom check
        checker.register_check("custom", custom_health_check)

        # Verify registration
        assert "custom" in checker.health_checks

        # Check specific component
        result = await checker.check_component_health("custom")  # type: ignore[attr-defined]

        assert result is not None
        assert result.name == "custom"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms == 25.0

    @pytest.mark.unit
    def test_health_status_serialization(self):
        """Test health status objects can be properly serialized"""
        # Create complex health status
        components = [
            ComponentHealth(
                name="api",
                status=HealthStatus.HEALTHY,
                response_time_ms=45.2,
                last_check=datetime.now(),
                metadata={"version": "1.0", "requests_per_second": 150},
            ),
            ComponentHealth(
                name="worker",
                status=HealthStatus.DEGRADED,
                error_message="High queue size",
            ),
        ]

        system_health = SystemHealth(
            overall_status=HealthStatus.DEGRADED,
            components=components,
            timestamp=datetime.now(),
            uptime_seconds=7200.5,
        )

        # Test serialization
        serialized = system_health.to_dict()

        assert isinstance(serialized, dict)
        assert serialized["overall_status"] == "degraded"
        assert len(serialized["components"]) == 2
        assert serialized["components"][0]["name"] == "api"
        assert serialized["components"][0]["status"] == "healthy"
        assert serialized["components"][1]["status"] == "degraded"
        assert "timestamp" in serialized
        assert serialized["uptime_seconds"] == 7200.5
