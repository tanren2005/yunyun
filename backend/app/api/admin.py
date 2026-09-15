from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.database import get_db
from app.models import (
    Attachment,
    BookComment,
    BookShare,
    Comment,
    Moment,
    MomentComment,
    Notification,
    Post,
    User,
)
from app.schemas import AdminUserOut, AdminUserUpdate, MessageOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    query = db.query(User)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(User.username.ilike(like), User.email.ilike(like), User.display_name.ilike(like))
        )
    return query.order_by(User.id.desc()).offset(skip).limit(limit).all()


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.id == admin.id and body.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用自己")
    if user.id == admin.id and body.is_admin is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消自己的管理员")

    if body.is_active is not None:
        user.is_active = body.is_active
        if not body.is_active:
            user.session_version = int(user.session_version or 0) + 1
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    if body.display_name is not None:
        user.display_name = body.display_name.strip()
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/kick", response_model=MessageOut)
def kick_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.session_version = int(user.session_version or 0) + 1
    db.commit()
    return MessageOut(message="已强制下线")


@router.delete("/users/{user_id}", response_model=MessageOut)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己")

    uid = user.id
    db.query(Notification).filter(
        or_(Notification.user_id == uid, Notification.actor_id == uid)
    ).delete(synchronize_session=False)

    db.query(Comment).filter(Comment.author_id == uid).delete(synchronize_session=False)

    post_ids = [p.id for p in db.query(Post.id).filter(Post.author_id == uid).all()]
    if post_ids:
        db.query(Attachment).filter(
            Attachment.owner_kind == "post", Attachment.owner_id.in_(post_ids)
        ).delete(synchronize_session=False)
        db.query(Comment).filter(Comment.post_id.in_(post_ids)).delete(synchronize_session=False)
        db.query(Post).filter(Post.author_id == uid).delete(synchronize_session=False)

    moment_ids = [m.id for m in db.query(Moment.id).filter(Moment.author_id == uid).all()]
    db.query(MomentComment).filter(MomentComment.author_id == uid).delete(synchronize_session=False)
    if moment_ids:
        db.query(Attachment).filter(
            Attachment.owner_kind == "moment", Attachment.owner_id.in_(moment_ids)
        ).delete(synchronize_session=False)
        db.query(MomentComment).filter(MomentComment.moment_id.in_(moment_ids)).delete(
            synchronize_session=False
        )
        db.query(Moment).filter(Moment.author_id == uid).delete(synchronize_session=False)

    book_ids = [b.id for b in db.query(BookShare.id).filter(BookShare.author_id == uid).all()]
    db.query(BookComment).filter(BookComment.author_id == uid).delete(synchronize_session=False)
    if book_ids:
        db.query(Attachment).filter(
            Attachment.owner_kind == "book", Attachment.owner_id.in_(book_ids)
        ).delete(synchronize_session=False)
        db.query(BookComment).filter(BookComment.book_id.in_(book_ids)).delete(synchronize_session=False)
        db.query(BookShare).filter(BookShare.author_id == uid).delete(synchronize_session=False)

    db.query(Attachment).filter(Attachment.uploader_id == uid).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return MessageOut(message="用户及其内容已永久删除")
