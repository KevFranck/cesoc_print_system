from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DesktopConfig:
    """Configuration minimale de la console d'administration."""

    api_base_url: str


@dataclass(slots=True)
class ClientStationConfig:
    """Configuration locale de la borne d'impression.

    Elle rassemble les paramètres nécessaires à l'API, au compte IMAP,
    à l'imprimante Windows et aux répertoires temporaires.
    """

    api_base_url: str
    station_code: str
    station_secret: str | None = None
    printer_name: str | None = None
    pdf_print_tool_path: str | None = None
    local_document_root: str = "runtime_documents"
    imap_host: str | None = None
    imap_port: int = 993
    imap_username: str | None = None
    imap_password: str | None = None
    mailbox_name: str = "INBOX"


class ConfigService:
    """Charge les fichiers de configuration locaux du desktop."""

    @staticmethod
    def load_desktop_config() -> DesktopConfig:
        return DesktopConfig(api_base_url="http://127.0.0.1:8000/api/v1")

    @staticmethod
    def load_client_station_config() -> ClientStationConfig:
        config_path = Path(__file__).resolve().parent.parent / "config" / "client_config.json"
        if not config_path.exists():
            example_path = Path(__file__).resolve().parent.parent / "config" / "client_config.example.json"
            if example_path.exists():
                raw = json.loads(example_path.read_text(encoding="utf-8"))
                return ClientStationConfig(**raw)
            return ClientStationConfig(api_base_url="http://127.0.0.1:8000/api/v1", station_code="POSTE-01")
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        return ClientStationConfig(**raw)
