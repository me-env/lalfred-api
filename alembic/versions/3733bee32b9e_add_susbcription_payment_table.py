"""Add susbcription payment table

Revision ID: 3733bee32b9e
Revises: 191bf477e9d1
Create Date: 2026-05-03 18:44:11.384295

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3733bee32b9e'
down_revision: str | None = '191bf477e9d1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('subscription_payments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('lemon_subscription_id', sa.String(length=255), nullable=False),
    sa.Column('lemon_invoice_id', sa.String(length=255), nullable=False),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_payments_ends_at'), 'subscription_payments', ['ends_at'], unique=False)
    op.create_index(op.f('ix_subscription_payments_lemon_invoice_id'), 'subscription_payments', ['lemon_invoice_id'], unique=True)
    op.create_index(op.f('ix_subscription_payments_lemon_subscription_id'), 'subscription_payments', ['lemon_subscription_id'], unique=False)
    op.create_index(op.f('ix_subscription_payments_starts_at'), 'subscription_payments', ['starts_at'], unique=False)
    op.create_index(op.f('ix_subscription_payments_user_id'), 'subscription_payments', ['user_id'], unique=False)



def downgrade() -> None:
    op.drop_index(op.f('ix_subscription_payments_user_id'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_starts_at'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_lemon_subscription_id'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_lemon_invoice_id'), table_name='subscription_payments')
    op.drop_index(op.f('ix_subscription_payments_ends_at'), table_name='subscription_payments')
    op.drop_table('subscription_payments')

