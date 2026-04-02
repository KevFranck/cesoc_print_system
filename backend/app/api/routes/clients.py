from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.client import ClientCreate, ClientListItem, ClientRead, RemainingPagesRead
from app.services.client_service import ClientService

router = APIRouter()


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> ClientRead:
    return ClientService(db).create_client(payload)


@router.get("", response_model=list[ClientListItem])
def list_clients(db: Session = Depends(get_db)) -> list[ClientListItem]:
    return ClientService(db).list_clients()


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)) -> ClientRead:
    return ClientService(db).get_client(client_id)


@router.get("/{client_id}/remaining-pages", response_model=RemainingPagesRead)
def get_remaining_pages(client_id: int, db: Session = Depends(get_db)) -> RemainingPagesRead:
    return ClientService(db).get_remaining_pages(client_id)
