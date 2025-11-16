"""
Alert Prioritization Service - FastAPI Application

This service provides intelligent alert prioritization using ML and rule-based logic.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uvicorn

from prioritizer import (
    IntelligentAlertPrioritizer,
    Alert,
    AlertPriority,
    PrioritizationResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
prioritization_requests = Counter(
    'alert_prioritization_requests_total',
    'Total number of alert prioritization requests',
    ['priority_level']
)
prioritization_duration = Histogram(
    'alert_prioritization_duration_seconds',
    'Time spent prioritizing alerts'
)

# Global prioritizer instance
prioritizer: Optional[IntelligentAlertPrioritizer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global prioritizer

    # Startup
    logger.info("Starting Alert Prioritization Service...")
    model_path = os.getenv('MODEL_PATH')
    prioritizer = IntelligentAlertPrioritizer(model_path=model_path)
    logger.info("Alert Prioritization Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Alert Prioritization Service...")


app = FastAPI(
    title="Alert Prioritization Service",
    description="Intelligent alert prioritization using ML and rule-based logic",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class AlertRequest(BaseModel):
    """Alert prioritization request."""
    alert_id: str = Field(..., description="Unique alert identifier")
    timestamp: datetime = Field(..., description="Alert timestamp")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity (critical, high, medium, low, info)")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    dest_ip: Optional[str] = Field(None, description="Destination IP address")
    user: Optional[str] = Field(None, description="User involved")
    asset: Optional[str] = Field(None, description="Asset involved")
    description: str = Field(..., description="Alert description")
    raw_score: float = Field(0.5, description="Raw alert score")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")


class PrioritizationResponse(BaseModel):
    """Alert prioritization response."""
    alert_id: str
    priority: str
    priority_score: float
    factors: Dict[str, float]
    recommended_sla_minutes: int
    reasoning: List[str]
    auto_actions: List[str]


class BatchPrioritizationRequest(BaseModel):
    """Batch alert prioritization request."""
    alerts: List[AlertRequest]


class BatchPrioritizationResponse(BaseModel):
    """Batch alert prioritization response."""
    results: List[PrioritizationResponse]
    total_processed: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="alert-prioritization",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/api/v1/prioritize", response_model=PrioritizationResponse)
async def prioritize_alert(request: AlertRequest):
    """
    Prioritize a single alert.

    Returns priority level, score, reasoning, and recommended actions.
    """
    try:
        with prioritization_duration.time():
            # Convert request to Alert object
            alert = Alert(
                alert_id=request.alert_id,
                timestamp=request.timestamp,
                alert_type=request.alert_type,
                severity=request.severity,
                source_ip=request.source_ip,
                dest_ip=request.dest_ip,
                user=request.user,
                asset=request.asset,
                description=request.description,
                raw_score=request.raw_score,
                metadata=request.metadata
            )

            # Prioritize alert
            result = prioritizer.prioritize_alert(alert)

            # Record metrics
            prioritization_requests.labels(
                priority_level=result.priority.name
            ).inc()

            # Convert timedelta to minutes
            sla_minutes = int(result.recommended_sla.total_seconds() / 60)

            return PrioritizationResponse(
                alert_id=result.alert_id,
                priority=result.priority.name,
                priority_score=result.priority_score,
                factors=result.factors,
                recommended_sla_minutes=sla_minutes,
                reasoning=result.reasoning,
                auto_actions=result.auto_actions
            )

    except Exception as e:
        logger.error(f"Error prioritizing alert {request.alert_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/prioritize/batch", response_model=BatchPrioritizationResponse)
async def prioritize_alerts_batch(request: BatchPrioritizationRequest):
    """
    Prioritize multiple alerts in batch.

    More efficient than individual requests for bulk processing.
    """
    try:
        with prioritization_duration.time():
            # Convert requests to Alert objects
            alerts = []
            for req in request.alerts:
                alert = Alert(
                    alert_id=req.alert_id,
                    timestamp=req.timestamp,
                    alert_type=req.alert_type,
                    severity=req.severity,
                    source_ip=req.source_ip,
                    dest_ip=req.dest_ip,
                    user=req.user,
                    asset=req.asset,
                    description=req.description,
                    raw_score=req.raw_score,
                    metadata=req.metadata
                )
                alerts.append(alert)

            # Prioritize all alerts
            results = prioritizer.prioritize_batch(alerts)

            # Convert results to response format
            responses = []
            for result in results:
                prioritization_requests.labels(
                    priority_level=result.priority.name
                ).inc()

                sla_minutes = int(result.recommended_sla.total_seconds() / 60)

                responses.append(PrioritizationResponse(
                    alert_id=result.alert_id,
                    priority=result.priority.name,
                    priority_score=result.priority_score,
                    factors=result.factors,
                    recommended_sla_minutes=sla_minutes,
                    reasoning=result.reasoning,
                    auto_actions=result.auto_actions
                ))

            return BatchPrioritizationResponse(
                results=responses,
                total_processed=len(responses)
            )

    except Exception as e:
        logger.error(f"Error in batch prioritization: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get prioritization statistics."""
    # This would typically query a database for historical stats
    return {
        "service": "alert-prioritization",
        "uptime": "healthy",
        "model_loaded": prioritizer is not None,
        "statistics": {
            "total_prioritized": "See /metrics endpoint",
            "average_processing_time": "See /metrics endpoint"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8090"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "production") == "development"
    )
