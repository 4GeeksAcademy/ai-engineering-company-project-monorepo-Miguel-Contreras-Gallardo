# services/api/app/schemas/audit.py

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Schema returned by the audit trail endpoint."""

    id: UUID
    incident_id: UUID
    changed_by: str
    changed_at: datetime
    field_name: str
    old_value: str | None = None
    new_value: str
    reason: str | None = None
    change_type: str

    model_config = {"from_attributes": True}