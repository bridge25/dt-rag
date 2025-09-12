"""Span range and performance indexes

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-15 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute SQL file statement-by-statement (handles DO $$ blocks)."""
    import os
    migration_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'migrations')
    sql_file = os.path.join(migration_dir, '0002_span_range_and_indexes.sql')

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    stmts = []
    buf = []
    i = 0
    in_dollar = False
    while i < len(sql):
        if sql[i:i+2] == '$$':
            in_dollar = not in_dollar
            buf.append('$$')
            i += 2
            continue
        ch = sql[i]
        if ch == ';' and not in_dollar:
            stmt = ''.join(buf).strip()
            if stmt:
                stmts.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = ''.join(buf).strip()
    if tail:
        stmts.append(tail)

    for stmt in stmts:
        # Skip pure-comment/empty statements
        cleaned = "\n".join(
            ln for ln in (stmt or "").splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ).strip()
        if not cleaned:
            continue
        try:
            op.execute(stmt)
        except Exception:
            print("\n[alembic 0002] FAILED STATEMENT:\n" + stmt[:1000] + "\n--- END STMT ---\n")
            raise


def downgrade() -> None:
    """Drop indexes and utility functions"""
    # Drop indexes (Alembic will handle this automatically in most cases)
    
    # Drop utility functions
    op.execute('DROP FUNCTION IF EXISTS chunk_span_length(int4range)')
    op.execute('DROP FUNCTION IF EXISTS spans_overlap(int4range, int4range)')
    op.execute('DROP FUNCTION IF EXISTS taxonomy_depth(TEXT[])')
    
    # Drop specific indexes created in this migration
    index_names = [
        'idx_chunks_span_gist',
        'idx_chunks_doc_span_gist', 
        'idx_taxonomy_canonical',
        'idx_doc_taxonomy_path',
        'idx_embeddings_bm25',
        'idx_chunks_chunk_index',
        'idx_doc_taxonomy_confidence',
        'idx_taxonomy_migrations_versions',
        'idx_taxonomy_nodes_active_version',
        'idx_chunks_metadata_cover',
        'idx_doc_taxonomy_composite',
        'idx_embeddings_model_created',
        'idx_documents_checksum_hash',
        'idx_chunks_text_length',
        'idx_taxonomy_path_depth',
        'idx_embeddings_model_lower',
        'idx_documents_title_trgm'
    ]
    
    for index_name in index_names:
        op.execute(f'DROP INDEX IF EXISTS {index_name}')
