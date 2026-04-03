from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.bonus_page_grant import BonusPageGrant
from app.repositories.bonus_page_repository import BonusPageRepository
from app.repositories.client_repository import ClientRepository
from app.schemas.bonus_page import BonusPageGrantCreate, BonusPageGrantRead


class OverrideService:
    """Enregistre les déblocages manuels et bonus de pages accordés par l'admin."""

    def __init__(self, db: Session) -> None:
        self.client_repository = ClientRepository(db)
        self.bonus_repository = BonusPageRepository(db)

    def grant_bonus_pages(self, user_id: int, payload: BonusPageGrantCreate) -> BonusPageGrantRead:
        client = self.client_repository.get_by_id(user_id)
        if not client:
            raise NotFoundError("Utilisateur introuvable.")
        grant = BonusPageGrant(
            client_id=user_id,
            pages=payload.pages,
            reason=payload.reason,
            granted_by=payload.granted_by,
            effective_date=datetime.now(timezone.utc).date(),
            expires_on=payload.expires_on,
        )
        created = self.bonus_repository.create(grant)
        return BonusPageGrantRead.model_validate(created)
