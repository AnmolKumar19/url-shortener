import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from user_agents import parse as parse_user_agent

from app.cache import cache_long_url, get_cached_long_url
from app.database import get_db
from app.models import Click, Link

router = APIRouter(tags=["redirect"])


def _log_click(db: Session, link_id: int, request: Request) -> None:
    ua_raw = request.headers.get("user-agent", "")
    parsed = parse_user_agent(ua_raw)

    if parsed.is_mobile:
        device = "mobile"
    elif parsed.is_tablet:
        device = "tablet"
    elif parsed.is_bot:
        device = "bot"
    else:
        device = "desktop"

    click = Click(
        link_id=link_id,
        referrer=request.headers.get("referer"),
        user_agent_raw=ua_raw,
        device=device,
        browser=parsed.browser.family,
        ip_address=request.client.host if request.client else None,
    )
    db.add(click)
    db.commit()


@router.get("/{short_code}")
def redirect_to_long_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    # 1. Try the cache first (this is the whole point of caching: skip the
    #    database entirely on the common case).
    long_url = get_cached_long_url(short_code)

    link = None
    if long_url is None:
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            raise HTTPException(status_code=404, detail="Short link not found")
        long_url = link.long_url
        cache_long_url(short_code, long_url)
    else:
        # We still need the Link row for validity checks and to log the click.
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            raise HTTPException(status_code=404, detail="Short link not found")

    if not link.is_active:
        raise HTTPException(status_code=410, detail="This link has been deactivated")
    if link.expires_at and link.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=410, detail="This link has expired")

    _log_click(db, link.id, request)
    return RedirectResponse(url=long_url, status_code=302)
