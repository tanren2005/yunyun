import random
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.data.daily_pool import POOL
from app.models import DailyReading

TZ = ZoneInfo("Asia/Shanghai")
KIND_LABEL = {
    "quote": "名句",
    "poem": "诗歌",
    "fiction": "云说",
    "essay": "云散",
    "prose": "云散",
}


def hour_slot() -> str:
    now = datetime.now(TZ)
    return now.strftime("%Y-%m-%d-%H")


def pick_random(exclude_title: str | None = None) -> dict:
    choices = [p for p in POOL if not exclude_title or p["title"] != exclude_title]
    if not choices:
        choices = POOL
    return random.choice(choices)


def _norm_title(title: str) -> str:
    return (title or "").replace("（节选）", "").replace("(节选)", "").strip()


def _pool_by_title() -> dict[str, dict]:
    return {_norm_title(p["title"]): p for p in POOL}


def refresh_row_from_pool(row: DailyReading) -> bool:
    """若词库有同名全文，则把库里的节选/旧稿同步成全文。"""
    piece = _pool_by_title().get(_norm_title(row.title))
    if not piece:
        return False
    changed = False
    if row.body != piece["body"]:
        row.body = piece["body"]
        changed = True
    if (row.note or "") != (piece.get("note") or ""):
        row.note = piece.get("note") or ""
        changed = True
    if row.source != piece["source"]:
        row.source = piece["source"]
        changed = True
    if row.kind != piece["kind"]:
        row.kind = piece["kind"]
        changed = True
    if row.title != piece["title"]:
        row.title = piece["title"]
        changed = True
    return changed


def ensure_current(db: Session) -> DailyReading:
    """每小时一篇；到点随机换新，同一小时内固定。"""
    slot = hour_slot()
    row = db.query(DailyReading).filter(DailyReading.day == slot).first()
    if row:
        if refresh_row_from_pool(row):
            db.commit()
            db.refresh(row)
        return row

    last = db.query(DailyReading).order_by(DailyReading.id.desc()).first()
    exclude = _norm_title(last.title) if last else None
    choices = [p for p in POOL if _norm_title(p["title"]) != exclude]
    piece = random.choice(choices or POOL)
    row = DailyReading(
        day=slot,
        kind=piece["kind"],
        title=piece["title"],
        body=piece["body"],
        source=piece["source"],
        note=piece.get("note", ""),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ensure_today(db: Session) -> DailyReading:
    return ensure_current(db)


def list_recent(db: Session, limit: int = 60) -> list[DailyReading]:
    ensure_current(db)
    rows = db.query(DailyReading).order_by(DailyReading.day.desc()).limit(limit).all()
    dirty = False
    for row in rows:
        if refresh_row_from_pool(row):
            dirty = True
    if dirty:
        db.commit()
        for row in rows:
            db.refresh(row)
    return rows
