from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientListItem, ClientRead, RemainingPagesRead


class ClientService:
    def __init__(self, db: Session) -> None:
        self.repository = ClientRepository(db)

    def create_client(self, payload: ClientCreate) -> ClientRead:
        client = Client(**payload.model_dump())
        created = self.repository.create(client)
        return ClientRead.model_validate(created)

    def list_clients(self) -> list[ClientListItem]:
        items = []
        for client in self.repository.list_all():
            used_pages = self.repository.get_printed_pages_today(client.id)
            active_sessions = sum(1 for session in client.sessions if session.status == "active")
            data = ClientRead.model_validate(client).model_dump()
            data["full_name"] = f"{client.first_name} {client.last_name}"
            data["active_session_count"] = active_sessions
            data["used_pages_today"] = used_pages
            data["remaining_pages"] = max(settings.default_daily_quota - used_pages, 0)
            items.append(ClientListItem.model_validate(data))
        return items

    def get_client(self, client_id: int) -> ClientRead:
        client = self.repository.get_by_id(client_id)
        if not client:
            raise NotFoundError("Client introuvable.")
        return ClientRead.model_validate(client)

    def get_remaining_pages(self, client_id: int) -> RemainingPagesRead:
        client = self.repository.get_by_id(client_id)
        if not client:
            raise NotFoundError("Client introuvable.")
        used_pages = self.repository.get_printed_pages_today(client_id)
        remaining = max(settings.default_daily_quota - used_pages, 0)
        return RemainingPagesRead(
            client_id=client_id,
            daily_quota=settings.default_daily_quota,
            used_pages_today=used_pages,
            remaining_pages=remaining,
        )
