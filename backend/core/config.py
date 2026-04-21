"""
ShadowTrap AI - Configuration Management
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # App
    APP_NAME: str = "ShadowTrap AI"
    APP_ENV: str = "production"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # MongoDB
    MONGODB_URL: str = "mongodb://shadowtrap_user:shadowtrap_pass@mongo:27017/shadowtrap"
    MONGODB_DB: str = "shadowtrap"

    # Cowrie
    COWRIE_LOG_PATH: str = "/cowrie/var/log/cowrie/cowrie.json"

    # GeoIP
    GEOIP_DB_PATH: str = "/app/data/GeoLite2-City.mmdb"

    # Telegram Alerts
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Discord Alerts
    DISCORD_ENABLED: bool = False
    DISCORD_WEBHOOK_URL: str = ""

    # Alert thresholds
    ALERT_THRESHOLD_ATTEMPTS: int = 10
    ALERT_THRESHOLD_WINDOW_SECONDS: int = 60

    # Attack classification
    CLASSIFIER_ENABLED: bool = True


settings = Settings()
