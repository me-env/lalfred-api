"""Drop payment and credit tables

The API no longer brokers payments or proxies inference: the app talks to
the providers directly with its own keys. Only Google sign-in (and, later,
cloud sync of keywords/snippets) lives here, so the whole credits/claims/
subscription ledger goes away.

Revision ID: 8f3c1d27a4b1
Revises: ec2b0fa1be2f
Create Date: 2026-09-20 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8f3c1d27a4b1'
down_revision: str | None = 'ec2b0fa1be2f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f('ix_credit_transactions_payment_claim_id'), table_name='credit_transactions')
    op.drop_index(op.f('ix_credit_transactions_user_id'), table_name='credit_transactions')
    op.drop_table('credit_transactions')

    op.drop_index(op.f('ix_subscription_payments_payment_claim_id'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_user_id'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_starts_at'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_ends_at'), table_name='subscription_payments')
    op.drop_table('subscription_payments')

    op.drop_index(op.f('ix_payment_claims_lemon_subscription_id'), table_name='payment_claims')
    op.drop_index(op.f('ix_payment_claims_claimed_by_user_id'), table_name='payment_claims')
    op.drop_index(op.f('ix_payment_claims_claim_key'), table_name='payment_claims')
    op.drop_index(op.f('ix_payment_claims_buyer_email'), table_name='payment_claims')
    op.drop_table('payment_claims')

    op.drop_column('users', 'credits')


def downgrade() -> None:
    """Recreate the schema as it stood at revision ec2b0fa1be2f (data is lost)."""
    op.add_column('users', sa.Column('credits', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('users', 'credits', server_default=None)

    op.create_table('payment_claims',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('claim_key', sa.String(length=64), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('buyer_email', sa.String(length=320), nullable=False),
    sa.Column('lemon_order_id', sa.String(length=255), nullable=True),
    sa.Column('lemon_invoice_id', sa.String(length=255), nullable=True),
    sa.Column('lemon_subscription_id', sa.String(length=255), nullable=True),
    sa.Column('credits_amount', sa.Integer(), nullable=True),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('claimed_by_user_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['claimed_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('lemon_invoice_id'),
    sa.UniqueConstraint('lemon_order_id')
    )
    op.create_index(op.f('ix_payment_claims_buyer_email'), 'payment_claims', ['buyer_email'], unique=False)
    op.create_index(op.f('ix_payment_claims_claim_key'), 'payment_claims', ['claim_key'], unique=True)
    op.create_index(op.f('ix_payment_claims_claimed_by_user_id'), 'payment_claims', ['claimed_by_user_id'], unique=False)
    op.create_index(op.f('ix_payment_claims_lemon_subscription_id'), 'payment_claims', ['lemon_subscription_id'], unique=False)

    op.create_table('subscription_payments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('payment_claim_id', sa.UUID(), nullable=False),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['payment_claim_id'], ['payment_claims.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_payments_ends_at'), 'subscription_payments', ['ends_at'], unique=False)
    op.create_index(op.f('ix_subscription_payments_starts_at'), 'subscription_payments', ['starts_at'], unique=False)
    op.create_index(op.f('ix_subscription_payments_user_id'), 'subscription_payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_subscription_payments_payment_claim_id'), 'subscription_payments', ['payment_claim_id'], unique=True)

    op.create_table('credit_transactions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('payment_claim_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('model', sa.String(length=50), nullable=True),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.Column('character_count', sa.Integer(), nullable=True),
    sa.Column('word_count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['payment_claim_id'], ['payment_claims.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_transactions_user_id'), 'credit_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_credit_transactions_payment_claim_id'), 'credit_transactions', ['payment_claim_id'], unique=True)
