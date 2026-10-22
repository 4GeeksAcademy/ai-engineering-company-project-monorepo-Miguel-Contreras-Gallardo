"""
Pydantic schemas for health-check endpoints.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schema for the main health-check endpoint."""

    status: str
    service: str
    version: str