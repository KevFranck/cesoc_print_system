from __future__ import annotations

from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.print_job import PrintJob
from app.models.station import Station
from app.models.station_session import StationSession
from app.schemas.dashboard import DashboardSummary


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self) -> DashboardSummary:
        total_clients = int(self.db.scalar(select(func.count(Client.id))) or 0)
        free_stations = int(self.db.scalar(select(func.count(Station.id)).where(Station.status == "available")) or 0)
        offline_stations = int(self.db.scalar(select(func.count(Station.id)).where(Station.status == "offline")) or 0)
        occupied_stations = int(self.db.scalar(select(func.count(Station.id)).where(Station.status == "occupied")) or 0)
        active_sessions = int(
            self.db.scalar(select(func.count(StationSession.id)).where(StationSession.status == "active")) or 0
        )
        now = datetime.now(timezone.utc)
        day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        prints_today = int(
            self.db.scalar(
                select(func.count(PrintJob.id)).where(
                    PrintJob.submitted_at >= day_start, PrintJob.submitted_at <= day_end
                )
            )
            or 0
        )
        pages_today = int(
            self.db.scalar(
                select(func.coalesce(func.sum(PrintJob.page_count), 0)).where(
                    PrintJob.submitted_at >= day_start, PrintJob.submitted_at <= day_end
                )
            )
            or 0
        )
        quota_alert_clients = int(
            self.db.scalar(
                select(func.count(Client.id)).where(
                    Client.id.in_(
                        select(PrintJob.client_id)
                        .where(PrintJob.submitted_at >= day_start, PrintJob.submitted_at <= day_end)
                        .group_by(PrintJob.client_id)
                        .having(func.sum(PrintJob.page_count) >= 8)
                    )
                )
            )
            or 0
        )

        return DashboardSummary(
            total_clients=total_clients,
            free_stations=free_stations,
            active_sessions=active_sessions,
            prints_today=prints_today,
            pages_today=pages_today,
            offline_stations=offline_stations,
            occupied_stations=occupied_stations,
            quota_alert_clients=quota_alert_clients,
        )
