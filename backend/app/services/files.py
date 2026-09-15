import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.models import Attachment

ALLOWED_EXT = {
    ".txt",
    ".md",
    ".pdf",
    ".doc",
    ".docx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".mp4",
    ".webm",
    ".mov",
    ".mp3",
    ".wav",
    ".m4a",
}

TEXT_EXT = {".txt", ".md"}
DOCX_EXT = {".docx"}


def upload_root() -> Path:
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ext_of(name: str) -> str:
    return Path(name or "").suffix.lower()


def save_upload(file: UploadFile) -> tuple[str, str, str, int]:
    settings = get_settings()
    original = Path(file.filename or "unnamed").name
    ext = ext_of(original)
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{ext or '未知'}。可用 txt/md/doc/docx/pdf、图片、音视频",
        )

    data = file.file.read()
    if not data:
        try:
            file.file.seek(0)
            data = file.file.read()
        except Exception:
            data = b""
    size = len(data)
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"「{original}」是空文件（0 字节）。请先在编辑器里保存内容，再重新选择上传。",
        )
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，上限 {settings.max_upload_mb} MB",
        )

    stored = f"{uuid.uuid4().hex}{ext}"
    dest = upload_root() / stored
    dest.write_bytes(data)
    mime = file.content_type or "application/octet-stream"
    return original, stored, mime, size


def extract_text(stored_name: str) -> str:
    path = upload_root() / stored_name
    ext = ext_of(stored_name)
    if ext in TEXT_EXT:
        raw = path.read_bytes()
        for enc in ("utf-8", "gb18030", "utf-16"):
            try:
                return raw.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        return ""
    if ext in DOCX_EXT:
        try:
            from docx import Document

            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception:
            return ""
    return ""


def public_url(stored_name: str) -> str:
    return f"/uploads/{stored_name}"


def to_out(item: Attachment) -> dict:
    ext = ext_of(item.original_name or item.stored_name)
    kind = "file"
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        kind = "image"
    elif ext in {".mp4", ".webm", ".mov"}:
        kind = "video"
    elif ext in {".mp3", ".wav", ".m4a"}:
        kind = "audio"
    elif ext in {".txt", ".md", ".pdf", ".doc", ".docx"}:
        kind = "document"
    return {
        "id": item.id,
        "original_name": item.original_name,
        "url": public_url(item.stored_name),
        "mime": item.mime,
        "size": item.size,
        "kind": kind,
    }


def map_for(db, owner_kind: str, owner_ids: list[int]) -> dict[int, list[dict]]:
    if not owner_ids:
        return {}
    rows = (
        db.query(Attachment)
        .filter(Attachment.owner_kind == owner_kind, Attachment.owner_id.in_(owner_ids))
        .order_by(Attachment.id.asc())
        .all()
    )
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row.owner_id, []).append(to_out(row))
    return grouped


def safe_filename_note(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()
