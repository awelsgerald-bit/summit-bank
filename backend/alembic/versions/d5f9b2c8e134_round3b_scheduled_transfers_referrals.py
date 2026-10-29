"""Round 3B: scheduled transfers and referrals

Revision ID: d5f9b2c8e134
Revises: c4e8a1b9d702
Create Date: 2026-10-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5f9b2c8e134'
down_revision: Union[str, None] = 'c4e8a1b9d702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('referral_code', sa.String(length=12), nullable=True))
    op.add_column('users', sa.Column('referred_by_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_referred_by', 'users', 'users', ['referred_by_user_id'], ['id'])
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)

    op.create_table(
        'scheduled_transfers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recipient_account_number', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('frequency', sa.String(length=10), nullable=False),
        sa.Column('anchor_day', sa.Integer(), nullable=False),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('run_count', sa.Integer(), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_status', sa.String(length=10), nullable=True),
        sa.Column('last_error', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_scheduled_transfers_id', 'scheduled_transfers', ['id'])
    op.create_index('ix_scheduled_transfers_user_id', 'scheduled_transfers', ['user_id'])
    op.create_index('ix_scheduled_transfers_next_run_at', 'scheduled_transfers', ['next_run_at'])

    op.create_table(
        'scheduled_transfer_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('schedule_id', sa.Integer(), sa.ForeignKey('scheduled_transfers.id'), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('outcome', sa.String(length=10), nullable=False),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=True),
        sa.Column('detail', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('schedule_id', 'due_at', name='uq_schedule_due_time'),
    )
    op.create_index('ix_scheduled_transfer_runs_id', 'scheduled_transfer_runs', ['id'])
    op.create_index('ix_scheduled_transfer_runs_schedule_id', 'scheduled_transfer_runs', ['schedule_id'])

    op.create_table(
        'referral_rewards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('referrer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('referred_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('qualifying_transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=False),
        sa.Column('bonus_amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('referrer_transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=True, unique=True),
        sa.Column('referred_transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_referral_rewards_id', 'referral_rewards', ['id'])
    op.create_index('ix_referral_rewards_referrer_id', 'referral_rewards', ['referrer_id'])


def downgrade() -> None:
    op.drop_index('ix_referral_rewards_referrer_id', table_name='referral_rewards')
    op.drop_index('ix_referral_rewards_id', table_name='referral_rewards')
    op.drop_table('referral_rewards')
    op.drop_index('ix_scheduled_transfer_runs_schedule_id', table_name='scheduled_transfer_runs')
    op.drop_index('ix_scheduled_transfer_runs_id', table_name='scheduled_transfer_runs')
    op.drop_table('scheduled_transfer_runs')
    op.drop_index('ix_scheduled_transfers_next_run_at', table_name='scheduled_transfers')
    op.drop_index('ix_scheduled_transfers_user_id', table_name='scheduled_transfers')
    op.drop_index('ix_scheduled_transfers_id', table_name='scheduled_transfers')
    op.drop_table('scheduled_transfers')
    op.drop_index('ix_users_referral_code', table_name='users')
    op.drop_constraint('fk_users_referred_by', 'users', type_='foreignkey')
    op.drop_column('users', 'referred_by_user_id')
    op.drop_column('users', 'referral_code')
