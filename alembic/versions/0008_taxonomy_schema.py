"""Add taxonomy schema tables

Revision ID: 0008
Revises: 0007
Create Date: 2025-10-06 00:00:00.000000

Implements PRD Annex C.4 taxonomy database schema:
- taxonomy_nodes: DAG node definitions
- taxonomy_edges: parent-child relationships
- doc_taxonomy: document-to-taxonomy mappings
- taxonomy_migrations: version migration history
- case_bank: query-response case storage
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create taxonomy tables per PRD specification"""
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

    if 'postgresql' not in database_url:
        print("SQLite detected - skipping taxonomy schema creation")
        return

    # Check if tables already exist before creating
    op.execute("""
        DO $$
        BEGIN
            -- 1. taxonomy_nodes table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'taxonomy_nodes'
            ) THEN
                CREATE TABLE taxonomy_nodes (
                    node_id UUID NOT NULL,
                    label TEXT,
                    canonical_path TEXT[],
                    version TEXT,
                    confidence FLOAT,
                    PRIMARY KEY (node_id)
                );
                RAISE NOTICE 'Created taxonomy_nodes table';
            ELSE
                RAISE NOTICE 'taxonomy_nodes table already exists, skipping';
            END IF;

            -- 2. taxonomy_edges table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'taxonomy_edges'
            ) THEN
                CREATE TABLE taxonomy_edges (
                    parent UUID NOT NULL,
                    child UUID NOT NULL,
                    version TEXT NOT NULL,
                    PRIMARY KEY (parent, child, version),
                    FOREIGN KEY (parent) REFERENCES taxonomy_nodes(node_id),
                    FOREIGN KEY (child) REFERENCES taxonomy_nodes(node_id)
                );
                RAISE NOTICE 'Created taxonomy_edges table';
            ELSE
                RAISE NOTICE 'taxonomy_edges table already exists, skipping';
            END IF;

            -- 3. doc_taxonomy table (requires documents table)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'doc_taxonomy'
            ) THEN
                -- Check if documents table exists before creating doc_taxonomy
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'documents'
                ) THEN
                    CREATE TABLE doc_taxonomy (
                        mapping_id SERIAL PRIMARY KEY,
                        doc_id UUID,
                        node_id UUID,
                        version TEXT,
                        path TEXT[],
                        confidence FLOAT,
                        hitl_required BOOLEAN DEFAULT false,
                        FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
                        FOREIGN KEY (node_id) REFERENCES taxonomy_nodes(node_id)
                    );
                    RAISE NOTICE 'Created doc_taxonomy table';
                ELSE
                    RAISE NOTICE 'documents table does not exist, skipping doc_taxonomy creation';
                END IF;
            ELSE
                RAISE NOTICE 'doc_taxonomy table already exists, skipping';
            END IF;

            -- 4. taxonomy_migrations table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'taxonomy_migrations'
            ) THEN
                CREATE TABLE taxonomy_migrations (
                    migration_id SERIAL PRIMARY KEY,
                    from_version TEXT,
                    to_version TEXT,
                    from_path TEXT[],
                    to_path TEXT[],
                    rationale TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                );
                RAISE NOTICE 'Created taxonomy_migrations table';
            ELSE
                RAISE NOTICE 'taxonomy_migrations table already exists, skipping';
            END IF;

            -- 5. case_bank table
            -- @CODE:CASEBANK-UNIFY-MIGRATION-001 - Updated field names to match production model
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'case_bank'
            ) THEN
                CREATE TABLE case_bank (
                    case_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,  -- Changed from response_text
                    sources JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Added
                    category_path TEXT[] NOT NULL,
                    query_vector FLOAT[],  -- Changed to nullable
                    quality FLOAT,  -- Changed from quality_score
                    usage_count INTEGER DEFAULT 0,  -- Added default
                    success_rate FLOAT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    last_used_at TIMESTAMP WITH TIME ZONE
                );
                RAISE NOTICE 'Created case_bank table';
            ELSE
                RAISE NOTICE 'case_bank table already exists, skipping';
            END IF;

            -- Create indexes if they don't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_taxonomy_nodes_canonical_path'
            ) THEN
                CREATE INDEX idx_taxonomy_nodes_canonical_path ON taxonomy_nodes USING gin (canonical_path);
                RAISE NOTICE 'Created index idx_taxonomy_nodes_canonical_path';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_doc_taxonomy_path'
            ) THEN
                CREATE INDEX idx_doc_taxonomy_path ON doc_taxonomy USING gin (path);
                RAISE NOTICE 'Created index idx_doc_taxonomy_path';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_doc_taxonomy_hitl'
            ) THEN
                CREATE INDEX idx_doc_taxonomy_hitl ON doc_taxonomy (hitl_required) WHERE hitl_required = true;
                RAISE NOTICE 'Created index idx_doc_taxonomy_hitl';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_taxonomy_nodes_version'
            ) THEN
                CREATE INDEX idx_taxonomy_nodes_version ON taxonomy_nodes (version);
                RAISE NOTICE 'Created index idx_taxonomy_nodes_version';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_taxonomy_edges_version'
            ) THEN
                CREATE INDEX idx_taxonomy_edges_version ON taxonomy_edges (version);
                RAISE NOTICE 'Created index idx_taxonomy_edges_version';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_doc_taxonomy_doc_id'
            ) THEN
                CREATE INDEX idx_doc_taxonomy_doc_id ON doc_taxonomy (doc_id);
                RAISE NOTICE 'Created index idx_doc_taxonomy_doc_id';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_doc_taxonomy_node_id'
            ) THEN
                CREATE INDEX idx_doc_taxonomy_node_id ON doc_taxonomy (node_id);
                RAISE NOTICE 'Created index idx_doc_taxonomy_node_id';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_case_bank_category'
            ) THEN
                CREATE INDEX idx_case_bank_category ON case_bank USING gin (category_path);
                RAISE NOTICE 'Created index idx_case_bank_category';
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    """Remove taxonomy tables in reverse order"""

    # Drop indexes first
    op.drop_index('idx_case_bank_category', table_name='case_bank')
    op.drop_index('idx_doc_taxonomy_node_id', table_name='doc_taxonomy')
    op.drop_index('idx_doc_taxonomy_doc_id', table_name='doc_taxonomy')
    op.drop_index('idx_taxonomy_edges_version', table_name='taxonomy_edges')
    op.drop_index('idx_taxonomy_nodes_version', table_name='taxonomy_nodes')
    op.drop_index('idx_doc_taxonomy_hitl', table_name='doc_taxonomy')
    op.drop_index('idx_doc_taxonomy_path', table_name='doc_taxonomy')
    op.drop_index('idx_taxonomy_nodes_canonical_path', table_name='taxonomy_nodes')

    # Drop tables in reverse dependency order
    op.drop_table('case_bank')
    op.drop_table('taxonomy_migrations')
    op.drop_table('doc_taxonomy')
    op.drop_table('taxonomy_edges')
    op.drop_table('taxonomy_nodes')
