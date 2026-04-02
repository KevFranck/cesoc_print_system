from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrintJobCreate(BaseModel):
    client_id: int
    station_code: str
    session_id: int | None = None
    document_name: str = Field(min_length=1, max_length=180)
    page_count: int = Field(ge=1, le=100)
    administrative_context: str = Field(min_length=3, max_length=255)


class PrintJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    station_id: int
    session_id: int | None
    document_name: str
    page_count: int
    status: str
    administrative_context: str
    submitted_at: datetime
    printed_at: datetime | None
    client_name: str | None = None
    station_code: str | None = None
    station_name: str | None = None
