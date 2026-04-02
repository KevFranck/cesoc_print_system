from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.admin_user import AdminUser
from app.models.app_setting import AppSetting


def init_db(db: Session) -> None:
    if not db.query(AdminUser).filter(AdminUser.username == settings.default_admin_username).first():
        db.add(
            AdminUser(
                username=settings.default_admin_username,
                full_name="Administrateur CESOC",
                hashed_password=hash_password(settings.default_admin_password),
            )
        )

    default_settings = {
        "daily_quota": (str(settings.default_daily_quota), "Quota quotidien par client"),
        "print_mode": ("supervised", "Mode de supervision des impressions"),
    }

    for key, (value, description) in default_settings.items():
        exists = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not exists:
            db.add(AppSetting(key=key, value=value, description=description))

    db.commit()
