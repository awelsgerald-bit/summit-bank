"""Add avatar to users

Revision ID: a1f3c9d2e801
Revises: 7c1e9a4b2d58
Create Date: 2026-10-27 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1f3c9d2e801'
down_revision: Union[str, None] = '7c1e9a4b2d58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar')
