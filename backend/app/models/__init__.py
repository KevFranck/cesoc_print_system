"""SQLAlchemy models.

Importer les modules ici permet à Alembic et à SQLAlchemy de découvrir toutes
les tables à partir d'un seul point central.
"""

from app.models import admin_user, app_setting, bonus_page_grant, client, imported_document, print_job, station, station_session

__all__ = [
    "admin_user",
    "app_setting",
    "bonus_page_grant",
    "client",
    "imported_document",
    "print_job",
    "station",
    "station_session",
]
