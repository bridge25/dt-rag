"""
Comprehensive Test Suite for API Key Validation

Tests the complete API key security implementation including:
- Format validation and entropy checks
- Rate limiting and abuse protection
- Database integration and permissions
- Audit logging and compliance features
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from apps.api.deps import (
    APIKeyValidator, verify_api_key, _check_rate_limit,
    _hash_api_key, _log_security_event
)
from apps.api.security import (
    SecureAPIKeyGenerator, APIKeyConfig, APIKeyManager,
    APIKeyCreateRequest, generate_production_key
)

class TestAPIKeyValidator:
    """Test the API key format validation logic"""

    def test_entropy_calculation(self):
        """Test Shannon entropy calculation"""
        # High entropy key
        high_entropy_key = "Kx2mP9zL4nQ8rT5wX7yC1vB6nM3kJ9hF"
        entropy = APIKeyValidator.calculate_entropy(high_entropy_key)
        assert entropy > 96, f"High entropy key should have >96 bits, got {entropy}"

        # Low entropy key (repeated characters)
        low_entropy_key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        entropy = APIKeyValidator.calculate_entropy(low_entropy_key)
        assert entropy < 50, f"Low entropy key should have <50 bits, got {entropy}"

        # Empty key
        assert APIKeyValidator.calculate_entropy("") == 0

    def test_character_composition_validation(self):
        """Test character composition requirements"""
        # Valid keys with mixed character types
        assert APIKeyValidator.validate_character_composition("Abc123!@#$%^&*()_+-=[]{}|;:,.<>?")
        assert APIKeyValidator.validate_character_composition("MySecureKey2023WithSpecial!")

        # Invalid keys
        assert not APIKeyValidator.validate_character_composition("onlylowercase")  # Too short + single type
        assert not APIKeyValidator.validate_character_composition("12345")  # Too short + single type
        assert not APIKeyValidator.validate_character_composition("abc")  # Too short

    def test_weak_pattern_detection(self):
        """Test detection of weak patterns"""
        # Valid keys without weak patterns
        assert APIKeyValidator.check_weak_patterns("Kx2mP9zL4nQ8rT5wX7yC1vB6nM3kJ9hF")
        assert APIKeyValidator.check_weak_patterns("SecureRandomKey2023WithoutPatterns")

        # Invalid keys with weak patterns
        assert not APIKeyValidator.check_weak_patterns("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")  # Repeated chars
        assert not APIKeyValidator.check_weak_patterns("1234567890123456789012345678901234")  # Sequential
        assert not APIKeyValidator.check_weak_patterns("passwordsecretadmintestdemoexample")  # Common words
        assert not APIKeyValidator.check_weak_patterns("qwertyuiopasdfghjklzxcvbnmqwertyu")  # Keyboard pattern

    def test_format_validation(self):
        """Test API key format validation"""
        # Valid formats
        assert APIKeyValidator.validate_format("YWJjZGVmZ2hpams123456789012345678") == "base64"
        assert APIKeyValidator.validate_format("abcdef1234567890abcdef1234567890ab") == "hex"
        assert APIKeyValidator.validate_format("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef12") == "alphanumeric"
        assert APIKeyValidator.validate_format("SecureKey2023_with-dots.and_dash123") == "secure"

        # Invalid formats
        assert APIKeyValidator.validate_format("") == "empty"
        assert APIKeyValidator.validate_format("abc") == "invalid"
        assert APIKeyValidator.validate_format("invalid@#$%^&*()characters") == "invalid"

    def test_comprehensive_validation(self):
        """Test the complete validation pipeline"""
        # Generate a secure key for testing
        generated_key = generate_production_key()
        is_valid, errors = APIKeyValidator.comprehensive_validate(generated_key.key)
        assert is_valid, f"Generated production key should be valid, errors: {errors}"

        # Test invalid keys
        is_valid, errors = APIKeyValidator.comprehensive_validate("short")
        assert not is_valid
        assert any("32 characters" in error for error in errors)

        is_valid, errors = APIKeyValidator.comprehensive_validate("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert not is_valid
        assert any("entropy" in error.lower() for error in errors)

class TestSecureAPIKeyGenerator:
    """Test the secure API key generation"""

    def test_base64_key_generation(self):
        """Test base64 key generation"""
        key = SecureAPIKeyGenerator.generate_base64_key(32)
        assert len(key) == 32
        assert APIKeyValidator.validate_format(key) == "base64"

    def test_hex_key_generation(self):
        """Test hexadecimal key generation"""
        key = SecureAPIKeyGenerator.generate_hex_key(32)
        assert len(key) == 32
        assert APIKeyValidator.validate_format(key) == "hex"

    def test_alphanumeric_key_generation(self):
        """Test alphanumeric key generation"""
        key = SecureAPIKeyGenerator.generate_alphanumeric_key(32)
        assert len(key) == 32
        assert APIKeyValidator.validate_format(key) == "alphanumeric"

    def test_mixed_key_generation(self):
        """Test mixed character key generation"""
        key = SecureAPIKeyGenerator.generate_mixed_key(32)
        assert len(key) == 32

        # Test with special characters
        key_with_special = SecureAPIKeyGenerator.generate_mixed_key(32, include_special=True)
        assert len(key_with_special) == 32

    def test_entropy_validation(self):
        """Test that generated keys have sufficient entropy"""
        for _ in range(10):  # Test multiple generations
            key = SecureAPIKeyGenerator.generate_base64_key(40)
            entropy = SecureAPIKeyGenerator.calculate_entropy(key)
            assert entropy > 96, f"Generated key entropy too low: {entropy}"

    def test_api_key_generation_with_config(self):
        """Test API key generation with different configurations"""
        config = APIKeyConfig(
            length=40,
            format_type="base64",
            prefix="test",
            checksum=True
        )

        generated_key = SecureAPIKeyGenerator.generate_api_key(config)
        assert generated_key.key.startswith("test_")
        assert "-" in generated_key.key  # Should have checksum
        assert generated_key.entropy_bits > 96

    def test_key_strength_validation(self):
        """Test validation of generated key strength"""
        generated_key = generate_production_key()
        is_strong, issues = SecureAPIKeyGenerator.validate_generated_key_strength(generated_key)
        assert is_strong, f"Production key should be strong, issues: {issues}"

    def test_hash_verification(self):
        """Test API key hashing and verification"""
        key = "test-api-key-for-hashing-verification"
        key_hash = SecureAPIKeyGenerator.generate_secure_hash(key)

        # Should verify correctly
        assert SecureAPIKeyGenerator.verify_key_hash(key, key_hash)

        # Should not verify with wrong key
        assert not SecureAPIKeyGenerator.verify_key_hash("wrong-key", key_hash)

class TestRateLimiting:
    """Test rate limiting functionality"""

    def setUp(self):
        """Clear rate limiting storage before each test"""
        from apps.api.deps import _api_key_attempts, _blocked_keys
        _api_key_attempts.clear()
        _blocked_keys.clear()

    def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality"""
        self.setUp()

        client_ip = "192.168.1.100"
        api_key = "test-api-key"

        # First 5 attempts should pass
        for i in range(5):
            assert _check_rate_limit(client_ip, api_key), f"Attempt {i+1} should pass"

        # 6th attempt should fail
        assert not _check_rate_limit(client_ip, api_key), "6th attempt should be rate limited"

    def test_rate_limiting_time_window(self):
        """Test rate limiting time window cleanup"""
        self.setUp()

        client_ip = "192.168.1.101"
        api_key = "test-api-key-2"

        # Simulate old attempts (should be cleaned up)
        from apps.api.deps import _api_key_attempts
        import time
        old_time = time.time() - 120  # 2 minutes ago
        _api_key_attempts[client_ip] = [old_time] * 10

        # New attempt should pass (old attempts cleaned up)
        assert _check_rate_limit(client_ip, api_key), "Should pass after cleanup"

    def test_different_ips_separate_limits(self):
        """Test that different IPs have separate rate limits"""
        self.setUp()

        ip1 = "192.168.1.100"
        ip2 = "192.168.1.101"
        api_key = "test-api-key"

        # Max out IP1
        for _ in range(5):
            _check_rate_limit(ip1, api_key)

        # IP1 should be limited, IP2 should still work
        assert not _check_rate_limit(ip1, api_key), "IP1 should be rate limited"
        assert _check_rate_limit(ip2, api_key), "IP2 should still work"

