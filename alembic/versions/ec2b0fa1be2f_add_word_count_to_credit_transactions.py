"""Add word_count to credit_transactions

Revision ID: ec2b0fa1be2f
Revises: 6b7b2f7ef805
Create Date: 2026-05-16 12:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ec2b0fa1be2f'
down_revision: str | None = '6b7b2f7ef805'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'credit_transactions',
        sa.Column('word_count', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('credit_transactions', 'word_count')
