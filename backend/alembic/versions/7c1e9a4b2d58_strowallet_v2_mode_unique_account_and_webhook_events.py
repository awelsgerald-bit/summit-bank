"""StroWallet v2: mode/provider, unique account number, webhook events table

Revision ID: 7c1e9a4b2d58
Revises: 1b6eae794ef6
Create Date: 2026-10-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1e9a4b2d58'
down_revision: Union[str, None] = '1b6eae794ef6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- strowallet_accounts: record mode + provider -------------------------------
    # Every row that exists today was created while the setting defaulted to sandbox.
    op.add_column(
        'strowallet_accounts',
        sa.Column('mode', sa.String(length=10), server_default='sandbox', nullable=False),
    )
    op.add_column('strowallet_accounts', sa.Column('provider', sa.String(length=30), nullable=True))

    # --- strowallet_accounts: unique account number --------------------------------
    # Render runs `alembic upgrade head` on every deploy, so a duplicate here would stop
    # the API from starting. Defensive: keep the oldest row for any duplicated number and
    # blank the later ones (marked failed, nothing deleted) so the unique index can build.
    op.execute(sa.text("""
        UPDATE strowallet_accounts
        SET nuban_account_number = NULL,
            status = 'failed',
            failure_reason = 'Duplicate account number cleared by migration 7c1e9a4b2d58'
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY nuban_account_number ORDER BY id
                       ) AS rn
                FROM strowallet_accounts
                WHERE nuban_account_number IS NOT NULL
            ) AS ranked
            WHERE ranked.rn > 1
        )
    """))
    op.create_index(
        op.f('ix_strowallet_accounts_nuban_account_number'),
        'strowallet_accounts',
        ['nuban_account_number'],
        unique=True,
    )

    # --- strowallet_webhook_events -------------------------------------------------
    op.create_table(
        'strowallet_webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_body', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivery_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('account_number', sa.String(length=20), nullable=True),
        sa.Column('transaction_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('settled_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='received', nullable=False),
        sa.Column('status_detail', sa.String(length=255), nullable=True),
        sa.Column('strowallet_account_id', sa.Integer(), nullable=True),
        sa.Column('verify_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('verify_response', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['strowallet_account_id'], ['strowallet_accounts.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id'),
    )
    op.create_index(op.f('ix_strowallet_webhook_events_id'), 'strowallet_webhook_events', ['id'], unique=False)
    op.create_index(op.f('ix_strowallet_webhook_events_session_id'), 'strowallet_webhook_events', ['session_id'], unique=True)
    op.create_index(op.f('ix_strowallet_webhook_events_account_number'), 'strowallet_webhook_events', ['account_number'], unique=False)
    op.create_index(op.f('ix_strowallet_webhook_events_strowallet_account_id'), 'strowallet_webhook_events', ['strowallet_account_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_strowallet_webhook_events_strowallet_account_id'), table_name='strowallet_webhook_events')
    op.drop_index(op.f('ix_strowallet_webhook_events_account_number'), table_name='strowallet_webhook_events')
    op.drop_index(op.f('ix_strowallet_webhook_events_session_id'), table_name='strowallet_webhook_events')
    op.drop_index(op.f('ix_strowallet_webhook_events_id'), table_name='strowallet_webhook_events')
    op.drop_table('strowallet_webhook_events')

    op.drop_index(op.f('ix_strowallet_accounts_nuban_account_number'), table_name='strowallet_accounts')
    op.drop_column('strowallet_accounts', 'provider')
    op.drop_column('strowallet_accounts', 'mode')