"""Create the telemetry event envelope table."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_telemetry_events"
down_revision: str | None = "0002_append_only_movements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telemetry_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_telemetry_events_event_type", "telemetry_events", ["event_type"]
    )
    op.create_index(
        "ix_telemetry_events_timestamp", "telemetry_events", ["timestamp"]
    )
    op.create_index(
        "ix_telemetry_events_session_id", "telemetry_events", ["session_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_telemetry_events_session_id", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_timestamp", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_event_type", table_name="telemetry_events")
    op.drop_table("telemetry_events")