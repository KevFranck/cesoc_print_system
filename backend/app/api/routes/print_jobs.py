from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.print_job import PrintJobCreate, PrintJobRead
from app.services.print_job_service import PrintJobService

router = APIRouter()


@router.post("", response_model=PrintJobRead, status_code=status.HTTP_201_CREATED)
def create_print_job(payload: PrintJobCreate, db: Session = Depends(get_db)) -> PrintJobRead:
    return PrintJobService(db).create_print_job(payload)


@router.get("", response_model=list[PrintJobRead])
def list_print_jobs(db: Session = Depends(get_db)) -> list[PrintJobRead]:
    return PrintJobService(db).list_jobs()


@router.get("/today", response_model=list[PrintJobRead])
def list_today_print_jobs(db: Session = Depends(get_db)) -> list[PrintJobRead]:
    return PrintJobService(db).list_today_jobs()
