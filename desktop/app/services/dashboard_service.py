from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from app.services.api_client import ApiClient, ApiError


class AdminDashboardService:
    """Service d'accès API utilisé par l'interface d'administration."""

    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def get_summary(self) -> dict:
        data = self.api_client.safe_get(
            "/dashboard/summary",
            {
                "total_clients": 0,
                "free_stations": 0,
                "active_sessions": 0,
                "prints_today": 0,
                "pages_today": 0,
                "offline_stations": 0,
            },
        )
        return data if isinstance(data, dict) else {}

    def get_report(self, period: str) -> dict:
        data = self.api_client.safe_get(
            f"/dashboard/report/{period}",
            {
                "period": period,
                "report_jobs_count": 0,
                "report_pages_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "unique_users": 0,
                "average_pages_per_job": 0.0,
                "period_points": [],
                "top_users": [],
                "totals": {},
            },
        )
        return data if isinstance(data, dict) else {}

    def get_clients(self) -> list[dict]:
        data = self.api_client.get("/users")
        return data if isinstance(data, list) else []

    def get_stations(self) -> list[dict]:
        data = self.api_client.safe_get("/stations", [])
        return data if isinstance(data, list) else []

    def get_print_jobs(self) -> list[dict]:
        data = self.api_client.safe_get("/print-jobs", [])
        return data if isinstance(data, list) else []

    def get_active_sessions(self) -> list[dict]:
        data = self.api_client.safe_get("/sessions/active", [])
        return data if isinstance(data, list) else []

    def create_client(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/users", payload)

    def create_station(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/stations", payload)

    def start_session(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/sessions/start", payload)

    def end_session(self, session_id: int) -> dict | None:
        return self.api_client.safe_post("/sessions/end", {"session_id": session_id})

    def create_print_job(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/print-jobs", payload)

    def get_quota_status(self, user_id: int) -> dict:
        data = self.api_client.get(f"/users/{user_id}/quota-status")
        return data if isinstance(data, dict) else {}

    def test_users_endpoint(self) -> tuple[bool, str]:
        """Aide l'UI admin à diagnostiquer clairement un problème de chargement."""

        try:
            data = self.api_client.get("/users")
        except ApiError as exc:
            return False, exc.message
        except Exception as exc:  # pragma: no cover - diagnostic UI only
            return False, str(exc)
        if not isinstance(data, list):
            return False, "La route /users a repondu avec un format inattendu."
        return True, f"{len(data)} utilisateur(s) recu(s) depuis l'API."

    def grant_bonus_pages(self, user_id: int, payload: dict) -> dict | None:
        return self.api_client.safe_post(f"/users/{user_id}/grant-bonus-pages", payload)

    def reset_user_password(self, user_id: int) -> dict | None:
        return self.api_client.safe_post(f"/users/{user_id}/reset-password", {})

    def export_report_csv(self, report: dict, destination: Path) -> None:
        """Exporte un rapport consolidé au format CSV pour l'équipe admin."""

        period_labels = {"daily": "Journalier", "monthly": "Mensuel", "yearly": "Annuel"}
        period = str(report.get("period") or "")
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        jobs_count = int(report.get("report_jobs_count") or 0)
        pages_count = int(report.get("report_pages_count") or 0)
        success_count = int(report.get("success_count") or 0)
        failed_count = int(report.get("failed_count") or 0)
        top_user = self._top_user(report.get("top_users", []))
        period_points = report.get("period_points", []) or [
            {
                "label": period_labels.get(period, period or "Non renseignee"),
                "jobs_count": jobs_count,
                "pages_count": pages_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "unique_users": report.get("unique_users", 0),
            }
        ]

        with destination.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "Vue",
                    "Genere le",
                    "Periode",
                    "Jobs",
                    "Pages",
                    "Reussies",
                    "Echecs",
                    "Taux de reussite",
                    "Moyenne pages/job",
                    "Usagers actifs",
                    "Total jobs",
                    "Total pages",
                    "Total reussies",
                    "Total echecs",
                    "Taux reussite total",
                    "Usagers actifs total",
                    "Top utilisateur",
                    "Top utilisateur email",
                    "Top utilisateur pages",
                    "Top utilisateur echecs",
                ]
            )
            for point in period_points:
                point_jobs = int(point.get("jobs_count") or 0)
                point_pages = int(point.get("pages_count") or 0)
                writer.writerow(
                    [
                        period_labels.get(period, period or "Non renseignee"),
                        generated_at,
                        point.get("label", ""),
                        point_jobs,
                        point_pages,
                        point.get("success_count", 0),
                        point.get("failed_count", 0),
                        self._format_rate(point.get("success_count", 0), point_jobs),
                        self._format_average(point_pages, point_jobs),
                        point.get("unique_users", 0),
                        jobs_count,
                        pages_count,
                        success_count,
                        failed_count,
                        self._format_rate(success_count, jobs_count),
                        report.get("unique_users", 0),
                        top_user.get("client_name", ""),
                        top_user.get("email", ""),
                        top_user.get("pages_count", 0),
                        top_user.get("failed_count", 0),
                    ]
                )

    def export_jobs_csv(self, jobs: list[dict], destination: Path) -> None:
        """Exporte l'historique détaillé des impressions."""

        with destination.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "ID job",
                    "Document",
                    "Client",
                    "Poste",
                    "Pages",
                    "Statut",
                    "Demarche",
                    "Demande le",
                    "Imprime le",
                ]
            )
            for job in jobs:
                writer.writerow(
                    [
                        job.get("id", ""),
                        job.get("document_name", ""),
                        job.get("client_name", ""),
                        job.get("station_code", ""),
                        job.get("page_count", 0),
                        job.get("status", ""),
                        job.get("administrative_context", ""),
                        job.get("submitted_at", ""),
                        job.get("printed_at", ""),
                    ]
                )

    def _format_rate(self, numerator: object, denominator: object) -> str:
        denominator_int = int(denominator or 0)
        if denominator_int <= 0:
            return "0%"
        return f"{round((int(numerator or 0) / denominator_int) * 100, 1)}%"

    def _format_average(self, numerator: object, denominator: object) -> str:
        denominator_int = int(denominator or 0)
        if denominator_int <= 0:
            return "0"
        return str(round(int(numerator or 0) / denominator_int, 2))

    def _build_user_reading(self, user: dict) -> str:
        pages = int(user.get("pages_count") or 0)
        failed = int(user.get("failed_count") or 0)
        if failed:
            return f"{pages} page(s), {failed} echec(s) a verifier"
        return f"{pages} page(s), aucun echec"

    def _top_user(self, users: object) -> dict:
        if not isinstance(users, list):
            return {}
        return max(users, key=lambda user: int(user.get("pages_count") or 0), default={})
