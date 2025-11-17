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

    # Check if agents table exists
    inspector = sa.inspect(bind)
    if 'agents' not in inspector.get_table_names():
        print("agents table does not exist - skipping migration")
        return

    # Check if columns already exist
    existing_columns = [col['name'] for col in inspector.get_columns('agents')]

    if is_postgresql:
        # PostgreSQL implementation
        if 'avatar_url' not in existing_columns:
            op.add_column(
                'agents',
                sa.Column('avatar_url', sa.String(500), nullable=True, comment='URL to Pokemon-style avatar image')
            )
            print("Added avatar_url column to agents")

        if 'rarity' not in existing_columns:
            op.add_column(
                'agents',
                sa.Column('rarity', sa.String(20), nullable=True, server_default='Common', comment='Agent rarity tier (Pokemon card style)')
            )
            print("Added rarity column to agents")

        if 'character_description' not in existing_columns:
            op.add_column(
                'agents',
                sa.Column('character_description', sa.Text(), nullable=True, comment='Character description for AI-generated avatars')
            )
            print("Added character_description column to agents")

        # Add CHECK constraint for rarity values if not exists
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'valid_rarity'
                ) THEN
                    ALTER TABLE agents ADD CONSTRAINT valid_rarity
                    CHECK (rarity IN ('Common', 'Rare', 'Epic', 'Legendary'));
                    RAISE NOTICE 'Added valid_rarity constraint to agents';
                ELSE
                    RAISE NOTICE 'valid_rarity constraint already exists, skipping';
                END IF;
            END
            $$;
        """)

    else:
        # SQLite implementation
        if 'avatar_url' not in existing_columns:
            op.add_column(
                'agents',
                sa.Column('avatar_url', sa.Text(), nullable=True)
            )
            print("Added avatar_url column to agents (SQLite)")

        if 'rarity' not in existing_columns:
            op.add_column(
                'agents',
                sa.Column('rarity', sa.Text(), nullable=True, server_default='Common')
            )
            print("Added rarity column to agents (SQLite)")

        if 'character_description' not in existing_columns:
            op.add_column(
                'agents',
                sa.Column('character_description', sa.Text(), nullable=True)
            )
            print("Added character_description column to agents (SQLite)")

        # SQLite CHECK constraints are supported but require table recreation for ALTER TABLE
        # For simplicity, we rely on application-level validation in SQLite

    print("Migration 0013 completed successfully")


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
