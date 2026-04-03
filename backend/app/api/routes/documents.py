from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.document import DocumentPrintRequest, ImportedDocumentCreate, ImportedDocumentRead, PrintJobStatusUpdate
from app.schemas.print_job import PrintJobRead
from app.services.document_service import DocumentService
from app.services.print_job_service import PrintJobService

router = APIRouter()


@router.get("/email/{user_id}", response_model=list[ImportedDocumentRead])
def list_email_documents(user_id: int, db: Session = Depends(get_db)) -> list[ImportedDocumentRead]:
    """Retourne les PDFs issus de la boîte mail associés à un utilisateur."""

    return DocumentService(db).list_email_documents(user_id)


@router.post("/import-usb", response_model=ImportedDocumentRead, status_code=status.HTTP_201_CREATED)
def import_usb_document(payload: ImportedDocumentCreate, db: Session = Depends(get_db)) -> ImportedDocumentRead:
    """Enregistre un PDF récupéré depuis une clé USB sur la borne."""

    return DocumentService(db).register_document(payload)


@router.post("/import-email", response_model=ImportedDocumentRead, status_code=status.HTTP_201_CREATED)
def import_email_document(payload: ImportedDocumentCreate, db: Session = Depends(get_db)) -> ImportedDocumentRead:
    """Enregistre un PDF récupéré depuis la boîte mail de service."""

    return DocumentService(db).register_document(payload)


@router.get("/user/{user_id}", response_model=list[ImportedDocumentRead])
def list_user_documents(user_id: int, db: Session = Depends(get_db)) -> list[ImportedDocumentRead]:
    """Liste tous les documents disponibles pour un utilisateur borne."""

    return DocumentService(db).list_user_documents(user_id)


@router.post("/{document_id}/print", response_model=PrintJobRead)
def print_document(document_id: int, payload: DocumentPrintRequest, db: Session = Depends(get_db)) -> PrintJobRead:
    """Réserve le quota et crée un job d'impression pour le document demandé."""

    return DocumentService(db).print_document(document_id, payload)


@router.post("/{document_id}/mark-status/{status}", response_model=ImportedDocumentRead)
def mark_document_status(document_id: int, status: str, db: Session = Depends(get_db)) -> ImportedDocumentRead:
    """Met à jour l'état métier du document après impression ou échec."""

    return DocumentService(db).mark_print_result(document_id, status)


@router.post("/jobs/{job_id}/status", response_model=PrintJobRead)
def update_print_job_status(job_id: int, payload: PrintJobStatusUpdate, db: Session = Depends(get_db)) -> PrintJobRead:
    """Réceptionne le résultat réel remonté par le PrintService Windows."""

    return PrintJobService(db).update_print_status(job_id, payload)
