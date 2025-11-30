"""Add Q-Table persistence for reinforcement learning weight optimization

Revision ID: 0014
Revises: 0013
Create Date: 2025-11-30 00:00:00.000000

@CODE:REFACTOR-PHASE-1-002

Adds q_table_entries table for persistent Q-Table storage.
Previously Q-Table data was stored in-memory and lost on restart.

Schema:
- id: Primary key (auto-increment)
- state_hash: Unique 64-char hash representing the state
- q_values: JSON array of 6 float values (Q-values for each action)
- updated_at: Last update timestamp
- access_count: Number of times this entry was accessed

Supports both PostgreSQL (JSONB) and SQLite (TEXT with JSON serialization).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        op.create_table(
            'q_table_entries',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('state_hash', sa.String(64), nullable=False, unique=True, index=True),
            sa.Column('q_values', postgresql.JSONB(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('access_count', sa.Integer(), server_default='0', nullable=False),
        )

        # Create index for faster lookups
        op.create_index('idx_qtable_state_hash', 'q_table_entries', ['state_hash'])
        op.create_index('idx_qtable_updated_at', 'q_table_entries', ['updated_at'])

        # Add constraint for valid access_count
        op.execute("""
            ALTER TABLE q_table_entries ADD CONSTRAINT valid_access_count
            CHECK (access_count >= 0)
        """)

    else:
        # SQLite fallback
        op.create_table(
            'q_table_entries',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('state_hash', sa.String(64), nullable=False, unique=True),
            sa.Column('q_values', sa.Text(), nullable=False),  # JSON serialized
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('access_count', sa.Integer(), server_default='0', nullable=False),
        )

        op.create_index('idx_qtable_state_hash_sqlite', 'q_table_entries', ['state_hash'])


def downgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    if is_postgresql:
        op.execute("ALTER TABLE q_table_entries DROP CONSTRAINT IF EXISTS valid_access_count")
        op.drop_index('idx_qtable_updated_at')
        op.drop_index('idx_qtable_state_hash')
    else:
        op.drop_index('idx_qtable_state_hash_sqlite')

    op.drop_table('q_table_entries')
