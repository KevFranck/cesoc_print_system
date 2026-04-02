from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.session import StationSessionRead
from app.schemas.station import StationCreate, StationRead
from app.services.station_service import StationService

router = APIRouter()


@router.post("", response_model=StationRead, status_code=status.HTTP_201_CREATED)
def create_station(payload: StationCreate, db: Session = Depends(get_db)) -> StationRead:
    return StationService(db).create_station(payload)


@router.get("", response_model=list[StationRead])
def list_stations(db: Session = Depends(get_db)) -> list[StationRead]:
    return StationService(db).list_stations()


@router.get("/{station_code}", response_model=StationRead)
def get_station(station_code: str, db: Session = Depends(get_db)) -> StationRead:
    return StationService(db).get_station_by_code(station_code)


@router.get("/{station_code}/active-session", response_model=StationSessionRead | None)
def get_active_session(station_code: str, db: Session = Depends(get_db)) -> StationSessionRead | None:
    return StationService(db).get_active_session(station_code)
