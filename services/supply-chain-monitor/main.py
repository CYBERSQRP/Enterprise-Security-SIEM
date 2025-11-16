#!/usr/bin/env python3
"""
Supply Chain Security Monitoring Service

This service monitors third-party vendors, SaaS providers, and supply chain
dependencies for security risks, anomalies, and potential compromises.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
import redis.asyncio as aioredis
import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VendorRiskLevel(str, Enum):
    """Vendor risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """Supply chain event types"""
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    API_CALL = "api_call"
    DATA_TRANSFER = "data_transfer"
    AUTH_EVENT = "auth_event"
    ANOMALY = "anomaly"


@dataclass
class Vendor:
    """Represents a third-party vendor"""
    id: str
    name: str
    category: str  # saas, infrastructure, development, security
    criticality: str  # critical, high, medium, low
    data_access_level: str  # full, limited, none
    last_assessment: Optional[datetime] = None
    risk_score: float = 0.0
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class VendorEvent:
    """Represents an event from a vendor"""
    id: str
    vendor_id: str
    event_type: EventType
    timestamp: datetime
    severity: str
    description: str
    source_ip: Optional[str] = None
    user: Optional[str] = None
    resource: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Vendor risk assessment result"""
    vendor_id: str
    vendor_name: str
    risk_score: float  # 0.0 to 100.0
    risk_level: VendorRiskLevel
    factors: Dict[str, float]
    recommendations: List[str]
    timestamp: datetime
    next_assessment: datetime


# Pydantic models for API
class VendorCreate(BaseModel):
    name: str
    category: str
    criticality: str
    data_access_level: str
    tags: List[str] = []
    metadata: Dict = {}


class VendorUpdate(BaseModel):
    enabled: Optional[bool] = None
    criticality: Optional[str] = None
    data_access_level: Optional[str] = None
    tags: Optional[List[str]] = None


class VendorEventCreate(BaseModel):
    vendor_id: str
    event_type: EventType
    severity: str
    description: str
    source_ip: Optional[str] = None
    user: Optional[str] = None
    resource: Optional[str] = None
    metadata: Dict = {}


class RiskAssessmentResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    risk_score: float
    risk_level: str
    factors: Dict[str, float]
    recommendations: List[str]
    timestamp: datetime


# Prometheus metrics
metrics_events_processed = Counter(
    'supply_chain_events_processed_total',
    'Total number of supply chain events processed',
    ['vendor_id', 'event_type']
)

metrics_vendors_monitored = Gauge(
    'supply_chain_vendors_monitored',
    'Number of vendors currently monitored'
)

metrics_risk_score = Gauge(
    'supply_chain_vendor_risk_score',
    'Vendor risk score',
    ['vendor_id', 'vendor_name']
)

metrics_assessment_duration = Histogram(
    'supply_chain_risk_assessment_duration_seconds',
    'Duration of risk assessment in seconds'
)

metrics_anomalies_detected = Counter(
    'supply_chain_anomalies_detected_total',
    'Total number of anomalies detected',
    ['vendor_id', 'anomaly_type']
)


class SupplyChainMonitor:
    """Main supply chain monitoring service"""

    def __init__(self):
        self.vendors: Dict[str, Vendor] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.running = False

        # Configuration
        self.config = {
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'postgres_url': os.getenv('POSTGRES_URL', 'postgresql://localhost:5432/siem'),
            'event_processing_interval': int(os.getenv('EVENT_PROCESSING_INTERVAL', '60')),
            'risk_assessment_interval': int(os.getenv('RISK_ASSESSMENT_INTERVAL', '3600')),
            'anomaly_threshold': float(os.getenv('ANOMALY_THRESHOLD', '0.75')),
        }

    async def start(self):
        """Start the monitoring service"""
        logger.info("Starting Supply Chain Monitor...")

        try:
            # Connect to Redis
            self.redis_client = await aioredis.from_url(
                self.config['redis_url'],
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")

            # Connect to PostgreSQL (commented out for now - would be implemented in production)
            # self.db_pool = await asyncpg.create_pool(self.config['postgres_url'])
            # logger.info("Connected to PostgreSQL")

            # Initialize default vendors
            await self.initialize_default_vendors()

            # Start background tasks
            self.running = True
            asyncio.create_task(self.event_processing_worker())
            asyncio.create_task(self.risk_assessment_worker())
            asyncio.create_task(self.anomaly_detection_worker())

            logger.info("Supply Chain Monitor started successfully")

        except Exception as e:
            logger.error(f"Failed to start Supply Chain Monitor: {e}")
            raise

    async def stop(self):
        """Stop the monitoring service"""
        logger.info("Stopping Supply Chain Monitor...")
        self.running = False

        if self.redis_client:
            await self.redis_client.close()

        if self.db_pool:
            await self.db_pool.close()

        logger.info("Supply Chain Monitor stopped")

    async def initialize_default_vendors(self):
        """Initialize default vendor list"""
        default_vendors = [
            Vendor(
                id="aws",
                name="Amazon Web Services",
                category="infrastructure",
                criticality="critical",
                data_access_level="full",
                tags=["cloud", "infrastructure", "compute"]
            ),
            Vendor(
                id="github",
                name="GitHub",
                category="development",
                criticality="high",
                data_access_level="full",
                tags=["code", "repository", "cicd"]
            ),
            Vendor(
                id="okta",
                name="Okta",
                category="security",
                criticality="critical",
                data_access_level="full",
                tags=["identity", "sso", "authentication"]
            ),
            Vendor(
                id="datadog",
                name="Datadog",
                category="infrastructure",
                criticality="high",
                data_access_level="limited",
                tags=["monitoring", "observability", "apm"]
            ),
            Vendor(
                id="salesforce",
                name="Salesforce",
                category="saas",
                criticality="high",
                data_access_level="limited",
                tags=["crm", "customer-data"]
            ),
        ]

        for vendor in default_vendors:
            self.vendors[vendor.id] = vendor
            logger.info(f"Initialized vendor: {vendor.name} ({vendor.id})")

        metrics_vendors_monitored.set(len(self.vendors))

    async def event_processing_worker(self):
        """Background worker for processing vendor events"""
        while self.running:
            try:
                # Process events from Redis queue
                # In production, this would read from a Kafka topic or Redis stream
                await asyncio.sleep(self.config['event_processing_interval'])

                logger.debug("Event processing cycle completed")

            except Exception as e:
                logger.error(f"Error in event processing worker: {e}")
                await asyncio.sleep(5)

    async def risk_assessment_worker(self):
        """Background worker for vendor risk assessment"""
        while self.running:
            try:
                for vendor_id, vendor in self.vendors.items():
                    if vendor.enabled:
                        assessment = await self.assess_vendor_risk(vendor_id)
                        if assessment:
                            logger.info(
                                f"Risk assessment for {vendor.name}: "
                                f"{assessment.risk_level.value} ({assessment.risk_score:.2f})"
                            )

                await asyncio.sleep(self.config['risk_assessment_interval'])

            except Exception as e:
                logger.error(f"Error in risk assessment worker: {e}")
                await asyncio.sleep(60)

    async def anomaly_detection_worker(self):
        """Background worker for anomaly detection"""
        while self.running:
            try:
                # Detect anomalies in vendor behavior
                # In production, this would use ML models
                await asyncio.sleep(300)  # Check every 5 minutes

                logger.debug("Anomaly detection cycle completed")

            except Exception as e:
                logger.error(f"Error in anomaly detection worker: {e}")
                await asyncio.sleep(30)

    async def assess_vendor_risk(self, vendor_id: str) -> Optional[RiskAssessment]:
        """Assess risk for a specific vendor"""
        vendor = self.vendors.get(vendor_id)
        if not vendor:
            return None

        # Risk factors with weights
        factors = {}

        # Data access level risk (0-25 points)
        access_scores = {
            "full": 25.0,
            "limited": 12.0,
            "none": 0.0
        }
        factors['data_access'] = access_scores.get(vendor.data_access_level, 15.0)

        # Criticality risk (0-25 points)
        criticality_scores = {
            "critical": 25.0,
            "high": 18.0,
            "medium": 10.0,
            "low": 5.0
        }
        factors['criticality'] = criticality_scores.get(vendor.criticality, 10.0)

        # Incident history (0-20 points) - simulated for now
        factors['incident_history'] = 8.0

        # Security posture (0-15 points) - simulated for now
        factors['security_posture'] = 7.0

        # Compliance status (0-15 points) - simulated for now
        factors['compliance'] = 5.0

        # Calculate total risk score
        risk_score = sum(factors.values())

        # Determine risk level
        if risk_score >= 75:
            risk_level = VendorRiskLevel.CRITICAL
        elif risk_score >= 50:
            risk_level = VendorRiskLevel.HIGH
        elif risk_score >= 25:
            risk_level = VendorRiskLevel.MEDIUM
        else:
            risk_level = VendorRiskLevel.LOW

        # Generate recommendations
        recommendations = []
        if factors['data_access'] > 15:
            recommendations.append("Review and minimize data access permissions")
        if factors['incident_history'] > 10:
            recommendations.append("Increase monitoring frequency due to incident history")
        if factors['security_posture'] > 10:
            recommendations.append("Request updated security certifications")

        # Update vendor risk score
        vendor.risk_score = risk_score
        vendor.last_assessment = datetime.utcnow()

        # Update Prometheus metric
        metrics_risk_score.labels(
            vendor_id=vendor.id,
            vendor_name=vendor.name
        ).set(risk_score)

        return RiskAssessment(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            risk_score=risk_score,
            risk_level=risk_level,
            factors=factors,
            recommendations=recommendations,
            timestamp=datetime.utcnow(),
            next_assessment=datetime.utcnow() + timedelta(hours=24)
        )

    async def process_vendor_event(self, event: VendorEventCreate) -> VendorEvent:
        """Process a vendor event"""
        vendor_event = VendorEvent(
            id=f"evt-{datetime.utcnow().timestamp()}",
            vendor_id=event.vendor_id,
            event_type=event.event_type,
            timestamp=datetime.utcnow(),
            severity=event.severity,
            description=event.description,
            source_ip=event.source_ip,
            user=event.user,
            resource=event.resource,
            metadata=event.metadata
        )

        # Update metrics
        metrics_events_processed.labels(
            vendor_id=event.vendor_id,
            event_type=event.event_type.value
        ).inc()

        # Check for anomalies
        is_anomalous = await self.detect_anomaly(vendor_event)
        if is_anomalous:
            metrics_anomalies_detected.labels(
                vendor_id=event.vendor_id,
                anomaly_type=event.event_type.value
            ).inc()
            logger.warning(
                f"Anomaly detected for vendor {event.vendor_id}: {event.description}"
            )

        return vendor_event

    async def detect_anomaly(self, event: VendorEvent) -> bool:
        """Detect if an event is anomalous"""
        # In production, this would use ML models
        # For now, simple heuristics

        # Example: Unusual time of day
        hour = event.timestamp.hour
        if hour < 6 or hour > 22:
            return True

        # Example: High severity events
        if event.severity == "critical":
            return True

        return False


# FastAPI application
app = FastAPI(
    title="Supply Chain Security Monitor",
    description="Monitor third-party vendors and supply chain security",
    version="1.0.0"
)

# Global service instance
monitor = SupplyChainMonitor()


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    await monitor.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    await monitor.stop()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    return {"status": "ready", "vendors_monitored": len(monitor.vendors)}


@app.get("/api/v1/vendors")
async def list_vendors():
    """List all monitored vendors"""
    vendors_list = [
        {
            "id": v.id,
            "name": v.name,
            "category": v.category,
            "criticality": v.criticality,
            "risk_score": v.risk_score,
            "enabled": v.enabled,
            "tags": v.tags
        }
        for v in monitor.vendors.values()
    ]
    return {
        "vendors": vendors_list,
        "count": len(vendors_list)
    }


@app.get("/api/v1/vendors/{vendor_id}")
async def get_vendor(vendor_id: str):
    """Get vendor details"""
    vendor = monitor.vendors.get(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return {
        "id": vendor.id,
        "name": vendor.name,
        "category": vendor.category,
        "criticality": vendor.criticality,
        "data_access_level": vendor.data_access_level,
        "risk_score": vendor.risk_score,
        "last_assessment": vendor.last_assessment,
        "enabled": vendor.enabled,
        "tags": vendor.tags,
        "metadata": vendor.metadata
    }


@app.post("/api/v1/vendors/{vendor_id}/assess")
async def assess_vendor(vendor_id: str):
    """Trigger risk assessment for a vendor"""
    assessment = await monitor.assess_vendor_risk(vendor_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return {
        "vendor_id": assessment.vendor_id,
        "vendor_name": assessment.vendor_name,
        "risk_score": assessment.risk_score,
        "risk_level": assessment.risk_level.value,
        "factors": assessment.factors,
        "recommendations": assessment.recommendations,
        "timestamp": assessment.timestamp.isoformat()
    }


@app.post("/api/v1/events")
async def create_event(event: VendorEventCreate):
    """Create a vendor event"""
    processed_event = await monitor.process_vendor_event(event)
    return {
        "id": processed_event.id,
        "vendor_id": processed_event.vendor_id,
        "event_type": processed_event.event_type.value,
        "timestamp": processed_event.timestamp.isoformat(),
        "severity": processed_event.severity
    }


# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


def main():
    """Main entry point"""
    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
