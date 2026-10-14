# services/api/app/services/audit_service.py

"""
Audit service — the core traceability component.

Every change to an incident MUST go through this service to ensure
the audit trail is complete and immutable (RF-05).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import IncidentAuditLog


class AuditService:
    """Handles all audit log operations."""

    def __init__(self, db: Session):
        self.db = db

    def log_change(
        self,
        incident_id: UUID,
        changed_by: str,
        field_name: str,
        old_value: str | None,
        new_value: str,
        reason: str | None = None,
        change_type: str = "update",
    ) -> IncidentAuditLog:
        """
        Register a change in the audit trail.

        Args:
            incident_id: The incident being modified.
            changed_by: Who made the change (email or user ID).
            field_name: What field changed (e.g. 'status', 'assigned_to', 'priority').
            old_value: The previous value (None if creating).
            new_value: The new value.
            reason: Why the change was made.
            change_type: Type of change (create | update | reassign | escalate | resolve | reopen).

        Returns:
            The created IncidentAuditLog record.
        """
        log_entry = IncidentAuditLog(
            incident_id=incident_id,
            changed_by=changed_by,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            change_type=change_type,
        )
        self.db.add(log_entry)
        return log_entry

    def get_audit_trail(
        self,
        incident_id: UUID,
    ) -> list[IncidentAuditLog]:
        """Return the full audit trail for an incident, ordered chronologically."""
        return (
            self.db.query(IncidentAuditLog)
            .filter(IncidentAuditLog.incident_id == incident_id)
            .order_by(IncidentAuditLog.changed_at.asc())
            .all()
        )

    def log_create(self, incident_id: UUID, created_by: str) -> IncidentAuditLog:
        """Log the creation of an incident."""
        return self.log_change(
            incident_id=incident_id,
            changed_by=created_by,
            field_name="status",
            old_value=None,
            new_value="reported",
            reason="Incidencia creada",
            change_type="create",
        )