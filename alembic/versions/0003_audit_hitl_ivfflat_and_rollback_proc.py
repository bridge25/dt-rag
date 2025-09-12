"""Audit log, HITL queue, vector indexes and rollback procedures

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-15 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute SQL file statement-by-statement (handles DO $$ blocks)."""
    import os
    migration_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'migrations')
    sql_file = os.path.join(migration_dir, '0003_audit_hitl_ivfflat_and_rollback_proc.sql')

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
        op.execute(stmt)


def downgrade() -> None:
    """Remove audit log, HITL queue, and rollback procedures"""
    
    # Drop triggers first
    op.execute('DROP TRIGGER IF EXISTS tr_audit_taxonomy_nodes ON taxonomy_nodes')
    
    # Drop trigger function
    op.execute('DROP FUNCTION IF EXISTS audit_taxonomy_changes()')
    
    # Drop views
    op.execute('DROP VIEW IF EXISTS v_low_confidence_classifications')
    op.execute('DROP VIEW IF EXISTS v_taxonomy_version_summary')
    
    # Drop functions and procedures
    op.execute('DROP FUNCTION IF EXISTS add_to_hitl_queue(UUID, JSONB, TEXT[], REAL)')
    op.execute('DROP PROCEDURE IF EXISTS taxonomy_rollback(INTEGER)')
    
    # Drop tables (conditional - using raw SQL to handle IF EXISTS)
    op.execute('DROP TABLE IF EXISTS hitl_queue CASCADE')
    op.execute('DROP TABLE IF EXISTS audit_log CASCADE')
    
    # Drop indexes conditionally
    op.execute('DROP INDEX IF EXISTS idx_embeddings_vec_ivf')
    op.execute('DROP INDEX IF EXISTS idx_audit_log_timestamp')
    op.execute('DROP INDEX IF EXISTS idx_audit_log_action_actor')
    op.execute('DROP INDEX IF EXISTS idx_audit_log_target')
    op.execute('DROP INDEX IF EXISTS idx_hitl_queue_status_priority')
    op.execute('DROP INDEX IF EXISTS idx_hitl_queue_confidence')
    op.execute('DROP INDEX IF EXISTS idx_hitl_queue_assigned')
