import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.v1.routes.monitoring import router as monitoring_router
from api.v1.routes.tickets import router as tickets_router
from config import settings
from infrastructure.rate_limiter import limiter
from infrastructure.app_context_builder import AppContextBuilder
from infrastructure.context_access import set_app_context
from utils.logging_config import setup_logging
from dotenv import load_dotenv

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    builder = AppContextBuilder(settings)
    ctx, stack = await builder.build()
    set_app_context(ctx)
    app.state.context = ctx

    try:
        yield
    finally:
        await stack.aclose()
        logger.info("Shutdown complete")


app = FastAPI(
    title="WMS Incident API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


app.include_router(tickets_router)
app.include_router(monitoring_router)
