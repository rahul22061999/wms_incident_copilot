"""
Rate limiter configuration (SlowAPI / limits).

storage_uri=None uses an in-memory counter store. This means:
- Rate limit counts reset on every server restart.
- Counts are NOT shared across multiple uvicorn workers or processes.

For a single-worker deployment this is fine. If you add workers (--workers N),
switch storage_uri to a Redis URL so all workers share the same counter.

The limiter instance must be registered on the FastAPI app at startup:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Without this wiring, the @limiter.limit() decorator is silently ignored.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings

_storage_uri = None  # in-memory; see module docstring before changing
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=settings.RATE_LIMIT_DEFAULT,
    storage_uri=_storage_uri
)
