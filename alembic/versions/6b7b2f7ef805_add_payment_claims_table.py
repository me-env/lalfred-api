"""

Revision ID: 6b7b2f7ef805
Revises: 3733bee32b9e
Create Date: 2026-05-05 23:22:26.542810

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b7b2f7ef805'
down_revision: str | None = '3733bee32b9e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('payment_claims',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('claim_key', sa.String(length=64), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('buyer_email', sa.String(length=320), nullable=False),
    sa.Column('lemon_order_id', sa.String(length=255), nullable=True),
    sa.Column('lemon_invoice_id', sa.String(length=255), nullable=True), sa.Column('lemon_subscription_id', sa.String(length=255), nullable=True),
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
    op.add_column('credit_transactions', sa.Column('payment_claim_id', sa.UUID(), nullable=True))
    op.drop_constraint(op.f('credit_transactions_lemon_order_id_key'), 'credit_transactions', type_='unique')
    op.create_index(op.f('ix_credit_transactions_payment_claim_id'), 'credit_transactions', ['payment_claim_id'], unique=True)
    op.create_foreign_key(None, 'credit_transactions', 'payment_claims', ['payment_claim_id'], ['id'])
    op.drop_column('credit_transactions', 'lemon_order_id')
    op.add_column('subscription_payments', sa.Column('payment_claim_id', sa.UUID(), nullable=False))
    op.drop_index(op.f('ix_subscription_payments_lemon_invoice_id'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_lemon_subscription_id'), table_name='subscription_payments')
    op.create_index(op.f('ix_subscription_payments_payment_claim_id'), 'subscription_payments', ['payment_claim_id'], unique=True)
    op.create_foreign_key(None, 'subscription_payments', 'payment_claims', ['payment_claim_id'], ['id'])
    op.drop_column('subscription_payments', 'lemon_subscription_id')
    op.drop_column('subscription_payments', 'lemon_invoice_id')
