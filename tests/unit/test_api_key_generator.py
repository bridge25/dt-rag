"""
Unit tests for API key generator module (apps.api.security.api_key_generator)

This test module provides comprehensive coverage for secure API key generation
functionality including format validation, entropy calculation, and security features.
"""

import pytest
import re
import hashlib
from unittest.mock import patch, Mock
from datetime import datetime, timezone

# Import the modules under test
from apps.api.security.api_key_generator import (
    APIKeyConfig,
    GeneratedAPIKey,
    SecureAPIKeyGenerator
)


class TestAPIKeyConfig:
    """Test cases for APIKeyConfig dataclass"""

    @pytest.mark.unit
    def test_api_key_config_defaults(self):
        """Test APIKeyConfig default values"""
        config = APIKeyConfig()

        assert config.length == 32
        assert config.format_type == "base64"
        assert config.include_special_chars is False
        assert config.prefix is None
        assert config.checksum is True

    @pytest.mark.unit
    def test_api_key_config_custom_values(self):
        """Test APIKeyConfig with custom values"""
        config = APIKeyConfig(
            length=64,
            format_type="hex",
            include_special_chars=True,
            prefix="dtrag",
            checksum=False
        )

        assert config.length == 64
        assert config.format_type == "hex"
        assert config.include_special_chars is True
        assert config.prefix == "dtrag"
        assert config.checksum is False


class TestGeneratedAPIKey:
    """Test cases for GeneratedAPIKey dataclass"""

    @pytest.mark.unit
    def test_generated_api_key_creation(self):
        """Test GeneratedAPIKey creation with all fields"""
        created_at = datetime.now(timezone.utc)

        api_key = GeneratedAPIKey(
            key="test-api-key-123",
            key_hash="salt:hash123",
            created_at=created_at,
            format_type="alphanumeric",
            entropy_bits=128.5,
            prefix="test",
            checksum="abcd"
        )

        assert api_key.key == "test-api-key-123"
        assert api_key.key_hash == "salt:hash123"
        assert api_key.created_at == created_at
        assert api_key.format_type == "alphanumeric"
        assert api_key.entropy_bits == 128.5
        assert api_key.prefix == "test"
        assert api_key.checksum == "abcd"

    @pytest.mark.unit
    def test_generated_api_key_optional_fields(self):
        """Test GeneratedAPIKey with optional fields as None"""
        api_key = GeneratedAPIKey(
            key="simple-key",
            key_hash="hash456",
            created_at=datetime.now(timezone.utc),
            format_type="base64",
            entropy_bits=64.0
        )

        assert api_key.prefix is None
        assert api_key.checksum is None


