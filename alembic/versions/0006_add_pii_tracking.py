"""Add PII tracking columns to chunks table

Revision ID: 0006
Revises: 0005
Create Date: 2025-10-02 00:00:00.000000

This migration adds PII (Personally Identifiable Information) tracking
capabilities to the chunks table to support document ingestion pipeline.

New columns:
- token_count: Number of tokens in chunk (for cost estimation)
- has_pii: Boolean flag indicating PII presence
- pii_types: Array of detected PII types (e.g., email, phone, ssn)
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add PII tracking columns to chunks table"""
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
        print("Adding PII tracking columns to PostgreSQL chunks table...")

        op.execute("""
            DO $$
            BEGIN
                -- Check if chunks table exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'chunks'
                ) THEN
                    -- Add token_count column
                    ALTER TABLE chunks
                    ADD COLUMN IF NOT EXISTS token_count INTEGER NOT NULL DEFAULT 0;

                    -- Add has_pii column
                    ALTER TABLE chunks
                    ADD COLUMN IF NOT EXISTS has_pii BOOLEAN NOT NULL DEFAULT FALSE;

                    -- Add pii_types column (array of text)
                    ALTER TABLE chunks
                    ADD COLUMN IF NOT EXISTS pii_types TEXT[] DEFAULT ARRAY[]::TEXT[];

                    -- Create index for PII filtering
                    CREATE INDEX IF NOT EXISTS idx_chunks_has_pii
                    ON chunks(has_pii)
                    WHERE has_pii = TRUE;

                    -- Create index for token count queries
                    CREATE INDEX IF NOT EXISTS idx_chunks_token_count
                    ON chunks(token_count);

                    -- Update existing rows with estimated token count
                    UPDATE chunks
                    SET token_count = GREATEST(LENGTH(text) / 4, 1)
                    WHERE token_count = 0;

                    -- Add constraint to ensure positive token count
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'chk_token_count_positive'
                    ) THEN
                        ALTER TABLE chunks
                        ADD CONSTRAINT chk_token_count_positive
                        CHECK (token_count > 0);
                    END IF;

                    -- Add column comments
                    COMMENT ON COLUMN chunks.token_count IS 'Number of tokens in chunk (tiktoken-based)';
                    COMMENT ON COLUMN chunks.has_pii IS 'Whether chunk contains personally identifiable information';
                    COMMENT ON COLUMN chunks.pii_types IS 'Array of PII types detected (e.g., resident_registration_number, phone_number, email, credit_card, bank_account)';

                    RAISE NOTICE 'PII tracking columns added successfully';
                ELSE
                    RAISE NOTICE 'chunks table does not exist yet, skipping migration';
                END IF;
            END
            $$;
        """)

        print("PII tracking migration completed")
    else:
        print("SQLite detected - adding PII tracking columns...")

        with op.batch_alter_table('chunks', schema=None) as batch_op:
            batch_op.add_column(sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'))
            batch_op.add_column(sa.Column('has_pii', sa.Boolean(), nullable=False, server_default='0'))
            batch_op.add_column(sa.Column('pii_types', sa.Text(), nullable=True))

        op.execute("""
            UPDATE chunks
            SET token_count = MAX(LENGTH(text) / 4, 1)
            WHERE token_count = 0;
        """)

        print("PII tracking columns added to SQLite")


def downgrade() -> None:
    """Remove PII tracking columns from chunks table"""
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
        print("Removing PII tracking columns from PostgreSQL chunks table...")

        op.execute("""
            -- Drop indexes
            DROP INDEX IF EXISTS idx_chunks_has_pii;
            DROP INDEX IF EXISTS idx_chunks_token_count;

            -- Drop constraint
            ALTER TABLE chunks DROP CONSTRAINT IF EXISTS chk_token_count_positive;

            -- Drop columns
            ALTER TABLE chunks DROP COLUMN IF EXISTS pii_types;
            ALTER TABLE chunks DROP COLUMN IF EXISTS has_pii;
            ALTER TABLE chunks DROP COLUMN IF EXISTS token_count;
        """)

        print("PII tracking columns removed successfully")
    else:
        print("SQLite detected - removing PII tracking columns...")

        with op.batch_alter_table('chunks', schema=None) as batch_op:
            batch_op.drop_column('pii_types')
            batch_op.drop_column('has_pii')
            batch_op.drop_column('token_count')

        print("PII tracking columns removed from SQLite")
