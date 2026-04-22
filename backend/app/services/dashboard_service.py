from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.print_job import PrintJob
from app.models.station import Station
from app.models.station_session import StationSession
from app.schemas.dashboard import DashboardPeriodPoint, DashboardReport, DashboardSummary, DashboardTopUser


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
                    PrintJob.status == "printed",
                    PrintJob.submitted_at >= day_start,
                    PrintJob.submitted_at <= day_end,
                )
            )
            or 0
        )
        quota_alert_clients = int(
            self.db.scalar(
                select(func.count(Client.id)).where(
                    Client.id.in_(
                        select(PrintJob.client_id)
                        .where(
                            PrintJob.status == "printed",
                            PrintJob.submitted_at >= day_start,
                            PrintJob.submitted_at <= day_end,
                        )
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

    def get_report(self, period: str) -> DashboardReport:
        """Construit un rapport agrégé pour l'admin.

        Pour ce MVP, l'agrégation est faite côté service Python. Cela reste
        lisible, facile à faire évoluer et largement suffisant pour les volumes
        attendus d'un centre local.
        """

        if period not in {"daily", "monthly", "yearly"}:
            period = "daily"

        period_start, period_end = self._period_bounds(period)
        jobs = self._get_report_jobs(period_start, period_end)
        grouped_metrics: dict[str, dict[str, int | set[int]]] = defaultdict(
            lambda: {
                "jobs_count": 0,
                "pages_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "unique_users": set(),
            }
        )
        users_metrics: dict[int, dict[str, int | str | None]] = defaultdict(
            lambda: {
                "user_id": 0,
                "client_name": "Utilisateur inconnu",
                "email": None,
                "jobs_count": 0,
                "pages_count": 0,
                "failed_count": 0,
            }
        )

        total_jobs = 0
        total_pages = 0
        success_count = 0
        failed_count = 0
        unique_users: set[int] = set()

        for job in jobs:
            label = self._build_period_label(job.submitted_at, period)
            metrics = grouped_metrics[label]
            metrics["jobs_count"] = int(metrics["jobs_count"]) + 1
            metrics["pages_count"] = int(metrics["pages_count"]) + int(job.page_count)
            if job.status == "printed":
                metrics["success_count"] = int(metrics["success_count"]) + 1
                success_count += 1
            if job.status == "failed":
                metrics["failed_count"] = int(metrics["failed_count"]) + 1
                failed_count += 1
            unique_bucket = metrics["unique_users"]
            if isinstance(unique_bucket, set):
                unique_bucket.add(job.client_id)

            total_jobs += 1
            total_pages += int(job.page_count)
            unique_users.add(job.client_id)

            user_metrics = users_metrics[job.client_id]
            user_metrics["user_id"] = job.client_id
            user_metrics["client_name"] = (
                f"{job.client.first_name} {job.client.last_name}" if job.client else "Utilisateur inconnu"
            )
            user_metrics["email"] = job.client.email if job.client else None
            user_metrics["jobs_count"] = int(user_metrics["jobs_count"]) + 1
            user_metrics["pages_count"] = int(user_metrics["pages_count"]) + int(job.page_count)
            if job.status == "failed":
                user_metrics["failed_count"] = int(user_metrics["failed_count"]) + 1

        period_points = [
            DashboardPeriodPoint(
                label=label,
                jobs_count=int(metrics["jobs_count"]),
                pages_count=int(metrics["pages_count"]),
                success_count=int(metrics["success_count"]),
                failed_count=int(metrics["failed_count"]),
                unique_users=len(metrics["unique_users"]) if isinstance(metrics["unique_users"], set) else 0,
            )
            for label, metrics in sorted(grouped_metrics.items(), key=lambda item: item[0], reverse=True)
        ]

        top_users = sorted(
            (
                DashboardTopUser(
                    user_id=int(metrics["user_id"]),
                    client_name=str(metrics["client_name"]),
                    email=str(metrics["email"]) if metrics["email"] else None,
                    jobs_count=int(metrics["jobs_count"]),
                    pages_count=int(metrics["pages_count"]),
                    failed_count=int(metrics["failed_count"]),
                )
                for metrics in users_metrics.values()
            ),
            key=lambda item: (item.pages_count, item.jobs_count),
            reverse=True,
        )[:8]

        return DashboardReport(
            period=period,  # type: ignore[arg-type]
            totals=self.get_summary(),
            report_jobs_count=total_jobs,
            report_pages_count=total_pages,
            success_count=success_count,
            failed_count=failed_count,
            unique_users=len(unique_users),
            average_pages_per_job=round(total_pages / total_jobs, 2) if total_jobs else 0.0,
            period_points=period_points,
            top_users=top_users,
        )

    def _get_report_jobs(self, period_start: datetime, period_end: datetime) -> list[PrintJob]:
        stmt = (
            select(PrintJob)
            .options(selectinload(PrintJob.client))
            .where(PrintJob.submitted_at >= period_start, PrintJob.submitted_at <= period_end)
            .order_by(PrintJob.submitted_at.desc())
        )
        return list(self.db.scalars(stmt))

    def _build_period_label(self, submitted_at: datetime, period: str) -> str:
        current = submitted_at.astimezone(timezone.utc)
        if period == "yearly":
            return current.strftime("%Y-%m")
        if period == "monthly":
            return current.strftime("%Y-%m-%d")
        return current.strftime("%H:00")

    def _period_bounds(self, period: str) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        if period == "yearly":
            start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
            end = datetime(now.year, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
            return start, end
        if period == "monthly":
            start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            if now.month == 12:
                next_month = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                next_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
            return start, next_month.replace(microsecond=0) - timedelta(microseconds=1)
        day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        return day_start, day_end
