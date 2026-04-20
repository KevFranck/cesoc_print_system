from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.imported_document import ImportedDocument
from app.models.print_job import PrintJob
from app.repositories.client_repository import ClientRepository
from app.repositories.print_job_repository import PrintJobRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.station_repository import StationRepository
from app.schemas.document import PrintJobStatusUpdate
from app.schemas.print_job import PrintJobCreate, PrintJobRead
from app.services.quota_service import QuotaService


class PrintJobService:
    """Pilote la réservation quota et l'historisation des impressions."""

    def __init__(self, db: Session) -> None:
        self.client_repository = ClientRepository(db)
        self.station_repository = StationRepository(db)
        self.session_repository = SessionRepository(db)
        self.repository = PrintJobRepository(db)
        self.quota_service = QuotaService(db)

    def create_print_job(self, payload: PrintJobCreate) -> PrintJobRead:
        client = self.client_repository.get_by_id(payload.client_id)
        if not client:
            raise NotFoundError("Client introuvable.")

        station = self.station_repository.get_by_code(payload.station_code)
        if not station:
            raise NotFoundError("Poste introuvable.")

        active_session = self.session_repository.get_active_for_station(station.id)
        if not active_session:
            raise ValidationError("Aucune session active sur ce poste.")

        if active_session.client_id != payload.client_id:
            raise ValidationError("Le client ne correspond pas a la session active du poste.")

        if payload.session_id and payload.session_id != active_session.id:
            raise ValidationError("La session fournie ne correspond pas a la session active.")

        self.quota_service.ensure_pages_available(client, payload.page_count)

        job = PrintJob(
            client_id=payload.client_id,
            station_id=station.id,
            session_id=active_session.id,
            document_name=payload.document_name,
            page_count=payload.page_count,
            administrative_context=payload.administrative_context,
            status="queued",
        )
        created = self.repository.create(job)
        return self._to_read(created)

    def create_print_job_from_document(
        self,
        document: ImportedDocument,
        station_code: str,
        printer_name: str | None,
        administrative_context: str,
        selected_page_count: int | None = None,
        selected_pages: str | None = None,
        copy_count: int = 1,
    ) -> PrintJobRead:
        client = self.client_repository.get_by_id(document.owner_client_id or 0)
        if not client:
            raise NotFoundError("Utilisateur du document introuvable.")
        station = self.station_repository.get_by_code(station_code)
        if not station:
            raise NotFoundError("Poste introuvable.")
        active_session = self.session_repository.get_active_for_station(station.id)
        if not active_session or active_session.client_id != client.id:
            raise ValidationError("Le poste n'a pas de session active correspondant a cet utilisateur.")
        base_page_count = selected_page_count or document.page_count
        effective_page_count = base_page_count * copy_count
        self.quota_service.ensure_pages_available(client, effective_page_count)
        job = PrintJob(
            client_id=client.id,
            station_id=station.id,
            session_id=active_session.id,
            document_id=document.id,
            document_name=document.original_filename,
            page_count=effective_page_count,
            selected_pages=selected_pages,
            administrative_context=administrative_context,
            printer_name=printer_name,
            status="queued",
        )
        created = self.repository.create(job)
        return self._to_read(created)

    def list_jobs(self) -> list[PrintJobRead]:
        return [self._to_read(job) for job in self.repository.list_all()]

    def list_today_jobs(self) -> list[PrintJobRead]:
        return [self._to_read(job) for job in self.repository.list_today()]

    def list_jobs_for_user(self, user_id: int) -> list[PrintJobRead]:
        return [self._to_read(job) for job in self.repository.list_for_user(user_id)]

    def update_print_status(self, job_id: int, payload: PrintJobStatusUpdate) -> PrintJobRead:
        job = self.repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job introuvable.")
        job.status = payload.status
        job.failure_reason = payload.failure_reason
        if payload.status == "printed":
            from datetime import datetime, timezone

            job.printed_at = datetime.now(timezone.utc)
        updated = self.repository.update(job)
        return self._to_read(updated)

    def _to_read(self, job: PrintJob) -> PrintJobRead:
        data = PrintJobRead.model_validate(job).model_dump()
        data["client_name"] = f"{job.client.first_name} {job.client.last_name}" if job.client else None
        data["station_code"] = job.station.code if job.station else None
        data["station_name"] = job.station.name if job.station else None
        return PrintJobRead.model_validate(data)
