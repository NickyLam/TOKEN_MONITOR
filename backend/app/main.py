"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.plugins.registry import discover_plugins
from app.routers import alerts, dashboard, plans, polling, usage, vendors
from app.scheduler.engine import init_scheduler, shutdown_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting Token Monitor...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Discover vendor plugins
    discover_plugins()
    from app.plugins.registry import all_plugins
    logger.info("Discovered %d plugins: %s", len(all_plugins()), list(all_plugins().keys()))

    # Start scheduler
    await init_scheduler()

    yield

    # Shutdown
    await shutdown_scheduler()
    logger.info("Token Monitor shut down")


app = FastAPI(
    title="Token Monitor",
    description="Personal dashboard to monitor AI coding tool subscriptions and token usage",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(vendors.router)
app.include_router(plans.router)
app.include_router(dashboard.router)
app.include_router(usage.router)
app.include_router(alerts.router)
app.include_router(polling.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "token-monitor"}
