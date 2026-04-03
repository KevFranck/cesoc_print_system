from __future__ import annotations

from dataclasses import dataclass

from app.services.api_client import ApiClient
from app.services.auth_service import AuthService, AuthenticatedUser
from app.services.config_service import ClientStationConfig
from app.services.email_refresh_service import EmailRefreshService
from app.services.pdf_preview_service import PdfPreviewService
from app.services.print_service import PrintResult, PrintService
from app.services.usb_monitor_service import LocalPdfDocument, UsbMonitorService


@dataclass(slots=True)
class RegisteredDocument:
    """Document local déjà synchronisé avec le backend."""

    id: int
    original_filename: str
    local_path: str
    page_count: int
    source_type: str
    source_label: str


class KioskWorkflowService:
    """Orchestre le parcours borne sans injecter de logique métier dans l'UI."""

    def __init__(self, api_client: ApiClient, config: ClientStationConfig) -> None:
        self.api_client = api_client
        self.config = config
        self.auth_service = AuthService(api_client)
        self.usb_service = UsbMonitorService()
        self.email_service = EmailRefreshService(config)
        self.preview_service = PdfPreviewService()
        self.print_service = PrintService(config)

    def authenticate_user(self, email: str) -> AuthenticatedUser:
        return self.auth_service.authenticate_by_email(email)

    def get_user_quota(self, user_id: int) -> dict:
        data = self.api_client.get(f"/users/{user_id}/quota-status")
        return data if isinstance(data, dict) else {}

    def load_usb_documents(self) -> list[LocalPdfDocument]:
        return self.usb_service.list_pdf_documents()

    def load_email_documents(self, sender_email: str | None = None) -> list[LocalPdfDocument]:
        return self.email_service.fetch_pdf_attachments(sender_email)

    def cleanup_session_artifacts(self) -> None:
        """Nettoie les artefacts temporaires liés à la session de borne."""

        self.email_service.clear_session_cache()

    def register_local_document(self, user_id: int, document: LocalPdfDocument) -> RegisteredDocument:
        route = "/documents/import-email" if document.source_type == "email" else "/documents/import-usb"
        payload = {
            "owner_client_id": user_id,
            "source_type": document.source_type,
            "source_label": document.source_label,
            "sender_email": document.sender_email,
            "original_filename": document.original_filename,
            "local_path": document.local_path,
            "page_count": document.page_count,
        }
        created = self.api_client.post(route, payload)
        return RegisteredDocument(
            id=int(created["id"]),
            original_filename=created["original_filename"],
            local_path=created["local_path"],
            page_count=int(created["page_count"]),
            source_type=created["source_type"],
            source_label=created.get("source_label") or "",
        )

    def print_registered_document(self, document: RegisteredDocument, context_label: str) -> tuple[dict, PrintResult]:
        job = self.api_client.post(
            f"/documents/{document.id}/print",
            {
                "station_code": self.config.station_code,
                "printer_name": self.config.printer_name,
                "administrative_context": context_label,
            },
        )
        result = self.print_service.print_pdf(document.local_path)
        self.api_client.post(
            f"/documents/jobs/{job['id']}/status",
            {"status": "printed" if result.success else "failed", "failure_reason": None if result.success else result.message},
        )
        self.api_client.post(
            f"/documents/{document.id}/mark-status/{'printed' if result.success else 'failed'}",
            {},
        )
        return job, result
