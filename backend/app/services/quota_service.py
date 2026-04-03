from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import Client
from app.models.print_job import PrintJob
from app.repositories.bonus_page_repository import BonusPageRepository
from app.repositories.client_repository import ClientRepository
from app.schemas.bonus_page import BonusPageGrantRead
from app.schemas.user import QuotaStatusRead


class QuotaService:
    """Calcule le quota quotidien effectif et l'état d'impression d'un usager."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.client_repository = ClientRepository(db)
        self.bonus_repository = BonusPageRepository(db)

    def get_quota_status(self, user_id: int) -> QuotaStatusRead:
        client = self.client_repository.get_by_id(user_id)
        if not client:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("Utilisateur introuvable.")
        return self.build_quota_status(client)

    def build_quota_status(self, client: Client) -> QuotaStatusRead:
        today = datetime.now(timezone.utc).date()
        printed_pages = self.client_repository.get_printed_pages_today(client.id)
        rejected_jobs = self._get_rejected_jobs_today(client.id)
        bonus_pages = self.bonus_repository.get_active_pages_for_date(client.id, today)
        effective_quota = settings.default_daily_quota + bonus_pages
        grants = [BonusPageGrantRead.model_validate(item) for item in self.bonus_repository.list_for_client(client.id)]
        return QuotaStatusRead(
            user_id=client.id,
            email=client.email,
            full_name=f"{client.first_name} {client.last_name}",
            base_daily_quota=settings.default_daily_quota,
            bonus_pages=bonus_pages,
            effective_quota=effective_quota,
            printed_pages_today=printed_pages,
            remaining_pages=max(effective_quota - printed_pages, 0),
            rejected_jobs_today=rejected_jobs,
            can_print=client.is_active and printed_pages < effective_quota,
            bonus_history=grants,
        )

    def ensure_pages_available(self, client: Client, pages_requested: int) -> QuotaStatusRead:
        status = self.build_quota_status(client)
        if status.remaining_pages < pages_requested:
            from app.core.exceptions import ValidationError

            raise ValidationError("Quota insuffisant pour imprimer ce document.")
        return status

    def _get_rejected_jobs_today(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        stmt = (
            select(func.count(PrintJob.id))
            .where(PrintJob.client_id == user_id)
            .where(PrintJob.submitted_at >= day_start, PrintJob.submitted_at <= day_end)
            .where(PrintJob.status == "failed")
        )
        return int(self.db.scalar(stmt) or 0)
