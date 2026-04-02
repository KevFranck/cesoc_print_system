from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.station_session import StationSession
from app.repositories.client_repository import ClientRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.station_repository import StationRepository
from app.schemas.session import SessionEndRequest, StationSessionCreate, StationSessionRead


class SessionService:
    def __init__(self, db: Session) -> None:
        self.station_repository = StationRepository(db)
        self.client_repository = ClientRepository(db)
        self.repository = SessionRepository(db)

    def start_session(self, payload: StationSessionCreate) -> StationSessionRead:
        station = self.station_repository.get_by_code(payload.station_code)
        if not station:
            raise NotFoundError("Poste introuvable.")

        client = self.client_repository.get_by_id(payload.client_id)
        if not client:
            raise NotFoundError("Client introuvable.")
        if not client.is_active:
            raise ConflictError("Ce client est inactif.")

        active_session = self.repository.get_active_for_station(station.id)
        if active_session:
            raise ConflictError("Une session est deja active sur ce poste.")

        station.status = "occupied"
        session = StationSession(
            station_id=station.id,
            client_id=client.id,
            purpose=payload.purpose,
            started_by=payload.started_by,
            notes=payload.notes,
            status="active",
        )
        created = self.repository.create(session)
        return self._to_read(created)

    def end_session(self, payload: SessionEndRequest) -> StationSessionRead:
        session = self.repository.get_by_id(payload.session_id)
        if not session:
            raise NotFoundError("Session introuvable.")
        if session.status != "active":
            raise ConflictError("Cette session est deja terminee.")

        session.status = "ended"
        session.ended_at = datetime.now(timezone.utc)
        if payload.notes:
            session.notes = payload.notes

        session.station.status = "available"
        updated = self.repository.update(session)
        return self._to_read(updated)

    def list_active_sessions(self) -> list[StationSessionRead]:
        return [self._to_read(session) for session in self.repository.list_active()]

    def _to_read(self, session: StationSession) -> StationSessionRead:
        data = StationSessionRead.model_validate(session).model_dump()
        data["client_name"] = f"{session.client.first_name} {session.client.last_name}" if session.client else None
        data["station_code"] = session.station.code if session.station else None
        data["station_name"] = session.station.name if session.station else None
        return StationSessionRead.model_validate(data)
