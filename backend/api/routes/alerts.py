"""
ShadowTrap AI - Alerts Routes
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, Body

from core.database import get_db
from services.alert_service import AlertService
from models.schemas import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sent: Optional[bool] = None,
    severity: Optional[str] = None,
):
    db = get_db()
    query = {}
    if sent is not None:
        query["sent"] = sent
    if severity:
        query["severity"] = severity

    total = await db.alerts.count_documents(query)
    skip = (page - 1) * per_page
    data = await db.alerts.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(per_page).to_list(per_page)

    return PaginatedResponse(total=total, page=page, per_page=per_page, data=data)


@router.post("/test")
async def send_test_alert():
    """Send a test alert to configured channels."""
    service = AlertService()
    message = (
        "🧪 *ShadowTrap AI - Test Alert*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Alert system is working correctly.\n"
        f"⏰ `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`"
    )
    sent = await service.send_custom_alert(message, severity="low")
    return {"sent": sent, "message": "Test alert triggered"}
