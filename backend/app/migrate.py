"""启动时补齐旧库缺列（create_all 不会改已有表）。"""

from sqlalchemy import text

from app.database import engine


def ensure_schema() -> None:
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0",
        "ALTER TABLE daily_readings ALTER COLUMN day TYPE VARCHAR(20)",
        "ALTER TABLE daily_readings ADD COLUMN IF NOT EXISTS note TEXT DEFAULT ''",
        "ALTER TABLE moment_comments ADD COLUMN IF NOT EXISTS parent_id INTEGER",
        "ALTER TABLE book_comments ADD COLUMN IF NOT EXISTS parent_id INTEGER",
    ]
    with engine.begin() as conn:
        for sql in stmts:
            try:
                conn.execute(text(sql))
            except Exception:
                # 非 Postgres 或缺表时忽略，create_all 会建新表
                pass
