from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Attachment, BookShare, Moment, Post, User
from app.services import files as file_service

router = APIRouter(tags=["files"])

OWNERS = {
    "post": Post,
    "posts": Post,
    "moment": Moment,
    "moments": Moment,
    "book": BookShare,
    "books": BookShare,
}

CANON = {
    "post": "post",
    "posts": "post",
    "moment": "moment",
    "moments": "moment",
    "book": "book",
    "books": "book",
}


def _get_owned(db: Session, kind: str, owner_id: int, user: User):
    model = OWNERS.get(kind)
    if not model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未知的附件类型")
    obj = db.get(model, owner_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对象不存在")
    if obj.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能给自己的内容上传附件")
    return obj


@router.post("/{kind}/{owner_id}/files")
def upload_files(
    kind: str,
    owner_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _get_owned(db, kind, owner_id, user)
    canon = CANON.get(kind, kind)
    settings = get_settings()
    existing = db.query(Attachment).filter(Attachment.owner_kind == canon, Attachment.owner_id == owner_id).count()
    if existing + len(files) > settings.max_files_per_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"每个条目最多 {settings.max_files_per_item} 个附件",
        )

    saved = []
    extracted_chunks: list[str] = []
    for f in files:
        original, stored, mime, size = file_service.save_upload(f)
        row = Attachment(
            owner_kind=canon,
            owner_id=owner_id,
            uploader_id=user.id,
            original_name=original,
            stored_name=stored,
            mime=mime,
            size=size,
        )
        db.add(row)
        db.flush()
        text = file_service.extract_text(stored)
        if text:
            extracted_chunks.append(f"【来自文件 {original}】\n{text}")
        saved.append(file_service.to_out(row))

    if canon == "post" and extracted_chunks and isinstance(obj, Post) and not (obj.content or "").strip():
        obj.content = "\n\n".join(extracted_chunks)[:100000]
        if not obj.summary:
            obj.summary = obj.content.replace("\n", " ")[:120]

    db.commit()
    return {"files": saved}
