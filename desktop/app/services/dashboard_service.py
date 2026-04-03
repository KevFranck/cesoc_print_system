from __future__ import annotations

import csv
from pathlib import Path

from app.services.api_client import ApiClient


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
        data = self.api_client.safe_get("/users", [])
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
        data = self.api_client.safe_get(f"/users/{user_id}/quota-status", {})
        return data if isinstance(data, dict) else {}

    def grant_bonus_pages(self, user_id: int, payload: dict) -> dict | None:
        return self.api_client.safe_post(f"/users/{user_id}/grant-bonus-pages", payload)

    def export_report_csv(self, report: dict, destination: Path) -> None:
        """Exporte un rapport consolidé au format CSV pour l'équipe admin."""

        with destination.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["period", report.get("period", "")])
            writer.writerow(["report_jobs_count", report.get("report_jobs_count", 0)])
            writer.writerow(["report_pages_count", report.get("report_pages_count", 0)])
            writer.writerow(["success_count", report.get("success_count", 0)])
            writer.writerow(["failed_count", report.get("failed_count", 0)])
            writer.writerow(["unique_users", report.get("unique_users", 0)])
            writer.writerow(["average_pages_per_job", report.get("average_pages_per_job", 0.0)])
            writer.writerow([])
            writer.writerow(["PERIOD_POINTS"])
            writer.writerow(["label", "jobs_count", "pages_count", "success_count", "failed_count", "unique_users"])
            for point in report.get("period_points", []):
                writer.writerow(
                    [
                        point.get("label", ""),
                        point.get("jobs_count", 0),
                        point.get("pages_count", 0),
                        point.get("success_count", 0),
                        point.get("failed_count", 0),
                        point.get("unique_users", 0),
                    ]
                )
            writer.writerow([])
            writer.writerow(["TOP_USERS"])
            writer.writerow(["user_id", "client_name", "email", "jobs_count", "pages_count", "failed_count"])
            for user in report.get("top_users", []):
                writer.writerow(
                    [
                        user.get("user_id", 0),
                        user.get("client_name", ""),
                        user.get("email", ""),
                        user.get("jobs_count", 0),
                        user.get("pages_count", 0),
                        user.get("failed_count", 0),
                    ]
                )

    def export_jobs_csv(self, jobs: list[dict], destination: Path) -> None:
        """Exporte l'historique détaillé des impressions."""

        with destination.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "id",
                    "document_name",
                    "client_name",
                    "station_code",
                    "page_count",
                    "status",
                    "administrative_context",
                    "submitted_at",
                    "printed_at",
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
