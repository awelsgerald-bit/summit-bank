"""Speed: indexes on the columns every screen filters by

Revision ID: e6a1c3d7f245
Revises: d5f9b2c8e134
Create Date: 2026-11-01 09:00:00.000000

Without these, listing "my transactions" or "my cards" reads the whole table. IF NOT EXISTS keeps the
migration safe to run twice and on a database that already has some of them.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e6a1c3d7f245'
down_revision: Union[str, None] = 'd5f9b2c8e134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ('transactions', 'sender_id'),
    ('transactions', 'receiver_id'),
    ('transactions', 'status'),
    ('beneficiaries', 'user_id'),
    ('card_applications', 'user_id'),
    ('fixed_deposits', 'user_id'),
    ('kyc_submissions', 'user_id'),
    ('loans', 'user_id'),
    ('paystack_payments', 'user_id'),
    ('wallet_applications', 'user_id'),
    ('ledger_entries', 'ledger_account_id'),
    ('ledger_entries', 'reference_transaction_id'),
]


def upgrade() -> None:
    for table, column in INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})')


def downgrade() -> None:
    for table, column in INDEXES:
        op.execute(f'DROP INDEX IF EXISTS ix_{table}_{column}')
