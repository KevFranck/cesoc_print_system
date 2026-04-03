from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.bonus_page import BonusPageGrantCreate, BonusPageGrantRead
from app.schemas.user import QuotaStatusRead, UserCreate, UserListItem, UserRead
from app.services.override_service import OverrideService
from app.services.user_service import UserService

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Crée un utilisateur borne accessible ensuite par email sur la borne."""

    return UserService(db).create_user(payload)


@router.get("", response_model=list[UserListItem])
def list_users(db: Session = Depends(get_db)) -> list[UserListItem]:
    """Liste tous les utilisateurs pour la console d'administration."""

    return UserService(db).list_users()


@router.get("/by-email/{email}", response_model=UserRead)
def get_user_by_email(email: str, db: Session = Depends(get_db)) -> UserRead:
    """Permet à la borne de connecter un usager par son email."""

    return UserService(db).get_user_by_email(email)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    """Retourne la fiche détaillée d'un utilisateur."""

    return UserService(db).get_user(user_id)


@router.get("/{user_id}/quota-status", response_model=QuotaStatusRead)
def get_quota_status(user_id: int, db: Session = Depends(get_db)) -> QuotaStatusRead:
    """Retourne le quota courant, les bonus et les rejets du jour."""

    return UserService(db).get_quota_status(user_id)


@router.post("/{user_id}/grant-bonus-pages", response_model=BonusPageGrantRead, status_code=status.HTTP_201_CREATED)
def grant_bonus_pages(
    user_id: int,
    payload: BonusPageGrantCreate,
    db: Session = Depends(get_db),
) -> BonusPageGrantRead:
    """Ajoute des pages bonus ou débloque manuellement un usager."""

    return OverrideService(db).grant_bonus_pages(user_id, payload)
