import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Links ----------

class LinkCreate(BaseModel):
    long_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None

    @field_validator("custom_alias")
    @classmethod
    def alias_is_url_safe(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not (3 <= len(v) <= 30):
            raise ValueError("custom_alias must be between 3 and 30 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("custom_alias may only contain letters, numbers, - and _")
        return v


class LinkOut(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    is_active: bool
    total_clicks: int = 0

    class Config:
        from_attributes = True


# ---------- Analytics ----------

class ClicksByDay(BaseModel):
    date: str
    clicks: int


class AnalyticsOut(BaseModel):
    short_code: str
    total_clicks: int
    clicks_by_day: list[ClicksByDay]
    top_referrers: dict[str, int]
    device_breakdown: dict[str, int]
    browser_breakdown: dict[str, int]
