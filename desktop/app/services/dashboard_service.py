from __future__ import annotations

from app.services.api_client import ApiClient


class AdminDashboardService:
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

    def get_clients(self) -> list[dict]:
        data = self.api_client.safe_get("/clients", [])
        return data if isinstance(data, list) else []

    def get_stations(self) -> list[dict]:
        data = self.api_client.safe_get("/stations", [])
        return data if isinstance(data, list) else []

    def get_print_jobs(self) -> list[dict]:
        data = self.api_client.safe_get("/print-jobs/today", [])
        return data if isinstance(data, list) else []

    def get_active_sessions(self) -> list[dict]:
        data = self.api_client.safe_get("/sessions/active", [])
        return data if isinstance(data, list) else []

    def create_client(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/clients", payload)

    def create_station(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/stations", payload)

    def start_session(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/sessions/start", payload)

    def end_session(self, session_id: int) -> dict | None:
        return self.api_client.safe_post("/sessions/end", {"session_id": session_id})

    def create_print_job(self, payload: dict) -> dict | None:
        return self.api_client.safe_post("/print-jobs", payload)
