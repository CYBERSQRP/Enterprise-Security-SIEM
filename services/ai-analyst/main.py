"""
AI Security Analyst Service - FastAPI Application

Provides intelligent AI-powered security analysis, automated triage,
and investigation recommendations.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uvicorn

from assistant import (
    AISecurityAnalyst,
    SecurityEvent,
    ThreatSeverity,
    InvestigationStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
analysis_requests = Counter(
    'ai_analyst_requests_total',
    'Total number of analysis requests',
    ['severity']
)
analysis_duration = Histogram(
    'ai_analyst_duration_seconds',
    'Time spent analyzing alerts'
)

# Global analyst instance
analyst: Optional[AISecurityAnalyst] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global analyst

    # Startup
    logger.info("Starting AI Security Analyst Service...")
    analyst = AISecurityAnalyst()
    logger.info("AI Security Analyst Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AI Security Analyst Service...")


app = FastAPI(
    title="AI Security Analyst Service",
    description="Intelligent AI-powered security analysis and investigation assistance",
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
class SecurityEventRequest(BaseModel):
    """Security event analysis request."""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., description="Event severity (critical, high, medium, low, info)")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    dest_ip: Optional[str] = Field(None, description="Destination IP address")
    user: Optional[str] = Field(None, description="User involved")
    process: Optional[str] = Field(None, description="Process name")
    raw_log: str = Field("", description="Raw log data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ThreatContextResponse(BaseModel):
    """Threat context information."""
    threat_type: str
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    iocs: List[str]
    confidence_score: float
    risk_score: float
    affected_assets: List[str]


class InvestigationRecommendationResponse(BaseModel):
    """Investigation recommendation."""
    recommendation_type: str
    priority: int
    description: str
    action_items: List[str]
    rationale: str
    estimated_impact: str
    confidence: float


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    event_id: str
    threat_context: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    related_events_count: int
    recommendations: List[Dict[str, Any]]
    next_steps: List[str]
    triage_decision: Dict[str, Any]
    timestamp: str


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
        service="ai-analyst",
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


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_event(request: SecurityEventRequest):
    """
    Analyze a security event and provide AI-powered insights.

    Returns comprehensive analysis including:
    - Threat context and MITRE ATT&CK mapping
    - Risk assessment
    - Investigation recommendations
    - Automated triage decision
    - Next steps for analysts
    """
    try:
        with analysis_duration.time():
            # Convert request to SecurityEvent
            severity_map = {
                'critical': ThreatSeverity.CRITICAL,
                'high': ThreatSeverity.HIGH,
                'medium': ThreatSeverity.MEDIUM,
                'low': ThreatSeverity.LOW,
                'info': ThreatSeverity.INFO
            }

            event = SecurityEvent(
                event_id=request.event_id,
                timestamp=request.timestamp,
                event_type=request.event_type,
                severity=severity_map.get(request.severity.lower(), ThreatSeverity.MEDIUM),
                source_ip=request.source_ip,
                dest_ip=request.dest_ip,
                user=request.user,
                process=request.process,
                raw_log=request.raw_log,
                metadata=request.metadata
            )

            # Analyze the event
            analysis = await analyst.analyze_alert(event)

            # Record metrics
            analysis_requests.labels(
                severity=request.severity
            ).inc()

            # Convert ThreatContext to dict
            threat_context = analysis['threat_context']
            threat_context_dict = {
                'threat_type': threat_context.threat_type,
                'mitre_tactics': threat_context.mitre_tactics,
                'mitre_techniques': threat_context.mitre_techniques,
                'iocs': threat_context.iocs,
                'confidence_score': threat_context.confidence_score,
                'risk_score': threat_context.risk_score,
                'affected_assets': threat_context.affected_assets,
                'timeline': threat_context.timeline
            }

            # Convert recommendations to dict
            recommendations_list = []
            for rec in analysis['recommendations']:
                recommendations_list.append({
                    'recommendation_type': rec.recommendation_type,
                    'priority': rec.priority,
                    'description': rec.description,
                    'action_items': rec.action_items,
                    'rationale': rec.rationale,
                    'estimated_impact': rec.estimated_impact,
                    'confidence': rec.confidence
                })

            return AnalysisResponse(
                event_id=analysis['event_id'],
                threat_context=threat_context_dict,
                risk_assessment=analysis['risk_assessment'],
                related_events_count=len(analysis['related_events']),
                recommendations=recommendations_list,
                next_steps=analysis['next_steps'],
                triage_decision=analysis['triage_decision'],
                timestamp=analysis['timestamp']
            )

    except Exception as e:
        logger.error(f"Error analyzing event {request.event_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/triage")
async def triage_alert(request: SecurityEventRequest):
    """
    Perform automated triage on a security alert.

    Returns triage decision without full analysis for faster processing.
    """
    try:
        # Convert request to SecurityEvent
        severity_map = {
            'critical': ThreatSeverity.CRITICAL,
            'high': ThreatSeverity.HIGH,
            'medium': ThreatSeverity.MEDIUM,
            'low': ThreatSeverity.LOW,
            'info': ThreatSeverity.INFO
        }

        event = SecurityEvent(
            event_id=request.event_id,
            timestamp=request.timestamp,
            event_type=request.event_type,
            severity=severity_map.get(request.severity.lower(), ThreatSeverity.MEDIUM),
            source_ip=request.source_ip,
            dest_ip=request.dest_ip,
            user=request.user,
            process=request.process,
            raw_log=request.raw_log,
            metadata=request.metadata
        )

        # Perform quick triage
        threat_context = await analyst._gather_threat_context(event)
        risk_assessment = analyst.risk_calculator.calculate_risk(event, threat_context)
        triage_decision = analyst._auto_triage(event, threat_context, risk_assessment)

        return {
            'event_id': event.event_id,
            'triage_decision': triage_decision,
            'threat_context': {
                'risk_score': threat_context.risk_score,
                'confidence_score': threat_context.confidence_score,
                'ioc_count': len(threat_context.iocs)
            }
        }

    except Exception as e:
        logger.error(f"Error triaging event {request.event_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/mitre/{event_type}")
async def get_mitre_mapping(event_type: str):
    """Get MITRE ATT&CK mapping for an event type."""
    try:
        mapping = analyst.knowledge_base.map_to_mitre(event_type)
        return {
            'event_type': event_type,
            'mapping': mapping
        }
    except Exception as e:
        logger.error(f"Error getting MITRE mapping: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get service statistics."""
    return {
        "service": "ai-analyst",
        "uptime": "healthy",
        "analyst_loaded": analyst is not None,
        "statistics": {
            "total_analyzed": "See /metrics endpoint",
            "average_analysis_time": "See /metrics endpoint"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8091"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "production") == "development"
    )
