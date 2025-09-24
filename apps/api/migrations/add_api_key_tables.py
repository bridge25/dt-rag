"""
Database Migration: Add API Key Security Tables

This migration adds comprehensive API key management tables with security features:
- api_keys: Main API key storage with hashed keys
- api_key_usage: Request tracking for rate limiting and analytics
- api_key_audit_log: Audit trail for compliance and security monitoring

Run with: python -m alembic revision --autogenerate -m "Add API key security tables"
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index

def upgrade():
    """Add API key security tables"""

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_id', sa.String(32), nullable=False),
        sa.Column('key_hash', sa.String(256), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(50), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=False, default='[]'),
        sa.Column('scope', sa.String(50), nullable=False, default='read'),
        sa.Column('allowed_ips', sa.Text(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=False, default=100),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_requests', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_keys
    op.create_index('idx_api_keys_key_id', 'api_keys', ['key_id'], unique=True)
    op.create_index('idx_api_keys_key_hash_active', 'api_keys', ['key_hash', 'is_active'])
    op.create_index('idx_api_keys_owner_active', 'api_keys', ['owner_id', 'is_active'])
    op.create_index('idx_api_keys_expires_at', 'api_keys', ['expires_at'])
    op.create_index('idx_api_keys_last_used', 'api_keys', ['last_used_at'])

    # Create api_key_usage table
    op.create_table(
        'api_key_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_id', sa.String(32), nullable=False),
        sa.Column('endpoint', sa.String(200), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_key_usage
    op.create_index('idx_api_key_usage_key_id', 'api_key_usage', ['key_id'])
    op.create_index('idx_api_key_usage_key_timestamp', 'api_key_usage', ['key_id', 'timestamp'])
    op.create_index('idx_api_key_usage_client_ip_timestamp', 'api_key_usage', ['client_ip', 'timestamp'])
    op.create_index('idx_api_key_usage_status_timestamp', 'api_key_usage', ['status_code', 'timestamp'])
    op.create_index('idx_api_key_usage_timestamp', 'api_key_usage', ['timestamp'])

    # Create api_key_audit_log table
    op.create_table(
        'api_key_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('key_id', sa.String(32), nullable=False),
        sa.Column('performed_by', sa.String(50), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=False),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('reason', sa.String(200), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_key_audit_log
    op.create_index('idx_api_key_audit_operation_timestamp', 'api_key_audit_log', ['operation', 'timestamp'])
    op.create_index('idx_api_key_audit_key_operation', 'api_key_audit_log', ['key_id', 'operation'])
    op.create_index('idx_api_key_audit_performed_by', 'api_key_audit_log', ['performed_by', 'timestamp'])
    op.create_index('idx_api_key_audit_timestamp', 'api_key_audit_log', ['timestamp'])

def downgrade():
    """Remove API key security tables"""

    # Drop tables in reverse order (due to potential foreign key constraints)
    op.drop_table('api_key_audit_log')
    op.drop_table('api_key_usage')
    op.drop_table('api_keys')

# Additional helper functions for data migration if needed
def create_default_admin_key():
    """Create a default admin API key for initial setup"""
    from ...security import generate_admin_key, APIKeyManager
    from ...database import get_sync_session

    # This would be called after the migration to create an initial admin key
    # Implementation would depend on your specific database setup
    pass

def migrate_existing_api_keys():
    """Migrate any existing API keys to the new secure format"""
    # If you have existing API keys in a different format, migrate them here
    pass

# Security validation functions
def validate_migration():
    """Validate that the migration was successful"""
    from sqlalchemy import create_engine, text
    from ...config import get_api_config

    config = get_api_config()
    engine = create_engine(config.database.url)

    with engine.connect() as conn:
        # Check that all tables exist
        tables = ['api_keys', 'api_key_usage', 'api_key_audit_log']
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"))
            if result.scalar() == 0:
                raise Exception(f"Table {table} was not created successfully")

        # Check that all indexes exist
        indexes = [
            'idx_api_keys_key_id',
            'idx_api_keys_key_hash_active',
            'idx_api_key_usage_key_timestamp',
            'idx_api_key_audit_operation_timestamp'
        ]

        for index in indexes:
            result = conn.execute(text(f"SELECT COUNT(*) FROM pg_indexes WHERE indexname = '{index}'"))
            if result.scalar() == 0:
                raise Exception(f"Index {index} was not created successfully")

    print("✅ API key security tables migration validated successfully")

if __name__ == "__main__":
    # This allows running the migration directly for testing
    print("🔐 API Key Security Tables Migration")
    print("This migration adds comprehensive API key management with:")
    print("- Secure hashed key storage")
    print("- Request tracking and rate limiting")
    print("- Comprehensive audit logging")
    print("- IP-based access control")
    print("- Automatic expiration support")
    print("\nRun with alembic for production deployment.")