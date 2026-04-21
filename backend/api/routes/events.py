"""
ShadowTrap AI - Events API Routes
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from core.database import get_db
from models.schemas import PaginatedResponse

router = APIRouter()


@router.get("/logins", response_model=PaginatedResponse)
async def get_login_attempts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    src_ip: Optional[str] = None,
    username: Optional[str] = None,
    success: Optional[bool] = None,
    country_code: Optional[str] = None,
    category: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    db = get_db()
    query = {}

    if src_ip:
        query["src_ip"] = src_ip
    if username:
        query["username"] = {"$regex": username, "$options": "i"}
    if success is not None:
        query["success"] = success
    if country_code:
        query["country_code"] = country_code.upper()
    if category:
        query["category"] = category

    date_filter = {}
    if from_date:
        date_filter["$gte"] = from_date
    if to_date:
        date_filter["$lte"] = to_date
    if date_filter:
        query["timestamp"] = date_filter

    total = await db.login_attempts.count_documents(query)
    skip = (page - 1) * per_page

    cursor = db.login_attempts.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(per_page)

    data = await cursor.to_list(per_page)

    return PaginatedResponse(total=total, page=page, per_page=per_page, data=data)


@router.get("/commands", response_model=PaginatedResponse)
async def get_commands(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    src_ip: Optional[str] = None,
    session: Optional[str] = None,
    dangerous_only: bool = False,
    search: Optional[str] = None,
):
    db = get_db()
    query = {}

    if src_ip:
        query["src_ip"] = src_ip
    if session:
        query["session"] = session
    if dangerous_only:
        query["is_dangerous"] = True
    if search:
        query["$text"] = {"$search": search}

    total = await db.commands.count_documents(query)
    skip = (page - 1) * per_page

    cursor = db.commands.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(per_page)

    data = await cursor.to_list(per_page)

    return PaginatedResponse(total=total, page=page, per_page=per_page, data=data)


@router.get("/sessions", response_model=PaginatedResponse)
async def get_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    src_ip: Optional[str] = None,
):
    db = get_db()
    query = {}
    if src_ip:
        query["src_ip"] = src_ip

    total = await db.sessions.count_documents(query)
    skip = (page - 1) * per_page

    cursor = db.sessions.find(query, {"_id": 0}).sort("start_time", -1).skip(skip).limit(per_page)

    data = await cursor.to_list(per_page)
    return PaginatedResponse(total=total, page=page, per_page=per_page, data=data)


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    db = get_db()
    session = await db.sessions.find_one({"session": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    logins = await db.login_attempts.find({"session": session_id}, {"_id": 0}).to_list(1000)

    commands = await db.commands.find({"session": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)

    return {
        "session": session,
        "login_attempts": logins,
        "commands": commands,
    }
