# services/api/app/schemas/incident.py

"""
Pydantic v2 schemas for incident CRUD operations.
Channels, categories, priorities and types align with CONTEXT.md definitions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Validators ───────────────────────────────────────────────────────────────

CHANNELS = {"email", "whatsapp", "phone", "portal_interno", "sistema", "portal_cliente"}
CATEGORIES = {"almacen", "ultima_milla", "logistica_inversa", "cx", "tecnologia", "comercial"}
PRIORITIES = {"critica", "alta", "normal", "baja"}
INCIDENT_TYPES = {"queja", "incidencia", "solicitud", "alerta"}
STATUSES = {"reported", "triaging", "assigned", "in_progress", "resolved", "verified", "closed", "reopened", "cancelled"}


# ── Create ───────────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    """Schema for creating a new incident."""

    title: str = Field(..., min_length=3, max_length=200, description="Título corto descriptivo")
    description: str = Field(..., min_length=10, description="Descripción detallada de la incidencia")

    # Canal de entrada (RF-01)
    channel: str = Field(..., description="Canal por el que entra la incidencia")
    channel_ref: Optional[str] = Field(None, max_length=100)

    # Clasificación (RF-02)
    category: str = Field(..., description="Categoría según departamento de TrackFlow")
    priority: str = Field("normal", description="Nivel de severidad/urgencia")
    incident_type: str = Field("incidencia", description="Tipo de incidencia")

    # Asignación inicial (opcional)
    assigned_area: Optional[str] = Field(None)
    assigned_to: Optional[str] = Field(None, max_length=100)

    # Enlace a entidad del dominio
    related_entity_type: Optional[str] = Field(None, max_length=30)
    related_entity_id: Optional[str] = Field(None, max_length=100)

    # Quién crea
    created_by: str = Field(..., min_length=1, max_length=100, description="Email o ID del usuario que reporta")

    # ── Validaciones ─────────────────────────────────────────────────────

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in CHANNELS:
            raise ValueError(
                f"Canal '{v}' no válido. Opciones: {', '.join(sorted(CHANNELS))}"
            )
        return v_lower

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in CATEGORIES:
            raise ValueError(
                f"Categoría '{v}' no válida. Opciones: {', '.join(sorted(CATEGORIES))}"
            )
        return v_lower

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in PRIORITIES:
            raise ValueError(
                f"Prioridad '{v}' no válida. Opciones: {', '.join(sorted(PRIORITIES))}"
            )
        return v_lower

    @field_validator("incident_type")
    @classmethod
    def validate_incident_type(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in INCIDENT_TYPES:
            raise ValueError(
                f"Tipo '{v}' no válido. Opciones: {', '.join(sorted(INCIDENT_TYPES))}"
            )
        return v_lower


# ── Update ───────────────────────────────────────────────────────────────────

class IncidentUpdate(BaseModel):
    """Schema for updating an incident. All fields optional — only changed fields are sent."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)

    # Clasificación
    category: Optional[str] = Field(None)
    priority: Optional[str] = Field(None)
    incident_type: Optional[str] = Field(None)

    # Asignación
    assigned_area: Optional[str] = Field(None)
    assigned_to: Optional[str] = Field(None, max_length=100)

    # Estado
    status: Optional[str] = Field(None)

    # Enlace a entidad
    related_entity_type: Optional[str] = Field(None, max_length=30)
    related_entity_id: Optional[str] = Field(None, max_length=100)

    # Resolución
    resolution: Optional[str] = Field(None)
    resolved_by: Optional[str] = Field(None, max_length=100)

    # Quién hace el cambio (obligatorio para auditoría)
    changed_by: str = Field(..., min_length=1, max_length=100, description="Email o ID del usuario que realiza el cambio")
    reason: Optional[str] = Field(None, description="Motivo del cambio (obligatorio para ciertas transiciones)")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        if v_lower not in CATEGORIES:
            raise ValueError(
                f"Categoría '{v}' no válida. Opciones: {', '.join(sorted(CATEGORIES))}"
            )
        return v_lower

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        if v_lower not in PRIORITIES:
            raise ValueError(
                f"Prioridad '{v}' no válida. Opciones: {', '.join(sorted(PRIORITIES))}"
            )
        return v_lower

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        if v_lower not in STATUSES:
            raise ValueError(
                f"Estado '{v}' no válido. Opciones: {', '.join(sorted(STATUSES))}"
            )
        return v_lower


# ── Response ─────────────────────────────────────────────────────────────────

class IncidentResponse(BaseModel):
    """Schema returned by the API when reading an incident."""

    id: UUID
    title: str
    description: str
    channel: str
    channel_ref: Optional[str] = None
    category: str
    priority: str
    incident_type: str
    assigned_area: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    status: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    created_at: datetime
    created_by: str
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── List params ──────────────────────────────────────────────────────────────

class IncidentListParams(BaseModel):
    """Query parameters for listing incidents with filters."""

    status: Optional[str] = Field(None, description="Filtrar por estado")
    category: Optional[str] = Field(None, description="Filtrar por categoría")
    priority: Optional[str] = Field(None, description="Filtrar por prioridad")
    assigned_to: Optional[str] = Field(None, description="Filtrar por responsable")
    assigned_area: Optional[str] = Field(None, description="Filtrar por área asignada")
    channel: Optional[str] = Field(None, description="Filtrar por canal de entrada")
    created_by: Optional[str] = Field(None, description="Filtrar por creador")
    q: Optional[str] = Field(None, description="Búsqueda textual en título/descripción")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# ── Stats ────────────────────────────────────────────────────────────────────

class IncidentStats(BaseModel):
    """Statistics and KPIs for incidents."""

    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_priority: dict[str, int]