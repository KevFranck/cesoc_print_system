from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.models.bonus_page_grant import BonusPageGrant
from app.repositories.base import BaseRepository


class BonusPageRepository(BaseRepository):
    """Encapsule l'accès aux bonus de pages accordés par le personnel."""

    def create(self, grant: BonusPageGrant) -> BonusPageGrant:
        self.db.add(grant)
        self.db.commit()
        self.db.refresh(grant)
        return grant

    def list_for_client(self, client_id: int) -> list[BonusPageGrant]:
        stmt = (
            select(BonusPageGrant)
            .where(BonusPageGrant.client_id == client_id)
            .order_by(BonusPageGrant.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_active_pages_for_date(self, client_id: int, target_date: date) -> int:
        stmt = (
            select(func.coalesce(func.sum(BonusPageGrant.pages), 0))
            .where(BonusPageGrant.client_id == client_id)
            .where(BonusPageGrant.effective_date <= target_date)
            .where((BonusPageGrant.expires_on.is_(None)) | (BonusPageGrant.expires_on >= target_date))
        )
        return int(self.db.scalar(stmt) or 0)
