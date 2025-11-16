"""
Digital Forensics Investigation Service - FastAPI Application

Provides forensic evidence collection, timeline analysis,
and investigation management capabilities.
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

from investigator import (
    ForensicInvestigator,
    ForensicCase,
    Evidence,
    EvidenceType,
    ForensicState
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
investigation_requests = Counter(
    'forensics_investigation_requests_total',
    'Total number of forensic investigation requests',
    ['case_state']
)
evidence_collection_requests = Counter(
    'forensics_evidence_collection_total',
    'Total number of evidence collection requests',
    ['evidence_type']
)
investigation_duration = Histogram(
    'forensics_investigation_duration_seconds',
    'Time spent on forensic investigations'
)

# Global investigator instance
investigator: Optional[ForensicInvestigator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global investigator

    # Startup
    logger.info("Starting Digital Forensics Investigation Service...")
    investigator = ForensicInvestigator()
    logger.info("Digital Forensics Investigation Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Digital Forensics Investigation Service...")


app = FastAPI(
    title="Digital Forensics Investigation Service",
    description="Advanced forensic investigation capabilities including evidence collection and timeline analysis",
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
class CreateCaseRequest(BaseModel):
    """Create forensic case request."""
    case_name: str = Field(..., description="Name of the forensic case")
    incident_id: str = Field(..., description="Related incident ID")
    investigator: str = Field(..., description="Lead investigator name")


class CollectEvidenceRequest(BaseModel):
    """Evidence collection request."""
    case_id: str = Field(..., description="Case ID")
    evidence_type: str = Field(..., description="Type of evidence (memory_dump, disk_image, network_pcap, log_file)")
    target_system: str = Field(..., description="Target system to collect from")
    collector: str = Field(..., description="Person collecting evidence")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Collection parameters")


class InvestigationRequest(BaseModel):
    """Investigation execution request."""
    case_id: str = Field(..., description="Case ID")
    target_systems: List[str] = Field(..., description="Systems to investigate")


class CaseResponse(BaseModel):
    """Forensic case response."""
    case_id: str
    case_name: str
    incident_id: str
    investigator: str
    created_at: str
    state: str
    evidence_count: int
    findings_count: int


class EvidenceResponse(BaseModel):
    """Evidence item response."""
    evidence_id: str
    evidence_type: str
    description: str
    source_system: str
    collection_timestamp: str
    collector: str
    hash_sha256: Optional[str]
    chain_of_custody_entries: int


class InvestigationResultResponse(BaseModel):
    """Investigation result response."""
    case_id: str
    evidence_count: int
    timeline_events: int
    findings_count: int
    recommendations: List[str]


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
        service="forensics-investigation",
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


@app.post("/api/v1/cases", response_model=CaseResponse)
async def create_case(request: CreateCaseRequest):
    """
    Create a new forensic investigation case.

    Returns case details including unique case ID.
    """
    try:
        case = investigator.create_case(
            case_name=request.case_name,
            incident_id=request.incident_id,
            investigator=request.investigator
        )

        investigation_requests.labels(
            case_state=case.state.value
        ).inc()

        return CaseResponse(
            case_id=case.case_id,
            case_name=case.case_name,
            incident_id=case.incident_id,
            investigator=case.investigator,
            created_at=case.created_at.isoformat(),
            state=case.state.value,
            evidence_count=len(case.evidence_items),
            findings_count=len(case.findings)
        )

    except Exception as e:
        logger.error(f"Error creating forensic case: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    """Get forensic case details."""
    try:
        case = investigator.cases.get(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

        return CaseResponse(
            case_id=case.case_id,
            case_name=case.case_name,
            incident_id=case.incident_id,
            investigator=case.investigator,
            created_at=case.created_at.isoformat(),
            state=case.state.value,
            evidence_count=len(case.evidence_items),
            findings_count=len(case.findings)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case {case_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/evidence/collect", response_model=EvidenceResponse)
async def collect_evidence(request: CollectEvidenceRequest):
    """
    Collect forensic evidence from a target system.

    Supports multiple evidence types:
    - memory_dump: Memory dump from target system
    - disk_image: Forensic disk image
    - network_pcap: Network traffic capture
    - log_file: Log file collection
    """
    try:
        case = investigator.cases.get(request.case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

        evidence = None
        evidence_type_map = {
            'memory_dump': EvidenceType.MEMORY_DUMP,
            'disk_image': EvidenceType.DISK_IMAGE,
            'network_pcap': EvidenceType.NETWORK_PCAP,
            'log_file': EvidenceType.LOG_FILE
        }

        if request.evidence_type == 'memory_dump':
            evidence = investigator.evidence_collector.collect_memory_dump(
                target_system=request.target_system,
                case_id=request.case_id,
                collector=request.collector
            )
        elif request.evidence_type == 'disk_image':
            evidence = investigator.evidence_collector.collect_disk_image(
                target_system=request.target_system,
                drive=request.parameters.get('drive', 'C:'),
                case_id=request.case_id,
                collector=request.collector
            )
        elif request.evidence_type == 'network_pcap':
            evidence = investigator.evidence_collector.collect_network_capture(
                target_interface=request.target_system,
                duration_seconds=request.parameters.get('duration_seconds', 60),
                case_id=request.case_id,
                collector=request.collector,
                filter_expression=request.parameters.get('filter')
            )
        elif request.evidence_type == 'log_file':
            from datetime import timedelta
            evidence = investigator.evidence_collector.collect_logs(
                target_system=request.target_system,
                log_paths=request.parameters.get('log_paths', ['/var/log/syslog']),
                start_time=datetime.utcnow() - timedelta(days=7),
                end_time=datetime.utcnow(),
                case_id=request.case_id,
                collector=request.collector
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported evidence type: {request.evidence_type}")

        # Add to case
        case.evidence_items.append(evidence)

        # Record metrics
        evidence_collection_requests.labels(
            evidence_type=request.evidence_type
        ).inc()

        return EvidenceResponse(
            evidence_id=evidence.evidence_id,
            evidence_type=evidence.evidence_type.value,
            description=evidence.description,
            source_system=evidence.source_system,
            collection_timestamp=evidence.collection_timestamp.isoformat(),
            collector=evidence.collector,
            hash_sha256=evidence.hash_sha256,
            chain_of_custody_entries=len(evidence.chain_of_custody)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting evidence: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/investigations/conduct", response_model=InvestigationResultResponse)
async def conduct_investigation(request: InvestigationRequest):
    """
    Conduct comprehensive forensic investigation.

    This will:
    1. Collect evidence from target systems
    2. Create forensic timeline
    3. Analyze artifacts
    4. Generate findings
    5. Provide recommendations
    """
    try:
        with investigation_duration.time():
            case = investigator.cases.get(request.case_id)
            if not case:
                raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

            result = investigator.conduct_investigation(
                case=case,
                target_systems=request.target_systems
            )

            investigation_requests.labels(
                case_state=case.state.value
            ).inc()

            return InvestigationResultResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conducting investigation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cases/{case_id}/report")
async def generate_report(case_id: str):
    """Generate forensic investigation report."""
    try:
        case = investigator.cases.get(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

        report = investigator.generate_report(case)
        return Response(content=report, media_type="application/json")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cases/{case_id}/timeline")
async def get_timeline(case_id: str):
    """Get forensic timeline for case."""
    try:
        case = investigator.cases.get(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

        if not case.timeline:
            return {"message": "No timeline available for this case"}

        timeline_viz = investigator.timeline_analyzer.visualize_timeline(
            case.timeline,
            output_format='json'
        )

        return Response(content=timeline_viz, media_type="application/json")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving timeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get forensic service statistics."""
    return {
        "service": "forensics-investigation",
        "uptime": "healthy",
        "total_cases": len(investigator.cases),
        "statistics": {
            "total_investigations": "See /metrics endpoint",
            "total_evidence_collected": "See /metrics endpoint"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8092"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "production") == "development"
    )
