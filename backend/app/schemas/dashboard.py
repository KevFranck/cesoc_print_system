from __future__ import annotations

from typing import Literal

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


class DashboardPeriodPoint(BaseModel):
    label: str
    jobs_count: int
    pages_count: int
    success_count: int
    failed_count: int
    unique_users: int


class DashboardTopUser(BaseModel):
    user_id: int
    client_name: str
    email: str | None = None
    jobs_count: int
    pages_count: int
    failed_count: int


class DashboardReport(BaseModel):
    period: Literal["daily", "monthly", "yearly"]
    totals: DashboardSummary
    report_jobs_count: int
    report_pages_count: int
    success_count: int
    failed_count: int
    unique_users: int
    average_pages_per_job: float
    period_points: list[DashboardPeriodPoint]
    top_users: list[DashboardTopUser]
