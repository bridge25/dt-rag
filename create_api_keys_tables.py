"""
Create API Keys Tables for SQLite

Direct table creation for SQLite databases.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.core.db_session import engine
from sqlalchemy import text

async def create_api_keys_tables():
    """Create API key tables in SQLite"""
    print("=" * 70)
    print("Creating API Keys Tables")
    print("=" * 70)
    print()

    async with engine.begin() as conn:
        # Create api_keys table
        print("Creating api_keys table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id VARCHAR(32) NOT NULL UNIQUE,
                key_hash VARCHAR(256) NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                owner_id VARCHAR(50),
                permissions TEXT NOT NULL DEFAULT '[]',
                scope VARCHAR(50) NOT NULL DEFAULT 'read',
                allowed_ips TEXT,
                rate_limit INTEGER NOT NULL DEFAULT 100,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                expires_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at DATETIME,
                total_requests INTEGER NOT NULL DEFAULT 0,
                failed_requests INTEGER NOT NULL DEFAULT 0
            )
        """))

        # Create indexes for api_keys
        print("Creating indexes for api_keys...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_keys_owner_active ON api_keys(owner_id, is_active)"))

        # Create api_key_usage table
        print("Creating api_key_usage table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_key_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id VARCHAR(32) NOT NULL,
                endpoint VARCHAR(200) NOT NULL,
                method VARCHAR(10) NOT NULL,
                client_ip VARCHAR(45) NOT NULL,
                user_agent VARCHAR(500),
                status_code INTEGER NOT NULL,
                response_time_ms INTEGER,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                request_metadata TEXT
            )
        """))

        # Create indexes for api_key_usage
        print("Creating indexes for api_key_usage...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_key_usage_key_id ON api_key_usage(key_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_key_usage_timestamp ON api_key_usage(timestamp)"))

        # Create api_key_audit_log table
        print("Creating api_key_audit_log table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_key_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation VARCHAR(50) NOT NULL,
                key_id VARCHAR(32) NOT NULL,
                performed_by VARCHAR(50),
                client_ip VARCHAR(45) NOT NULL,
                old_values TEXT,
                new_values TEXT,
                reason VARCHAR(200),
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create indexes for api_key_audit_log
        print("Creating indexes for api_key_audit_log...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_key_audit_operation ON api_key_audit_log(operation)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_key_audit_timestamp ON api_key_audit_log(timestamp)"))

    print()
    print("=" * 70)
    print("✅ API Keys tables created successfully!")
    print("=" * 70)
    print()
    print("Tables created:")
    print("  - api_keys")
    print("  - api_key_usage")
    print("  - api_key_audit_log")
    print()

if __name__ == "__main__":
    asyncio.run(create_api_keys_tables())
