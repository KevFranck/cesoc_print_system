from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.station import Station
from app.models.station_session import StationSession
from app.repositories.base import BaseRepository


class StationRepository(BaseRepository):
    def create(self, station: Station) -> Station:
        self.db.add(station)
        self.db.commit()
        self.db.refresh(station)
        return station

    def list_all(self) -> list[Station]:
        stmt = (
            select(Station)
            .options(
                selectinload(Station.sessions).selectinload(StationSession.client),
                selectinload(Station.print_jobs),
            )
            .order_by(Station.code.asc())
        )
        return list(self.db.scalars(stmt))

    def get_by_code(self, station_code: str) -> Station | None:
        stmt = (
            select(Station)
            .options(
                selectinload(Station.sessions).selectinload(StationSession.client),
                selectinload(Station.print_jobs),
            )
            .where(Station.code == station_code)
        )
        return self.db.scalar(stmt)
