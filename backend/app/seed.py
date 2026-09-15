from app.config import get_settings
from app.database import SessionLocal
from app.models import Category, User

DEFAULT_CATEGORIES = [
    ("prose", "云散", "记叙与抒情并重的散文作品", 1),
    ("fiction", "云说", "短篇与微型小说", 2),
    ("poetry", "诗歌", "现代诗与旧体诗", 3),
    ("essay", "云笔", "随想、札记与日常书写", 4),
]


def seed_categories() -> None:
    db = SessionLocal()
    try:
        for slug, name, desc, order in DEFAULT_CATEGORIES:
            row = db.query(Category).filter(Category.slug == slug).first()
            if row:
                row.name = name
                row.description = desc
                row.sort_order = order
            else:
                db.add(Category(slug=slug, name=name, description=desc, sort_order=order))
        db.commit()
    finally:
        db.close()


def seed_admin() -> None:
    settings = get_settings()
    name = (settings.admin_username or "").strip()
    if not name:
        return
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter((User.username == name) | (User.display_name == name))
            .first()
        )
        if user and not user.is_admin:
            user.is_admin = True
            db.commit()
    finally:
        db.close()
