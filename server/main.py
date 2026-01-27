"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import structlog

from config import settings
from db import init_db_pool, close_db_pool
from .services.redis import init_redis, close_redis
from .runs_router import router as runs_router
from .users_router import router as users_router
from .ui_router import router as ui_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    await init_db_pool(settings.database_url)
    await init_redis(settings.redis_url)
    logger.info("services_initialized", db_url=settings.database_url, redis_url=settings.redis_url)
    yield
    await close_db_pool()
    await close_redis()
    logger.info("services_closed")


app = FastAPI(
    title="Polaris Evaluation API",
    version="0.4.0",
    lifespan=lifespan,
)

# Mount static files for UI (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# Include routers
app.include_router(runs_router)
app.include_router(users_router)
app.include_router(ui_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
