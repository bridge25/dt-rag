"""
Insert test API key into database for testing
"""
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from apps.core.db_session import async_session
from apps.api.security.api_key_storage import APIKey, APIKeyManager, APIKeyCreateRequest

async def insert_test_api_key():
    """Insert test API key that matches test_frontend_api.py"""

    # The API key used in test_frontend_api.py
    test_api_key = "7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"

    async with async_session() as session:
        # Create API key manager
        manager = APIKeyManager(session)

        # Check if key already exists
        from sqlalchemy import select
        result = await session.execute(
            select(APIKey).where(APIKey.name == "Test Frontend Key")
        )
        existing_key = result.scalar_one_or_none()

        if existing_key:
            print(f"Test API key already exists: {existing_key.key_id}")
            print(f"  Name: {existing_key.name}")
            print(f"  Scope: {existing_key.scope}")
            print(f"  Active: {existing_key.is_active}")
            return

        # Hash the test API key using PBKDF2 (same as APIKeyGenerator)
        salt = "test_salt_for_frontend_key"
        key_hash_raw = hashlib.pbkdf2_hmac('sha256', test_api_key.encode(), salt.encode(), 100000)
        key_hash = f"{salt}:{key_hash_raw.hex()}"

        # Generate unique key ID
        key_id = hashlib.md5(test_api_key.encode()).hexdigest()[:16]

        # Create API key record
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name="Test Frontend Key",
            description="API key for frontend integration testing",
            owner_id="test_user",
            permissions='["read", "write"]',
            scope="write",  # Allow search operations
            allowed_ips=None,  # Allow from any IP
            rate_limit=1000,  # High limit for testing
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            total_requests=0,
            failed_requests=0
        )

        session.add(api_key)
        await session.commit()

        print("Test API key inserted successfully!")
        print(f"  Key ID: {key_id}")
        print(f"  Name: {api_key.name}")
        print(f"  Scope: {api_key.scope}")
        print(f"  Rate Limit: {api_key.rate_limit}")
        print(f"  Expires: {api_key.expires_at}")
        print(f"\nYou can now use this API key in test_frontend_api.py")

if __name__ == "__main__":
    asyncio.run(insert_test_api_key())
