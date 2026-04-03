from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

try:
    from PySide6.QtPdf import QPdfDocument
except Exception:  # pragma: no cover - dépend de l'installation Qt PDF
    QPdfDocument = None  # type: ignore[assignment]


class PdfPreviewService:
    """Fournit le comptage des pages et, si disponible, le chargement preview Qt."""

    def get_page_count(self, pdf_path: str) -> int:
        """Compte les pages d'un PDF pour alimenter l'UI et le quota."""

        reader = PdfReader(pdf_path)
        return len(reader.pages)

    def create_pdf_document(self, pdf_path: str):  # type: ignore[no-untyped-def]
        """Charge un document Qt PDF si le module est disponible.

        Le widget d'aperçu doit conserver l'objet retourné sur lui-même pour
        éviter que Qt ne le libère trop tôt, ce qui faisait disparaître
        l'aperçu dans certaines sessions.
        """

        if QPdfDocument is None:
            return None
        document = QPdfDocument()
        document.load(str(Path(pdf_path)))
        if document.status() != QPdfDocument.Status.Ready:
            return None
        return document
