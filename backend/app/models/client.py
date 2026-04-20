from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Client(TimestampMixin, Base):
    """Représente un usager du centre.

    Dans ce MVP, l'email sert d'identifiant de connexion sur la borne. Les liens
    vers les documents importés et les bonus de pages permettent de suivre
    précisément l'usage quotidien et les déblocages manuels.
    """

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(150), nullable=True, unique=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    administrative_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sessions = relationship("StationSession", back_populates="client")
    print_jobs = relationship("PrintJob", back_populates="client")
    imported_documents = relationship("ImportedDocument", back_populates="owner")
    bonus_page_grants = relationship("BonusPageGrant", back_populates="client")
