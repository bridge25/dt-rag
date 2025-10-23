"""
Create Initial Admin API Key

This script creates a secure admin API key for bootstrapping the system.
Run once during initial setup.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.api.database import get_async_session
from apps.api.security.api_key_storage import APIKeyManager, APIKeyCreateRequest
from apps.api.security.api_key_generator import generate_admin_key


async def create_initial_admin_key():
    """Create an initial admin API key for system bootstrap"""

    print("=" * 70)
    print("DT-RAG Admin API Key Generator")
    print("=" * 70)
    print()

    # Get database session
    async for db in get_async_session():
        try:
            key_manager = APIKeyManager(db)

            # Check if admin keys already exist
            existing_keys = await key_manager.list_api_keys(active_only=True)
            admin_keys = [k for k in existing_keys if k.scope == "admin"]

            if admin_keys:
                print(f"⚠️  {len(admin_keys)} admin key(s) already exist:")
                for key in admin_keys:
                    print(f"   - {key.name} (key_id: {key.key_id}, created: {key.created_at})")
                print()

                response = input("Do you want to create another admin key? (yes/no): ")
                if response.lower() != "yes":
                    print("\nAborted. No new key created.")
                    return
                print()

            # Get key details
            name = input("Enter API key name (default: 'Initial Admin Key'): ").strip()
            if not name:
                name = "Initial Admin Key"

            description = input("Enter description (optional): ").strip()
            if not description:
                description = "Auto-generated admin key for system bootstrap"

            # Create request
            create_request = APIKeyCreateRequest(
                name=name,
                description=description,
                owner_id="system",
                permissions=["*"],  # All permissions
                scope="admin",
                allowed_ips=None,  # No IP restrictions for initial setup
                rate_limit=1000,  # Higher rate limit for admin
                expires_days=None  # No expiration
            )

            # Generate the API key
            plaintext_key, key_info = await key_manager.create_api_key(
                request=create_request,
                created_by="system_bootstrap",
                client_ip="127.0.0.1"
            )

            print()
            print("=" * 70)
            print("✅ Admin API Key Created Successfully!")
            print("=" * 70)
            print()
            print("⚠️  IMPORTANT: Save this key securely! It will not be shown again.")
            print()
            print(f"API Key: {plaintext_key}")
            print()
            print("Key Details:")
            print(f"  - Key ID: {key_info.key_id}")
            print(f"  - Name: {key_info.name}")
            print(f"  - Scope: {key_info.scope}")
            print(f"  - Rate Limit: {key_info.rate_limit} requests/hour")
            print(f"  - Created: {key_info.created_at}")
            print(f"  - Expires: {'Never' if not key_info.expires_at else key_info.expires_at}")
            print()
            print("Usage Example:")
            print(f'  curl -H "X-API-Key: {plaintext_key}" http://localhost:8000/api/v1/search/')
            print()
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Error creating admin API key: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(create_initial_admin_key())
