"""Reject updates and deletes against confirmed movements."""

from collections.abc import Sequence

from alembic import op


revision: str = "0002_append_only_movements"
down_revision: str | None = "0001_inventory_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION prevent_movement_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'confirmed movements are immutable';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER movements_are_append_only
        BEFORE UPDATE OR DELETE ON movements
        FOR EACH ROW EXECUTE FUNCTION prevent_movement_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER movements_are_append_only ON movements")
    op.execute("DROP FUNCTION prevent_movement_mutation()")
