from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.session import SessionEndRequest, StationSessionCreate, StationSessionRead
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/start", response_model=StationSessionRead, status_code=status.HTTP_201_CREATED)
def start_session(payload: StationSessionCreate, db: Session = Depends(get_db)) -> StationSessionRead:
    return SessionService(db).start_session(payload)


@router.post("/end", response_model=StationSessionRead)
def end_session(payload: SessionEndRequest, db: Session = Depends(get_db)) -> StationSessionRead:
    return SessionService(db).end_session(payload)


@router.get("/active", response_model=list[StationSessionRead])
def list_active_sessions(db: Session = Depends(get_db)) -> list[StationSessionRead]:
    return SessionService(db).list_active_sessions()
