"""
ShadowTrap AI - SSH Honeypot Intelligence Platform
FastAPI Backend Application
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.routes import alerts, events, health, stats
from core.config import settings
from core.database import init_db
from services.log_watcher import LogWatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("shadowtrap")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🕷️  ShadowTrap AI starting...")
    await init_db()

    log_watcher = LogWatcher(settings.COWRIE_LOG_PATH)
    watcher_task = asyncio.create_task(log_watcher.watch())
    app.state.log_watcher = log_watcher

    logger.info("✅ ShadowTrap AI is active and hunting.")
    yield

    watcher_task.cancel()
    try:
        await watcher_task
    except asyncio.CancelledError:
        pass
    logger.info("🛑 ShadowTrap AI stopped.")


app = FastAPI(
    title="ShadowTrap AI",
    description="SSH Honeypot Intelligence Platform powered by Cowrie",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Statistics"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
