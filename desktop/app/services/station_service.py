from __future__ import annotations

from app.services.api_client import ApiClient
from app.services.config_service import ClientStationConfig


class ClientStationService:
    def __init__(self, api_client: ApiClient, config: ClientStationConfig) -> None:
        self.api_client = api_client
        self.config = config

    def get_station(self) -> dict:
        data = self.api_client.safe_get(
            f"/stations/{self.config.station_code}",
            {
                "code": self.config.station_code,
                "name": self.config.station_code,
                "status": "offline",
                "location": "Non configure",
            },
        )
        return data if isinstance(data, dict) else {}

    def get_active_session(self) -> dict | None:
        data = self.api_client.safe_get(f"/stations/{self.config.station_code}/active-session", None)
        return data if isinstance(data, dict) else None

    def get_remaining_pages(self, client_id: int) -> dict:
        data = self.api_client.safe_get(
            f"/clients/{client_id}/remaining-pages",
            {"remaining_pages": 0, "daily_quota": 10, "used_pages_today": 0, "client_id": client_id},
        )
        return data if isinstance(data, dict) else {}
