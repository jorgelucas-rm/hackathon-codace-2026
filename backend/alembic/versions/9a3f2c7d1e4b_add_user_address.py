"""add user address

Revision ID: 9a3f2c7d1e4b
Revises: 64d27fc2cb39
Create Date: 2026-07-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9a3f2c7d1e4b'
down_revision: Union[str, None] = '64d27fc2cb39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('street', sa.String(length=250), nullable=True))
    op.add_column('user', sa.Column('number', sa.String(length=20), nullable=True))
    op.add_column('user', sa.Column('zip_code', sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'zip_code')
    op.drop_column('user', 'number')
    op.drop_column('user', 'street')
