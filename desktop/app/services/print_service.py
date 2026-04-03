from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.services.config_service import ClientStationConfig


@dataclass(slots=True)
class PrintResult:
    """Résultat d'une tentative d'impression locale sur Windows."""

    success: bool
    message: str


class PrintService:
    """Encapsule l'impression PDF Windows.

    Le chemin le plus fiable en production est l'usage d'un outil CLI comme
    SumatraPDF. Un fallback `os.startfile(..., "print")` reste proposé pour la
    démonstration, mais il est moins déterministe.
    """

    def __init__(self, config: ClientStationConfig) -> None:
        self.config = config

    def print_pdf(self, pdf_path: str) -> PrintResult:
        if self.config.pdf_print_tool_path and Path(self.config.pdf_print_tool_path).exists():
            return self._print_with_sumatra(pdf_path)
        if os.name == "nt":
            try:
                os.startfile(pdf_path, "print")  # type: ignore[attr-defined]
                return PrintResult(True, "Impression lancee via le shell Windows.")
            except OSError as exc:
                return PrintResult(False, f"Echec impression Windows: {exc}")
        return PrintResult(False, "Impression Windows non disponible sur ce systeme.")

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
        except Exception as exc:  # pragma: no cover - dépend du poste Windows
            return PrintResult(False, f"Echec SumatraPDF: {exc}")
