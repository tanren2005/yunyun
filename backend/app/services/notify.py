from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import Notification

TZ = ZoneInfo("Asia/Shanghai")


def push(
    db: Session,
    *,
    user_id: int,
    actor_id: int | None,
    kind: str,
    title: str,
    body: str = "",
    link: str = "",
) -> None:
    if actor_id is not None and actor_id == user_id:
        return
    db.add(
        Notification(
            user_id=user_id,
            actor_id=actor_id,
            kind=kind,
            title=title,
            body=body[:500],
            link=link,
            is_read=False,
        )
    )
