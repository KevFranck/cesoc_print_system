from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import clients, dashboard, documents, print_jobs, sessions, stations, users

api_router = APIRouter()
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stations.router, prefix="/stations", tags=["stations"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(print_jobs.router, prefix="/print-jobs", tags=["print-jobs"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
