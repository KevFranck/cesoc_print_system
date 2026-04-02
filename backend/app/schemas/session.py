from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StationSessionCreate(BaseModel):
    station_code: str
    client_id: int
    purpose: str = Field(min_length=3, max_length=255)
    started_by: str | None = Field(default="Personnel CESOC", max_length=120)
    notes: str | None = Field(default=None, max_length=255)


class SessionEndRequest(BaseModel):
    session_id: int
    notes: str | None = Field(default=None, max_length=255)


class StationSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    client_id: int
    started_by: str | None
    purpose: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    notes: str | None
    client_name: str | None = None
    station_code: str | None = None
    station_name: str | None = None
