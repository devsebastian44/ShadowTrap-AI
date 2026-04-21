"""
ShadowTrap AI - GeoIP Lookup Service
Uses MaxMind GeoLite2 database for IP geolocation.
Falls back to ip-api.com if local DB is unavailable.
"""

import logging
from pathlib import Path

import httpx

logger = logging.getLogger("shadowtrap.geo")

_cache: dict = {}


class GeoService:
    def __init__(self, db_path: str = "/app/data/GeoLite2-City.mmdb"):
        self.db_path = Path(db_path)
        self._reader = None
        self._load_reader()

    def _load_reader(self):
        if self.db_path.exists():
            try:
                import maxminddb

                self._reader = maxminddb.open_database(str(self.db_path))
                logger.info("✅ GeoLite2 database loaded")
            except Exception as e:
                logger.warning(f"Failed to load GeoLite2 DB: {e}. Using fallback API.")
        else:
            logger.warning("GeoLite2 DB not found. Using ip-api.com fallback (rate limited).")

    async def lookup(self, ip: str) -> dict:
        if not ip or ip in ("127.0.0.1", "::1", "unknown"):
            return self._empty_geo()

        if ip in _cache:
            return _cache[ip]

        result = self._empty_geo()

        if self._reader:
            result = self._lookup_local(ip)
        else:
            result = await self._lookup_remote(ip)

        _cache[ip] = result
        return result

    def _lookup_local(self, ip: str) -> dict:
        try:
            record = self._reader.get(ip)
            if not record:
                return self._empty_geo()
            return {
                "country_code": record.get("country", {}).get("iso_code"),
                "country_name": record.get("country", {}).get("names", {}).get("en"),
                "city": record.get("city", {}).get("names", {}).get("en"),
                "latitude": record.get("location", {}).get("latitude"),
                "longitude": record.get("location", {}).get("longitude"),
                "isp": None,
            }
        except Exception as e:
            logger.debug(f"Local GeoIP lookup failed for {ip}: {e}")
            return self._empty_geo()

    async def _lookup_remote(self, ip: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={"fields": "status,country,countryCode,city,lat,lon,isp"},
                )
                data = r.json()
                if data.get("status") == "success":
                    return {
                        "country_code": data.get("countryCode"),
                        "country_name": data.get("country"),
                        "city": data.get("city"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "isp": data.get("isp"),
                    }
        except Exception as e:
            logger.debug(f"Remote GeoIP lookup failed for {ip}: {e}")
        return self._empty_geo()

    def _empty_geo(self) -> dict:
        return {
            "country_code": None,
            "country_name": None,
            "city": None,
            "latitude": None,
            "longitude": None,
            "isp": None,
        }
