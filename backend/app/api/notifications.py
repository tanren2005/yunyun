from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Notification, User
from app.schemas import MessageOut, NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read.is_(False))
        .count()
    )
    return UnreadCountOut(count=n)


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/read-all", response_model=MessageOut)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
    return MessageOut(message="已全部标为已读")


@router.post("/{nid}/read", response_model=MessageOut)
def read_one(nid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(Notification, nid)
    if row and row.user_id == user.id:
        row.is_read = True
        db.commit()
    return MessageOut(message="ok")
