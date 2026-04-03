from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.imported_document import ImportedDocument
from app.repositories.client_repository import ClientRepository
from app.repositories.imported_document_repository import ImportedDocumentRepository
from app.repositories.station_repository import StationRepository
from app.schemas.document import DocumentPrintRequest, ImportedDocumentCreate, ImportedDocumentRead
from app.schemas.print_job import PrintJobRead
from app.services.print_job_service import PrintJobService


class DocumentService:
    """Gère l'enregistrement et la lecture des documents importés sur la borne."""

    def __init__(self, db: Session) -> None:
        self.client_repository = ClientRepository(db)
        self.document_repository = ImportedDocumentRepository(db)
        self.station_repository = StationRepository(db)
        self.print_job_service = PrintJobService(db)

    def register_document(self, payload: ImportedDocumentCreate) -> ImportedDocumentRead:
        if not Path(payload.local_path).suffix.lower() == ".pdf":
            raise ValidationError("Seuls les documents PDF sont acceptes dans ce MVP.")
        if payload.owner_client_id:
            user = self.client_repository.get_by_id(payload.owner_client_id)
            if not user:
                raise NotFoundError("Utilisateur introuvable.")
        document = ImportedDocument(**payload.model_dump(), status="available")
        created = self.document_repository.create(document)
        return self._to_read(created)

    def list_email_documents(self, user_id: int) -> list[ImportedDocumentRead]:
        client = self.client_repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        return [self._to_read(document) for document in self.document_repository.list_for_user(user_id, "email")]

    def list_user_documents(self, user_id: int) -> list[ImportedDocumentRead]:
        client = self.client_repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        return [self._to_read(document) for document in self.document_repository.list_for_user(user_id)]

    def print_document(self, document_id: int, payload: DocumentPrintRequest) -> PrintJobRead:
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document introuvable.")
        if document.owner_client_id is None:
            raise ValidationError("Le document n'est pas associe a un utilisateur.")
        if document.status not in {"available", "failed"}:
            raise ValidationError("Ce document n'est plus disponible pour impression.")
        normalized_selection, selected_page_count = self._resolve_selected_pages(document.page_count, payload.selected_pages)
        if payload.selected_page_count and payload.selected_page_count != selected_page_count:
            raise ValidationError("Le nombre de pages selectionnees ne correspond pas a la plage demandee.")
        job = self.print_job_service.create_print_job_from_document(
            document,
            payload.station_code,
            payload.printer_name,
            payload.administrative_context,
            selected_page_count=selected_page_count,
            selected_pages=normalized_selection,
        )
        document.status = "reserved"
        document.processed_at = datetime.now(timezone.utc)
        self.document_repository.update(document)
        return job

    def mark_print_result(self, document_id: int, status: str) -> ImportedDocumentRead:
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document introuvable.")
        document.status = "printed" if status == "printed" else "failed"
        document.processed_at = datetime.now(timezone.utc)
        updated = self.document_repository.update(document)
        return self._to_read(updated)

    def _to_read(self, document: ImportedDocument) -> ImportedDocumentRead:
        data = ImportedDocumentRead.model_validate(document).model_dump()
        data["owner_name"] = f"{document.owner.first_name} {document.owner.last_name}" if document.owner else None
        return ImportedDocumentRead.model_validate(data)

    def _resolve_selected_pages(self, total_pages: int, raw_selection: str | None) -> tuple[str | None, int]:
        if not raw_selection or not raw_selection.strip():
            return None, total_pages

        selected_pages: set[int] = set()
        parts = [part.strip() for part in raw_selection.split(",") if part.strip()]
        if not parts:
            raise ValidationError("La selection de pages est invalide.")

        for part in parts:
            if "-" in part:
                start_raw, end_raw = [item.strip() for item in part.split("-", 1)]
                if not start_raw.isdigit() or not end_raw.isdigit():
                    raise ValidationError("La selection de pages contient une plage invalide.")
                start, end = int(start_raw), int(end_raw)
                if start < 1 or end < start or end > total_pages:
                    raise ValidationError("La selection de pages depasse le nombre de pages du document.")
                selected_pages.update(range(start, end + 1))
            else:
                if not part.isdigit():
                    raise ValidationError("La selection de pages contient une valeur invalide.")
                page_number = int(part)
                if page_number < 1 or page_number > total_pages:
                    raise ValidationError("La selection de pages depasse le nombre de pages du document.")
                selected_pages.add(page_number)

        normalized = ",".join(str(page_number) for page_number in sorted(selected_pages))
        return normalized, len(selected_pages)
