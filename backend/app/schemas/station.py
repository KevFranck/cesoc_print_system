from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StationCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    status: str = Field(default="available", max_length=30)
    secret: str | None = Field(default=None, max_length=120)


class StationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str | None
    status: str
    secret: str | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime
    active_session_id: int | None = None
    active_client_id: int | None = None
    active_client_name: str | None = None
