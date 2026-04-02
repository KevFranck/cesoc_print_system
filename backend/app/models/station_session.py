from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import utcnow


class StationSession(Base):
    __tablename__ = "station_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    started_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purpose: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    station = relationship("Station", back_populates="sessions")
    client = relationship("Client", back_populates="sessions")
    print_jobs = relationship("PrintJob", back_populates="session")
