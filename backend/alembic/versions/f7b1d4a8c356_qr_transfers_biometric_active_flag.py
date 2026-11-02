"""QR transfers, fingerprint/Face ID credentials, and an account active flag

Revision ID: f7b1d4a8c356
Revises: e6a0c3d9f245
Create Date: 2026-11-02 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'f7b1d4a8c356'
down_revision: Union[str, None] = 'e6a0c3d9f245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table(
        'qr_payment_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(24), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('reference', sa.String(60), nullable=True),
        sa.Column('note', sa.String(140), nullable=True),
        sa.Column('status', sa.String(12), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_qr_payment_requests_id', 'qr_payment_requests', ['id'])
    op.create_index('ix_qr_payment_requests_code', 'qr_payment_requests', ['code'], unique=True)
    op.create_index('ix_qr_payment_requests_user_id', 'qr_payment_requests', ['user_id'])

    op.create_table(
        'qr_transfers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('reference', sa.String(24), nullable=False),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=False, unique=True),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('receiver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('payment_request_id', sa.Integer(), sa.ForeignKey('qr_payment_requests.id'), nullable=True, unique=True),
        sa.Column('idempotency_key', sa.String(64), nullable=False),
        sa.Column('request_fingerprint', sa.String(64), nullable=False),
        sa.Column('narration', sa.String(140), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('sender_id', 'idempotency_key', name='uq_qr_transfer_idempotency'),
    )
    op.create_index('ix_qr_transfers_id', 'qr_transfers', ['id'])
    op.create_index('ix_qr_transfers_reference', 'qr_transfers', ['reference'], unique=True)
    op.create_index('ix_qr_transfers_sender_id', 'qr_transfers', ['sender_id'])
    op.create_index('ix_qr_transfers_receiver_id', 'qr_transfers', ['receiver_id'])
    op.create_index('ix_qr_transfers_created_at', 'qr_transfers', ['created_at'])

    op.create_table(
        'webauthn_credentials',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('credential_id', sa.String(512), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('algorithm', sa.Integer(), nullable=False),
        sa.Column('sign_count', sa.Integer(), nullable=False),
        sa.Column('rp_id', sa.String(255), nullable=False),
        sa.Column('label', sa.String(60), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_webauthn_credentials_id', 'webauthn_credentials', ['id'])
    op.create_index('ix_webauthn_credentials_user_id', 'webauthn_credentials', ['user_id'])
    op.create_index('ix_webauthn_credentials_credential_id', 'webauthn_credentials', ['credential_id'], unique=True)


def downgrade() -> None:
    op.drop_table('webauthn_credentials')
    op.drop_table('qr_transfers')
    op.drop_table('qr_payment_requests')
    op.drop_column('users', 'is_active')
