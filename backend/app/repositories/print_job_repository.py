from __future__ import annotations

from datetime import datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.print_job import PrintJob
from app.repositories.base import BaseRepository


class PrintJobRepository(BaseRepository):
    def create(self, job: PrintJob) -> PrintJob:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_all(self) -> list[PrintJob]:
        stmt = (
            select(PrintJob)
            .options(
                selectinload(PrintJob.client),
                selectinload(PrintJob.station),
                selectinload(PrintJob.session),
            )
            .order_by(PrintJob.submitted_at.desc())
        )
        return list(self.db.scalars(stmt))

    def list_today(self) -> list[PrintJob]:
        now = datetime.now(timezone.utc)
        day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        stmt = (
            select(PrintJob)
            .options(
                selectinload(PrintJob.client),
                selectinload(PrintJob.station),
                selectinload(PrintJob.session),
            )
            .where(PrintJob.submitted_at >= day_start)
            .where(PrintJob.submitted_at <= day_end)
            .order_by(PrintJob.submitted_at.desc())
        )
        return list(self.db.scalars(stmt))
