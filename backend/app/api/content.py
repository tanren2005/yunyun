from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Attachment, Category, Comment, Post, User
from app.schemas import (
    CategoryOut,
    CommentCreate,
    CommentOut,
    MessageOut,
    PostCreate,
    PostListItem,
    PostOut,
    PostUpdate,
)
from app.services import files as file_service
from app.services import notify as notify_service

router = APIRouter(tags=["content"])


def _can_moderate(user: User, author_id: int) -> bool:
    return bool(user.is_admin) or user.id == author_id


def _delete_comment_subtree(db: Session, root_id: int) -> int:
    """删除评论及其全部回复，返回删除条数。"""
    ids = [root_id]
    changed = True
    while changed:
        changed = False
        kids = db.query(Comment.id).filter(Comment.parent_id.in_(ids)).all()
        for (kid,) in kids:
            if kid not in ids:
                ids.append(kid)
                changed = True
    db.query(Comment).filter(Comment.id.in_(ids)).delete(synchronize_session=False)
    return len(ids)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.sort_order, Category.id).all()


@router.get("/posts", response_model=list[PostListItem])
def list_posts(
    category: str | None = Query(default=None, description="栏目 slug"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    q = db.query(Post).options(joinedload(Post.author), joinedload(Post.category))
    if category:
        q = q.join(Category).filter(Category.slug == category)
    posts = q.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    atts = file_service.map_for(db, "post", [p.id for p in posts])
    items = []
    for p in posts:
        item = PostListItem.model_validate(p)
        item.has_files = bool(atts.get(p.id))
        items.append(item)
    return items


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.category))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    post.view_count += 1
    db.commit()
    db.refresh(post)
    out = PostOut.model_validate(post)
    out.attachments = file_service.map_for(db, "post", [post.id]).get(post.id, [])
    return out


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.get(Category, body.category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="栏目不存在")

    text = (body.content or "").strip()
    summary = body.summary.strip() or text.replace("\n", " ")[:120]
    post = Post(
        title=body.title.strip(),
        content=body.content or "",
        summary=summary,
        author_id=user.id,
        category_id=body.category_id,
    )
    db.add(post)
    db.commit()
    post = (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.category))
        .filter(Post.id == post.id)
        .one()
    )
    out = PostOut.model_validate(post)
    out.attachments = []
    return out


@router.patch("/posts/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    body: PostUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    if post.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能编辑自己的作品")

    if body.title is not None:
        post.title = body.title.strip()
    if body.content is not None:
        post.content = body.content
    if body.summary is not None:
        post.summary = body.summary.strip()
    if body.category_id is not None:
        if not db.get(Category, body.category_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="栏目不存在")
        post.category_id = body.category_id

    db.commit()
    post = (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.category))
        .filter(Post.id == post_id)
        .one()
    )
    out = PostOut.model_validate(post)
    out.attachments = file_service.map_for(db, "post", [post.id]).get(post.id, [])
    return out


@router.delete("/posts/{post_id}", response_model=MessageOut)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    if not _can_moderate(user, post.author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该作品")
    db.query(Attachment).filter(
        Attachment.owner_kind == "post", Attachment.owner_id == post_id
    ).delete(synchronize_session=False)
    db.query(Comment).filter(Comment.post_id == post_id).delete(synchronize_session=False)
    db.delete(post)
    db.commit()
    return MessageOut(message="已删除")


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    if not db.get(Post, post_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    return (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    if body.parent_id is not None:
        parent = db.get(Comment, body.parent_id)
        if not parent or parent.post_id != post_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="回复的评论不存在")

    comment = Comment(
        post_id=post_id,
        author_id=user.id,
        parent_id=body.parent_id,
        content=body.content.strip(),
    )
    post.comment_count += 1
    db.add(comment)

    target_id = post.author_id
    note = f"{user.display_name} 评论了你的作品《{post.title}》"
    if body.parent_id is not None:
        parent = db.get(Comment, body.parent_id)
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
        link=f"/posts/{post_id}",
    )
    db.commit()
    comment = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.id == comment.id)
        .one()
    )
    return comment


@router.delete("/posts/{post_id}/comments/{comment_id}", response_model=MessageOut)
def delete_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
    comment = db.get(Comment, comment_id)
    if not comment or comment.post_id != post_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if not _can_moderate(user, comment.author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该评论")
    removed = _delete_comment_subtree(db, comment_id)
    post.comment_count = max(0, int(post.comment_count or 0) - removed)
    db.commit()
    return MessageOut(message="评论已删除")
