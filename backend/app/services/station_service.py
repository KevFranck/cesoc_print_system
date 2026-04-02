from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.station import Station
from app.repositories.session_repository import SessionRepository
from app.repositories.station_repository import StationRepository
from app.schemas.session import StationSessionRead
from app.schemas.station import StationCreate, StationRead


class StationService:
    def __init__(self, db: Session) -> None:
        self.repository = StationRepository(db)
        self.session_repository = SessionRepository(db)

    def create_station(self, payload: StationCreate) -> StationRead:
        if self.repository.get_by_code(payload.code):
            raise ConflictError("Un poste avec ce code existe deja.")
        station = Station(**payload.model_dump())
        created = self.repository.create(station)
        return StationRead.model_validate(created)

    def list_stations(self) -> list[StationRead]:
        return [self._to_read(station) for station in self.repository.list_all()]

    def get_station_by_code(self, station_code: str) -> StationRead:
        station = self.repository.get_by_code(station_code)
        if not station:
            raise NotFoundError("Poste introuvable.")
        return self._to_read(station)

    def get_active_session(self, station_code: str) -> StationSessionRead | None:
        station = self.repository.get_by_code(station_code)
        if not station:
            raise NotFoundError("Poste introuvable.")
        session = self.session_repository.get_active_for_station(station.id)
        if not session:
            return None
        data = StationSessionRead.model_validate(session).model_dump()
        data["client_name"] = f"{session.client.first_name} {session.client.last_name}" if session.client else None
        data["station_code"] = session.station.code if session.station else None
        data["station_name"] = session.station.name if session.station else None
        return StationSessionRead.model_validate(data)

    def _to_read(self, station: Station) -> StationRead:
        active_session = next((session for session in station.sessions if session.status == "active"), None)
        data = StationRead.model_validate(station).model_dump()
        if active_session and active_session.client:
            data["active_session_id"] = active_session.id
            data["active_client_id"] = active_session.client_id
            data["active_client_name"] = f"{active_session.client.first_name} {active_session.client.last_name}"
        return StationRead.model_validate(data)
