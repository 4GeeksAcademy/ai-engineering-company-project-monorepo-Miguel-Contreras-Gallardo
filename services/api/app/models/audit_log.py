# services/api/app/models/audit_log.py

"""
SQLAlchemy model for incident audit trail.
Every change to an incident MUST be logged here — this is the core traceability requirement.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class IncidentAuditLog(Base):
    """Registro inmutable de cada cambio en una incidencia (RF-05: Trazabilidad)."""

    __tablename__ = "incident_audit_log"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Quién y cuándo
    changed_by = Column(String(100), nullable=False)
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Qué cambió
    field_name = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)

    # Por qué
    reason = Column(Text, nullable=True)

    # Tipo de cambio
    change_type = Column(
        String(20),
        nullable=False,
        default="update",
    )