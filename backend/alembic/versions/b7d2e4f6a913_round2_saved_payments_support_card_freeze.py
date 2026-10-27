"""Round 2: saved payments, support tickets, card freeze

Revision ID: b7d2e4f6a913
Revises: a1f3c9d2e801
Create Date: 2026-10-27 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7d2e4f6a913'
down_revision: Union[str, None] = 'a1f3c9d2e801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('label', sa.String(length=60), nullable=False),
        sa.Column('recipient_account_number', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('last_paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_saved_payments_id', 'saved_payments', ['id'])
    op.create_index('ix_saved_payments_user_id', 'saved_payments', ['user_id'])

    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('subject', sa.String(length=120), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('admin_reply', sa.Text(), nullable=True),
        sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_support_tickets_id', 'support_tickets', ['id'])
    op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'])
    op.create_index('ix_support_tickets_created_at', 'support_tickets', ['created_at'])

    op.add_column(
        'card_applications',
        sa.Column('is_frozen', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('card_applications', 'is_frozen')
    op.drop_index('ix_support_tickets_created_at', table_name='support_tickets')
    op.drop_index('ix_support_tickets_user_id', table_name='support_tickets')
    op.drop_index('ix_support_tickets_id', table_name='support_tickets')
    op.drop_table('support_tickets')
    op.drop_index('ix_saved_payments_user_id', table_name='saved_payments')
    op.drop_index('ix_saved_payments_id', table_name='saved_payments')
    op.drop_table('saved_payments')
