"""
Secure API Key Generation Utilities

This module provides production-ready API key generation with cryptographic security,
proper entropy, and compliance with security best practices.

@CODE:AUTH-002
"""

import secrets
import base64
import string
import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class APIKeyConfig:
    """Configuration for API key generation"""

    length: int = 32
    format_type: str = "base64"  # base64, hex, alphanumeric, mixed
    include_special_chars: bool = False
    prefix: Optional[str] = None
    checksum: bool = True


@dataclass
class GeneratedAPIKey:
    """Generated API key with metadata"""

    key: str
    key_hash: str
    created_at: datetime
    format_type: str
    entropy_bits: float
    prefix: Optional[str] = None
    checksum: Optional[str] = None


class SecureAPIKeyGenerator:
    """
    Production-ready API key generator with cryptographic security

    Features:
    - Cryptographically secure random generation
    - Multiple format options (base64, hex, alphanumeric, mixed)
    - Configurable length and complexity
    - Entropy calculation and validation
    - Optional prefixes and checksums
    - Secure hashing for storage
    """

    # Character sets for different formats
    CHARSET_BASE64 = string.ascii_letters + string.digits + "+/"
    CHARSET_HEX = string.hexdigits.lower()
    CHARSET_ALPHANUMERIC = string.ascii_letters + string.digits
    CHARSET_SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    CHARSET_MIXED = string.ascii_letters + string.digits + "_-."

    @classmethod
    def generate_base64_key(cls, length: int = 32) -> str:
        """Generate a base64-encoded API key"""
        # Generate random bytes and encode as base64
        random_bytes = secrets.token_bytes(
            length * 3 // 4
        )  # Adjust for base64 encoding
        key = base64.urlsafe_b64encode(random_bytes).decode("ascii")

        # Trim to exact length and remove padding
        return key[:length].rstrip("=")

    @classmethod
    def generate_hex_key(cls, length: int = 32) -> str:
        """Generate a hexadecimal API key"""
        return secrets.token_hex(length // 2)

    @classmethod
    def generate_alphanumeric_key(cls, length: int = 32) -> str:
        """Generate an alphanumeric API key"""
        return "".join(secrets.choice(cls.CHARSET_ALPHANUMERIC) for _ in range(length))

    @classmethod
    def generate_mixed_key(cls, length: int = 32, include_special: bool = False) -> str:
        """Generate a mixed-character API key"""
        charset = cls.CHARSET_MIXED
        if include_special:
            charset += cls.CHARSET_SPECIAL[:5]  # Add limited special chars

        return "".join(secrets.choice(charset) for _ in range(length))

    @classmethod
    def calculate_entropy(cls, key: str) -> float:
        """Calculate Shannon entropy of the generated key"""
        if not key:
            return 0.0

        # Count character frequencies
        frequencies: dict[str, int] = {}
        for char in key:
            frequencies[char] = frequencies.get(char, 0) + 1

        # Calculate Shannon entropy
        import math

        entropy = 0.0
        length = len(key)

        for count in frequencies.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy * length

    @classmethod
    def add_checksum(cls, key: str) -> str:
        """Add a simple checksum to the API key"""
        checksum = hashlib.md5(key.encode()).hexdigest()[:4]
        return f"{key}-{checksum}"

    @classmethod
    def generate_secure_hash(cls, key: str, salt: Optional[str] = None) -> str:
        """Generate a secure hash for API key storage"""
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for secure hashing
        key_hash = hashlib.pbkdf2_hmac("sha256", key.encode(), salt.encode(), 100000)
        return f"{salt}:{key_hash.hex()}"

    @classmethod
    def verify_key_hash(cls, key: str, stored_hash: str) -> bool:
        """Verify an API key against its stored hash"""
        try:
            salt, key_hash = stored_hash.split(":", 1)
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256", key.encode(), salt.encode(), 100000
            )
            return computed_hash.hex() == key_hash
        except (ValueError, IndexError):
            return False

    @classmethod
    def generate_api_key(cls, config: APIKeyConfig) -> GeneratedAPIKey:
        """
        Generate a secure API key with the specified configuration

        Args:
            config: API key generation configuration

        Returns:
            GeneratedAPIKey: The generated key with metadata

        Raises:
            ValueError: If configuration is invalid
        """
        if config.length < 16:
            raise ValueError("API key length must be at least 16 characters")

        # Generate the key based on format
        if config.format_type == "base64":
            key = cls.generate_base64_key(config.length)
        elif config.format_type == "hex":
            key = cls.generate_hex_key(config.length)
        elif config.format_type == "alphanumeric":
            key = cls.generate_alphanumeric_key(config.length)
        elif config.format_type == "mixed":
            key = cls.generate_mixed_key(config.length, config.include_special_chars)
        else:
            raise ValueError(f"Unsupported format type: {config.format_type}")

        # Add prefix if specified
        if config.prefix:
            key = f"{config.prefix}_{key}"

        # Add checksum if requested
        checksum = None
        if config.checksum:
            checksum = hashlib.md5(key.encode()).hexdigest()[:4]
            key = f"{key}-{checksum}"

        # Calculate entropy
        entropy = cls.calculate_entropy(key)

        # Generate secure hash for storage
        key_hash = cls.generate_secure_hash(key)

        # Log key generation (without exposing the actual key)
        logger.info(
            f"Generated API key: format={config.format_type}, "
            f"length={len(key)}, entropy={entropy:.1f} bits"
        )

        return GeneratedAPIKey(
            key=key,
            key_hash=key_hash,
            created_at=datetime.now(timezone.utc),
            format_type=config.format_type,
            entropy_bits=entropy,
            prefix=config.prefix,
            checksum=checksum,
        )

    @classmethod
    def generate_multiple_keys(
        cls, count: int, config: APIKeyConfig
    ) -> List[GeneratedAPIKey]:
        """Generate multiple API keys with the same configuration"""
        if count <= 0 or count > 100:
            raise ValueError("Key count must be between 1 and 100")

        keys = []
        for _ in range(count):
            keys.append(cls.generate_api_key(config))

        return keys

    @classmethod
    def validate_generated_key_strength(
        cls, generated_key: GeneratedAPIKey
    ) -> Tuple[bool, List[str]]:
        """Validate the strength of a generated API key"""
        errors = []

        # Check minimum entropy
        if generated_key.entropy_bits < 96:
            errors.append(
                f"Low entropy: {generated_key.entropy_bits:.1f} bits (minimum: 96)"
            )

        # Check length
        if len(generated_key.key) < 32:
            errors.append(
                f"Short length: {len(generated_key.key)} characters (minimum: 32)"
            )

        # Check for repeated patterns
        key = generated_key.key
        if len(set(key)) < len(key) * 0.7:  # Less than 70% unique characters
            errors.append("Too many repeated characters")

        return len(errors) == 0, errors


