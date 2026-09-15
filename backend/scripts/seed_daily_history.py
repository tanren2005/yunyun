from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.data.daily_pool import POOL
from app.models import DailyReading

TZ = ZoneInfo("Asia/Shanghai")
db = SessionLocal()

# 清空后按「长文优先」回填，便于立刻看到完整背影/荷塘月色等
db.query(DailyReading).delete()
db.commit()

priority_titles = [
    "背影",
    "荷塘月色",
    "春",
    "匆匆",
    "孔乙己",
    "故乡",
    "社戏",
    "一件小事",
    "落花生",
    "桃花源记",
    "岳阳楼记",
    "醉翁亭记",
]
by_title = {p["title"]: p for p in POOL}
ordered = [by_title[t] for t in priority_titles if t in by_title]
rest = [p for p in POOL if p["title"] not in {x["title"] for x in ordered}]
pieces = ordered + rest

now = datetime.now(TZ)
for i, piece in enumerate(pieces[:12]):
    slot = (now - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
    db.add(
        DailyReading(
            day=slot,
            kind=piece["kind"],
            title=piece["title"],
            body=piece["body"],
            source=piece["source"],
            note=piece.get("note", ""),
        )
    )
db.commit()
rows = db.query(DailyReading).order_by(DailyReading.day.desc()).all()
print("count", len(rows))
for r in rows:
    print(r.day, r.kind, r.title, len(r.body or ""))
db.close()
