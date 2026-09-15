from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Attachment, BookComment, BookShare, Moment, MomentComment, User
from app.schemas import (
    BookCreate,
    BookOut,
    CommentCreate,
    CommentOut,
    DailyOut,
    MessageOut,
    MomentCreate,
    MomentOut,
)
from app.services import daily as daily_service
from app.services import files as file_service
from app.services import notify as notify_service
from app.services.daily import KIND_LABEL

router = APIRouter(tags=["community"])


def _can_moderate(user: User, author_id: int) -> bool:
    return bool(user.is_admin) or user.id == author_id


def _delete_moment_comment_subtree(db: Session, root_id: int) -> int:
    ids = [root_id]
    changed = True
    while changed:
        changed = False
        kids = db.query(MomentComment.id).filter(MomentComment.parent_id.in_(ids)).all()
        for (kid,) in kids:
            if kid not in ids:
                ids.append(kid)
                changed = True
    db.query(MomentComment).filter(MomentComment.id.in_(ids)).delete(synchronize_session=False)
    return len(ids)


def _delete_book_comment_subtree(db: Session, root_id: int) -> int:
    ids = [root_id]
    changed = True
    while changed:
        changed = False
        kids = db.query(BookComment.id).filter(BookComment.parent_id.in_(ids)).all()
        for (kid,) in kids:
            if kid not in ids:
                ids.append(kid)
                changed = True
    db.query(BookComment).filter(BookComment.id.in_(ids)).delete(synchronize_session=False)
    return len(ids)


def _moment_out(db: Session, moment: Moment) -> MomentOut:
    out = MomentOut.model_validate(moment)
    out.attachments = file_service.map_for(db, "moment", [moment.id]).get(moment.id, [])
    return out


def _book_out(db: Session, book: BookShare) -> BookOut:
    out = BookOut.model_validate(book)
    out.attachments = file_service.map_for(db, "book", [book.id]).get(book.id, [])
    return out


@router.get("/daily", response_model=DailyOut)
def get_daily(db: Session = Depends(get_db)):
    row = daily_service.ensure_current(db)
    return DailyOut(
        id=row.id,
        day=row.day,
        kind=row.kind,
        kind_label=KIND_LABEL.get(row.kind, row.kind),
        title=row.title,
        body=row.body,
        source=row.source,
        note=getattr(row, "note", "") or "",
    )


@router.get("/daily/history", response_model=list[DailyOut])
def daily_history(limit: int = Query(60, ge=1, le=120), db: Session = Depends(get_db)):
    rows = daily_service.list_recent(db, limit=limit)
    return [
        DailyOut(
            id=r.id,
            day=r.day,
            kind=r.kind,
            kind_label=KIND_LABEL.get(r.kind, r.kind),
            title=r.title,
            body=r.body,
            source=r.source,
            note=getattr(r, "note", "") or "",
        )
        for r in rows
    ]


@router.get("/moments", response_model=list[MomentOut])
def list_moments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Moment)
        .options(joinedload(Moment.author))
        .order_by(Moment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_moment_out(db, m) for m in rows]


