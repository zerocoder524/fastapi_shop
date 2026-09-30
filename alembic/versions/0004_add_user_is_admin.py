"""Add is_admin flag to users.

Revision ID: 0004_add_user_is_admin
Revises: 0003_create_stock_movements
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_add_user_is_admin"
down_revision: Union[str, Sequence[str], None] = "0003_create_stock_movements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default=false makes the migration safe for existing rows:
    # every already registered user becomes a regular (non-admin) user.
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