class TestSecurityLogging:
    """Test security event logging"""

    @patch('apps.api.deps.security_logger')
    def test_security_event_logging(self, mock_logger):
        """Test that security events are logged properly"""
        api_key = "test-api-key-for-logging"
        client_ip = "192.168.1.100"

        _log_security_event("TEST_EVENT", api_key, client_ip, "Test details")

        # Verify logger was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        assert "API_KEY_SECURITY_EVENT: TEST_EVENT" in call_args
        assert _hash_api_key(api_key) in call_args
        assert client_ip in call_args
        assert "Test details" in call_args

    def test_api_key_hashing(self):
        """Test API key hashing for logs"""
        api_key = "sensitive-api-key-that-should-be-hashed"
        hash1 = _hash_api_key(api_key)
        hash2 = _hash_api_key(api_key)

        # Should be consistent
        assert hash1 == hash2

        # Should be different for different keys
        different_hash = _hash_api_key("different-api-key")
        assert hash1 != different_hash

        # Should be shortened (16 chars)
        assert len(hash1) == 16

@pytest.mark.asyncio
class TestAPIKeyValidationIntegration:
    """Integration tests for the complete API key validation flow"""

    async def test_missing_api_key(self):
        """Test validation with missing API key"""
        request = Mock()
        request.client.host = "192.168.1.100"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request, None)

        assert exc_info.value.status_code == 403
        assert "API key required" in exc_info.value.detail

    async def test_invalid_format_api_key(self):
        """Test validation with invalid format API key"""
        request = Mock()
        request.client.host = "192.168.1.100"
        request.url.path = "/test"
        request.method = "GET"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request, "short")

        assert exc_info.value.status_code == 403
        assert "Invalid API key format" in exc_info.value.detail["error"]

    @patch('apps.api.deps.get_async_session')
    async def test_valid_api_key_flow(self, mock_get_session):
        """Test complete validation flow with valid API key"""
        # Mock database session and manager
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Generate a valid API key
        generated_key = generate_production_key()

        # Mock successful database validation
        with patch('apps.api.deps.APIKeyManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager

            # Mock API key info
            mock_api_key_info = Mock()
            mock_api_key_info.key_id = "test-key-id"
            mock_api_key_info.scope = "read"
            mock_api_key_info.permissions = ["read"]

            mock_manager.verify_api_key.return_value = mock_api_key_info

            # Create request mock
            request = Mock()
            request.client.host = "192.168.1.100"
            request.url.path = "/test"
            request.method = "GET"

            # Should succeed
            result = await verify_api_key(request, generated_key.key)
            assert result == mock_api_key_info

    async def test_rate_limiting_integration(self):
        """Test rate limiting integration in validation flow"""
        request = Mock()
        request.client.host = "192.168.1.100"

        # Generate valid API key
        generated_key = generate_production_key()

        # Simulate rate limiting by making multiple requests
        for i in range(5):
            try:
                await verify_api_key(request, generated_key.key)
            except HTTPException:
                pass  # Expected to fail on database validation

        # Next request should be rate limited
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request, generated_key.key)

        assert exc_info.value.status_code == 429

