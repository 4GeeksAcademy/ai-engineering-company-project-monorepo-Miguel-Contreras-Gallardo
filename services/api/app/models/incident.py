# services/api/app/models/incident.py

"""
SQLAlchemy model for incidents.
Maps directly to the `incidents` table defined in incident-manager-plan.md.

Channels, categories, priorities and types match the CONTEXT.md definitions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base

# ── Constants matching CONTEXT.md ────────────────────────────────────────────

CHANNELS = [
    "email",
    "whatsapp",
    "phone",
    "portal_interno",
    "sistema",          # Alertas automáticas del sistema
    "portal_cliente",   # Marcas B2B reportando directamente
]

CATEGORIES = [
    "almacen",
    "ultima_milla",
    "logistica_inversa",
    "cx",
    "tecnologia",
    "comercial",
]

PRIORITIES = [
    "critica",
    "alta",
    "normal",
    "baja",
]

INCIDENT_TYPES = [
    "queja",
    "incidencia",
    "solicitud",
    "alerta",
]

STATUSES = [
    "reported",
    "triaging",
    "assigned",
    "in_progress",
    "resolved",
    "verified",
    "closed",
    "reopened",
    "cancelled",
]

AREAS = [
    "almacen",
    "ultima_milla",
    "logistica_inversa",
    "cx",
    "tecnologia",
    "comercial",
]


class Incident(Base):
    """Representa una desviación operativa que requiere seguimiento y auditoría."""

    __tablename__ = "incidents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # ── Canal de entrada (RF-01) ─────────────────────────────────────────
    channel = Column(
        SAEnum(*CHANNELS, name="incident_channel"),
        nullable=False,
    )
    channel_ref = Column(String(100), nullable=True)

    # ── Clasificación (RF-02) ────────────────────────────────────────────
    category = Column(
        SAEnum(*CATEGORIES, name="incident_category"),
        nullable=False,
    )
    priority = Column(
        SAEnum(*PRIORITIES, name="incident_priority"),
        nullable=False,
        default="normal",
    )
    incident_type = Column(
        SAEnum(*INCIDENT_TYPES, name="incident_type"),
        nullable=False,
        default="incidencia",
    )

    # ── Asignación (RF-03) ──────────────────────────────────────────────
    assigned_area = Column(
        SAEnum(*AREAS, name="incident_assigned_area"),
        nullable=True,
    )
    assigned_to = Column(String(100), nullable=True)
    assigned_by = Column(String(100), nullable=True)

    # ── Estado (RF-04) ──────────────────────────────────────────────────
    status = Column(
        SAEnum(*STATUSES, name="incident_status"),
        nullable=False,
        default="reported",
    )

    # ── Enlaces a entidades del dominio TrackFlow ───────────────────────
    related_entity_type = Column(String(30), nullable=True)
    related_entity_id = Column(String(100), nullable=True)

    # ── Resolución ──────────────────────────────────────────────────────
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)

    # ── Metadatos ───────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(100), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def dict(self):
        """Return a plain dict representation (for audit logging)."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "channel": self.channel,
            "channel_ref": self.channel_ref,
            "category": self.category,
            "priority": self.priority,
            "incident_type": self.incident_type,
            "assigned_area": self.assigned_area,
            "assigned_to": self.assigned_to,
            "assigned_by": self.assigned_by,
            "status": self.status,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }