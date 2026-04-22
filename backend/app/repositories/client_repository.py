from __future__ import annotations

from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.print_job import PrintJob
from app.models.station_session import StationSession
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository):
    """Accès à la table des usagers / utilisateurs de la borne."""

    def create(self, client: Client) -> Client:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def save(self, client: Client) -> Client:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def list_all(self) -> list[Client]:
        stmt = (
            select(Client)
            .options(
                selectinload(Client.sessions).selectinload(StationSession.station),
            )
            .order_by(Client.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_by_id(self, client_id: int) -> Client | None:
        return self.db.get(Client, client_id)

    def get_by_email(self, email: str) -> Client | None:
        stmt = select(Client).where(func.lower(Client.email) == email.lower())
        return self.db.scalar(stmt)

    def get_printed_pages_today(self, client_id: int) -> int:
        now = datetime.now(timezone.utc)
        day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        stmt = (
            select(func.coalesce(func.sum(PrintJob.page_count), 0))
            .where(PrintJob.client_id == client_id)
            .where(PrintJob.status == "printed")
            .where(PrintJob.submitted_at >= day_start)
            .where(PrintJob.submitted_at <= day_end)
        )
        return int(self.db.scalar(stmt) or 0)
