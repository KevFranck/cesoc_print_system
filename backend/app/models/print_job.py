from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import utcnow


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    session_id: Mapped[int | None] = mapped_column(ForeignKey("station_sessions.id"), nullable=True)
    document_name: Mapped[str] = mapped_column(String(180))
    page_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    administrative_context: Mapped[str] = mapped_column(String(255))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client = relationship("Client", back_populates="print_jobs")
    station = relationship("Station", back_populates="print_jobs")
    session = relationship("StationSession", back_populates="print_jobs")
