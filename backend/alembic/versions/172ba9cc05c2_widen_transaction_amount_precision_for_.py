"""Widen transaction amount precision for BTC

Revision ID: 172ba9cc05c2
Revises: 287d8417458e
Create Date: 2026-09-06 02:48:25.604651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '172ba9cc05c2'
down_revision: Union[str, None] = '287d8417458e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column(
            'amount',
            existing_type=sa.Numeric(precision=14, scale=2),
            type_=sa.Numeric(precision=20, scale=8),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column(
            'amount',
            existing_type=sa.Numeric(precision=20, scale=8),
            type_=sa.Numeric(precision=14, scale=2),
            existing_nullable=False,
        )
