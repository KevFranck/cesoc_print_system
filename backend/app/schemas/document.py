from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportedDocumentCreate(BaseModel):
    """Déclare au backend un PDF importé localement sur la borne."""

    owner_client_id: int | None = None
    source_type: str = Field(pattern="^(usb|email)$")
    source_label: str | None = Field(default=None, max_length=180)
    sender_email: str | None = Field(default=None, max_length=150)
    original_filename: str = Field(min_length=1, max_length=255)
    local_path: str = Field(min_length=1, max_length=500)
    page_count: int = Field(ge=1, le=1000)


class ImportedDocumentRead(BaseModel):
    """Objet retourné à la borne pour afficher une liste de documents PDF."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_client_id: int | None
    source_type: str
    source_label: str | None
    sender_email: str | None
    original_filename: str
    local_path: str
    page_count: int
    status: str
    imported_at: datetime
    processed_at: datetime | None
    owner_name: str | None = None


class DocumentPrintRequest(BaseModel):
    """Demande d'impression déclenchée par la borne pour un document importé."""

    station_code: str
    printer_name: str | None = Field(default=None, max_length=180)
    administrative_context: str = Field(min_length=3, max_length=255)
    selected_pages: str | None = Field(default=None, max_length=120)
    selected_page_count: int | None = Field(default=None, ge=1, le=1000)


class PrintJobStatusUpdate(BaseModel):
    """Mise à jour du statut réel après tentative d'impression Windows."""

    status: str = Field(pattern="^(printed|failed)$")
    failure_reason: str | None = Field(default=None, max_length=255)
