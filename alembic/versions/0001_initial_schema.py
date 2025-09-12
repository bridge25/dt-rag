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
    """Execute SQL file statement-by-statement (handles DO $$ blocks)."""
    import os
    migration_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'migrations')
    sql_file = os.path.join(migration_dir, '0001_initial_schema.sql')

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
                lines = [ln.strip() for ln in stmt.splitlines() if ln.strip()]
                if not lines or all(ln.startswith('--') for ln in lines):
                    buf = []
                    i += 1
                    continue
                stmts.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = ''.join(buf).strip()
    if tail:
        lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
        if lines and not all(ln.startswith('--') for ln in lines):
            stmts.append(tail)

    for stmt in stmts:
        cleaned = "\n".join(
            ln for ln in (stmt or "").splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ).strip()
        if not cleaned:
            continue
        try:
            op.execute(stmt)
        except Exception:
            print("\n[alembic 0001] FAILED STATEMENT:\n" + stmt[:1000] + "\n--- END STMT ---\n")
            raise


def downgrade() -> None:
    """Drop all tables created in initial schema"""
    # Drop tables in reverse dependency order using IF EXISTS
    op.execute('DROP TABLE IF EXISTS doc_taxonomy CASCADE')
    op.execute('DROP TABLE IF EXISTS embeddings CASCADE')
    op.execute('DROP TABLE IF EXISTS chunks CASCADE')
    op.execute('DROP TABLE IF EXISTS documents CASCADE')
    op.execute('DROP TABLE IF EXISTS taxonomy_migrations CASCADE')
    op.execute('DROP TABLE IF EXISTS taxonomy_edges CASCADE')
    op.execute('DROP TABLE IF EXISTS taxonomy_nodes CASCADE')
    
    # Drop extensions (optional - may be used by other schemas)
    # op.execute('DROP EXTENSION IF EXISTS vector')
    # op.execute('DROP EXTENSION IF EXISTS btree_gist')
