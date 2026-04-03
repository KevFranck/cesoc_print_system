from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BonusPageGrantCreate(BaseModel):
    """Payload reçu quand un agent ajoute un bonus de pages à un usager."""

    pages: int = Field(ge=1, le=500)
    reason: str = Field(min_length=3, max_length=255)
    granted_by: str = Field(default="Personnel CESOC", max_length=120)
    expires_on: date | None = None


class BonusPageGrantRead(BaseModel):
    """Lecture normalisée d'un bonus de pages déjà enregistré."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    pages: int
    reason: str
    granted_by: str
    effective_date: date
    expires_on: date | None
    created_at: datetime
