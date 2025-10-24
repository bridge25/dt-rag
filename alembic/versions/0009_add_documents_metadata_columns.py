"""Add metadata columns to documents table

Revision ID: 0009
Revises: 0008
Create Date: 2025-10-07 12:00:00.000000

Adds missing columns to documents table to match ORM model:
- title (Text)
- content_type (String(100))
- file_size (Integer)
- checksum (String(64))
- doc_metadata (JSON/JSONB)
- chunk_metadata (JSON/JSONB)
- processed_at (DateTime)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to documents table"""

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

    is_postgresql = 'postgresql' in database_url

    # Check if we're in offline mode (MockConnection doesn't support inspection)
    is_offline_mode = bind.__class__.__name__ == 'MockConnection'

    if is_offline_mode:
        # In offline mode, generate SQL for all columns unconditionally
        op.add_column('documents', sa.Column('title', sa.Text(), nullable=True))
        op.add_column('documents', sa.Column('content_type', sa.String(100), nullable=False, server_default='text/plain'))
        op.add_column('documents', sa.Column('file_size', sa.Integer(), nullable=True))
        op.add_column('documents', sa.Column('checksum', sa.String(64), nullable=True))

        if is_postgresql:
            op.add_column('documents', sa.Column('doc_metadata', postgresql.JSONB(), nullable=False, server_default='{}'))
            op.add_column('documents', sa.Column('chunk_metadata', postgresql.JSONB(), nullable=False, server_default='{}'))
        else:
            op.add_column('documents', sa.Column('doc_metadata', sa.TEXT(), nullable=False, server_default='{}'))
            op.add_column('documents', sa.Column('chunk_metadata', sa.TEXT(), nullable=False, server_default='{}'))

        op.add_column('documents', sa.Column('processed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        return

    # Online mode: check existing columns before adding
    inspector = sa.inspect(bind)

    if 'documents' not in inspector.get_table_names():
        print("documents table does not exist - skipping migration")
        return

    existing_columns = [col['name'] for col in inspector.get_columns('documents')]

    if 'title' not in existing_columns:
        op.add_column('documents',
                     sa.Column('title', sa.Text(), nullable=True))
        print("Added title column to documents")

    if 'content_type' not in existing_columns:
        op.add_column('documents',
                     sa.Column('content_type', sa.String(100), nullable=False, server_default='text/plain'))
        print("Added content_type column to documents")

    if 'file_size' not in existing_columns:
        op.add_column('documents',
                     sa.Column('file_size', sa.Integer(), nullable=True))
        print("Added file_size column to documents")

    if 'checksum' not in existing_columns:
        op.add_column('documents',
                     sa.Column('checksum', sa.String(64), nullable=True))
        print("Added checksum column to documents")

    if 'doc_metadata' not in existing_columns:
        if is_postgresql:
            op.add_column('documents',
                         sa.Column('doc_metadata', postgresql.JSONB(), nullable=False, server_default='{}'))
        else:
            op.add_column('documents',
                         sa.Column('doc_metadata', sa.TEXT(), nullable=False, server_default='{}'))
        print("Added doc_metadata column to documents")

    if 'chunk_metadata' not in existing_columns:
        if is_postgresql:
            op.add_column('documents',
                         sa.Column('chunk_metadata', postgresql.JSONB(), nullable=False, server_default='{}'))
        else:
            op.add_column('documents',
                         sa.Column('chunk_metadata', sa.TEXT(), nullable=False, server_default='{}'))
        print("Added chunk_metadata column to documents")

    if 'processed_at' not in existing_columns:
        op.add_column('documents',
                     sa.Column('processed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        print("Added processed_at column to documents")

    print("Migration 0009 completed successfully")


def downgrade() -> None:
    """Remove added columns from documents table"""

    bind = op.get_bind()

    # Check if we're in offline mode (MockConnection doesn't support inspection)
    is_offline_mode = bind.__class__.__name__ == 'MockConnection'

    if is_offline_mode:
        # In offline mode, generate SQL for dropping all columns unconditionally
        for column in ['processed_at', 'chunk_metadata', 'doc_metadata', 'checksum',
                       'file_size', 'content_type', 'title']:
            op.drop_column('documents', column)
        return

    # Online mode: check existing columns before dropping
    inspector = sa.inspect(bind)

    if 'documents' not in inspector.get_table_names():
        return

    existing_columns = [col['name'] for col in inspector.get_columns('documents')]

    for column in ['processed_at', 'chunk_metadata', 'doc_metadata', 'checksum',
                   'file_size', 'content_type', 'title']:
        if column in existing_columns:
            op.drop_column('documents', column)
            print(f"Dropped {column} column from documents")

    print("Downgrade 0009 completed")
