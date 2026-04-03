from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.user import QuotaStatusRead, UserCreate, UserListItem, UserRead
from app.services.quota_service import QuotaService


class UserService:
    """Service métier orienté 'utilisateurs borne' basé sur le modèle Client."""

    def __init__(self, db: Session) -> None:
        self.repository = ClientRepository(db)
        self.quota_service = QuotaService(db)

    def create_user(self, payload: UserCreate) -> UserRead:
        if payload.email and self.repository.get_by_email(payload.email):
            raise ConflictError("Un utilisateur avec cet email existe deja.")
        created = self.repository.create(Client(**payload.model_dump()))
        return UserRead.model_validate(created)

    def list_users(self) -> list[UserListItem]:
        users: list[UserListItem] = []
        for client in self.repository.list_all():
            quota = self.quota_service.build_quota_status(client)
            data = UserRead.model_validate(client).model_dump()
            data["full_name"] = f"{client.first_name} {client.last_name}"
            data["active_session_count"] = sum(1 for session in client.sessions if session.status == "active")
            data["used_pages_today"] = quota.printed_pages_today
            data["remaining_pages"] = quota.remaining_pages
            users.append(UserListItem.model_validate(data))
        return users

    def get_user(self, user_id: int) -> UserRead:
        client = self.repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        return UserRead.model_validate(client)

    def get_user_by_email(self, email: str) -> UserRead:
        client = self.repository.get_by_email(email)
        if not client:
            raise NotFoundError("Utilisateur introuvable pour cet email.")
        return UserRead.model_validate(client)

    def get_quota_status(self, user_id: int) -> QuotaStatusRead:
        return self.quota_service.get_quota_status(user_id)
