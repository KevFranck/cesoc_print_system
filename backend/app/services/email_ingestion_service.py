from __future__ import annotations

from pathlib import Path

from app.schemas.document import ImportedDocumentCreate


class EmailIngestionService:
    """Service utilitaire côté backend pour normaliser une pièce jointe email.

    L'ingestion IMAP réelle est faite sur la borne. Le backend garde ce service
    pour documenter et encapsuler la transformation vers le payload standard.
    """

    @staticmethod
    def build_payload(
        local_path: str,
        page_count: int,
        sender_email: str | None,
        owner_client_id: int | None,
    ) -> ImportedDocumentCreate:
        return ImportedDocumentCreate(
            owner_client_id=owner_client_id,
            source_type="email",
            source_label="Boite mail de service",
            sender_email=sender_email,
            original_filename=Path(local_path).name,
            local_path=local_path,
            page_count=page_count,
        )
