from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.services.config_service import ClientStationConfig


@dataclass(slots=True)
class PrintResult:
    """Resultat d'une tentative d'impression locale sur Windows."""

    success: bool
    message: str


class PrintService:
    """Encapsule l'impression PDF Windows.

    Pour gerer une selection de pages sans dependre des options du driver,
    le service fabrique au besoin un PDF temporaire ne contenant que les pages
    demandees, puis imprime ce sous-document.
    """

    def __init__(self, config: ClientStationConfig) -> None:
        self.config = config

    def resolve_page_selection(self, total_pages: int, raw_selection: str | None) -> tuple[str | None, int]:
        """Valide une saisie de type `1-3,5` et renvoie une version normalisee."""

        if not raw_selection or not raw_selection.strip():
            return None, total_pages

        selected_pages: set[int] = set()
        parts = [part.strip() for part in raw_selection.split(",") if part.strip()]
        if not parts:
            raise ValueError("La selection de pages est vide ou invalide.")

        for part in parts:
            if "-" in part:
                start_raw, end_raw = [item.strip() for item in part.split("-", 1)]
                if not start_raw.isdigit() or not end_raw.isdigit():
                    raise ValueError("Une plage de pages est invalide.")
                start, end = int(start_raw), int(end_raw)
                if start < 1 or end < start or end > total_pages:
                    raise ValueError("La plage de pages depasse le nombre de pages du document.")
                selected_pages.update(range(start, end + 1))
            else:
                if not part.isdigit():
                    raise ValueError("Une page selectionnee est invalide.")
                page_number = int(part)
                if page_number < 1 or page_number > total_pages:
                    raise ValueError("La selection de pages depasse le nombre de pages du document.")
                selected_pages.add(page_number)

        normalized = ",".join(str(page_number) for page_number in sorted(selected_pages))
        return normalized, len(selected_pages)

    def print_pdf(self, pdf_path: str, selected_pages: str | None = None) -> PrintResult:
        temp_subset_path: Path | None = None
        effective_path = pdf_path
        try:
            if selected_pages:
                temp_subset_path = self._build_subset_pdf(pdf_path, selected_pages)
                effective_path = str(temp_subset_path)

            if self.config.pdf_print_tool_path and Path(self.config.pdf_print_tool_path).exists():
                return self._print_with_sumatra(effective_path)
            if os.name == "nt":
                try:
                    os.startfile(effective_path, "print")  # type: ignore[attr-defined]
                    return PrintResult(True, "Impression lancee via le shell Windows.")
                except OSError as exc:
                    return PrintResult(False, f"Echec impression Windows: {exc}")
            return PrintResult(False, "Impression Windows non disponible sur ce systeme.")
        finally:
            if temp_subset_path and temp_subset_path.exists():
                temp_subset_path.unlink(missing_ok=True)

    def _print_with_sumatra(self, pdf_path: str) -> PrintResult:
        command = [
            self.config.pdf_print_tool_path or "",
            "-print-to",
            self.config.printer_name or "",
            "-silent",
            pdf_path,
        ]
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=45)
            return PrintResult(True, completed.stdout.strip() or "Impression Sumatra terminee.")
        except Exception as exc:  # pragma: no cover - depends on workstation state
            return PrintResult(False, f"Echec SumatraPDF: {exc}")

    def _build_subset_pdf(self, pdf_path: str, selected_pages: str) -> Path:
        """Construit un PDF temporaire avec seulement les pages choisies."""

        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        normalized, _ = self.resolve_page_selection(len(reader.pages), selected_pages)
        for page_token in (normalized or "").split(","):
            if page_token:
                writer.add_page(reader.pages[int(page_token) - 1])

        temp_dir = Path(self.config.local_document_root).resolve() / "print_subsets"
        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="subset_", suffix=".pdf", delete=False, dir=temp_dir) as handle:
            writer.write(handle)
            return Path(handle.name)
