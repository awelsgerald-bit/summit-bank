"""Update default currency to NGN

Revision ID: d0d917bfee5e
Revises: 172ba9cc05c2
Create Date: 2026-09-07 09:01:54.081218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0d917bfee5e'
down_revision: Union[str, None] = '172ba9cc05c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE transactions SET currency = 'NGN' WHERE currency = 'USD'")
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('currency', server_default='NGN')


def downgrade() -> None:
    op.execute("UPDATE transactions SET currency = 'USD' WHERE currency = 'NGN'")
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('currency', server_default='USD')