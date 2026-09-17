"""Add stock_quantity to products.

Revision ID: 0002_add_stock_quantity
Revises: 0001_initial
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_stock_quantity"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default=0 makes the migration safe for existing rows:
    # the already existing products receive stock_quantity = 0.
    op.add_column(
        "products",
        sa.Column(
            "stock_quantity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("products", "stock_quantity")
