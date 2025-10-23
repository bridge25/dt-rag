"""Add API key security tables

Revision ID: 0010
Revises: 0009
Create Date: 2025-10-08 10:00:00.000000

Adds comprehensive API key management tables with security features:
- api_keys: Main API key storage with hashed keys
- api_key_usage: Request tracking for rate limiting and analytics
- api_key_audit_log: Audit trail for compliance and security monitoring
"""
from alembic import op
import sqlalchemy as sa

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        sa.Column('permissions', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('scope', sa.String(50), nullable=False, server_default='read'),
        sa.Column('allowed_ips', sa.Text(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_keys
    op.create_index('idx_api_keys_key_id', 'api_keys', ['key_id'], unique=True)
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
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
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('request_metadata', sa.Text(), nullable=True),
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
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_key_audit_log
    op.create_index('idx_api_key_audit_operation', 'api_key_audit_log', ['operation'])
    op.create_index('idx_api_key_audit_operation_timestamp', 'api_key_audit_log', ['operation', 'timestamp'])
    op.create_index('idx_api_key_audit_key_operation', 'api_key_audit_log', ['key_id', 'operation'])
    op.create_index('idx_api_key_audit_performed_by', 'api_key_audit_log', ['performed_by', 'timestamp'])
    op.create_index('idx_api_key_audit_timestamp', 'api_key_audit_log', ['timestamp'])


def downgrade() -> None:
    """Remove API key security tables"""

    # Drop tables in reverse order
    op.drop_table('api_key_audit_log')
    op.drop_table('api_key_usage')
    op.drop_table('api_keys')
