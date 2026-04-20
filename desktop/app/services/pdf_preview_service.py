from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

try:
    import fitz
except Exception:  # pragma: no cover - optional local dependency
    fitz = None  # type: ignore[assignment]

try:
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QImage
    from PySide6.QtPdf import QPdfDocument
except Exception:  # pragma: no cover - depends on the local Qt PDF install
    QSize = None  # type: ignore[assignment]
    QImage = None  # type: ignore[assignment]
    QPdfDocument = None  # type: ignore[assignment]


class PdfPreviewService:
    """Gère le comptage des pages et la prévisualisation complète du document."""

    def get_page_count(self, pdf_path: str) -> int:
        """Retourne le nombre de pages utilisé par l'interface et le quota."""

        reader = PdfReader(pdf_path)
        return len(reader.pages)

    def build_preview_payload(self, pdf_path: str, width: int = 860, max_pages: int = 12) -> dict[str, object]:
        """Retourne les meilleures données d'aperçu disponibles pour un PDF.

        L'aperçu rend plusieurs pages afin d'afficher le document comme une
        séquence lisible. ``max_pages`` évite de surcharger les postes publics
        les plus lents.
        """

        images, image_source = self._build_best_images(pdf_path, width, max_pages)
        page_count = self.get_page_count(pdf_path)
        return {
            "images": images,
            "image_source": image_source,
            "page_count": page_count,
            "rendered_pages": len(images),
        }

    def _build_best_images(self, pdf_path: str, width: int, max_pages: int) -> tuple[list[QImage], str | None]:
        """Essaie d'abord le moteur le plus fiable, puis le moteur de secours."""

        pymupdf_images = self._render_with_pymupdf(pdf_path, width, max_pages)
        if pymupdf_images:
            return pymupdf_images, "pymupdf"

        qt_images = self._render_with_qtpdf(pdf_path, width, max_pages)
        if qt_images:
            return qt_images, "qtpdf"

        return [], None

    def _render_with_pymupdf(self, pdf_path: str, width: int, max_pages: int) -> list[QImage]:
        """Rend plusieurs pages avec PyMuPDF quand il est disponible."""

        if fitz is None or QImage is None:
            return []

        images: list[QImage] = []
        try:
            with fitz.open(pdf_path) as document:
                total = min(document.page_count, max_pages)
                for page_index in range(total):
                    page = document.load_page(page_index)
                    page_rect = page.rect
                    if page_rect.width <= 0:
                        continue
                    zoom = width / float(page_rect.width)
                    matrix = fitz.Matrix(zoom, zoom)
                    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    image = QImage(
                        pixmap.samples,
                        pixmap.width,
                        pixmap.height,
                        pixmap.stride,
                        QImage.Format.Format_RGB888,
                    )
                    if not image.isNull():
                        images.append(image.copy())
        except Exception:
            return []
        return images

    def _render_with_qtpdf(self, pdf_path: str, width: int, max_pages: int) -> list[QImage]:
        """Rend plusieurs pages en images quand QtPdf est disponible."""

        if QPdfDocument is None or QSize is None or QImage is None:
            return []

        document = QPdfDocument()
        document.load(str(Path(pdf_path)))
        if document.status() != QPdfDocument.Status.Ready or document.pageCount() <= 0:
            return []

        images: list[QImage] = []
        total = min(document.pageCount(), max_pages)
        for page_index in range(total):
            page_size = document.pagePointSize(page_index)
            if page_size.isEmpty():
                continue
            aspect_ratio = page_size.height() / max(page_size.width(), 1.0)
            target_size = QSize(width, max(1, int(width * aspect_ratio)))
            try:
                image = document.render(page_index, target_size)
            except Exception:
                continue
            if image is not None and not image.isNull():
                images.append(image)
        return images
