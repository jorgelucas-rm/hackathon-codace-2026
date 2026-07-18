"""add user avatar

Revision ID: 12f41c645904
Revises: 02d2598303f7
Create Date: 2026-07-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '12f41c645904'
down_revision: Union[str, None] = '02d2598303f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column(
            'avatar',
            sa.String(length=500),
            server_default=sa.text("'avatar/default.png'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('user', 'avatar')
