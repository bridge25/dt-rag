"""Fix token_count constraint and default value

@CODE:DATABASE-001:MIGRATION:TOKEN-COUNT-FIX
@SPEC:DATABASE-001
@TEST:test_schema.py::test_chunks_token_count_constraint

Revision ID: 4b62d8cc3712
Revises: 9e61c0aac4be
Create Date: 2025-10-22 15:18:43.124938

This migration fixes the token_count column to have a default value
that satisfies the CHECK constraint (token_count > 0).

Changes:
- Update existing token_count=0 rows to 1
- Change default value from 0 to 1
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b62d8cc3712'
down_revision = '9e61c0aac4be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix token_count default value and existing data"""

    bind = op.get_bind()

    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            database_url = str(bind.get_bind().url)
    except AttributeError:
        database_url = bind.dialect.name

    if 'postgresql' in database_url:
        print("Fixing token_count constraint and default value...")

        # Step 1: Update existing rows with token_count=0 to 1
        op.execute("""
            UPDATE chunks
            SET token_count = GREATEST(LENGTH(text) / 4, 1)
            WHERE token_count = 0;
        """)
        print("Updated existing token_count=0 rows")

        # Step 2: Change default value from 0 to 1
        op.execute("""
            ALTER TABLE chunks
            ALTER COLUMN token_count SET DEFAULT 1;
        """)
        print("Changed token_count default value to 1")

        print("Token_count fix completed successfully")
    else:
        print("SQLite detected - fixing token_count...")

        # Update existing rows
        op.execute("""
            UPDATE chunks
            SET token_count = MAX(LENGTH(text) / 4, 1)
            WHERE token_count = 0;
        """)

        print("Token_count fix completed for SQLite")


def downgrade() -> None:
    """Revert token_count default value to 0"""

    bind = op.get_bind()

    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            database_url = str(bind.get_bind().url)
    except AttributeError:
        database_url = bind.dialect.name

    if 'postgresql' in database_url:
        print("Reverting token_count default value to 0...")

        op.execute("""
            ALTER TABLE chunks
            ALTER COLUMN token_count SET DEFAULT 0;
        """)

        print("Reverted token_count default value to 0")
    else:
        print("SQLite detected - no action needed for downgrade")