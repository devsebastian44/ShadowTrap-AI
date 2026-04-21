"""
ShadowTrap AI - Alert Service
Sends real-time alerts to Telegram and/or Discord.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

from core.config import settings

logger = logging.getLogger("shadowtrap.alerts")


class AlertService:

    async def check_and_alert(self, src_ip: str, timestamp: datetime, db):
        """Check if an IP has exceeded the threshold and trigger alert."""
        window_start = timestamp - timedelta(seconds=settings.ALERT_THRESHOLD_WINDOW_SECONDS)

        count = await db.login_attempts.count_documents({
            "src_ip": src_ip,
            "timestamp": {"$gte": window_start},
        })

        if count >= settings.ALERT_THRESHOLD_ATTEMPTS:
            # Check if we already alerted for this IP recently
            recent_alert = await db.alerts.find_one({
                "src_ip": src_ip,
                "timestamp": {"$gte": window_start},
                "event_type": "brute_force_threshold",
            })

            if not recent_alert:
                await self._create_and_send_alert(src_ip, count, db)

    async def _create_and_send_alert(self, src_ip: str, attempts: int, db):
        message = (
            f"🚨 *ShadowTrap AI Alert*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 IP: `{src_ip}`\n"
            f"🔢 Attempts: `{attempts}` in {settings.ALERT_THRESHOLD_WINDOW_SECONDS}s\n"
            f"⏰ Time: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Category: *Brute Force Attack*"
        )

        alert_doc = {
            "timestamp": datetime.now(timezone.utc),
            "src_ip": src_ip,
            "event_type": "brute_force_threshold",
            "message": message,
            "severity": "high",
            "attempts_count": attempts,
            "sent": False,
        }

        result = await db.alerts.insert_one(alert_doc)
        alert_id = result.inserted_id

        sent = False
        if settings.TELEGRAM_ENABLED:
            sent = await self._send_telegram(message)
        if settings.DISCORD_ENABLED:
            sent = await self._send_discord(message) or sent

        await db.alerts.update_one(
            {"_id": alert_id},
            {"$set": {"sent": sent}}
        )

        logger.warning(f"🚨 Alert triggered for {src_ip} ({attempts} attempts). Sent={sent}")

    async def _send_telegram(self, message: str) -> bool:
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "text": message,
                        "parse_mode": "Markdown",
                    }
                )
                return r.status_code == 200
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")
            return False

    async def _send_discord(self, message: str) -> bool:
        if not settings.DISCORD_WEBHOOK_URL:
            return False
        # Convert markdown for Discord
        discord_message = message.replace("*", "**").replace("`", "`")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    settings.DISCORD_WEBHOOK_URL,
                    json={
                        "content": discord_message,
                        "username": "ShadowTrap AI",
                        "avatar_url": "https://i.imgur.com/shadowtrap.png",
                    }
                )
                return r.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Discord alert failed: {e}")
            return False

    async def send_custom_alert(self, message: str, severity: str = "medium") -> bool:
        """Send a custom alert message directly."""
        sent = False
        if settings.TELEGRAM_ENABLED:
            sent = await self._send_telegram(message)
        if settings.DISCORD_ENABLED:
            sent = await self._send_discord(message) or sent
        return sent
