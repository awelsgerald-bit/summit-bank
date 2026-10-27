"""Round 3a: transaction PIN columns and Save4Me savings tables

Revision ID: c4e8a1b9d702
Revises: b7d2e4f6a913
Create Date: 2026-10-27 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4e8a1b9d702'
down_revision: Union[str, None] = 'b7d2e4f6a913'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('transaction_pin_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('pin_failed_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('pin_locked_until', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'savings_pots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('target_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('balance', sa.Numeric(14, 2), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_savings_pots_id', 'savings_pots', ['id'])
    op.create_index('ix_savings_pots_user_id', 'savings_pots', ['user_id'])

    op.create_table(
        'savings_movements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pot_id', sa.Integer(), sa.ForeignKey('savings_pots.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('pot_balance_after', sa.Numeric(14, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_savings_movements_id', 'savings_movements', ['id'])
    op.create_index('ix_savings_movements_pot_id', 'savings_movements', ['pot_id'])


def downgrade() -> None:
    op.drop_index('ix_savings_movements_pot_id', table_name='savings_movements')
    op.drop_index('ix_savings_movements_id', table_name='savings_movements')
    op.drop_table('savings_movements')
    op.drop_index('ix_savings_pots_user_id', table_name='savings_pots')
    op.drop_index('ix_savings_pots_id', table_name='savings_pots')
    op.drop_table('savings_pots')
    op.drop_column('users', 'pin_locked_until')
    op.drop_column('users', 'pin_failed_attempts')
    op.drop_column('users', 'transaction_pin_hash')
