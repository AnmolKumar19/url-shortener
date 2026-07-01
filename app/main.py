from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.limiter import limiter
from app.routers import analytics, auth, links, redirect

# Create tables on startup. For a real production app you'd use Alembic
# migrations instead, but create_all() is the right level of complexity here.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="A URL shortener with auth, click analytics, and Redis caching.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(links.router)
app.include_router(analytics.router)

app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard/")


# IMPORTANT: the redirect router owns the catch-all "/{short_code}" route,
# so it must be included LAST — every other route (including /health above)
# must be registered before this, or it would get shadowed and treated as
# a short code lookup instead.
app.include_router(redirect.router)
