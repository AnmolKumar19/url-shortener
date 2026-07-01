from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.cache import cache_long_url, invalidate
from app.database import get_db
from app.limiter import limiter
from app.config import settings
from app.models import Click, Link, User
from app.schemas import LinkCreate, LinkOut
from app.security import get_current_user, get_current_user_optional
from app.utils import encode_base62

router = APIRouter(prefix="/links", tags=["links"])


def _to_link_out(link: Link, db: Session) -> LinkOut:
    total_clicks = db.query(Click).filter(Click.link_id == link.id).count()
    return LinkOut(
        short_code=link.short_code,
        short_url=f"{settings.base_url}/{link.short_code}",
        long_url=link.long_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        is_active=link.is_active,
        total_clicks=total_clicks,
    )


@router.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.create_link_rate_limit)
def create_link(
    request: Request,
    payload: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    long_url_str = str(payload.long_url)

    if payload.custom_alias:
        clash = db.query(Link).filter(Link.short_code == payload.custom_alias).first()
        if clash:
            raise HTTPException(status_code=409, detail="That alias is already taken")
        link = Link(
            long_url=long_url_str,
            short_code=payload.custom_alias,
            is_custom_alias=True,
            expires_at=payload.expires_at,
            owner_id=current_user.id if current_user else None,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
    else:
        # Insert first (without a short_code) to get an auto-increment ID,
        # then derive the short_code from that ID. See app/utils.py for why.
        link = Link(
            long_url=long_url_str,
            expires_at=payload.expires_at,
            owner_id=current_user.id if current_user else None,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        link.short_code = encode_base62(link.id)
        db.commit()
        db.refresh(link)

    cache_long_url(link.short_code, link.long_url)
    return _to_link_out(link, db)


@router.get("", response_model=list[LinkOut])
def list_my_links(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    links = db.query(Link).filter(Link.owner_id == current_user.id).all()
    return [_to_link_out(link, db) for link in links]


@router.get("/{short_code}", response_model=LinkOut)
def get_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    return _to_link_out(link, db)


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this link")
    link.is_active = False
    db.commit()
    invalidate(short_code)
