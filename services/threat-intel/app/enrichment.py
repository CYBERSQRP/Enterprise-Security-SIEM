import asyncio
import logging
from typing import Dict, Any, List

import httpx

from app.config import settings
from app.models import IOCType, ThreatLevel, EnrichmentResponse

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service for enriching indicators with threat intelligence"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def enrich(self, value: str, ioc_type: IOCType) -> EnrichmentResponse:
        """Enrich an indicator from multiple sources"""
        tasks = []

        if ioc_type == IOCType.IP:
            if settings.abuseipdb_api_key:
                tasks.append(self._enrich_ip_abuseipdb(value))
            if settings.virustotal_api_key:
                tasks.append(self._enrich_virustotal(value, "ip"))

        elif ioc_type == IOCType.DOMAIN:
            if settings.virustotal_api_key:
                tasks.append(self._enrich_virustotal(value, "domain"))

        elif ioc_type == IOCType.FILE_HASH:
            if settings.virustotal_api_key:
                tasks.append(self._enrich_virustotal(value, "file"))

        if not tasks:
            return EnrichmentResponse(
                value=value,
                ioc_type=ioc_type,
                is_malicious=False,
                threat_level=None,
                sources=[],
                metadata={}
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        is_malicious = False
        sources = []
        metadata = {}
        threat_level = None

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Enrichment error: {result}")
                continue

            if result.get("is_malicious"):
                is_malicious = True

            if result.get("source"):
                sources.append(result["source"])

            metadata.update(result.get("data", {}))

            if result.get("threat_level"):
                # Take the highest threat level
                result_level = result["threat_level"]
                if threat_level is None or self._compare_threat_levels(result_level, threat_level) > 0:
                    threat_level = result_level

        return EnrichmentResponse(
            value=value,
            ioc_type=ioc_type,
            is_malicious=is_malicious,
            threat_level=threat_level,
            sources=sources,
            metadata=metadata
        )

    async def _enrich_ip_abuseipdb(self, ip: str) -> Dict[str, Any]:
        """Enrich IP using AbuseIPDB"""
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                "Key": settings.abuseipdb_api_key,
                "Accept": "application/json"
            }
            params = {"ipAddress": ip, "maxAgeInDays": 90}

            response = await self.client.get(url, headers=headers, params=params)
            data = response.json()

            if "data" in data:
                abuse_score = data["data"].get("abuseConfidenceScore", 0)
                is_malicious = abuse_score > 50

                threat_level = None
                if abuse_score > 80:
                    threat_level = ThreatLevel.CRITICAL
                elif abuse_score > 60:
                    threat_level = ThreatLevel.HIGH
                elif abuse_score > 40:
                    threat_level = ThreatLevel.MEDIUM
                elif abuse_score > 0:
                    threat_level = ThreatLevel.LOW

                return {
                    "source": "AbuseIPDB",
                    "is_malicious": is_malicious,
                    "threat_level": threat_level,
                    "data": {
                        "abuseipdb": {
                            "abuse_score": abuse_score,
                            "total_reports": data["data"].get("totalReports", 0),
                            "is_whitelisted": data["data"].get("isWhitelisted", False)
                        }
                    }
                }

        except Exception as e:
            logger.error(f"AbuseIPDB enrichment error: {e}")

        return {"source": "AbuseIPDB", "is_malicious": False, "data": {}}

    async def _enrich_virustotal(self, value: str, indicator_type: str) -> Dict[str, Any]:
        """Enrich indicator using VirusTotal"""
        try:
            headers = {"x-apikey": settings.virustotal_api_key}

            if indicator_type == "ip":
                url = f"https://www.virustotal.com/api/v3/ip_addresses/{value}"
            elif indicator_type == "domain":
                url = f"https://www.virustotal.com/api/v3/domains/{value}"
            elif indicator_type == "file":
                url = f"https://www.virustotal.com/api/v3/files/{value}"
            else:
                return {"source": "VirusTotal", "is_malicious": False, "data": {}}

            response = await self.client.get(url, headers=headers)
            data = response.json()

            if "data" in data and "attributes" in data["data"]:
                attrs = data["data"]["attributes"]
                stats = attrs.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                is_malicious = malicious > 0
                threat_level = None

                if total > 0:
                    malicious_ratio = malicious / total
                    if malicious_ratio > 0.5:
                        threat_level = ThreatLevel.CRITICAL
                    elif malicious_ratio > 0.3:
                        threat_level = ThreatLevel.HIGH
                    elif malicious_ratio > 0.1:
                        threat_level = ThreatLevel.MEDIUM
                    elif malicious > 0:
                        threat_level = ThreatLevel.LOW

                return {
                    "source": "VirusTotal",
                    "is_malicious": is_malicious,
                    "threat_level": threat_level,
                    "data": {
                        "virustotal": {
                            "malicious": malicious,
                            "total": total,
                            "stats": stats
                        }
                    }
                }

        except Exception as e:
            logger.error(f"VirusTotal enrichment error: {e}")

        return {"source": "VirusTotal", "is_malicious": False, "data": {}}

    def _compare_threat_levels(self, level1: ThreatLevel, level2: ThreatLevel) -> int:
        """Compare two threat levels. Returns 1 if level1 > level2, -1 if level1 < level2, 0 if equal"""
        levels = [ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        idx1 = levels.index(level1)
        idx2 = levels.index(level2)

        if idx1 > idx2:
            return 1
        elif idx1 < idx2:
            return -1
        return 0

    async def close(self):
        await self.client.aclose()
