"""
Centralized app configuration.

All settings are read from environment variables (or a .env file) so the
same code runs the same way locally, in Docker, and in production. See
.env.example for the full list of variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database. Defaults to a local SQLite file so the project runs with
    # zero setup; point DATABASE_URL at Postgres for production.
    database_url: str = "sqlite:///./urlshortener.db"

    # Redis is optional. If it can't be reached, the app falls back to
    # hitting the database directly on every redirect (see app/cache.py).
    redis_url: str = "redis://localhost:6379/0"

    # JWT auth
    secret_key: str = "change-this-in-production-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    # Where the app is hosted, used to build full short URLs in responses.
    base_url: str = "http://localhost:8000"

    # Rate limiting for link creation (prevents abuse of a public endpoint).
    create_link_rate_limit: str = "20/minute"


settings = Settings()
