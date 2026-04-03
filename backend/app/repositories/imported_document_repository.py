from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.imported_document import ImportedDocument
from app.repositories.base import BaseRepository


class ImportedDocumentRepository(BaseRepository):
    """Accès aux documents PDF importés depuis USB ou email."""

    def create(self, document: ImportedDocument) -> ImportedDocument:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: ImportedDocument) -> ImportedDocument:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, document_id: int) -> ImportedDocument | None:
        stmt = (
            select(ImportedDocument)
            .options(selectinload(ImportedDocument.owner))
            .where(ImportedDocument.id == document_id)
        )
        return self.db.scalar(stmt)

    def list_for_user(self, user_id: int, source_type: str | None = None) -> list[ImportedDocument]:
        stmt = (
            select(ImportedDocument)
            .options(selectinload(ImportedDocument.owner))
            .where(ImportedDocument.owner_client_id == user_id)
            .order_by(ImportedDocument.imported_at.desc())
        )
        if source_type:
            stmt = stmt.where(ImportedDocument.source_type == source_type)
        return list(self.db.scalars(stmt))

    def list_recent_unassigned_email(self) -> list[ImportedDocument]:
        stmt = (
            select(ImportedDocument)
            .where(ImportedDocument.owner_client_id.is_(None), ImportedDocument.source_type == "email")
            .order_by(ImportedDocument.imported_at.desc())
        )
        return list(self.db.scalars(stmt))
