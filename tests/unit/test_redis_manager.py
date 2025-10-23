"""
Unit tests for Redis manager module (apps.api.cache.redis_manager)

This test module provides comprehensive coverage for Redis connection management,
caching operations, and fallback functionality.
"""

import pytest
import asyncio
import json
import pickle
import gzip
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import the modules under test
from apps.api.cache.redis_manager import (
    RedisConfig,
    RedisManager
)


class TestRedisConfig:
    """Test cases for RedisConfig dataclass"""

    @pytest.mark.unit
    def test_redis_config_defaults(self):
        """Test RedisConfig default values"""
        config = RedisConfig()

        # Basic connection settings
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.username is None

        # Connection pool settings
        assert config.max_connections == 50
        assert config.retry_on_timeout is True
        assert config.socket_keepalive is True
        assert config.health_check_interval == 30

        # Timeout settings
        assert config.socket_timeout == 5.0
        assert config.socket_connect_timeout == 5.0

        # Compression settings
        assert config.enable_compression is True
        assert config.compression_threshold == 1024
        assert config.compression_level == 6

        # TTL settings
        assert config.default_ttl == 3600

    @pytest.mark.unit
    def test_redis_config_custom_values(self):
        """Test RedisConfig with custom values"""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            username="redis_user",
            max_connections=100,
            socket_timeout=10.0,
            enable_compression=False,
            default_ttl=7200
        )

        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert config.username == "redis_user"
        assert config.max_connections == 100
        assert config.socket_timeout == 10.0
        assert config.enable_compression is False
        assert config.default_ttl == 7200

    @pytest.mark.unit
    def test_redis_config_post_init_socket_keepalive_options(self):
        """Test RedisConfig post_init sets socket keepalive options"""
        config = RedisConfig()

        assert config.socket_keepalive_options is not None
        assert isinstance(config.socket_keepalive_options, dict)
        assert 1 in config.socket_keepalive_options  # TCP_KEEPIDLE
        assert 2 in config.socket_keepalive_options  # TCP_KEEPINTVL
        assert 3 in config.socket_keepalive_options  # TCP_KEEPCNT

    @pytest.mark.unit
    def test_redis_config_post_init_ttl_configs(self):
        """Test RedisConfig post_init sets TTL configurations"""
        config = RedisConfig()

        assert config.ttl_configs is not None
        assert isinstance(config.ttl_configs, dict)
        assert 'search_results' in config.ttl_configs
        assert 'embeddings' in config.ttl_configs
        assert 'query_suggestions' in config.ttl_configs
        assert 'user_preferences' in config.ttl_configs
        assert 'health_check' in config.ttl_configs
        assert 'metrics' in config.ttl_configs

        # Check specific TTL values
        assert config.ttl_configs['search_results'] == 3600
        assert config.ttl_configs['embeddings'] == 86400 * 7
        assert config.ttl_configs['health_check'] == 300

    @pytest.mark.unit
    def test_redis_config_custom_ttl_configs(self):
        """Test RedisConfig with custom TTL configurations"""
        custom_ttl = {'custom_key': 1800}
        config = RedisConfig(ttl_configs=custom_ttl)

        assert config.ttl_configs == custom_ttl

    @pytest.mark.unit
    def test_redis_config_custom_socket_keepalive_options(self):
        """Test RedisConfig with custom socket keepalive options"""
        custom_options = {1: 5, 2: 10, 3: 15}
        config = RedisConfig(socket_keepalive_options=custom_options)

        assert config.socket_keepalive_options == custom_options


