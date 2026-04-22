from __future__ import annotations

"""Smoke test local pour verifier les points de lancement essentiels.

Le script utilise une base SQLite temporaire afin de tester les routes FastAPI
sans exiger PostgreSQL. Il construit aussi les fenetres Qt en mode offscreen
pour attraper les erreurs d'import ou d'initialisation de l'interface.
"""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DESKTOP = ROOT / "desktop"
SMOKE_DB = BACKEND / "_local_smoke.sqlite3"


def _prepend_path(path: Path) -> None:
    text_path = str(path)
    if text_path not in sys.path:
        sys.path.insert(0, text_path)


def _clear_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def run_backend_smoke() -> None:
    if SMOKE_DB.exists():
        SMOKE_DB.unlink()

    os.environ["DATABASE_URL"] = f"sqlite:///{SMOKE_DB.as_posix()}"
    _prepend_path(BACKEND)

    from fastapi.testclient import TestClient

    import app.models  # noqa: F401
    from app.db.base import Base
    from app.db.session import engine
    from app.main import app

    try:
        Base.metadata.create_all(bind=engine)

        with TestClient(app) as client:
            health = client.get("/health")
            assert health.status_code == 200, health.text

            user = client.post(
                "/api/v1/users/register",
                json={
                    "first_name": "Test",
                    "last_name": "Local",
                    "email": "test.local@example.com",
                    "password": "test1234",
                },
            )
            assert user.status_code == 201, user.text
            user_id = user.json()["id"]

            station = client.post(
                "/api/v1/stations",
                json={"code": "POSTE-01", "name": "Poste 01", "status": "available"},
            )
            assert station.status_code == 201, station.text

            session = client.post(
                "/api/v1/sessions/start",
                json={"station_code": "POSTE-01", "client_id": user_id, "purpose": "Test local"},
            )
            assert session.status_code == 201, session.text

        job = client.post(
            "/api/v1/print-jobs",
            json={
                    "client_id": user_id,
                    "station_code": "POSTE-01",
                    "document_name": "demo.pdf",
                    "page_count": 2,
                    "administrative_context": "Test local",
                },
        )
        assert job.status_code == 201, job.text
        job_id = job.json()["id"]

        failed_status = client.post(
            f"/api/v1/documents/jobs/{job_id}/status",
            json={"status": "failed", "failure_reason": "Aucune imprimante detectee"},
        )
        assert failed_status.status_code == 200, failed_status.text

        quota = client.get(f"/api/v1/users/{user_id}/quota-status")
        assert quota.status_code == 200, quota.text
        assert quota.json()["printed_pages_today"] == 0, quota.text
        assert quota.json()["remaining_pages"] == quota.json()["effective_quota"], quota.text

        report = client.get("/api/v1/dashboard/report/daily")
        assert report.status_code == 200, report.text
        assert report.json()["report_jobs_count"] == 1, report.text
    finally:
        engine.dispose()
        if SMOKE_DB.exists():
            SMOKE_DB.unlink()

    print("Backend smoke OK")


def run_desktop_smoke() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _clear_app_modules()
    _prepend_path(DESKTOP)

    from PySide6.QtWidgets import QApplication

    from app.services.api_client import ApiClient
    from app.services.config_service import ConfigService
    from app.ui.admin.main_window import AdminMainWindow
    from app.ui.kiosk_client.main_window import KioskMainWindow

    qt_app = QApplication.instance() or QApplication([])
    api = ApiClient("http://127.0.0.1:8000/api/v1")
    admin = AdminMainWindow(api)
    kiosk = KioskMainWindow(api, ConfigService.load_client_station_config())
    assert admin.windowTitle()
    assert kiosk.windowTitle()
    qt_app.quit()

    print("Desktop smoke OK")


def main() -> None:
    run_backend_smoke()
    run_desktop_smoke()
    print("Local smoke test OK")


if __name__ == "__main__":
    main()
