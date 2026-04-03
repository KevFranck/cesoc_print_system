"""kiosk mvp extensions

Revision ID: 20260402_0002
Revises: 20260402_0001
Create Date: 2026-04-02 02:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0002"
down_revision = "20260402_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_clients_email", "clients", ["email"])

    op.create_table(
        "bonus_page_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("granted_by", sa.String(length=120), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bonus_page_grants_id", "bonus_page_grants", ["id"], unique=False)

    op.create_table(
        "imported_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_client_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_label", sa.String(length=180), nullable=True),
        sa.Column("sender_email", sa.String(length=150), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("local_path", sa.String(length=500), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_imported_documents_id", "imported_documents", ["id"], unique=False)

    op.add_column("print_jobs", sa.Column("document_id", sa.Integer(), nullable=True))
    op.add_column("print_jobs", sa.Column("printer_name", sa.String(length=180), nullable=True))
    op.add_column("print_jobs", sa.Column("failure_reason", sa.String(length=255), nullable=True))
    op.create_foreign_key("fk_print_jobs_document_id", "print_jobs", "imported_documents", ["document_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_print_jobs_document_id", "print_jobs", type_="foreignkey")
    op.drop_column("print_jobs", "failure_reason")
    op.drop_column("print_jobs", "printer_name")
    op.drop_column("print_jobs", "document_id")
    op.drop_index("ix_imported_documents_id", table_name="imported_documents")
    op.drop_table("imported_documents")
    op.drop_index("ix_bonus_page_grants_id", table_name="bonus_page_grants")
    op.drop_table("bonus_page_grants")
    op.drop_constraint("uq_clients_email", "clients", type_="unique")
