from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.theme import build_stylesheet
from app.services.api_client import ApiClient
from app.services.config_service import ConfigService
from app.ui.admin.main_window import AdminMainWindow
from app.ui.client.main_window import ClientMainWindow


def _build_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("CESOC Print System")
    app.setStyleSheet(build_stylesheet())
    return app


def run_admin_app() -> None:
    app = _build_app()
    config = ConfigService.load_desktop_config()
    window = AdminMainWindow(ApiClient(config.api_base_url))
    window.show()
    sys.exit(app.exec())


def run_client_app() -> None:
    app = _build_app()
    config = ConfigService.load_client_station_config()
    window = ClientMainWindow(ApiClient(config.api_base_url), config)
    window.show()
    sys.exit(app.exec())
