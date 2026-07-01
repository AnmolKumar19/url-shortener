import collections
import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Click, Link
from app.schemas import AnalyticsOut, ClicksByDay

router = APIRouter(prefix="/links", tags=["analytics"])


@router.get("/{short_code}/analytics", response_model=AnalyticsOut)
def get_analytics(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")

    clicks = db.query(Click).filter(Click.link_id == link.id).all()

    by_day: collections.Counter = collections.Counter()
    referrers: collections.Counter = collections.Counter()
    devices: collections.Counter = collections.Counter()
    browsers: collections.Counter = collections.Counter()

    for c in clicks:
        day = c.timestamp.date().isoformat() if c.timestamp else "unknown"
        by_day[day] += 1
        referrers[c.referrer or "direct"] += 1
        devices[c.device or "unknown"] += 1
        browsers[c.browser or "unknown"] += 1

    clicks_by_day = [
        ClicksByDay(date=day, clicks=count)
        for day, count in sorted(by_day.items())
    ]

    return AnalyticsOut(
        short_code=short_code,
        total_clicks=len(clicks),
        clicks_by_day=clicks_by_day,
        top_referrers=dict(referrers.most_common(10)),
        device_breakdown=dict(devices),
        browser_breakdown=dict(browsers),
    )
