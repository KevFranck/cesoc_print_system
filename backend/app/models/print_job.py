from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import utcnow


class PrintJob(Base):
    """Historise chaque tentative d'impression validée par le logiciel.

    Le statut est mis à jour par la borne après la tentative d'impression réelle.
    """

    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    session_id: Mapped[int | None] = mapped_column(ForeignKey("station_sessions.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("imported_documents.id"), nullable=True)
    document_name: Mapped[str] = mapped_column(String(180))
    page_count: Mapped[int] = mapped_column(Integer)
    selected_pages: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    administrative_context: Mapped[str] = mapped_column(String(255))
    printer_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client = relationship("Client", back_populates="print_jobs")
    station = relationship("Station", back_populates="print_jobs")
    session = relationship("StationSession", back_populates="print_jobs")
    document = relationship("ImportedDocument", back_populates="print_jobs")
