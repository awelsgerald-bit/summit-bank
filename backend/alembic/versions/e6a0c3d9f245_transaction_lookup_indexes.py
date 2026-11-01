"""Speed: indexes for the columns every history, statement and balance lookup filters on

Revision ID: e6a0c3d9f245
Revises: d5f9b2c8e134
Create Date: 2026-11-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e6a0c3d9f245'
down_revision: Union[str, None] = 'd5f9b2c8e134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ('ix_transactions_sender_id', 'sender_id'),
    ('ix_transactions_receiver_id', 'receiver_id'),
    ('ix_transactions_status', 'status'),
]


def upgrade() -> None:
    # IF NOT EXISTS keeps a deploy from failing if one of these was ever made by hand.
    for name, column in INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON transactions ({column})')


def downgrade() -> None:
    for name, _ in INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')
