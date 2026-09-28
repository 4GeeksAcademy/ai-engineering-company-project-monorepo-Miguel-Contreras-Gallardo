"""Create the inventory catalog and append-only movement ledger."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_inventory_ledger"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("reorder_point", sa.Integer(), server_default="0", nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("sku"),
    )
    op.create_table(
        "warehouses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lots",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["sku"], ["articles.sku"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku", "code", name="uq_lot_sku_code"),
        sa.UniqueConstraint("sku", "id", name="uq_lot_sku_id"),
    )
    op.create_table(
        "movements",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("request_key", sa.String(), nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("warehouse_id", sa.String(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("adjustment_direction", sa.String(length=20), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type IN ('entrada', 'salida', 'ajuste')",
            name="ck_movement_type",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_movement_quantity_positive"),
        sa.CheckConstraint(
            "(type = 'ajuste' AND adjustment_direction IN ('aumentar', 'reducir')) "
            "OR (type <> 'ajuste' AND adjustment_direction IS NULL)",
            name="ck_movement_adjustment_direction",
        ),
        sa.ForeignKeyConstraint(
            ["sku", "lot_id"],
            ["lots.sku", "lots.id"],
            name="fk_movement_lot",
        ),
        sa.ForeignKeyConstraint(
            ["warehouse_id"],
            ["warehouses.id"],
            name="fk_movement_warehouse",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_key", name="uq_movement_request_key"),
        sa.UniqueConstraint("sequence", name="uq_movement_sequence"),
    )
    op.create_index(
        "ix_movements_lot_warehouse_sequence",
        "movements",
        ["lot_id", "warehouse_id", "sequence"],
    )
    op.bulk_insert(
        sa.table(
            "warehouses",
            sa.column("id", sa.String()),
            sa.column("name", sa.String()),
            sa.column("location", sa.String()),
        ),
        [
            {
                "id": "LAX",
                "name": "Los Angeles Warehouse",
                "location": "Los Angeles, USA",
            },
            {
                "id": "ZAZ",
                "name": "Zaragoza Warehouse",
                "location": "Zaragoza, Spain",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_movements_lot_warehouse_sequence", table_name="movements")
    op.drop_table("movements")
    op.drop_table("lots")
    op.drop_table("warehouses")
    op.drop_table("articles")