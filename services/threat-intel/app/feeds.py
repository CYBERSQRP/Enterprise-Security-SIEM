import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.models import IOCModel, IOCType, ThreatLevel

logger = logging.getLogger(__name__)


class FeedManager:
    """Manager for threat intelligence feeds"""

    def __init__(self):
        self.update_interval = settings.feed_update_interval

    async def start(self):
        """Start the feed update loop"""
        logger.info("Starting threat feed manager")

        while True:
            try:
                await self.update_feeds()
            except Exception as e:
                logger.error(f"Error updating feeds: {e}")

            await asyncio.sleep(self.update_interval)

    async def update_feeds(self):
        """Update all threat feeds"""
        logger.info("Updating threat feeds")

        tasks = [
            self.update_abuse_ch_feeds(),
            self.update_otx_feed(),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Threat feeds updated")

    async def update_abuse_ch_feeds(self):
        """Update Abuse.ch threat feeds"""
        try:
            import httpx

            # Feodo Tracker (Botnet C2 IPs)
            async with httpx.AsyncClient() as client:
                response = await client.get("https://feodotracker.abuse.ch/downloads/ipblocklist.txt")
                if response.status_code == 200:
                    ips = [line.strip() for line in response.text.split('\n')
                           if line.strip() and not line.startswith('#')]

                    await self._store_iocs(
                        ips,
                        IOCType.IP,
                        ThreatLevel.HIGH,
                        "Abuse.ch Feodo Tracker"
                    )

                    logger.info(f"Updated {len(ips)} IPs from Feodo Tracker")

        except Exception as e:
            logger.error(f"Error updating Abuse.ch feeds: {e}")

    async def update_otx_feed(self):
        """Update AlienVault OTX feed"""
        if not settings.otx_api_key:
            logger.debug("OTX API key not configured, skipping")
            return

        try:
            from OTXv2 import OTXv2

            otx = OTXv2(settings.otx_api_key)
            pulses = otx.getall()

            iocs_by_type = {
                IOCType.IP: [],
                IOCType.DOMAIN: [],
                IOCType.FILE_HASH: [],
                IOCType.URL: [],
            }

            for pulse in pulses:
                for indicator in pulse.get('indicators', []):
                    ioc_type_str = indicator.get('type', '')
                    value = indicator.get('indicator', '')

                    if not value:
                        continue

                    # Map OTX types to our IOC types
                    if ioc_type_str in ['IPv4', 'IPv6']:
                        iocs_by_type[IOCType.IP].append(value)
                    elif ioc_type_str == 'domain':
                        iocs_by_type[IOCType.DOMAIN].append(value)
                    elif ioc_type_str in ['FileHash-MD5', 'FileHash-SHA1', 'FileHash-SHA256']:
                        iocs_by_type[IOCType.FILE_HASH].append(value)
                    elif ioc_type_str == 'URL':
                        iocs_by_type[IOCType.URL].append(value)

            # Store IOCs
            for ioc_type, values in iocs_by_type.items():
                if values:
                    await self._store_iocs(
                        values[:1000],  # Limit to prevent overload
                        ioc_type,
                        ThreatLevel.MEDIUM,
                        "AlienVault OTX"
                    )

                    logger.info(f"Updated {len(values)} {ioc_type} IOCs from OTX")

        except Exception as e:
            logger.error(f"Error updating OTX feed: {e}")

    async def _store_iocs(
        self,
        values: List[str],
        ioc_type: IOCType,
        threat_level: ThreatLevel,
        source: str
    ):
        """Store IOCs in database"""
        async with async_session_maker() as session:
            now = datetime.utcnow()

            for value in values:
                # Check if IOC already exists
                from sqlalchemy import select, and_
                stmt = select(IOCModel).where(
                    and_(
                        IOCModel.value == value,
                        IOCModel.ioc_type == ioc_type
                    )
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update last_seen
                    existing.last_seen = now
                else:
                    # Create new IOC
                    ioc = IOCModel(
                        ioc_type=ioc_type,
                        value=value,
                        threat_level=threat_level,
                        source=source,
                        description=f"IOC from {source}",
                        tags=[source.lower().replace(' ', '-')],
                        metadata={},
                        first_seen=now,
                        last_seen=now,
                        is_active=True
                    )
                    session.add(ioc)

            await session.commit()