class TestProductionReadiness:
    """Test production readiness and edge cases"""

    def test_memory_usage(self):
        """Test that key generation doesn't consume excessive memory"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Generate many keys
        for _ in range(1000):
            key = SecureAPIKeyGenerator.generate_base64_key(32)
            entropy = APIKeyValidator.calculate_entropy(key)
            assert entropy > 80  # Reasonable entropy

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Should not increase memory by more than 50MB
        assert memory_increase < 50 * 1024 * 1024, f"Memory increase too high: {memory_increase / 1024 / 1024:.1f}MB"

    def test_performance_benchmarks(self):
        """Test performance of key validation"""
        import time

        # Generate test key
        generated_key = generate_production_key()

        # Benchmark validation performance
        start_time = time.time()
        for _ in range(100):
            is_valid, errors = APIKeyValidator.comprehensive_validate(generated_key.key)
            assert is_valid

        end_time = time.time()
        avg_time = (end_time - start_time) / 100

        # Should validate in less than 10ms on average
        assert avg_time < 0.01, f"Validation too slow: {avg_time*1000:.1f}ms average"

    def test_concurrent_validation(self):
        """Test concurrent API key validation"""
        import threading
        import queue

        generated_key = generate_production_key()
        results = queue.Queue()
        errors = queue.Queue()

        def validate_key():
            try:
                is_valid, validation_errors = APIKeyValidator.comprehensive_validate(generated_key.key)
                results.put(is_valid)
            except Exception as e:
                errors.put(e)

        # Run concurrent validations
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=validate_key)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        assert errors.empty(), f"Concurrent validation errors: {list(errors.queue)}"
        assert results.qsize() == 50, "Not all validations completed"

        # All should be valid
        while not results.empty():
            assert results.get() == True

if __name__ == "__main__":
    # Run tests manually for development
    pytest.main([__file__, "-v", "--tb=short"])