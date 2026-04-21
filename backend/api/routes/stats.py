"""
ShadowTrap AI - Statistics API Routes
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from core.database import get_db

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    hours: int = Query(24, ge=1, le=720, description="Hours of data to include"),
):
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    match_stage = {"$match": {"timestamp": {"$gte": since}}}

    # Parallel aggregations
    total_attempts = await db.login_attempts.count_documents({"timestamp": {"$gte": since}})
    total_commands = await db.commands.count_documents({"timestamp": {"$gte": since}})
    total_sessions = await db.sessions.count_documents({"start_time": {"$gte": since}})

    # Unique IPs
    unique_ips = len(await db.login_attempts.distinct("src_ip", {"timestamp": {"$gte": since}}))
    unique_usernames = len(await db.login_attempts.distinct("username", {"timestamp": {"$gte": since}}))
    unique_passwords = len(await db.login_attempts.distinct("password", {"timestamp": {"$gte": since}}))

    # Top IPs
    top_ips = await db.login_attempts.aggregate(
        [
            match_stage,
            {
                "$group": {
                    "_id": "$src_ip",
                    "count": {"$sum": 1},
                    "country": {"$first": "$country_name"},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$project": {"ip": "$_id", "count": 1, "country": 1, "_id": 0}},
        ]
    ).to_list(10)

    # Top usernames
    top_usernames = await db.login_attempts.aggregate(
        [
            match_stage,
            {"$group": {"_id": "$username", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$project": {"username": "$_id", "count": 1, "_id": 0}},
        ]
    ).to_list(10)

    # Top passwords
    top_passwords = await db.login_attempts.aggregate(
        [
            match_stage,
            {"$group": {"_id": "$password", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$project": {"password": "$_id", "count": 1, "_id": 0}},
        ]
    ).to_list(10)

    # Top countries
    top_countries = await db.login_attempts.aggregate(
        [
            match_stage,
            {"$match": {"country_code": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$country_code",
                    "count": {"$sum": 1},
                    "country_name": {"$first": "$country_name"},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 15},
            {"$project": {"country_code": "$_id", "count": 1, "country_name": 1, "_id": 0}},
        ]
    ).to_list(15)

    # Attacks over time (hourly buckets)
    bucket_size = 3600 if hours <= 24 else 86400  # hourly or daily
    attacks_over_time = await db.login_attempts.aggregate(
        [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "$toDate": {
                            "$subtract": [
                                {"$toLong": "$timestamp"},
                                {"$mod": [{"$toLong": "$timestamp"}, bucket_size * 1000]},
                            ]
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"time": "$_id", "count": 1, "_id": 0}},
        ]
    ).to_list(1000)

    # Category distribution
    category_distribution = await db.login_attempts.aggregate(
        [
            match_stage,
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"category": "$_id", "count": 1, "_id": 0}},
        ]
    ).to_list(20)

    # Recent successful logins
    recent_successes = (
        await db.login_attempts.find({"success": True, "timestamp": {"$gte": since}}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(10)
        .to_list(10)
    )

    return {
        "period_hours": hours,
        "total_attempts": total_attempts,
        "unique_ips": unique_ips,
        "unique_usernames": unique_usernames,
        "unique_passwords": unique_passwords,
        "total_commands": total_commands,
        "total_sessions": total_sessions,
        "top_ips": top_ips,
        "top_usernames": top_usernames,
        "top_passwords": top_passwords,
        "top_countries": top_countries,
        "attacks_over_time": attacks_over_time,
        "category_distribution": category_distribution,
        "recent_successes": recent_successes,
    }


@router.get("/ip/{ip_address}")
async def get_ip_profile(ip_address: str):
    """Full profile of a specific attacker IP."""
    db = get_db()

    total = await db.login_attempts.count_documents({"src_ip": ip_address})
    if total == 0:
        return {"ip": ip_address, "total_attempts": 0, "found": False}

    first_seen = await db.login_attempts.find_one({"src_ip": ip_address}, sort=[("timestamp", 1)])
    last_seen = await db.login_attempts.find_one({"src_ip": ip_address}, sort=[("timestamp", -1)])

    usernames = await db.login_attempts.distinct("username", {"src_ip": ip_address})
    passwords = await db.login_attempts.distinct("password", {"src_ip": ip_address})
    commands = await db.commands.find({"src_ip": ip_address}, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)

    geo = {k: last_seen.get(k) for k in ["country_code", "country_name", "city", "latitude", "longitude", "isp"]}

    return {
        "ip": ip_address,
        "found": True,
        "geo": geo,
        "total_attempts": total,
        "unique_usernames": len(usernames),
        "unique_passwords": len(passwords),
        "usernames_tried": usernames[:20],
        "passwords_tried": passwords[:20],
        "first_seen": first_seen.get("timestamp") if first_seen else None,
        "last_seen": last_seen.get("timestamp") if last_seen else None,
        "commands": commands,
        "category": last_seen.get("category"),
    }
