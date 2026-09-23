# services/api/app/services/incident_service.py

"""
Incident service — core business logic.

Every mutation (create, update, transition) logs an entry in the audit trail.
State transitions are validated against a strict state machine (RF-04 + RF-05).
"""

from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.audit_service import AuditService


# ── State machine (RF-04) ────────────────────────────────────────────────────

# Valid transitions: source → {targets}
VALID_TRANSITIONS: dict[str, set[str]] = {
    "reported": {"triaging", "cancelled"},
    "triaging": {"assigned", "cancelled", "reported"},
    "assigned": {"in_progress", "triaging", "cancelled"},
    "in_progress": {"resolved", "assigned", "cancelled"},
    "resolved": {"verified", "reopened", "cancelled"},
    "verified": {"closed", "reopened"},
    "closed": {"reopened"},
    "reopened": {"triaging", "assigned", "in_progress", "cancelled"},
    "cancelled": set(),  # Terminal state — no transitions out
}

# Transitions that require a reason/motivo
TRANSITIONS_REQUIRING_REASON: set[tuple[str, str]] = {
    ("in_progress", "cancelled"),
    ("resolved", "reopened"),
    ("closed", "reopened"),
    ("assigned", "cancelled"),
}


class IncidentService:
    """Handles all incident business logic with audit trail."""

    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ── Create ───────────────────────────────────────────────────────────

    def create_incident(self, data: IncidentCreate) -> Incident:
        """Create a new incident and log the creation in the audit trail."""
        incident = Incident(
            id=uuid4(),
            title=data.title,
            description=data.description,
            channel=data.channel,
            channel_ref=data.channel_ref,
            category=data.category,
            priority=data.priority,
            incident_type=data.incident_type,
            assigned_area=data.assigned_area,
            assigned_to=data.assigned_to,
            status="reported",
            related_entity_type=data.related_entity_type,
            related_entity_id=data.related_entity_id,
            created_by=data.created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(incident)
        self.db.flush()  # Get the ID without committing

        # Log creation in audit trail
        self.audit.log_create(incident_id=incident.id, created_by=data.created_by)

        # If initially assigned, log the assignment
        if data.assigned_to:
            self.audit.log_change(
                incident_id=incident.id,
                changed_by=data.created_by,
                field_name="assigned_to",
                old_value=None,
                new_value=data.assigned_to,
                reason="Asignación inicial",
                change_type="update",
            )

        self.db.commit()
        self.db.refresh(incident)
        return incident

    # ── Get ──────────────────────────────────────────────────────────────

    def get_incident(self, incident_id: UUID) -> Incident | None:
        """Get a single incident by ID."""
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    # ── List ─────────────────────────────────────────────────────────────

    def list_incidents(
        self,
        status: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
        assigned_area: str | None = None,
        channel: str | None = None,
        created_by: str | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Incident], int]:
        """
        List incidents with filters and text search.
        Returns (incidents, total_count).
        """
        query = self.db.query(Incident)

        if status:
            query = query.filter(Incident.status == status)
        if category:
            query = query.filter(Incident.category == category)
        if priority:
            query = query.filter(Incident.priority == priority)
        if assigned_to:
            query = query.filter(Incident.assigned_to == assigned_to)
        if assigned_area:
            query = query.filter(Incident.assigned_area == assigned_area)
        if channel:
            query = query.filter(Incident.channel == channel)
        if created_by:
            query = query.filter(Incident.created_by == created_by)
        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    Incident.title.ilike(search),
                    Incident.description.ilike(search),
                )
            )

        total = query.count()
        incidents = (
            query.order_by(Incident.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return incidents, total

    # ── Update ───────────────────────────────────────────────────────────

    def update_incident(self, incident_id: UUID, data: IncidentUpdate) -> Incident | None:
        """
        Update an incident and log every changed field in the audit trail.

        This is the heart of the traceability system (RF-05).
        """
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        changes: list[dict] = []
        update_data = data.model_dump(exclude_unset=True, exclude={"changed_by", "reason"})

        # Build list of changes before applying them
        for field, new_value in update_data.items():
            if new_value is None:
                continue
            current_value = getattr(incident, field, None)

            # Normalize for comparison
            str_current = str(current_value) if current_value is not None else None
            str_new = str(new_value)

            if str_current == str_new:
                continue  # No actual change

            # Validate state transition if changing status
            if field == "status":
                if not self._is_valid_transition(incident.status, new_value):
                    raise ValueError(
                        f"Transición de estado no válida: {incident.status} → {new_value}. "
                        f"Transiciones válidas desde '{incident.status}': "
                        f"{', '.join(sorted(VALID_TRANSITIONS.get(incident.status, set())))}"
                    )

            old_value = str(current_value) if current_value is not None else None

            # Determine change_type for status transitions
            change_type = "update"
            if field == "status":
                change_type = self._classify_status_change(
                    incident.status, new_value
                )

            changes.append({
                "field_name": field,
                "old_value": old_value,
                "new_value": str_new,
                "change_type": change_type,
                "reason": data.reason,
            })

            # Apply the change to the model
            setattr(incident, field, new_value)

        # Special handling for resolution fields
        if hasattr(data, "resolution") and data.resolution:
            incident.resolved_at = datetime.now(timezone.utc)
            incident.resolved_by = data.resolved_by

        # Update the timestamp
        incident.updated_at = datetime.now(timezone.utc)

        # Persist all audit log entries
        for change in changes:
            self.audit.log_change(
                incident_id=incident.id,
                changed_by=data.changed_by,
                field_name=change["field_name"],
                old_value=change["old_value"],
                new_value=change["new_value"],
                reason=change["reason"],
                change_type=change["change_type"],
            )

        self.db.commit()
        self.db.refresh(incident)
        return incident

    # ── Stats ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get aggregate statistics for all incidents."""
        total = self.db.query(Incident).count()

        from sqlalchemy import func

        by_status_rows = (
            self.db.query(Incident.status, func.count(Incident.id))
            .group_by(Incident.status)
            .all()
        )
        by_category_rows = (
            self.db.query(Incident.category, func.count(Incident.id))
            .group_by(Incident.category)
            .all()
        )
        by_priority_rows = (
            self.db.query(Incident.priority, func.count(Incident.id))
            .group_by(Incident.priority)
            .all()
        )

        return {
            "total": total,
            "by_status": {row[0]: row[1] for row in by_status_rows},
            "by_category": {row[0]: row[1] for row in by_category_rows},
            "by_priority": {row[0]: row[1] for row in by_priority_rows},
        }

    # ── Assign to area (RF-03) ───────────────────────────────────────────

    def assign_incident(
        self,
        incident_id: UUID,
        assigned_area: str,
        assigned_by: str,
        assigned_to: str | None = None,
        reason: str | None = None,
    ) -> Incident:
        """
        Assign an incident to an area and optionally to a person.

        Automatically transitions the incident:
        - reported → triaging → assigned
        - triaging → assigned
        - assigned → (reassign, same area or new)
        """
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incidencia {incident_id} no encontrada")

        old_status = incident.status

        # ── Guard: can only assign from active states ────────────────────
        assignable_from = {"reported", "triaging", "assigned", "in_progress", "reopened"}
        if old_status not in assignable_from:
            raise ValueError(
                f"No se puede asignar una incidencia en estado '{old_status}'. "
                f"Solo se puede asignar desde: {', '.join(sorted(assignable_from))}"
            )

        # ── Record old values for audit ──────────────────────────────────
        old_area = str(incident.assigned_area) if incident.assigned_area else None
        old_assignee = str(incident.assigned_to) if incident.assigned_to else None

        # ── Apply assignment ─────────────────────────────────────────────
        incident.assigned_area = assigned_area
        incident.assigned_to = assigned_to
        incident.assigned_by = assigned_by
        incident.updated_at = datetime.now(timezone.utc)

        # ── Auto-transition: reported → triaging → assigned ──────────────
        if old_status == "reported":
            incident.status = "triaging"
            self.audit.log_change(
                incident_id=incident.id,
                changed_by=assigned_by,
                field_name="status",
                old_value=old_status,
                new_value="triaging",
                reason=f"Inicio de triaje para asignación a {assigned_area}",
                change_type="update",
            )

        incident.status = "assigned"

        # ── Log assignment in audit ──────────────────────────────────────
        if old_area != assigned_area:
            self.audit.log_change(
                incident_id=incident.id,
                changed_by=assigned_by,
                field_name="assigned_area",
                old_value=old_area,
                new_value=assigned_area,
                reason=reason or f"Asignación a área {assigned_area}",
                change_type="assignment",
            )

        if old_assignee != assigned_to:
            self.audit.log_change(
                incident_id=incident.id,
                changed_by=assigned_by,
                field_name="assigned_to",
                old_value=old_assignee,
                new_value=assigned_to,
                reason=reason or f"Asignación a responsable {assigned_to}" if assigned_to else "Sin responsable asignado",
                change_type="assignment",
            )

        self.audit.log_change(
            incident_id=incident.id,
            changed_by=assigned_by,
            field_name="assigned_by",
            old_value=None,
            new_value=assigned_by,
            reason=reason or f"Asignación realizada por {assigned_by}",
            change_type="update",
        )

        self.audit.log_change(
            incident_id=incident.id,
            changed_by=assigned_by,
            field_name="status",
            old_value="triaging" if old_status == "reported" else old_status,
            new_value="assigned",
            reason=reason or f"Incidencia asignada a {assigned_area}",
            change_type="update",
        )

        self.db.commit()
        self.db.refresh(incident)
        return incident

    # ── Transition status (RF-04) ────────────────────────────────────────

    def transition_status(
        self,
        incident_id: UUID,
        new_status: str,
        changed_by: str,
        reason: str | None = None,
        resolution: str | None = None,
        resolved_by: str | None = None,
    ) -> Incident:
        """
        Perform an explicit status transition on an incident.

        Validates the transition against the state machine.
        Special handling for:
        - resolved: sets resolved_at / resolved_by
        - reopened: clears resolution data
        - closed: finalises
        - cancelled: requires reason
        """
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incidencia {incident_id} no encontrada")

        old_status = incident.status

        # ── Validate transition ──────────────────────────────────────────
        if not self._is_valid_transition(old_status, new_status):
            raise ValueError(
                f"Transición no válida: {old_status} → {new_status}. "
                f"Desde '{old_status}' solo puedes ir a: "
                f"{', '.join(sorted(VALID_TRANSITIONS.get(old_status, set())))}"
            )

        # ── Require reason for certain transitions ───────────────────────
        if (old_status, new_status) in TRANSITIONS_REQUIRING_REASON and not reason:
            raise ValueError(
                f"La transición {old_status} → {new_status} requiere un motivo (reason)."
            )

        # ── Side effects per transition ──────────────────────────────────
        if new_status == "resolved":
            if not resolution:
                raise ValueError("Para pasar a 'resolved' debes proporcionar una resolución (resolution).")
            incident.resolution = resolution
            incident.resolved_at = datetime.now(timezone.utc)
            incident.resolved_by = resolved_by or changed_by

        elif new_status == "reopened":
            # Clear resolution data to signal it's active again
            incident.resolution = None
            incident.resolved_at = None
            incident.resolved_by = None

        elif new_status == "cancelled":
            # Keep the resolution as the cancellation note
            if resolution:
                incident.resolution = resolution

        # ── Apply the transition ─────────────────────────────────────────
        incident.status = new_status
        incident.updated_at = datetime.now(timezone.utc)

        # ── Classify and log ─────────────────────────────────────────────
        change_type = self._classify_status_change(old_status, new_status)
        self.audit.log_change(
            incident_id=incident.id,
            changed_by=changed_by,
            field_name="status",
            old_value=old_status,
            new_value=new_status,
            reason=reason or f"Transición de {old_status} → {new_status}",
            change_type=change_type,
        )

        self.db.commit()
        self.db.refresh(incident)
        return incident

    # ── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _is_valid_transition(current_status: str, new_status: str) -> bool:
        """Check if a state transition is allowed by the state machine."""
        allowed = VALID_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    @staticmethod
    def _classify_status_change(old_status: str, new_status: str) -> str:
        """Classify the type of status change for audit purposes."""
        classification_map = {
            ("in_progress", "resolved"): "resolve",
            ("verified", "closed"): "resolve",
            ("assigned", "in_progress"): "update",
            ("resolved", "reopened"): "reopen",
            ("reported", "triaging"): "update",
            ("triaging", "assigned"): "update",
        }
        direct = set()

        # Escalate if priority increased
        priority_levels = {"baja": 0, "normal": 1, "alta": 2, "critica": 3}

        return classification_map.get((old_status, new_status), "update")