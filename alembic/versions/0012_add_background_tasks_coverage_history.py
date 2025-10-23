"""Add background_tasks and coverage_history tables for Agent Growth Platform Phase 3

Revision ID: 0012
Revises: 0011
Create Date: 2025-10-12 00:00:00.000000

Adds background_tasks table (15 columns) for real background task processing.
Adds coverage_history table (7 columns) for time-series coverage tracking.
Supports both PostgreSQL (native UUID, JSONB) and SQLite (JSON serialization).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        # PostgreSQL: background_tasks table
        op.create_table(
            'background_tasks',
            sa.Column('task_id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('task_type', sa.String(50), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(now() AT TIME ZONE 'UTC')")),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('result', postgresql.JSONB(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('webhook_url', sa.Text(), nullable=True),
            sa.Column('webhook_retry_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('cancellation_requested', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('queue_position', sa.Integer(), nullable=True),
            sa.Column('progress_percentage', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('estimated_completion_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ['agent_id'],
                ['agents.agent_id'],
                name='fk_background_tasks_agent_id',
                ondelete='CASCADE'
            )
        )

        # PostgreSQL: background_tasks indexes
        op.create_index('idx_background_tasks_agent_id', 'background_tasks', ['agent_id'])
        op.create_index('idx_background_tasks_status', 'background_tasks', ['status'])
        op.create_index('idx_background_tasks_created_at', 'background_tasks', [sa.text('created_at DESC')])
        op.create_index('idx_background_tasks_agent_status', 'background_tasks', ['agent_id', 'status'])

        # PostgreSQL: coverage_history table
        op.create_table(
            'coverage_history',
            sa.Column('history_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text("(now() AT TIME ZONE 'UTC')")),
            sa.Column('overall_coverage', sa.Float(), nullable=False),
            sa.Column('total_documents', sa.Integer(), nullable=False),
            sa.Column('total_chunks', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
            sa.ForeignKeyConstraint(
                ['agent_id'],
                ['agents.agent_id'],
                name='fk_coverage_history_agent_id',
                ondelete='CASCADE'
            )
        )

        # PostgreSQL: coverage_history indexes
        op.create_index('idx_coverage_history_agent_id', 'coverage_history', ['agent_id'])
        op.create_index('idx_coverage_history_timestamp', 'coverage_history', [sa.text('timestamp DESC')])
        op.create_index('idx_coverage_history_agent_timestamp', 'coverage_history', ['agent_id', sa.text('timestamp DESC')])

        # PostgreSQL: CHECK constraints for coverage_history
        op.execute("""
            ALTER TABLE coverage_history ADD CONSTRAINT valid_overall_coverage
            CHECK (overall_coverage >= 0.0 AND overall_coverage <= 100.0)
        """)
        op.execute("""
            ALTER TABLE coverage_history ADD CONSTRAINT valid_total_documents
            CHECK (total_documents >= 0)
        """)
        op.execute("""
            ALTER TABLE coverage_history ADD CONSTRAINT valid_total_chunks
            CHECK (total_chunks >= 0)
        """)

        # PostgreSQL: Table comments
        op.execute("""
            COMMENT ON TABLE background_tasks IS 'Stores background task status for agent operations (coverage, gaps, reports)'
        """)
        op.execute("""
            COMMENT ON COLUMN background_tasks.task_type IS 'Task type identifier for dispatching to appropriate worker'
        """)
        op.execute("""
            COMMENT ON COLUMN background_tasks.status IS 'Task lifecycle: pending → running → completed|failed|cancelled|timeout'
        """)
        op.execute("""
            COMMENT ON COLUMN background_tasks.result IS 'JSONB result data structure (varies by task_type)'
        """)
        op.execute("""
            COMMENT ON COLUMN background_tasks.webhook_url IS 'Optional webhook URL for task completion notification'
        """)
        op.execute("""
            COMMENT ON COLUMN background_tasks.cancellation_requested IS 'Cooperative cancellation flag polled by workers'
        """)
        op.execute("""
            COMMENT ON TABLE coverage_history IS 'Time-series coverage data for agent performance tracking (90-day retention)'
        """)
        op.execute("""
            COMMENT ON COLUMN coverage_history.overall_coverage IS 'Overall coverage percentage (0.0-100.0)'
        """)
        op.execute("""
            COMMENT ON COLUMN coverage_history.timestamp IS 'UTC timestamp of coverage calculation'
        """)
        op.execute("""
            COMMENT ON COLUMN coverage_history.version IS 'Taxonomy version used for coverage calculation'
        """)

    else:
        # SQLite: background_tasks table
        op.create_table(
            'background_tasks',
            sa.Column('task_id', sa.String(36), primary_key=True),
            sa.Column('agent_id', sa.String(36), nullable=False),
            sa.Column('task_type', sa.String(50), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('result', sa.Text(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('webhook_url', sa.Text(), nullable=True),
            sa.Column('webhook_retry_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('cancellation_requested', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('queue_position', sa.Integer(), nullable=True),
            sa.Column('progress_percentage', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('estimated_completion_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ['agent_id'],
                ['agents.agent_id'],
                name='fk_background_tasks_agent_id',
                ondelete='CASCADE'
            )
        )

        # SQLite: background_tasks indexes
        op.create_index('idx_background_tasks_agent_id', 'background_tasks', ['agent_id'])
        op.create_index('idx_background_tasks_status', 'background_tasks', ['status'])
        op.create_index('idx_background_tasks_created_at', 'background_tasks', ['created_at'])
        op.create_index('idx_background_tasks_agent_status', 'background_tasks', ['agent_id', 'status'])

        # SQLite: coverage_history table
        op.create_table(
            'coverage_history',
            sa.Column('history_id', sa.String(36), primary_key=True, server_default=sa.func.lower(sa.func.hex(sa.func.randomblob(16)))),
            sa.Column('agent_id', sa.String(36), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('overall_coverage', sa.Float(), nullable=False),
            sa.Column('total_documents', sa.Integer(), nullable=False),
            sa.Column('total_chunks', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
            sa.ForeignKeyConstraint(
                ['agent_id'],
                ['agents.agent_id'],
                name='fk_coverage_history_agent_id',
                ondelete='CASCADE'
            ),
            sa.CheckConstraint('overall_coverage >= 0.0 AND overall_coverage <= 100.0', name='valid_overall_coverage'),
            sa.CheckConstraint('total_documents >= 0', name='valid_total_documents'),
            sa.CheckConstraint('total_chunks >= 0', name='valid_total_chunks')
        )

        # SQLite: coverage_history indexes
        op.create_index('idx_coverage_history_agent_id', 'coverage_history', ['agent_id'])
        op.create_index('idx_coverage_history_timestamp', 'coverage_history', ['timestamp'])
        op.create_index('idx_coverage_history_agent_timestamp', 'coverage_history', ['agent_id', 'timestamp'])


def downgrade() -> None:
    op.drop_table('coverage_history')
    op.drop_table('background_tasks')
