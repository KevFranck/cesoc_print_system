"""add client passwords

Revision ID: 20260413_0004
Revises: 20260403_0003
Create Date: 2026-04-13 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0004"
down_revision = "20260403_0003"
branch_labels = None
depends_on = None


DEFAULT_HASHED_PASSWORD = "506b9a7604beb2b250c165bf238159d4cb3e674f59c3b0c8a7a24f8c6853ad6b"


def upgrade() -> None:
    op.add_column("clients", sa.Column("hashed_password", sa.String(length=255), nullable=True))
    op.execute(f"UPDATE clients SET hashed_password = '{DEFAULT_HASHED_PASSWORD}' WHERE hashed_password IS NULL")
    op.alter_column("clients", "hashed_password", existing_type=sa.String(length=255), nullable=False)
    op.execute("UPDATE bonus_page_grants SET expires_on = effective_date WHERE expires_on IS NULL")


def downgrade() -> None:
    op.drop_column("clients", "hashed_password")
