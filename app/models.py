import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    links = relationship("Link", back_populates="owner")


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    # short_code is filled in AFTER insert (it's derived from the id via
    # base62 encoding) unless the user supplied a custom alias.
    short_code = Column(String, unique=True, index=True, nullable=True)
    long_url = Column(String, nullable=False)
    is_custom_alias = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    owner = relationship("User", back_populates="links")
    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow, index=True)
    referrer = Column(String, nullable=True)
    user_agent_raw = Column(String, nullable=True)
    device = Column(String, nullable=True)   # mobile / tablet / desktop / bot
    browser = Column(String, nullable=True)  # Chrome / Safari / Firefox / ...
    ip_address = Column(String, nullable=True)

    link = relationship("Link", back_populates="clicks")
