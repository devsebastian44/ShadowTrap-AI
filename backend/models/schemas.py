"""
ShadowTrap AI - Data Models
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class AttackCategory(str, Enum):
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    DICTIONARY_ATTACK = "dictionary_attack"
    BOT_SCAN = "bot_scan"
    TARGETED = "targeted"
    UNKNOWN = "unknown"


# ─── Login Attempt ────────────────────────────────────────────────────────────

class LoginAttempt(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    session: str
    timestamp: datetime
    src_ip: str
    src_port: Optional[int] = None
    username: str
    password: str
    success: bool = False
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: AttackCategory = AttackCategory.UNKNOWN

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ─── Command ──────────────────────────────────────────────────────────────────

class Command(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    session: str
    timestamp: datetime
    src_ip: str
    input: str
    is_dangerous: bool = False
    danger_tags: List[str] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ─── Session ──────────────────────────────────────────────────────────────────

class Session(BaseModel):
    session: str
    src_ip: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    login_attempts: int = 0
    commands_count: int = 0
    successful_login: bool = False
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    category: AttackCategory = AttackCategory.UNKNOWN

    class Config:
        populate_by_name = True


# ─── Alert ────────────────────────────────────────────────────────────────────

class Alert(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    timestamp: datetime
    src_ip: str
    event_type: str
    message: str
    severity: str = "medium"  # low, medium, high, critical
    sent: bool = False
    attempts_count: Optional[int] = None
    country: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ─── Stats ────────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_attempts: int
    unique_ips: int
    unique_usernames: int
    unique_passwords: int
    total_commands: int
    total_sessions: int
    top_ips: List[dict]
    top_usernames: List[dict]
    top_passwords: List[dict]
    top_countries: List[dict]
    attacks_over_time: List[dict]
    category_distribution: List[dict]


# ─── API Response Schemas ──────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    data: List[dict]
