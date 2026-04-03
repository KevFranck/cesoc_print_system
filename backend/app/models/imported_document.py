from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import utcnow


class ImportedDocument(Base):
    """Décrit un PDF importé temporairement sur la borne puis synchronisé.

    Le document peut provenir d'une clé USB, d'un email ou d'une autre source
    supervisée. Le backend stocke la métadonnée métier et le chemin de travail.
    """

    __tablename__ = "imported_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30))
    source_label: Mapped[str | None] = mapped_column(String(180), nullable=True)
    sender_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    local_path: Mapped[str] = mapped_column(String(500))
    page_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="available")
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship("Client", back_populates="imported_documents")
    print_jobs = relationship("PrintJob", back_populates="document")
