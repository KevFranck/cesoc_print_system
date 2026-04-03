from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import utcnow


class BonusPageGrant(Base):
    """Trace un déblocage manuel ou un ajout de pages pour un usager.

    Chaque entrée reste historisée pour garder une piste d'audit sur les
    dépassements de quota et les interventions du personnel.
    """

    __tablename__ = "bonus_page_grants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    pages: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(255))
    granted_by: Mapped[str] = mapped_column(String(120), default="Personnel CESOC")
    effective_date: Mapped[date] = mapped_column(Date, default=date.today)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="bonus_page_grants")
