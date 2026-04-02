from __future__ import annotations

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_clients: int
    free_stations: int
    active_sessions: int
    prints_today: int
    pages_today: int
    offline_stations: int
    occupied_stations: int
    quota_alert_clients: int