@router.post("/moments", response_model=MomentOut, status_code=status.HTTP_201_CREATED)
def create_moment(
    body: MomentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not (body.content or "").strip():
        # 允许稍后上传文件，先建一条空动态
        pass
    moment = Moment(author_id=user.id, content=(body.content or "").strip())
    db.add(moment)
    db.commit()
    moment = db.query(Moment).options(joinedload(Moment.author)).filter(Moment.id == moment.id).one()
    return _moment_out(db, moment)


@router.delete("/moments/{moment_id}", response_model=MessageOut)
def delete_moment(
    moment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    moment = db.get(Moment, moment_id)
    if not moment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="动态不存在")
    if not _can_moderate(user, moment.author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该动态")
    db.query(Attachment).filter(
        Attachment.owner_kind == "moment", Attachment.owner_id == moment_id
    ).delete(synchronize_session=False)
    db.query(MomentComment).filter(MomentComment.moment_id == moment_id).delete(
        synchronize_session=False
    )
    db.delete(moment)
    db.commit()
    return MessageOut(message="已删除")


@router.get("/moments/{moment_id}/comments", response_model=list[CommentOut])
def list_moment_comments(moment_id: int, db: Session = Depends(get_db)):
    if not db.get(Moment, moment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="动态不存在")
    return (
        db.query(MomentComment)
        .options(joinedload(MomentComment.author))
        .filter(MomentComment.moment_id == moment_id)
        .order_by(MomentComment.created_at.asc())
        .all()
    )


@router.post("/moments/{moment_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_moment_comment(
    moment_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    moment = db.get(Moment, moment_id)
    if not moment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="动态不存在")
    if body.parent_id is not None:
        parent = db.get(MomentComment, body.parent_id)
        if not parent or parent.moment_id != moment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="回复的评论不存在")

    comment = MomentComment(
        moment_id=moment_id,
        author_id=user.id,
        parent_id=body.parent_id,
        content=body.content.strip(),
    )
    moment.comment_count += 1
    db.add(comment)

    target_id = moment.author_id
    note = f"{user.display_name} 回应了你的云间动态"
    if body.parent_id is not None:
        parent = db.get(MomentComment, body.parent_id)
        if parent:
            target_id = parent.author_id
            note = f"{user.display_name} 回复了你的评论"
    notify_service.push(
        db,
        user_id=target_id,
        actor_id=user.id,
        kind="reply",
        title=note,
        body=body.content.strip()[:120],
        link="/moments",
    )
    db.commit()
    return (
        db.query(MomentComment)
        .options(joinedload(MomentComment.author))
        .filter(MomentComment.id == comment.id)
        .one()
    )


@router.delete("/moments/{moment_id}/comments/{comment_id}", response_model=MessageOut)
def delete_moment_comment(
    moment_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    moment = db.get(Moment, moment_id)
    if not moment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="动态不存在")
    comment = db.get(MomentComment, comment_id)
    if not comment or comment.moment_id != moment_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if not _can_moderate(user, comment.author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该评论")
    removed = _delete_moment_comment_subtree(db, comment_id)
    moment.comment_count = max(0, int(moment.comment_count or 0) - removed)
    db.commit()
    return MessageOut(message="评论已删除")


@router.get("/books", response_model=list[BookOut])
def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(BookShare)
        .options(joinedload(BookShare.author))
        .order_by(BookShare.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_book_out(db, b) for b in rows]


@router.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookShare).options(joinedload(BookShare.author)).filter(BookShare.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享不存在")
    return _book_out(db, book)


@router.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(
    body: BookCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = BookShare(
        author_id=user.id,
        book_title=body.book_title.strip(),
        book_author=body.book_author.strip(),
        content=body.content.strip(),
    )
    db.add(book)
    db.commit()
    book = db.query(BookShare).options(joinedload(BookShare.author)).filter(BookShare.id == book.id).one()
    return _book_out(db, book)


@router.delete("/books/{book_id}", response_model=MessageOut)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(BookShare, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享不存在")
    if not _can_moderate(user, book.author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该分享")
    db.query(Attachment).filter(
        Attachment.owner_kind == "book", Attachment.owner_id == book_id
    ).delete(synchronize_session=False)
    db.query(BookComment).filter(BookComment.book_id == book_id).delete(synchronize_session=False)
    db.delete(book)
    db.commit()
    return MessageOut(message="已删除")


@router.get("/books/{book_id}/comments", response_model=list[CommentOut])
def list_book_comments(book_id: int, db: Session = Depends(get_db)):
    if not db.get(BookShare, book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享不存在")
    return (
        db.query(BookComment)
        .options(joinedload(BookComment.author))
        .filter(BookComment.book_id == book_id)
        .order_by(BookComment.created_at.asc())
        .all()
    )


@router.post("/books/{book_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_book_comment(
    book_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(BookShare, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享不存在")
    if body.parent_id is not None:
        parent = db.get(BookComment, body.parent_id)
        if not parent or parent.book_id != book_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="回复的评论不存在")

    comment = BookComment(
        book_id=book_id,
        author_id=user.id,
        parent_id=body.parent_id,
        content=body.content.strip(),
    )
    book.comment_count += 1
    db.add(comment)

    target_id = book.author_id
    note = f"{user.display_name} 评论了你的云友会分享《{book.book_title}》"
    if body.parent_id is not None:
        parent = db.get(BookComment, body.parent_id)
        if parent:
            target_id = parent.author_id
            note = f"{user.display_name} 回复了你的评论"
    notify_service.push(
        db,
        user_id=target_id,
        actor_id=user.id,
        kind="reply",
        title=note,
        body=body.content.strip()[:120],
        link="/club",
    )
    db.commit()
    return (
        db.query(BookComment)
        .options(joinedload(BookComment.author))
        .filter(BookComment.id == comment.id)
        .one()
    )


@router.delete("/books/{book_id}/comments/{comment_id}", response_model=MessageOut)
def delete_book_comment(
    book_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(BookShare, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享不存在")
    comment = db.get(BookComment, comment_id)
    if not comment or comment.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if not _can_moderate(user, comment.author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该评论")
    removed = _delete_book_comment_subtree(db, comment_id)
    book.comment_count = max(0, int(book.comment_count or 0) - removed)
    db.commit()
    return MessageOut(message="评论已删除")
