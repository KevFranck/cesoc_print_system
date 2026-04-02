from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    administrative_note: str | None = Field(default=None, max_length=255)


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    administrative_note: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClientListItem(ClientRead):
    full_name: str
    active_session_count: int = 0
    used_pages_today: int = 0
    remaining_pages: int = 0


class RemainingPagesRead(BaseModel):
    client_id: int
    daily_quota: int
    used_pages_today: int
    remaining_pages: int
