"""Create stock_movements audit table.

Revision ID: 0003_create_stock_movements
Revises: 0002_add_stock_quantity
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_create_stock_movements"
down_revision: Union[str, Sequence[str], None] = "0002_add_stock_quantity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stock_movements_order_id",
        "stock_movements",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_movements_product_id",
        "stock_movements",
        ["product_id"],
        unique=False,
    )

    # Existing products predate stock movement auditing. Preserve their
    # current stock as an explicit opening balance so the history has a
    # well-defined starting point without trying to reconstruct the past.
    op.execute(
        """
        INSERT INTO stock_movements (
            product_id,
            movement_type,
            quantity_change,
            balance_after,
            note
        )
        SELECT
            id,
            'opening_balance',
            stock_quantity,
            stock_quantity,
            'Opening balance at stock movement migration'
        FROM products
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stock_movements_product_id",
        table_name="stock_movements",
    )
    op.drop_index(
        "ix_stock_movements_order_id",
        table_name="stock_movements",
    )
    op.drop_table("stock_movements")
