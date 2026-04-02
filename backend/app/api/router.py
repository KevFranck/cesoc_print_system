from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import clients, dashboard, print_jobs, sessions, stations

api_router = APIRouter()
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(stations.router, prefix="/stations", tags=["stations"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(print_jobs.router, prefix="/print-jobs", tags=["print-jobs"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