class TestRedisManager:
    """Test cases for RedisManager class"""

    @pytest.fixture
    def redis_config(self):
        """Create Redis configuration for testing"""
        return RedisConfig(
            host="test-redis",
            port=6379,
            default_ttl=1800
        )

    @pytest.fixture
    def redis_manager(self, redis_config):
        """Create RedisManager instance for testing"""
        return RedisManager(redis_config)

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        client = AsyncMock()
        client.ping.return_value = True
        client.get.return_value = None
        client.set.return_value = True
        client.delete.return_value = 1
        client.exists.return_value = False
        client.expire.return_value = True
        client.keys.return_value = []
        client.close.return_value = None
        return client

    @pytest.mark.unit
    def test_redis_manager_init_with_config(self, redis_config):
        """Test RedisManager initialization with config"""
        manager = RedisManager(redis_config)

        assert manager.config == redis_config
        assert manager.client is None
        assert manager.connection_pool is None
        assert manager.is_connected is False
        assert manager.connection_attempts == 0
        assert manager.max_retry_attempts == 3

        # Check stats initialization
        assert manager.stats['operations_total'] == 0
        assert manager.stats['operations_success'] == 0
        assert manager.stats['operations_failed'] == 0

    @pytest.mark.unit
    def test_redis_manager_init_without_config(self):
        """Test RedisManager initialization without config"""
        manager = RedisManager()

        assert isinstance(manager.config, RedisConfig)
        assert manager.config.host == "localhost"  # Default value

    @pytest.mark.unit
    async def test_initialize_redis_not_available(self, redis_manager):
        """Test initialization when Redis is not available"""
        with patch('apps.api.cache.redis_manager.REDIS_AVAILABLE', False):
            result = await redis_manager.initialize()

            assert result is False
            assert redis_manager.is_connected is False

    @pytest.mark.unit
    async def test_initialize_redis_available_success(self, redis_manager, mock_redis_client):
        """Test successful initialization when Redis is available"""
        with patch('apps.api.cache.redis_manager.REDIS_AVAILABLE', True):
            with patch('apps.api.cache.redis_manager.redis') as mock_redis:
                mock_pool = Mock()
                mock_redis.ConnectionPool.return_value = mock_pool
                mock_redis.Redis.return_value = mock_redis_client

                result = await redis_manager.initialize()

                assert result is True
                assert redis_manager.is_connected is True
                assert redis_manager.client == mock_redis_client
                assert redis_manager.connection_pool == mock_pool
                mock_redis_client.ping.assert_called_once()

    @pytest.mark.unit
    async def test_initialize_redis_connection_error(self, redis_manager, mock_redis_client):
        """Test initialization with Redis connection error"""
        with patch('apps.api.cache.redis_manager.REDIS_AVAILABLE', True):
            with patch('apps.api.cache.redis_manager.redis') as mock_redis:
                # Configure mock to raise ConnectionError
                from redis.exceptions import ConnectionError
                mock_redis_client.ping.side_effect = ConnectionError("Connection failed")
                mock_redis.Redis.return_value = mock_redis_client

                result = await redis_manager.initialize()

                assert result is False
                assert redis_manager.is_connected is False

    @pytest.mark.unit
    async def test_get_redis_not_connected(self, redis_manager):
        """Test get operation when Redis is not connected"""
        result = await redis_manager.get("test_key")

        assert result is None

    @pytest.mark.unit
    async def test_get_redis_connected_key_exists(self, redis_manager, mock_redis_client):
        """Test get operation when key exists"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        test_value = {"data": "test_value"}
        serialized_value = json.dumps(test_value).encode()
        mock_redis_client.get.return_value = serialized_value

        # Execute
        result = await redis_manager.get("test_key")

        # Assert
        assert result == test_value
        mock_redis_client.get.assert_called_once_with("test_key")
        assert redis_manager.stats['operations_success'] == 1

    @pytest.mark.unit
    async def test_get_redis_connected_key_not_exists(self, redis_manager, mock_redis_client):
        """Test get operation when key does not exist"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.get.return_value = None

        # Execute
        result = await redis_manager.get("nonexistent_key")

        # Assert
        assert result is None
        mock_redis_client.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.unit
    async def test_get_redis_error(self, redis_manager, mock_redis_client):
        """Test get operation with Redis error"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        from redis.exceptions import RedisError
        mock_redis_client.get.side_effect = RedisError("Redis error")

        # Execute
        result = await redis_manager.get("test_key")

        # Assert
        assert result is None
        assert redis_manager.stats['operations_failed'] == 1

    @pytest.mark.unit
    async def test_set_redis_not_connected(self, redis_manager):
        """Test set operation when Redis is not connected"""
        result = await redis_manager.set("test_key", {"data": "value"})

        assert result is False

    @pytest.mark.unit
    async def test_set_redis_connected_success(self, redis_manager, mock_redis_client):
        """Test successful set operation"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        redis_manager.config.default_ttl = 3600
        mock_redis_client.set.return_value = True

        # Execute
        result = await redis_manager.set("test_key", {"data": "test_value"})

        # Assert
        assert result is True
        mock_redis_client.set.assert_called_once()
        args, kwargs = mock_redis_client.set.call_args
        assert args[0] == "test_key"
        assert "ex" in kwargs
        assert kwargs["ex"] == 3600

    @pytest.mark.unit
    async def test_set_with_custom_ttl(self, redis_manager, mock_redis_client):
        """Test set operation with custom TTL"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.set.return_value = True

        # Execute
        result = await redis_manager.set("test_key", {"data": "value"}, ttl=7200)

        # Assert
        assert result is True
        args, kwargs = mock_redis_client.set.call_args
        assert kwargs["ex"] == 7200

    @pytest.mark.unit
    async def test_set_redis_error(self, redis_manager, mock_redis_client):
        """Test set operation with Redis error"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        from redis.exceptions import RedisError
        mock_redis_client.set.side_effect = RedisError("Redis error")

        # Execute
        result = await redis_manager.set("test_key", {"data": "value"})

        # Assert
        assert result is False
        assert redis_manager.stats['operations_failed'] == 1

    @pytest.mark.unit
    async def test_delete_redis_not_connected(self, redis_manager):
        """Test delete operation when Redis is not connected"""
        result = await redis_manager.delete("test_key")

        assert result is False

    @pytest.mark.unit
    async def test_delete_redis_connected_success(self, redis_manager, mock_redis_client):
        """Test successful delete operation"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.delete.return_value = 1

        # Execute
        result = await redis_manager.delete("test_key")

        # Assert
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")
        assert redis_manager.stats['operations_success'] == 1

    @pytest.mark.unit
    async def test_delete_key_not_exists(self, redis_manager, mock_redis_client):
        """Test delete operation when key does not exist"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.delete.return_value = 0  # Key didn't exist

        # Execute
        result = await redis_manager.delete("nonexistent_key")

        # Assert
        assert result is False

    @pytest.mark.unit
    async def test_exists_redis_not_connected(self, redis_manager):
        """Test exists operation when Redis is not connected"""
        result = await redis_manager.exists("test_key")

        assert result is False

    @pytest.mark.unit
    async def test_exists_redis_connected_key_exists(self, redis_manager, mock_redis_client):
        """Test exists operation when key exists"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.exists.return_value = 1

        # Execute
        result = await redis_manager.exists("test_key")

        # Assert
        assert result is True
        mock_redis_client.exists.assert_called_once_with("test_key")

    @pytest.mark.unit
    async def test_exists_redis_connected_key_not_exists(self, redis_manager, mock_redis_client):
        """Test exists operation when key does not exist"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.exists.return_value = 0

        # Execute
        result = await redis_manager.exists("nonexistent_key")

        # Assert
        assert result is False

    @pytest.mark.unit
    async def test_expire_redis_not_connected(self, redis_manager):
        """Test expire operation when Redis is not connected"""
        result = await redis_manager.expire("test_key", 3600)

        assert result is False

    @pytest.mark.unit
    async def test_expire_redis_connected_success(self, redis_manager, mock_redis_client):
        """Test successful expire operation"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.expire.return_value = True

        # Execute
        result = await redis_manager.expire("test_key", 7200)

        # Assert
        assert result is True
        mock_redis_client.expire.assert_called_once_with("test_key", 7200)

    @pytest.mark.unit
    async def test_keys_redis_not_connected(self, redis_manager):
        """Test keys operation when Redis is not connected"""
        result = await redis_manager.keys("pattern*")

        assert result == []

    @pytest.mark.unit
    async def test_keys_redis_connected_success(self, redis_manager, mock_redis_client):
        """Test successful keys operation"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.keys.return_value = [b"key1", b"key2", b"key3"]

        # Execute
        result = await redis_manager.keys("test_*")

        # Assert
        assert result == ["key1", "key2", "key3"]
        mock_redis_client.keys.assert_called_once_with("test_*")

    @pytest.mark.unit
    async def test_clear_pattern_redis_not_connected(self, redis_manager):
        """Test clear_pattern operation when Redis is not connected"""
        result = await redis_manager.clear_pattern("test_*")

        assert result == 0

    @pytest.mark.unit
    async def test_clear_pattern_redis_connected_success(self, redis_manager, mock_redis_client):
        """Test successful clear_pattern operation"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.keys.return_value = [b"key1", b"key2", b"key3"]
        mock_redis_client.delete.return_value = 3

        # Execute
        result = await redis_manager.clear_pattern("test_*")

        # Assert
        assert result == 3
        mock_redis_client.keys.assert_called_once_with("test_*")
        mock_redis_client.delete.assert_called_once()

    @pytest.mark.unit
    def test_get_stats(self, redis_manager):
        """Test getting Redis manager statistics"""
        # Setup some stats
        redis_manager.stats['operations_total'] = 100
        redis_manager.stats['operations_success'] = 95
        redis_manager.stats['operations_failed'] = 5

        # Execute
        stats = redis_manager.get_stats()

        # Assert
        assert stats['operations_total'] == 100
        assert stats['operations_success'] == 95
        assert stats['operations_failed'] == 5
        assert 'success_rate' in stats
        assert stats['success_rate'] == 0.95

    @pytest.mark.unit
    def test_get_stats_no_operations(self, redis_manager):
        """Test getting stats when no operations performed"""
        stats = redis_manager.get_stats()

        assert stats['success_rate'] == 0.0

    @pytest.mark.unit
    async def test_health_check_redis_not_connected(self, redis_manager):
        """Test health check when Redis is not connected"""
        health = await redis_manager.health_check()

        assert health['status'] == 'disconnected'
        assert health['connected'] is False
        assert 'error' in health

    @pytest.mark.unit
    async def test_health_check_redis_connected_healthy(self, redis_manager, mock_redis_client):
        """Test health check when Redis is connected and healthy"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        mock_redis_client.ping.return_value = True

        # Execute
        health = await redis_manager.health_check()

        # Assert
        assert health['status'] == 'healthy'
        assert health['connected'] is True
        assert health['ping_success'] is True
        assert 'response_time_ms' in health
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.unit
    async def test_health_check_redis_connected_unhealthy(self, redis_manager, mock_redis_client):
        """Test health check when Redis is connected but ping fails"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True
        from redis.exceptions import RedisError
        mock_redis_client.ping.side_effect = RedisError("Ping failed")

        # Execute
        health = await redis_manager.health_check()

        # Assert
        assert health['status'] == 'unhealthy'
        assert health['connected'] is True
        assert health['ping_success'] is False

    @pytest.mark.unit
    async def test_close_redis_connected(self, redis_manager, mock_redis_client):
        """Test close operation when Redis is connected"""
        # Setup
        redis_manager.client = mock_redis_client
        redis_manager.is_connected = True

        # Execute
        await redis_manager.close()

        # Assert
        mock_redis_client.close.assert_called_once()
        assert redis_manager.is_connected is False

    @pytest.mark.unit
    async def test_close_redis_not_connected(self, redis_manager):
        """Test close operation when Redis is not connected"""
        # Should not raise any errors
        await redis_manager.close()

        assert redis_manager.is_connected is False


class TestRedisManagerSerialization:
    """Test cases for Redis data serialization and compression"""

    @pytest.fixture
    def redis_manager_with_compression(self):
        """Create RedisManager with compression enabled"""
        config = RedisConfig(enable_compression=True, compression_threshold=10)
        return RedisManager(config)

    @pytest.fixture
    def redis_manager_without_compression(self):
        """Create RedisManager with compression disabled"""
        config = RedisConfig(enable_compression=False)
        return RedisManager(config)

    @pytest.mark.unit
    def test_serialize_simple_data(self, redis_manager_without_compression):
        """Test serialization of simple data without compression"""
        data = {"key": "value", "number": 42}

        serialized = redis_manager_without_compression._serialize(data)

        assert isinstance(serialized, bytes)
        # Should be JSON serialized
        deserialized = json.loads(serialized.decode())
        assert deserialized == data

    @pytest.mark.unit
    def test_serialize_complex_data(self, redis_manager_without_compression):
        """Test serialization of complex data structures"""
        data = {
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
            "datetime": datetime.now().isoformat()
        }

        serialized = redis_manager_without_compression._serialize(data)
        deserialized = json.loads(serialized.decode())

        assert deserialized["list"] == [1, 2, 3]
        assert deserialized["nested"]["inner"] == "value"

    @pytest.mark.unit
    def test_serialize_with_compression_small_data(self, redis_manager_with_compression):
        """Test serialization with compression for small data (below threshold)"""
        data = {"small": "data"}

        serialized = redis_manager_with_compression._serialize(data)

        # Small data should not be compressed
        assert not serialized.startswith(b'\x1f\x8b')  # gzip magic number

    @pytest.mark.unit
    def test_serialize_with_compression_large_data(self, redis_manager_with_compression):
        """Test serialization with compression for large data"""
        # Create large data that exceeds compression threshold
        data = {"large_data": "x" * 1000}

        serialized = redis_manager_with_compression._serialize(data)

        # Large data should be compressed (starts with gzip magic number)
        assert serialized.startswith(b'\x1f\x8b')

    @pytest.mark.unit
    def test_deserialize_simple_data(self, redis_manager_without_compression):
        """Test deserialization of simple data"""
        original_data = {"key": "value", "number": 42}
        serialized = json.dumps(original_data).encode()

        deserialized = redis_manager_without_compression._deserialize(serialized)

        assert deserialized == original_data

    @pytest.mark.unit
    def test_deserialize_compressed_data(self, redis_manager_with_compression):
        """Test deserialization of compressed data"""
        original_data = {"large_data": "x" * 1000}
        json_data = json.dumps(original_data).encode()
        compressed_data = gzip.compress(json_data, compresslevel=6)

        deserialized = redis_manager_with_compression._deserialize(compressed_data)

        assert deserialized == original_data

    @pytest.mark.unit
    def test_deserialize_invalid_data(self, redis_manager_without_compression):
        """Test deserialization of invalid data"""
        invalid_data = b"invalid json data"

        result = redis_manager_without_compression._deserialize(invalid_data)

        assert result is None

    @pytest.mark.unit
    def test_deserialize_none(self, redis_manager_without_compression):
        """Test deserialization of None"""
        result = redis_manager_without_compression._deserialize(None)

        assert result is None


class TestRedisManagerIntegration:
    """Integration tests for Redis manager functionality"""

    @pytest.fixture
    def redis_manager_integration(self):
        """Create RedisManager for integration testing"""
        config = RedisConfig(
            host="localhost",
            port=6379,
            enable_compression=True,
            compression_threshold=100
        )
        return RedisManager(config)

    @pytest.mark.unit
    async def test_full_operation_cycle(self, redis_manager_integration, mock_redis_client):
        """Test complete cycle of set, get, exists, expire, delete operations"""
        # Setup
        redis_manager_integration.client = mock_redis_client
        redis_manager_integration.is_connected = True

        test_data = {"test": "integration_data", "timestamp": datetime.now().isoformat()}
        key = "integration_test_key"

        # Mock responses
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = json.dumps(test_data).encode()
        mock_redis_client.exists.return_value = 1
        mock_redis_client.expire.return_value = True
        mock_redis_client.delete.return_value = 1

        # Test set
        set_result = await redis_manager_integration.set(key, test_data, ttl=3600)
        assert set_result is True

        # Test get
        get_result = await redis_manager_integration.get(key)
        assert get_result == test_data

        # Test exists
        exists_result = await redis_manager_integration.exists(key)
        assert exists_result is True

        # Test expire
        expire_result = await redis_manager_integration.expire(key, 1800)
        assert expire_result is True

        # Test delete
        delete_result = await redis_manager_integration.delete(key)
        assert delete_result is True

        # Verify all operations were called
        mock_redis_client.set.assert_called_once()
        mock_redis_client.get.assert_called_once_with(key)
        mock_redis_client.exists.assert_called_once_with(key)
        mock_redis_client.expire.assert_called_once_with(key, 1800)
        mock_redis_client.delete.assert_called_once_with(key)

    @pytest.mark.unit
    async def test_batch_operations(self, redis_manager_integration, mock_redis_client):
        """Test batch operations with multiple keys"""
        # Setup
        redis_manager_integration.client = mock_redis_client
        redis_manager_integration.is_connected = True

        keys = ["key1", "key2", "key3"]
        mock_redis_client.keys.return_value = [k.encode() for k in keys]
        mock_redis_client.delete.return_value = len(keys)

        # Test clearing pattern
        result = await redis_manager_integration.clear_pattern("key*")

        assert result == 3
        mock_redis_client.keys.assert_called_once_with("key*")
        mock_redis_client.delete.assert_called_once()

    @pytest.mark.unit
    async def test_error_resilience(self, redis_manager_integration, mock_redis_client):
        """Test error handling and resilience"""
        # Setup
        redis_manager_integration.client = mock_redis_client
        redis_manager_integration.is_connected = True

        from redis.exceptions import RedisError

        # Test that operations handle errors gracefully
        mock_redis_client.get.side_effect = RedisError("Connection lost")
        get_result = await redis_manager_integration.get("test_key")
        assert get_result is None

        mock_redis_client.set.side_effect = RedisError("Write failed")
        set_result = await redis_manager_integration.set("test_key", {"data": "value"})
        assert set_result is False

        # Check error stats
        assert redis_manager_integration.stats['operations_failed'] == 2