# Predefined configurations for common use cases
PRODUCTION_CONFIG = APIKeyConfig(
    length=40,
    format_type="base64",
    include_special_chars=False,
    prefix="prod",
    checksum=True,
)

DEVELOPMENT_CONFIG = APIKeyConfig(
    length=32,
    format_type="mixed",
    include_special_chars=False,
    prefix="dev",
    checksum=False,
)

ADMIN_CONFIG = APIKeyConfig(
    length=48,
    format_type="base64",
    include_special_chars=True,
    prefix="admin",
    checksum=True,
)


# Convenience functions
def generate_production_key() -> GeneratedAPIKey:
    """Generate a production-ready API key"""
    return SecureAPIKeyGenerator.generate_api_key(PRODUCTION_CONFIG)


def generate_development_key() -> GeneratedAPIKey:
    """Generate a development API key"""
    return SecureAPIKeyGenerator.generate_api_key(DEVELOPMENT_CONFIG)


def generate_admin_key() -> GeneratedAPIKey:
    """Generate an admin API key"""
    return SecureAPIKeyGenerator.generate_api_key(ADMIN_CONFIG)


def generate_custom_key(
    length: int = 32,
    format_type: str = "base64",
    prefix: Optional[str] = None,
    include_special: bool = False,
    checksum: bool = True,
) -> GeneratedAPIKey:
    """Generate a custom API key with specified parameters"""
    config = APIKeyConfig(
        length=length,
        format_type=format_type,
        include_special_chars=include_special,
        prefix=prefix,
        checksum=checksum,
    )
    return SecureAPIKeyGenerator.generate_api_key(config)


# CLI utility function
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def main() -> None:
    """CLI utility for generating API keys"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate secure API keys")
    parser.add_argument(
        "--count", type=int, default=1, help="Number of keys to generate"
    )
    parser.add_argument("--length", type=int, default=32, help="Key length")
    parser.add_argument(
        "--format",
        choices=["base64", "hex", "alphanumeric", "mixed"],
        default="base64",
        help="Key format",
    )
    parser.add_argument("--prefix", type=str, help="Key prefix")
    parser.add_argument(
        "--special", action="store_true", help="Include special characters"
    )
    parser.add_argument("--no-checksum", action="store_true", help="Disable checksum")

    args = parser.parse_args()

    config = APIKeyConfig(
        length=args.length,
        format_type=args.format,
        include_special_chars=args.special,
        prefix=args.prefix,
        checksum=not args.no_checksum,
    )

    print(f"Generating {args.count} API key(s) with configuration:")
    print(f"  Length: {config.length}")
    print(f"  Format: {config.format_type}")
    print(f"  Prefix: {config.prefix or 'None'}")
    print(f"  Special chars: {config.include_special_chars}")
    print(f"  Checksum: {config.checksum}")
    print()

    keys = SecureAPIKeyGenerator.generate_multiple_keys(args.count, config)

    for i, key_data in enumerate(keys, 1):
        print(f"Key {i}:")
        print(f"  API Key: {key_data.key}")
        print(f"  Hash: {key_data.key_hash}")
        print(f"  Entropy: {key_data.entropy_bits:.1f} bits")
        print(f"  Created: {key_data.created_at.isoformat()}")

        is_strong, issues = SecureAPIKeyGenerator.validate_generated_key_strength(
            key_data
        )
        print(f"  Strong: {is_strong}")
        if issues:
            print(f"  Issues: {', '.join(issues)}")
        print()


if __name__ == "__main__":
    main()
