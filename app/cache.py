"""
Cache-aside layer for the hot path: resolving a short_code -> long_url on
every redirect.

Design decision: redirects are, by far, the highest-traffic endpoint of a
URL shortener (every click hits it, vs. link creation which is rare by
comparison). Caching this lookup in Redis means most requests never touch
Postgres at all.

Resilience decision: if Redis is unreachable (not installed, wrong URL,
network blip), the app should NOT go down — it should just fall back to
querying the database directly. That's why every function here wraps the
Redis call in a try/except and returns None / no-ops on failure instead of
raising. This is a real production pattern worth explaining in interviews:
a cache should degrade gracefully, never become a single point of failure.
"""
import redis

from app.config import settings

_client: redis.Redis | None = None
_redis_available = True

LINK_TTL_SECONDS = 60 * 60  # 1 hour


def _get_client() -> redis.Redis | None:
    global _client, _redis_available
    if not _redis_available:
        return None
    if _client is None:
        try:
            _client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
            _client.ping()
        except redis.RedisError:
            _redis_available = False
            return None
    return _client


def get_cached_long_url(short_code: str) -> str | None:
    client = _get_client()
    if client is None:
        return None
    try:
        value = client.get(f"link:{short_code}")
        return value.decode() if value else None
    except redis.RedisError:
        return None


def cache_long_url(short_code: str, long_url: str) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(f"link:{short_code}", LINK_TTL_SECONDS, long_url)
    except redis.RedisError:
        pass


def invalidate(short_code: str) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(f"link:{short_code}")
    except redis.RedisError:
        pass
