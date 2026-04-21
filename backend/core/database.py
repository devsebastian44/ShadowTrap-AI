"""
ShadowTrap AI - Database Layer (MongoDB via Motor)
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from core.config import settings

logger = logging.getLogger("shadowtrap.db")

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None


async def init_db():
    global _client, _db
    logger.info(f"Connecting to MongoDB: {settings.MONGODB_URL}")
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _db = _client[settings.MONGODB_DB]
    await _create_indexes()
    logger.info(f"✅ MongoDB connected: database '{settings.MONGODB_DB}'")


async def _create_indexes():
    # login_attempts collection
    await _db.login_attempts.create_indexes(
        [
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("src_ip", ASCENDING)]),
            IndexModel([("username", ASCENDING)]),
            IndexModel([("country_code", ASCENDING)]),
            IndexModel([("session", ASCENDING)]),
        ]
    )

    # commands collection
    await _db.commands.create_indexes(
        [
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("src_ip", ASCENDING)]),
            IndexModel([("session", ASCENDING)]),
            IndexModel([("input", "text")]),
        ]
    )

    # sessions collection
    await _db.sessions.create_indexes(
        [
            IndexModel([("session", ASCENDING)], unique=True),
            IndexModel([("src_ip", ASCENDING)]),
            IndexModel([("start_time", DESCENDING)]),
        ]
    )

    # alerts collection
    await _db.alerts.create_indexes(
        [
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("src_ip", ASCENDING)]),
            IndexModel([("sent", ASCENDING)]),
        ]
    )

    logger.info("✅ Database indexes created")


def get_db() -> AsyncIOMotorDatabase:
    return _db
