from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.station_session import StationSession
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository):
    def create(self, session: StationSession) -> StationSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update(self, session: StationSession) -> StationSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_active_for_station(self, station_id: int) -> StationSession | None:
        stmt = (
            select(StationSession)
            .options(selectinload(StationSession.client), selectinload(StationSession.station))
            .where(
                StationSession.station_id == station_id,
                StationSession.status == "active",
            )
        )
        return self.db.scalar(stmt)

    def get_by_id(self, session_id: int) -> StationSession | None:
        stmt = (
            select(StationSession)
            .options(selectinload(StationSession.client), selectinload(StationSession.station))
            .where(StationSession.id == session_id)
        )
        return self.db.scalar(stmt)

    def list_active(self) -> list[StationSession]:
        stmt = (
            select(StationSession)
            .options(selectinload(StationSession.client), selectinload(StationSession.station))
            .where(StationSession.status == "active")
            .order_by(StationSession.started_at.desc())
        )
        return list(self.db.scalars(stmt))
