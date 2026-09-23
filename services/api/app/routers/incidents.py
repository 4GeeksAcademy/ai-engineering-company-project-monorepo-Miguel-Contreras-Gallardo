# services/api/app/routers/incidents.py

"""
Incident CRUD endpoints (RF-01 through RF-06).

Base path: /api/v1/incidents

Every mutation is logged in the audit trail (RF-05).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentStats,
    IncidentAssign,
    IncidentTransition,
)
from app.schemas.audit import AuditLogResponse
from app.services.incident_service import IncidentService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


# ── POST: Create incident ────────────────────────────────────────────────────

@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva incidencia (RF-01)",
    description="Crea una incidencia desde cualquier canal. Queda registrada en estado 'reported' "
                "con trazabilidad en el audit log.",
)
def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    incident = service.create_incident(data)
    return incident


# ── GET: List incidents ──────────────────────────────────────────────────────

@router.get(
    "",
    response_model=dict,
    summary="Listar incidencias (RF-06)",
    description="Lista incidencias con filtros por estado, categoría, prioridad, responsable, "
                "área, canal y búsqueda textual.",
)
def list_incidents(
    status: str | None = Query(None, description="Filtrar por estado"),
    category: str | None = Query(None, description="Filtrar por categoría"),
    priority: str | None = Query(None, description="Filtrar por prioridad"),
    assigned_to: str | None = Query(None, description="Filtrar por responsable"),
    assigned_area: str | None = Query(None, description="Filtrar por área asignada"),
    channel: str | None = Query(None, description="Filtrar por canal de entrada"),
    created_by: str | None = Query(None, description="Filtrar por creador"),
    q: str | None = Query(None, description="Búsqueda textual en título/descripción"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    incidents, total = service.list_incidents(
        status=status,
        category=category,
        priority=priority,
        assigned_to=assigned_to,
        assigned_area=assigned_area,
        channel=channel,
        created_by=created_by,
        q=q,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [IncidentResponse.model_validate(i) for i in incidents],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── GET: Stats ───────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=IncidentStats,
    summary="Estadísticas de incidencias",
    description="Agregación de incidencias por estado, categoría y prioridad.",
)
def get_stats(
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    return service.get_stats()


# ── GET: Get incident by ID ──────────────────────────────────────────────────

@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Obtener detalle de incidencia (RF-06)",
    description="Devuelve todos los campos de una incidencia por su ID.",
)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    incident = service.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incident_id} no encontrada",
        )
    return incident


# ── PATCH: Update incident ───────────────────────────────────────────────────

@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Actualizar incidencia (RF-04 + RF-05)",
    description="Actualiza una incidencia. Cada cambio se registra en el audit log con "
                "quién, qué, cuándo y por qué. Las transiciones de estado están validadas.",
)
def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    try:
        incident = service.update_incident(incident_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incident_id} no encontrada",
        )
    return incident


# ── GET: Audit trail ─────────────────────────────────────────────────────────

@router.get(
    "/{incident_id}/audit",
    response_model=list[AuditLogResponse],
    summary="Historial de auditoría (RF-05 ⭐)",
    description="Devuelve el registro cronológico completo de todos los cambios realizados "
                "sobre una incidencia: quién, qué, cuándo y por qué.",
)
def get_audit_trail(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    audit_service = AuditService(db)
    # Verify incident exists
    incident_service = IncidentService(db)
    incident = incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incident_id} no encontrada",
        )
    return audit_service.get_audit_trail(incident_id)


# ── POST: Assign incident to area (RF-03) ──────────────────────────────────

@router.post(
    "/{incident_id}/assign",
    response_model=IncidentResponse,
    summary="Asignar incidencia a área responsable (RF-03)",
    description="Asigna una incidencia a un área y opcionalmente a una persona. "
                "Auto-transiciona: reported → triaging → assigned. "
                "Cada cambio queda registrado en el audit log.",
)
def assign_incident(
    incident_id: UUID,
    data: IncidentAssign,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    try:
        incident = service.assign_incident(
            incident_id=incident_id,
            assigned_area=data.assigned_area,
            assigned_by=data.assigned_by,
            assigned_to=data.assigned_to,
            reason=data.reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incident_id} no encontrada",
        )
    return incident


# ── POST: Transition status (RF-04) ─────────────────────────────────────────

@router.post(
    "/{incident_id}/transition",
    response_model=IncidentResponse,
    summary="Transicionar estado de incidencia (RF-04)",
    description="Cambia el estado de una incidencia validando la transición contra la máquina de estados. "
                "Gestiona efectos secundarios: resolución (resolved), reapertura (reopened), cancelación (cancelled). "
                "Todo queda registrado en el audit log.",
)
def transition_status(
    incident_id: UUID,
    data: IncidentTransition,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    try:
        incident = service.transition_status(
            incident_id=incident_id,
            new_status=data.status,
            changed_by=data.changed_by,
            reason=data.reason,
            resolution=data.resolution,
            resolved_by=data.resolved_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incident_id} no encontrada",
        )
    return incident