"""
ShadowTrap AI - Attack Classifier
Heuristic-based classification of attack patterns.
"""

import logging

from models.schemas import AttackCategory

logger = logging.getLogger("shadowtrap.classifier")

# Common bot credentials
BOT_USERNAMES = {"admin", "root", "user", "test", "guest", "pi", "ubuntu", "ec2-user", "oracle"}
BOT_PASSWORDS = {"admin", "password", "123456", "root", "toor", "pass", "12345", "1234"}

# Known credential stuffing wordlists indicators
DICT_USERNAMES = {"administrator", "Administrator", "Admin", "ROOT", "ADMIN"}


class AttackClassifier:
    async def classify_login(self, src_ip: str, username: str, db) -> AttackCategory:
        """Classify a login attempt based on behavioral patterns."""
        if not db:
            return AttackCategory.UNKNOWN

        # Count attempts from this IP in last 5 minutes
        from datetime import datetime, timedelta, timezone

        window = datetime.now(timezone.utc) - timedelta(minutes=5)
        count = await db.login_attempts.count_documents({"src_ip": src_ip, "timestamp": {"$gte": window}})

        # Bot scan: high volume, common credentials
        if count > 20 and username.lower() in BOT_USERNAMES:
            return AttackCategory.BOT_SCAN

        # Brute force: same IP, many attempts, varying passwords
        if count > 50:
            # Check if passwords are varied (not same password repeated)
            pipeline = [
                {"$match": {"src_ip": src_ip, "timestamp": {"$gte": window}}},
                {"$group": {"_id": "$password"}},
                {"$count": "unique_passwords"},
            ]
            result = await db.login_attempts.aggregate(pipeline).to_list(1)
            if result and result[0].get("unique_passwords", 0) > 10:
                return AttackCategory.BRUTE_FORCE

        # Credential stuffing: many IPs trying same credentials
        if username.lower() in BOT_USERNAMES:
            return AttackCategory.CREDENTIAL_STUFFING

        # Dictionary attack: sequential common passwords
        if count > 10 and count <= 50:
            return AttackCategory.DICTIONARY_ATTACK

        # Targeted: low volume, specific non-common usernames
        if count < 5 and username not in BOT_USERNAMES:
            return AttackCategory.TARGETED

        return AttackCategory.UNKNOWN
