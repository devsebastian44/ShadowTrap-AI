"""
ShadowTrap AI - Health & Alerts Routes
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from core.database import get_db

router = APIRouter()


# ─── Health ───────────────────────────────────────────────────────────────────


@router.get("/health")
async def health_check():
    db = get_db()
    try:
        await db.command("ping")
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "service": "ShadowTrap AI",
        "version": "1.0.0",
    }
