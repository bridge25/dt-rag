"""Merge migration branches after PR #48

Revision ID: 1361849bf32d
Revises: 0012, da725cdb420a
Create Date: 2025-10-23 23:58:50.843966

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1361849bf32d'
down_revision = ('0012', 'da725cdb420a')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass