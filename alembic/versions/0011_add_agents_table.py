"""Add agents table for Agent Growth Platform Phase 0

Revision ID: 0011
Revises: 0010
Create Date: 2025-10-12 00:00:00.000000

Adds agents table with 19 columns for Agent Growth Platform.
Supports both PostgreSQL (native UUID[], JSONB) and SQLite (JSON serialization).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        op.create_table(
            'agents',
            sa.Column('agent_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('taxonomy_node_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
            sa.Column('taxonomy_version', sa.Text(), nullable=False, server_default='1.0.0'),
            sa.Column('scope_description', sa.Text(), nullable=True),
            sa.Column('total_documents', sa.Integer(), server_default='0'),
            sa.Column('total_chunks', sa.Integer(), server_default='0'),
            sa.Column('coverage_percent', sa.Float(), server_default='0.0'),
            sa.Column('last_coverage_update', sa.DateTime(), nullable=True),
            sa.Column('level', sa.Integer(), server_default='1'),
            sa.Column('current_xp', sa.Integer(), server_default='0'),
            sa.Column('total_queries', sa.Integer(), server_default='0'),
            sa.Column('successful_queries', sa.Integer(), server_default='0'),
            sa.Column('avg_faithfulness', sa.Float(), server_default='0.0'),
            sa.Column('avg_response_time_ms', sa.Float(), server_default='0.0'),
            sa.Column('retrieval_config', postgresql.JSONB(), server_default='{"top_k": 5, "strategy": "hybrid"}'),
            sa.Column('features_config', postgresql.JSONB(), server_default='{}'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('last_query_at', sa.DateTime(), nullable=True),
        )

        op.create_index('idx_agents_taxonomy', 'agents', ['taxonomy_node_ids'], postgresql_using='gin')
        op.create_index('idx_agents_level', 'agents', ['level'])
        op.create_index('idx_agents_coverage', 'agents', [sa.text('coverage_percent DESC')])

        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_level
            CHECK (level >= 1 AND level <= 5)
        """)
        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_xp
            CHECK (current_xp >= 0)
        """)
        op.execute("""
            ALTER TABLE agents ADD CONSTRAINT valid_coverage
            CHECK (coverage_percent >= 0 AND coverage_percent <= 100)
        """)

    else:
        op.create_table(
            'agents',
            sa.Column('agent_id', sa.String(36), primary_key=True),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('taxonomy_node_ids', sa.Text(), nullable=False),
            sa.Column('taxonomy_version', sa.Text(), nullable=False, server_default='1.0.0'),
            sa.Column('scope_description', sa.Text(), nullable=True),
            sa.Column('total_documents', sa.Integer(), server_default='0'),
            sa.Column('total_chunks', sa.Integer(), server_default='0'),
            sa.Column('coverage_percent', sa.Float(), server_default='0.0'),
            sa.Column('last_coverage_update', sa.DateTime(), nullable=True),
            sa.Column('level', sa.Integer(), server_default='1'),
            sa.Column('current_xp', sa.Integer(), server_default='0'),
            sa.Column('total_queries', sa.Integer(), server_default='0'),
            sa.Column('successful_queries', sa.Integer(), server_default='0'),
            sa.Column('avg_faithfulness', sa.Float(), server_default='0.0'),
            sa.Column('avg_response_time_ms', sa.Float(), server_default='0.0'),
            sa.Column('retrieval_config', sa.Text(), server_default='{"top_k": 5, "strategy": "hybrid"}'),
            sa.Column('features_config', sa.Text(), server_default='{}'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('last_query_at', sa.DateTime(), nullable=True),
        )

        op.create_index('idx_agents_level', 'agents', ['level'])
        op.create_index('idx_agents_coverage', 'agents', ['coverage_percent'])


def downgrade() -> None:
    op.drop_table('agents')
