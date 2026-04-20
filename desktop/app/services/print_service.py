from __future__ import annotations

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
        self._sumatra_candidates = [
            Path("C:/Tools/SumatraPDF/SumatraPDF.exe"),
            Path("C:/Program Files/SumatraPDF/SumatraPDF.exe"),
            Path("C:/Program Files (x86)/SumatraPDF/SumatraPDF.exe"),
        ]

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

    def resolve_copy_count(self, raw_copy_count: str | None) -> int:
        if not raw_copy_count or not raw_copy_count.strip():
            return 1
        if not raw_copy_count.strip().isdigit():
            raise ValueError("Le nombre de copies est invalide.")
        copy_count = int(raw_copy_count.strip())
        if copy_count < 1 or copy_count > 20:
            raise ValueError("Le nombre de copies doit etre compris entre 1 et 20.")
        return copy_count

    def print_pdf(self, pdf_path: str, selected_pages: str | None = None, copy_count: int = 1) -> PrintResult:
        temp_subset_path: Path | None = None
        effective_path = pdf_path
        try:
            if selected_pages:
                temp_subset_path = self._build_subset_pdf(pdf_path, selected_pages)
                effective_path = str(temp_subset_path)

            sumatra_path = self._resolve_sumatra_path()
            if sumatra_path:
                printer_validation = self._validate_printer_name()
                if printer_validation:
                    return printer_validation
                return self._print_with_sumatra(effective_path, sumatra_path, copy_count)
            return PrintResult(
                False,
                "Aucun moteur d'impression silencieux n'est disponible. "
                "Installez SumatraPDF ou configurez `pdf_print_tool_path` vers son executable.",
            )
        finally:
            if temp_subset_path and temp_subset_path.exists():
                temp_subset_path.unlink(missing_ok=True)

    def _resolve_sumatra_path(self) -> Path | None:
        configured_path = Path(self.config.pdf_print_tool_path) if self.config.pdf_print_tool_path else None
        if configured_path and configured_path.exists():
            return configured_path
        return next((path for path in self._sumatra_candidates if path.exists()), None)

    def _validate_printer_name(self) -> PrintResult | None:
        if not self.config.printer_name or not self.config.printer_name.strip():
            return PrintResult(False, "Aucune imprimante n'est configuree pour cette borne.")

        installed_printers = self._list_installed_printers()
        if installed_printers and self.config.printer_name not in installed_printers:
            printer_list = ", ".join(installed_printers)
            return PrintResult(
                False,
                f"Imprimante '{self.config.printer_name}' introuvable sur ce poste. Disponibles: {printer_list}",
            )
        return None

    def _list_installed_printers(self) -> list[str]:
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Add-Type -AssemblyName System.Drawing; [System.Drawing.Printing.PrinterSettings]::InstalledPrinters | ForEach-Object { $_ }",
        ]
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
        except Exception:
            return []
        return [line.strip() for line in completed.stdout.splitlines() if line.strip()]

    def _print_with_sumatra(self, pdf_path: str, executable_path: Path, copy_count: int) -> PrintResult:
        command = [
            str(executable_path),
            "-print-to",
            self.config.printer_name or "",
            "-print-settings",
            f"{copy_count}x",
            "-silent",
            pdf_path,
        ]
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=45)
            copies_label = "copie" if copy_count == 1 else "copies"
            return PrintResult(True, completed.stdout.strip() or f"Impression Sumatra terminee ({copy_count} {copies_label}).")
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
