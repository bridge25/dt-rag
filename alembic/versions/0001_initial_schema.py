"""Initial schema - taxonomy, documents, chunks, embeddings

Revision ID: 0001
Revises: 
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute SQL migration file: 0001_initial_schema.sql"""
    # Read and execute the SQL file
    import os
    migration_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'migrations')
    sql_file = os.path.join(migration_dir, '0001_initial_schema.sql')
    
    with open(sql_file, 'r') as f:
        sql_commands = f.read()
    
    # Execute the SQL commands
    op.execute(sql_commands)


def downgrade() -> None:
    """Drop all tables created in initial schema"""
    # Drop tables in reverse dependency order
    op.drop_table('doc_taxonomy')
    op.drop_table('embeddings') 
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('taxonomy_migrations')
    op.drop_table('taxonomy_edges')
    op.drop_table('taxonomy_nodes')
    
    # Drop extensions (optional - may be used by other schemas)
    # op.execute('DROP EXTENSION IF EXISTS vector')
    # op.execute('DROP EXTENSION IF EXISTS btree_gist')