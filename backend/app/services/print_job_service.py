from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.print_job import PrintJob
from app.repositories.client_repository import ClientRepository
from app.repositories.print_job_repository import PrintJobRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.station_repository import StationRepository
from app.schemas.print_job import PrintJobCreate, PrintJobRead


class PrintJobService:
    def __init__(self, db: Session) -> None:
        self.client_repository = ClientRepository(db)
        self.station_repository = StationRepository(db)
        self.session_repository = SessionRepository(db)
        self.repository = PrintJobRepository(db)

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

        used_pages = self.client_repository.get_printed_pages_today(payload.client_id)
        if used_pages + payload.page_count > settings.default_daily_quota:
            raise ValidationError("Le quota journalier du client serait depasse.")

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

    def list_jobs(self) -> list[PrintJobRead]:
        return [self._to_read(job) for job in self.repository.list_all()]

    def list_today_jobs(self) -> list[PrintJobRead]:
        return [self._to_read(job) for job in self.repository.list_today()]

    def _to_read(self, job: PrintJob) -> PrintJobRead:
        data = PrintJobRead.model_validate(job).model_dump()
        data["client_name"] = f"{job.client.first_name} {job.client.last_name}" if job.client else None
        data["station_code"] = job.station.code if job.station else None
        data["station_name"] = job.station.name if job.station else None
        return PrintJobRead.model_validate(data)
