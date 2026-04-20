from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.bonus_page import BonusPageGrantRead
from app.schemas.client import ClientCreate, ClientListItem, ClientRead


class UserCreate(ClientCreate):
    """Alias métier pour la création d'un utilisateur borne."""

    email: EmailStr
    password: str | None = Field(default=None, min_length=4, max_length=100)


class UserRegister(BaseModel):
    """Inscription autonome depuis la borne."""

    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=4, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)


class UserPasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=4, max_length=100)


class UserRead(ClientRead):
    """Alias métier pour la lecture d'un utilisateur borne."""


class UserListItem(ClientListItem):
    """Vue synthétique dédiée à l'administration des utilisateurs."""


class QuotaStatusRead(BaseModel):
    """Synthèse complète du quota quotidien d'un utilisateur."""

    user_id: int
    email: str | None
    full_name: str
    base_daily_quota: int
    bonus_pages: int
    effective_quota: int
    printed_pages_today: int
    remaining_pages: int
    rejected_jobs_today: int
    can_print: bool
    bonus_history: list[BonusPageGrantRead] = Field(default_factory=list)