class TestSecureAPIKeyGenerator:
    """Test cases for SecureAPIKeyGenerator class"""

    @pytest.mark.unit
    def test_generate_base64_key_default_length(self):
        """Test base64 key generation with default length"""
        key = SecureAPIKeyGenerator.generate_base64_key()

        assert len(key) == 32
        # Should contain only base64 characters (without padding)
        assert re.match(r'^[A-Za-z0-9+/_-]+$', key)
        assert '=' not in key  # No padding

    @pytest.mark.unit
    def test_generate_base64_key_custom_length(self):
        """Test base64 key generation with custom length"""
        key = SecureAPIKeyGenerator.generate_base64_key(64)

        assert len(key) == 64
        assert re.match(r'^[A-Za-z0-9+/_-]+$', key)

    @pytest.mark.unit
    def test_generate_base64_key_uniqueness(self):
        """Test that base64 keys are unique"""
        keys = [SecureAPIKeyGenerator.generate_base64_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

    @pytest.mark.unit
    def test_generate_hex_key_default_length(self):
        """Test hex key generation with default length"""
        key = SecureAPIKeyGenerator.generate_hex_key()

        assert len(key) == 32
        # Should contain only lowercase hex characters
        assert re.match(r'^[0-9a-f]+$', key)

    @pytest.mark.unit
    def test_generate_hex_key_custom_length(self):
        """Test hex key generation with custom length"""
        key = SecureAPIKeyGenerator.generate_hex_key(48)

        assert len(key) == 48
        assert re.match(r'^[0-9a-f]+$', key)

    @pytest.mark.unit
    def test_generate_hex_key_uniqueness(self):
        """Test that hex keys are unique"""
        keys = [SecureAPIKeyGenerator.generate_hex_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

    @pytest.mark.unit
    def test_generate_alphanumeric_key_default_length(self):
        """Test alphanumeric key generation with default length"""
        key = SecureAPIKeyGenerator.generate_alphanumeric_key()

        assert len(key) == 32
        # Should contain only alphanumeric characters
        assert re.match(r'^[A-Za-z0-9]+$', key)

    @pytest.mark.unit
    def test_generate_alphanumeric_key_custom_length(self):
        """Test alphanumeric key generation with custom length"""
        key = SecureAPIKeyGenerator.generate_alphanumeric_key(16)

        assert len(key) == 16
        assert re.match(r'^[A-Za-z0-9]+$', key)

    @pytest.mark.unit
    def test_generate_alphanumeric_key_uniqueness(self):
        """Test that alphanumeric keys are unique"""
        keys = [SecureAPIKeyGenerator.generate_alphanumeric_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

    @pytest.mark.unit
    def test_generate_mixed_key_without_special(self):
        """Test mixed key generation without special characters"""
        key = SecureAPIKeyGenerator.generate_mixed_key(32, include_special=False)

        assert len(key) == 32
        # Should contain alphanumeric plus _-.
        assert re.match(r'^[A-Za-z0-9_.-]+$', key)

    @pytest.mark.unit
    def test_generate_mixed_key_with_special(self):
        """Test mixed key generation with special characters"""
        key = SecureAPIKeyGenerator.generate_mixed_key(32, include_special=True)

        assert len(key) == 32
        # Should contain alphanumeric, _-., and limited special chars
        assert re.match(r'^[A-Za-z0-9_.!@#$%^-]+$', key)

    @pytest.mark.unit
    def test_generate_mixed_key_uniqueness(self):
        """Test that mixed keys are unique"""
        keys = [SecureAPIKeyGenerator.generate_mixed_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

    @pytest.mark.unit
    def test_calculate_entropy_empty_string(self):
        """Test entropy calculation for empty string"""
        entropy = SecureAPIKeyGenerator.calculate_entropy("")

        assert entropy == 0.0

    @pytest.mark.unit
    def test_calculate_entropy_single_character(self):
        """Test entropy calculation for repeated single character"""
        entropy = SecureAPIKeyGenerator.calculate_entropy("aaaa")

        # Should have very low entropy for repeated characters
        assert entropy >= 0.0
        assert entropy < 10.0

    @pytest.mark.unit
    def test_calculate_entropy_mixed_characters(self):
        """Test entropy calculation for mixed characters"""
        entropy = SecureAPIKeyGenerator.calculate_entropy("abcdefghijklmnopqrstuvwxyz123456")

        # Should have higher entropy for diverse characters
        assert entropy > 50.0

    @pytest.mark.unit
    def test_calculate_entropy_consistency(self):
        """Test entropy calculation consistency"""
        test_string = "TestString123"

        entropy1 = SecureAPIKeyGenerator.calculate_entropy(test_string)
        entropy2 = SecureAPIKeyGenerator.calculate_entropy(test_string)

        assert entropy1 == entropy2

    @pytest.mark.unit
    def test_add_checksum(self):
        """Test checksum addition to API key"""
        original_key = "testkey123"
        key_with_checksum = SecureAPIKeyGenerator.add_checksum(original_key)

        # Should have original key plus hyphen and 4-character checksum
        assert key_with_checksum.startswith(original_key + "-")
        checksum = key_with_checksum.split("-", 1)[1]
        assert len(checksum) == 4
        assert re.match(r'^[0-9a-f]+$', checksum)

    @pytest.mark.unit
    def test_add_checksum_consistency(self):
        """Test checksum consistency for same input"""
        key = "consistentkey"

        checksum1 = SecureAPIKeyGenerator.add_checksum(key)
        checksum2 = SecureAPIKeyGenerator.add_checksum(key)

        assert checksum1 == checksum2

    @pytest.mark.unit
    def test_generate_secure_hash_with_salt(self):
        """Test secure hash generation with provided salt"""
        key = "testkey123"
        salt = "testsalt"

        key_hash = SecureAPIKeyGenerator.generate_secure_hash(key, salt)

        assert ":" in key_hash
        stored_salt, hash_value = key_hash.split(":", 1)
        assert stored_salt == salt
        assert len(hash_value) == 64  # SHA256 hex length

    @pytest.mark.unit
    def test_generate_secure_hash_without_salt(self):
        """Test secure hash generation without provided salt (auto-generated)"""
        key = "testkey123"

        key_hash = SecureAPIKeyGenerator.generate_secure_hash(key)

        assert ":" in key_hash
        stored_salt, hash_value = key_hash.split(":", 1)
        assert len(stored_salt) == 32  # Generated salt length
        assert len(hash_value) == 64  # SHA256 hex length

    @pytest.mark.unit
    def test_generate_secure_hash_consistency(self):
        """Test secure hash consistency with same salt"""
        key = "testkey123"
        salt = "fixedsalt"

        hash1 = SecureAPIKeyGenerator.generate_secure_hash(key, salt)
        hash2 = SecureAPIKeyGenerator.generate_secure_hash(key, salt)

        assert hash1 == hash2

    @pytest.mark.unit
    def test_generate_secure_hash_different_salts(self):
        """Test secure hash produces different results with different salts"""
        key = "testkey123"

        hash1 = SecureAPIKeyGenerator.generate_secure_hash(key, "salt1")
        hash2 = SecureAPIKeyGenerator.generate_secure_hash(key, "salt2")

        assert hash1 != hash2

    @pytest.mark.unit
    def test_verify_key_hash_correct(self):
        """Test key hash verification with correct key"""
        original_key = "testkey123"
        stored_hash = SecureAPIKeyGenerator.generate_secure_hash(original_key, "testsalt")

        is_valid = SecureAPIKeyGenerator.verify_key_hash(original_key, stored_hash)

        assert is_valid is True

    @pytest.mark.unit
    def test_verify_key_hash_incorrect(self):
        """Test key hash verification with incorrect key"""
        original_key = "testkey123"
        wrong_key = "wrongkey456"
        stored_hash = SecureAPIKeyGenerator.generate_secure_hash(original_key, "testsalt")

        is_valid = SecureAPIKeyGenerator.verify_key_hash(wrong_key, stored_hash)

        assert is_valid is False

    @pytest.mark.unit
    def test_verify_key_hash_invalid_format(self):
        """Test key hash verification with invalid hash format"""
        key = "testkey123"
        invalid_hash = "invalidhashformat"

        is_valid = SecureAPIKeyGenerator.verify_key_hash(key, invalid_hash)

        assert is_valid is False

    @pytest.mark.unit
    def test_verify_key_hash_missing_colon(self):
        """Test key hash verification with missing colon separator"""
        key = "testkey123"
        invalid_hash = "saltwithoutcolonhash"

        is_valid = SecureAPIKeyGenerator.verify_key_hash(key, invalid_hash)

        assert is_valid is False

    @pytest.mark.unit
    def test_generate_api_key_base64_default(self):
        """Test API key generation with base64 format and default config"""
        config = APIKeyConfig()

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert isinstance(generated, GeneratedAPIKey)
        assert len(generated.key) == 32 + 1 + 4  # key + hyphen + checksum
        assert generated.format_type == "base64"
        assert generated.entropy_bits > 0
        assert generated.created_at is not None
        assert generated.key_hash is not None
        assert ":" in generated.key_hash  # Contains salt:hash format
        assert generated.checksum is not None

    @pytest.mark.unit
    def test_generate_api_key_hex_format(self):
        """Test API key generation with hex format"""
        config = APIKeyConfig(format_type="hex", length=32, checksum=False)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert generated.format_type == "hex"
        assert len(generated.key) == 32
        assert re.match(r'^[0-9a-f]+$', generated.key)
        assert generated.checksum is None

    @pytest.mark.unit
    def test_generate_api_key_alphanumeric_format(self):
        """Test API key generation with alphanumeric format"""
        config = APIKeyConfig(format_type="alphanumeric", length=24)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert generated.format_type == "alphanumeric"
        # Length includes checksum: 24 + 1 + 4 = 29
        assert len(generated.key) == 24 + 1 + 4
        # Base part should be alphanumeric (before checksum)
        base_key = generated.key.split('-')[0]
        assert re.match(r'^[A-Za-z0-9]+$', base_key)

    @pytest.mark.unit
    def test_generate_api_key_mixed_format(self):
        """Test API key generation with mixed format"""
        config = APIKeyConfig(format_type="mixed", include_special_chars=True)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert generated.format_type == "mixed"
        # Check that key contains expected character types
        base_key = generated.key.split('-')[0]  # Remove checksum
        assert re.match(r'^[A-Za-z0-9_.!@#$%^-]+$', base_key)

    @pytest.mark.unit
    def test_generate_api_key_with_prefix(self):
        """Test API key generation with prefix"""
        config = APIKeyConfig(prefix="dtrag", length=24)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert generated.key.startswith("dtrag_")
        assert generated.prefix == "dtrag"
        # Total length: prefix + underscore + key + hyphen + checksum
        expected_length = len("dtrag") + 1 + 24 + 1 + 4
        assert len(generated.key) == expected_length

    @pytest.mark.unit
    def test_generate_api_key_without_checksum(self):
        """Test API key generation without checksum"""
        config = APIKeyConfig(checksum=False, length=32)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert "-" not in generated.key
        assert generated.checksum is None
        assert len(generated.key) == 32

    @pytest.mark.unit
    def test_generate_api_key_minimum_length(self):
        """Test API key generation with minimum allowed length"""
        config = APIKeyConfig(length=16, checksum=False)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        assert len(generated.key) == 16

    @pytest.mark.unit
    def test_generate_api_key_length_too_short(self):
        """Test API key generation with length below minimum"""
        config = APIKeyConfig(length=8)  # Below minimum of 16

        with pytest.raises(ValueError, match="API key length must be at least 16 characters"):
            SecureAPIKeyGenerator.generate_api_key(config)

    @pytest.mark.unit
    def test_generate_api_key_invalid_format(self):
        """Test API key generation with invalid format type"""
        config = APIKeyConfig(format_type="invalid")

        with pytest.raises(ValueError, match="Unsupported format type: invalid"):
            SecureAPIKeyGenerator.generate_api_key(config)

    @pytest.mark.unit
    def test_generate_api_key_entropy_calculation(self):
        """Test that generated API keys have reasonable entropy"""
        config = APIKeyConfig(length=32, checksum=False)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        # Base64 keys should have decent entropy
        assert generated.entropy_bits > 50.0
        assert generated.entropy_bits <= 256.0  # Reasonable upper bound

    @pytest.mark.unit
    @patch('apps.api.security.api_key_generator.logger')
    def test_generate_api_key_logging(self, mock_logger):
        """Test that API key generation logs appropriate information"""
        config = APIKeyConfig(format_type="hex", length=24)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        # Should log without exposing the actual key
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "format=hex" in log_message
        assert "length=" in log_message
        assert "entropy=" in log_message
        # Should not contain the actual key
        assert generated.key not in log_message

    @pytest.mark.unit
    def test_generate_api_key_unique_keys(self):
        """Test that multiple API key generations produce unique keys"""
        config = APIKeyConfig()

        keys = []
        for _ in range(50):
            generated = SecureAPIKeyGenerator.generate_api_key(config)
            keys.append(generated.key)

        # All keys should be unique
        assert len(set(keys)) == 50

    @pytest.mark.unit
    def test_generate_api_key_hash_verification_integration(self):
        """Test integration between key generation and hash verification"""
        config = APIKeyConfig(length=32, checksum=False)

        generated = SecureAPIKeyGenerator.generate_api_key(config)

        # Verify that the generated hash can be verified with the original key
        is_valid = SecureAPIKeyGenerator.verify_key_hash(generated.key, generated.key_hash)
        assert is_valid is True

        # Verify that wrong key fails verification
        wrong_key = "wrong" + generated.key[5:]
        is_valid = SecureAPIKeyGenerator.verify_key_hash(wrong_key, generated.key_hash)
        assert is_valid is False

    @pytest.mark.unit
    def test_character_sets_defined(self):
        """Test that all character sets are properly defined"""
        assert len(SecureAPIKeyGenerator.CHARSET_BASE64) == 64  # A-Z, a-z, 0-9, +, /
        assert len(SecureAPIKeyGenerator.CHARSET_HEX) == 16     # 0-9, a-f
        assert len(SecureAPIKeyGenerator.CHARSET_ALPHANUMERIC) == 62  # A-Z, a-z, 0-9
        assert len(SecureAPIKeyGenerator.CHARSET_SPECIAL) > 0
        assert len(SecureAPIKeyGenerator.CHARSET_MIXED) > 60

        # Verify no overlap issues
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
                  for c in SecureAPIKeyGenerator.CHARSET_BASE64)
        assert all(c in "0123456789abcdef"
                  for c in SecureAPIKeyGenerator.CHARSET_HEX)

    @pytest.mark.unit
    def test_comprehensive_api_key_formats(self):
        """Test comprehensive API key generation across all supported formats"""
        formats = ["base64", "hex", "alphanumeric", "mixed"]

        for format_type in formats:
            config = APIKeyConfig(format_type=format_type, length=32, checksum=False)
            generated = SecureAPIKeyGenerator.generate_api_key(config)

            assert generated.format_type == format_type
            assert len(generated.key) == 32
            assert generated.entropy_bits > 0

            # Format-specific checks
            if format_type == "hex":
                assert re.match(r'^[0-9a-f]+$', generated.key)
            elif format_type == "alphanumeric":
                assert re.match(r'^[A-Za-z0-9]+$', generated.key)


class TestSecurityFeatures:
    """Test security-related features and edge cases"""

    @pytest.mark.unit
    def test_salt_randomness(self):
        """Test that salt generation is properly random"""
        salts = []
        for _ in range(100):
            key_hash = SecureAPIKeyGenerator.generate_secure_hash("testkey")
            salt = key_hash.split(":")[0]
            salts.append(salt)

        # All salts should be unique
        assert len(set(salts)) == 100
        # All salts should be proper length
        assert all(len(s) == 32 for s in salts)

    @pytest.mark.unit
    def test_pbkdf2_security_parameters(self):
        """Test that PBKDF2 uses secure parameters"""
        key = "testkey"
        salt = "testsalt"

        # Test that it uses 100,000 iterations (secure parameter)
        with patch('hashlib.pbkdf2_hmac') as mock_pbkdf2:
            mock_pbkdf2.return_value = b'fake_hash'

            SecureAPIKeyGenerator.generate_secure_hash(key, salt)

            mock_pbkdf2.assert_called_once_with('sha256', key.encode(), salt.encode(), 100000)

    @pytest.mark.unit
    def test_timing_attack_resistance(self):
        """Test basic timing attack resistance in hash verification"""
        original_key = "testkey123"
        stored_hash = SecureAPIKeyGenerator.generate_secure_hash(original_key)

        # Test with correct key
        result1 = SecureAPIKeyGenerator.verify_key_hash(original_key, stored_hash)

        # Test with completely different key (should take similar time)
        result2 = SecureAPIKeyGenerator.verify_key_hash("completelydifferentkey", stored_hash)

        assert result1 is True
        assert result2 is False
        # In a real timing attack test, we would measure execution time,
        # but for unit tests we just verify the functionality works correctly

    @pytest.mark.unit
    def test_checksum_collision_resistance(self):
        """Test that checksums are resistant to simple collisions"""
        keys = [f"testkey{i}" for i in range(1000)]
        checksums = []

        for key in keys:
            key_with_checksum = SecureAPIKeyGenerator.add_checksum(key)
            checksum = key_with_checksum.split('-')[1]
            checksums.append(checksum)

        # Should have very few collisions in MD5 checksums for different inputs
        unique_checksums = len(set(checksums))
        collision_rate = (len(checksums) - unique_checksums) / len(checksums)
        assert collision_rate < 0.01  # Less than 1% collision rate