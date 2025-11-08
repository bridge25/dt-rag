"""Add Pokemon avatar fields to agents table

Revision ID: 0013
Revises: 0012
Create Date: 2025-11-08 21:00:00.000000

@CODE:POKEMON-IMAGE-COMPLETE-001-DB-001

Adds avatar_url, rarity, character_description columns to agents table
for Pokemon-style Agent Card avatar system.

Supports both PostgreSQL and SQLite:
- PostgreSQL: VARCHAR(500), String(20), TEXT
- SQLite: Same types but with TEXT fallback for large strings

Migration Safety:
- All new columns are nullable=True (preserves existing data)
- rarity has default='Common' (ensures consistent state)
- character_description is nullable (future AI avatar feature)
- CHECK constraint on rarity ensures valid values
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Pokemon avatar fields to agents table"""
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        # PostgreSQL implementation
        op.add_column(
            'agents',
            sa.Column('avatar_url', sa.String(500), nullable=True, comment='URL to Pokemon-style avatar image')
        )
        op.add_column(
            'agents',
            sa.Column('rarity', sa.String(20), nullable=True, server_default='Common', comment='Agent rarity tier (Pokemon card style)')
        )
        op.add_column(
            'agents',
            sa.Column('character_description', sa.Text(), nullable=True, comment='Character description for AI-generated avatars')
        )

        # Add CHECK constraint for rarity values
        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_rarity
            CHECK (rarity IN ('Common', 'Rare', 'Epic', 'Legendary'))
        """)

    else:
        # SQLite implementation
        op.add_column(
            'agents',
            sa.Column('avatar_url', sa.Text(), nullable=True)
        )
        op.add_column(
            'agents',
            sa.Column('rarity', sa.Text(), nullable=True, server_default='Common')
        )
        op.add_column(
            'agents',
            sa.Column('character_description', sa.Text(), nullable=True)
        )

        # SQLite CHECK constraints are supported but require table recreation for ALTER TABLE
        # For simplicity, we rely on application-level validation in SQLite


def downgrade() -> None:
    """Remove Pokemon avatar fields from agents table"""
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        # Drop CHECK constraint first
        op.execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS valid_rarity")

    # Drop columns (works for both PostgreSQL and SQLite)
    op.drop_column('agents', 'character_description')
    op.drop_column('agents', 'rarity')
    op.drop_column('agents', 'avatar_url')
