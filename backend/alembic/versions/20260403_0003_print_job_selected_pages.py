"""add selected pages to print jobs

Revision ID: 20260403_0003
Revises: 20260402_0002
Create Date: 2026-04-03 10:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260403_0003"
down_revision = "20260402_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("print_jobs", sa.Column("selected_pages", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("print_jobs", "selected_pages")
