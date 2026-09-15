import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, community, content, notifications, uploads
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.migrate import ensure_schema
from app.seed import seed_admin, seed_categories
from app.services.daily import ensure_current
from app.services.files import upload_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = upload_root()
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    seed_categories()
    seed_admin()
    db = SessionLocal()
    try:
        ensure_current(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "name": settings.app_name}
