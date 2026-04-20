from __future__ import annotations

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.user import QuotaStatusRead, UserCreate, UserLogin, UserPasswordChange, UserRegister, UserListItem, UserRead
from app.services.quota_service import QuotaService


DEFAULT_USER_PASSWORD = "cesoc"


class UserService:
    """Service métier orienté 'utilisateurs borne' basé sur le modèle Client."""

    def __init__(self, db: Session) -> None:
        self.repository = ClientRepository(db)
        self.quota_service = QuotaService(db)

    def create_user(self, payload: UserCreate) -> UserRead:
        if payload.email and self.repository.get_by_email(payload.email):
            raise ConflictError("Un utilisateur avec cet email existe deja.")
        data = payload.model_dump()
        password = data.pop("password") or DEFAULT_USER_PASSWORD
        created = self.repository.create(Client(**data, hashed_password=hash_password(password)))
        return UserRead.model_validate(created)

    def register_user(self, payload: UserRegister) -> UserRead:
        if self.repository.get_by_email(payload.email):
            raise ConflictError("Un utilisateur avec cet email existe deja.")
        data = payload.model_dump()
        password = data.pop("password")
        data["administrative_note"] = "Compte cree par l'utilisateur"
        created = self.repository.create(Client(**data, hashed_password=hash_password(password)))
        return UserRead.model_validate(created)

    def authenticate_user(self, payload: UserLogin) -> UserRead:
        client = self.repository.get_by_email(payload.email)
        if not client or not client.is_active:
            raise AuthenticationError("Email ou mot de passe incorrect.")
        hashed_password = client.hashed_password or hash_password(DEFAULT_USER_PASSWORD)
        if not verify_password(payload.password, hashed_password):
            raise AuthenticationError("Email ou mot de passe incorrect.")
        return UserRead.model_validate(client)

    def change_password(self, user_id: int, payload: UserPasswordChange) -> UserRead:
        client = self.repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        hashed_password = client.hashed_password or hash_password(DEFAULT_USER_PASSWORD)
        if not verify_password(payload.current_password, hashed_password):
            raise AuthenticationError("Mot de passe actuel incorrect.")
        if payload.new_password == DEFAULT_USER_PASSWORD:
            raise ValidationError("Choisis un mot de passe plus robuste que le mot de passe par defaut.")
        client.hashed_password = hash_password(payload.new_password)
        updated = self.repository.save(client)
        return UserRead.model_validate(updated)

    def reset_password(self, user_id: int) -> UserRead:
        client = self.repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        client.hashed_password = hash_password(DEFAULT_USER_PASSWORD)
        updated = self.repository.save(client)
        return UserRead.model_validate(updated)

    def list_users(self) -> list[UserListItem]:
        users: list[UserListItem] = []
        for client in self.repository.list_all():
            quota = self._safe_quota_status(client)
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
        client = self.repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        return self._safe_quota_status(client)

    def _safe_quota_status(self, client: Client) -> QuotaStatusRead:
        """Retourne un quota exploitable même si les tables de bonus ne sont pas prêtes.

        Cela évite de bloquer complètement l'interface admin lorsqu'une migration
        n'a pas encore été appliquée ou qu'un objet de quota est temporairement
        indisponible. L'admin garde ainsi la liste des utilisateurs visible.
        """

        try:
            return self.quota_service.build_quota_status(client)
        except (OperationalError, ProgrammingError):
            return QuotaStatusRead(
                user_id=client.id,
                email=client.email,
                full_name=f"{client.first_name} {client.last_name}",
                base_daily_quota=settings.default_daily_quota,
                bonus_pages=0,
                effective_quota=settings.default_daily_quota,
                printed_pages_today=0,
                remaining_pages=settings.default_daily_quota,
                rejected_jobs_today=0,
                can_print=client.is_active,
                bonus_history=[],
            )
