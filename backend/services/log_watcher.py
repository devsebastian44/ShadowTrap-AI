"""
ShadowTrap AI - Cowrie Log Watcher (tail -f equivalent)
Parses Cowrie JSON logs in real-time and stores events to MongoDB.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from core.database import get_db
from services.alert_service import AlertService
from services.classifier import AttackClassifier
from services.geo_service import GeoService

logger = logging.getLogger("shadowtrap.watcher")


class LogWatcher:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.geo = GeoService()
        self.alerter = AlertService()
        self.classifier = AttackClassifier()
        self._position = 0

    async def watch(self):
        logger.info(f"👁️  Watching Cowrie log: {self.log_path}")
        while True:
            try:
                if not self.log_path.exists():
                    await asyncio.sleep(2)
                    continue

                current_size = os.path.getsize(self.log_path)
                if current_size < self._position:
                    # Log rotated
                    self._position = 0

                if current_size > self._position:
                    with open(self.log_path, "r") as f:
                        f.seek(self._position)
                        new_lines = f.readlines()
                        self._position = f.tell()

                    for line in new_lines:
                        line = line.strip()
                        if line:
                            await self._process_line(line)

            except Exception as e:
                logger.error(f"Log watcher error: {e}")

            await asyncio.sleep(1)

    async def _process_line(self, line: str):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return

        event_id = event.get("eventid", "")

        if event_id == "cowrie.login.failed":
            await self._handle_login(event, success=False)
        elif event_id == "cowrie.login.success":
            await self._handle_login(event, success=True)
        elif event_id == "cowrie.command.input":
            await self._handle_command(event)
        elif event_id in ("cowrie.session.connect", "cowrie.session.closed"):
            await self._handle_session(event)

    async def _handle_login(self, event: dict, success: bool):
        db = get_db()
        src_ip = event.get("src_ip", "unknown")
        timestamp = self._parse_timestamp(event.get("timestamp"))

        geo_data = await self.geo.lookup(src_ip)
        category = await self.classifier.classify_login(src_ip, event.get("username", ""), db)

        doc = {
            "session": event.get("session", ""),
            "timestamp": timestamp,
            "src_ip": src_ip,
            "src_port": event.get("src_port"),
            "username": event.get("username", ""),
            "password": event.get("password", ""),
            "success": success,
            "category": category.value,
            **geo_data,
        }

        await db.login_attempts.insert_one(doc)

        if success:
            logger.warning(f"🚨 SUCCESSFUL LOGIN: {src_ip} → {doc['username']}:{doc['password']}")

        await self.alerter.check_and_alert(src_ip, timestamp, db)

    async def _handle_command(self, event: dict):
        db = get_db()
        cmd_input = event.get("input", "")
        danger_tags = self._classify_command(cmd_input)

        doc = {
            "session": event.get("session", ""),
            "timestamp": self._parse_timestamp(event.get("timestamp")),
            "src_ip": event.get("src_ip", "unknown"),
            "input": cmd_input,
            "is_dangerous": len(danger_tags) > 0,
            "danger_tags": danger_tags,
        }

        await db.commands.insert_one(doc)

        if danger_tags:
            logger.warning(f"⚠️  Dangerous command from {doc['src_ip']}: {cmd_input[:100]}")

    async def _handle_session(self, event: dict):
        db = get_db()
        session_id = event.get("session", "")
        event_id = event.get("eventid", "")

        if event_id == "cowrie.session.connect":
            geo_data = await self.geo.lookup(event.get("src_ip", ""))
            await db.sessions.update_one(
                {"session": session_id},
                {
                    "$set": {
                        "session": session_id,
                        "src_ip": event.get("src_ip", "unknown"),
                        "src_port": event.get("src_port"),
                        "start_time": self._parse_timestamp(event.get("timestamp")),
                        **geo_data,
                    }
                },
                upsert=True,
            )
        elif event_id == "cowrie.session.closed":
            end_time = self._parse_timestamp(event.get("timestamp"))
            duration = int(event.get("duration", 0))
            await db.sessions.update_one(
                {"session": session_id},
                {"$set": {"end_time": end_time, "duration_seconds": duration}},
            )

    def _classify_command(self, cmd: str) -> list:
        tags = []
        cmd_lower = cmd.lower()

        dangerous_patterns = {
            "wget": "downloader",
            "curl": "downloader",
            "chmod +x": "privilege",
            "chmod 777": "privilege",
            "/etc/passwd": "credential_access",
            "/etc/shadow": "credential_access",
            "nc ": "netcat",
            "ncat": "netcat",
            "rm -rf": "destructive",
            "dd if=": "destructive",
            "iptables": "firewall_tamper",
            "base64": "obfuscation",
            "python -c": "code_exec",
            "perl -e": "code_exec",
            "bash -i": "reverse_shell",
            "/dev/tcp": "reverse_shell",
            "crontab": "persistence",
            "useradd": "persistence",
        }

        for pattern, tag in dangerous_patterns.items():
            if pattern in cmd_lower and tag not in tags:
                tags.append(tag)

        return tags

    def _parse_timestamp(self, ts: str) -> datetime:
        if not ts:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
