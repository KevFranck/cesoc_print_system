from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AppSetting(TimestampMixin, Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(120), unique=True)
    value: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
