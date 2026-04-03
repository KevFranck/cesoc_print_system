from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LocalPdfDocument:
    """Décrit un PDF trouvé localement sur USB ou dans le cache email."""

    source_type: str
    source_label: str
    original_filename: str
    local_path: str
    page_count: int
    sender_email: str | None = None


class UsbMonitorService:
    """Détecte les volumes amovibles Windows et liste les PDF utilisables.

    Le but n'est pas d'exposer tout le système de fichiers à l'usager, mais de
    présenter directement les documents PDF trouvés sur des supports USB.
    """

    DRIVE_REMOVABLE = 2

    def list_pdf_documents(self) -> list[LocalPdfDocument]:
        from app.services.pdf_preview_service import PdfPreviewService

        documents: list[LocalPdfDocument] = []
        preview_service = PdfPreviewService()
        for drive in self._get_removable_drives():
            for root, _, files in os.walk(drive):
                for filename in files:
                    if not filename.lower().endswith(".pdf"):
                        continue
                    full_path = str(Path(root) / filename)
                    page_count = preview_service.get_page_count(full_path)
                    documents.append(
                        LocalPdfDocument(
                            source_type="usb",
                            source_label=drive,
                            original_filename=filename,
                            local_path=full_path,
                            page_count=page_count,
                        )
                    )
        return documents

    def _get_removable_drives(self) -> list[str]:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        drives: list[str] = []
        for index in range(26):
            if bitmask & (1 << index):
                drive = f"{chr(65 + index)}:\\"
                if ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive)) == self.DRIVE_REMOVABLE:
                    drives.append(drive)
        return drives
