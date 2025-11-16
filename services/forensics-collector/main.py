#!/usr/bin/env python3
"""
Forensics Evidence Collector Service

This service manages forensic evidence collection, chain of custody tracking,
memory analysis, malware sandbox integration, and timeline reconstruction.
"""

import asyncio
import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvidenceType(str, Enum):
    """Types of forensic evidence"""
    MEMORY_DUMP = "memory_dump"
    DISK_IMAGE = "disk_image"
    FILE = "file"
    NETWORK_CAPTURE = "network_capture"
    LOG_FILE = "log_file"
    MALWARE_SAMPLE = "malware_sample"
    REGISTRY_HIVE = "registry_hive"
    TIMELINE = "timeline"


class EvidenceStatus(str, Enum):
    """Evidence processing status"""
    COLLECTED = "collected"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"
    FAILED = "failed"


class AnalysisType(str, Enum):
    """Types of forensic analysis"""
    MEMORY_ANALYSIS = "memory_analysis"
    MALWARE_ANALYSIS = "malware_analysis"
    FILE_SYSTEM_ANALYSIS = "file_system_analysis"
    TIMELINE_ANALYSIS = "timeline_analysis"
    YARA_SCAN = "yara_scan"


@dataclass
class Evidence:
    """Forensic evidence item"""
    id: str
    evidence_type: EvidenceType
    incident_id: str
    collected_by: str
    collected_at: datetime
    status: EvidenceStatus
    file_path: Optional[str] = None
    file_size: int = 0
    sha256_hash: Optional[str] = None
    md5_hash: Optional[str] = None
    description: str = ""
    metadata: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    chain_of_custody: List[Dict] = field(default_factory=list)


@dataclass
class ChainOfCustodyEntry:
    """Chain of custody tracking entry"""
    timestamp: datetime
    action: str  # collected, transferred, analyzed, accessed
    user: str
    details: str
    hash_verified: bool = False


@dataclass
class MemoryAnalysisResult:
    """Results from memory dump analysis"""
    evidence_id: str
    volatility_profile: str
    processes: List[Dict]
    network_connections: List[Dict]
    loaded_modules: List[Dict]
    suspicious_findings: List[str]
    analysis_timestamp: datetime
    completed_plugins: List[str]


@dataclass
class MalwareAnalysisResult:
    """Results from malware analysis"""
    evidence_id: str
    file_hash: str
    malware_family: Optional[str]
    threat_category: str
    behavior: Dict
    network_iocs: List[str]
    file_iocs: List[str]
    yara_matches: List[str]
    sandbox_url: Optional[str]
    analysis_timestamp: datetime


# Pydantic models for API
class EvidenceCreate(BaseModel):
    evidence_type: EvidenceType
    incident_id: str
    collected_by: str
    description: str = ""
    tags: List[str] = []
    metadata: Dict = {}


class EvidenceUpdate(BaseModel):
    status: Optional[EvidenceStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict] = None


class MemoryAnalysisRequest(BaseModel):
    evidence_id: str
    volatility_profile: str = "Win10x64_19041"
    plugins: List[str] = ["pslist", "netscan", "malfind", "cmdline"]


class MalwareAnalysisRequest(BaseModel):
    evidence_id: str
    sandbox: str = "cuckoo"  # cuckoo, joe, anyrun
    timeout: int = 300


class TimelineRequest(BaseModel):
    incident_id: str
    start_time: datetime
    end_time: datetime
    sources: List[str] = ["events", "logs", "filesystem"]


# Prometheus metrics
metrics_evidence_collected = Counter(
    'forensics_evidence_collected_total',
    'Total evidence items collected',
    ['evidence_type']
)

metrics_analyses_completed = Counter(
    'forensics_analyses_completed_total',
    'Total forensic analyses completed',
    ['analysis_type']
)

metrics_evidence_stored = Gauge(
    'forensics_evidence_stored_bytes',
    'Total evidence storage in bytes'
)

metrics_analysis_duration = Histogram(
    'forensics_analysis_duration_seconds',
    'Duration of forensic analysis',
    ['analysis_type']
)

metrics_chain_violations = Counter(
    'forensics_chain_of_custody_violations_total',
    'Chain of custody violations detected'
)


class ForensicsCollector:
    """Main forensics evidence collection service"""

    def __init__(self):
        self.evidence_store: Dict[str, Evidence] = {}
        self.running = False

        self.config = {
            'storage_path': os.getenv('EVIDENCE_STORAGE_PATH', '/data/evidence'),
            'volatility_path': os.getenv('VOLATILITY_PATH', '/opt/volatility3'),
            'cuckoo_api': os.getenv('CUCKOO_API', 'http://localhost:8090'),
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', str(10 * 1024**3))),  # 10GB
        }

        # Ensure storage path exists
        os.makedirs(self.config['storage_path'], exist_ok=True)

    async def start(self):
        """Start the forensics service"""
        logger.info("Starting Forensics Collector...")

        self.running = True

        # Start background tasks
        asyncio.create_task(self.evidence_monitoring_worker())
        asyncio.create_task(self.hash_verification_worker())

        logger.info("Forensics Collector started successfully")

    async def stop(self):
        """Stop the forensics service"""
        logger.info("Stopping Forensics Collector...")
        self.running = False
        logger.info("Forensics Collector stopped")

    async def evidence_monitoring_worker(self):
        """Monitor evidence processing status"""
        while self.running:
            try:
                # Update storage metrics
                total_size = sum(e.file_size for e in self.evidence_store.values())
                metrics_evidence_stored.set(total_size)

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in evidence monitoring: {e}")
                await asyncio.sleep(10)

    async def hash_verification_worker(self):
        """Periodically verify evidence integrity"""
        while self.running:
            try:
                for evidence_id, evidence in self.evidence_store.items():
                    if evidence.file_path and os.path.exists(evidence.file_path):
                        current_hash = await self.calculate_hash(evidence.file_path)
                        if current_hash != evidence.sha256_hash:
                            logger.error(
                                f"Hash mismatch for evidence {evidence_id}! "
                                f"Possible tampering detected."
                            )
                            metrics_chain_violations.inc()

                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in hash verification: {e}")
                await asyncio.sleep(300)

    async def collect_evidence(
        self,
        evidence_create: EvidenceCreate,
        file: Optional[UploadFile] = None
    ) -> Evidence:
        """Collect and store forensic evidence"""
        evidence_id = str(uuid.uuid4())

        # Create evidence record
        evidence = Evidence(
            id=evidence_id,
            evidence_type=evidence_create.evidence_type,
            incident_id=evidence_create.incident_id,
            collected_by=evidence_create.collected_by,
            collected_at=datetime.utcnow(),
            status=EvidenceStatus.COLLECTED,
            description=evidence_create.description,
            metadata=evidence_create.metadata,
            tags=evidence_create.tags,
        )

        # Add initial chain of custody entry
        evidence.chain_of_custody.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'collected',
            'user': evidence_create.collected_by,
            'details': f'Evidence collected: {evidence_create.description}',
            'hash_verified': False
        })

        # Store file if provided
        if file:
            file_path = os.path.join(
                self.config['storage_path'],
                evidence_id,
                file.filename
            )
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save file and calculate hashes
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)

            evidence.file_path = file_path
            evidence.file_size = len(content)
            evidence.sha256_hash = hashlib.sha256(content).hexdigest()
            evidence.md5_hash = hashlib.md5(content).hexdigest()

            logger.info(
                f"Evidence file stored: {file_path} "
                f"(SHA256: {evidence.sha256_hash})"
            )

        # Store evidence
        self.evidence_store[evidence_id] = evidence

        # Update metrics
        metrics_evidence_collected.labels(
            evidence_type=evidence_create.evidence_type.value
        ).inc()

        logger.info(f"Evidence collected: {evidence_id} ({evidence.evidence_type.value})")

        return evidence

    async def calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def analyze_memory_dump(
        self,
        request: MemoryAnalysisRequest
    ) -> MemoryAnalysisResult:
        """Analyze memory dump using Volatility"""
        evidence = self.evidence_store.get(request.evidence_id)
        if not evidence:
            raise ValueError(f"Evidence not found: {request.evidence_id}")

        if evidence.evidence_type != EvidenceType.MEMORY_DUMP:
            raise ValueError(f"Evidence is not a memory dump")

        logger.info(f"Starting memory analysis for {request.evidence_id}")

        # Update status
        evidence.status = EvidenceStatus.PROCESSING

        # In production, this would run Volatility plugins
        # For now, return simulated results
        result = MemoryAnalysisResult(
            evidence_id=request.evidence_id,
            volatility_profile=request.volatility_profile,
            processes=[
                {"pid": 1234, "name": "explorer.exe", "ppid": 100},
                {"pid": 5678, "name": "suspicious.exe", "ppid": 1234},
            ],
            network_connections=[
                {"local": "192.168.1.100:49152", "remote": "93.184.216.34:443", "state": "ESTABLISHED"},
            ],
            loaded_modules=[],
            suspicious_findings=[
                "Process injection detected in PID 5678",
                "Unsigned driver loaded: malicious.sys",
            ],
            analysis_timestamp=datetime.utcnow(),
            completed_plugins=request.plugins
        )

        # Update evidence status
        evidence.status = EvidenceStatus.ANALYZED
        evidence.chain_of_custody.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'analyzed',
            'user': 'system',
            'details': 'Memory analysis completed',
            'hash_verified': True
        })

        # Update metrics
        metrics_analyses_completed.labels(
            analysis_type=AnalysisType.MEMORY_ANALYSIS.value
        ).inc()

        logger.info(f"Memory analysis completed for {request.evidence_id}")

        return result

    async def analyze_malware(
        self,
        request: MalwareAnalysisRequest
    ) -> MalwareAnalysisResult:
        """Submit malware to sandbox for analysis"""
        evidence = self.evidence_store.get(request.evidence_id)
        if not evidence:
            raise ValueError(f"Evidence not found: {request.evidence_id}")

        logger.info(f"Starting malware analysis for {request.evidence_id}")

        # Update status
        evidence.status = EvidenceStatus.PROCESSING

        # In production, this would submit to actual sandbox
        # For now, return simulated results
        result = MalwareAnalysisResult(
            evidence_id=request.evidence_id,
            file_hash=evidence.sha256_hash or "unknown",
            malware_family="TrojanDownloader.Generic",
            threat_category="trojan",
            behavior={
                "network": ["Connects to C2: 93.184.216.34"],
                "file": ["Creates: C:\\Windows\\Temp\\payload.exe"],
                "registry": ["Modifies: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"],
            },
            network_iocs=["93.184.216.34", "malicious-domain.com"],
            file_iocs=["payload.exe", "malicious.dll"],
            yara_matches=["trojan_generic", "suspicious_strings"],
            sandbox_url=f"http://sandbox.local/analysis/{evidence.id}",
            analysis_timestamp=datetime.utcnow()
        )

        # Update evidence status
        evidence.status = EvidenceStatus.ANALYZED
        evidence.chain_of_custody.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'analyzed',
            'user': 'system',
            'details': f'Malware analysis completed via {request.sandbox}',
            'hash_verified': True
        })

        # Update metrics
        metrics_analyses_completed.labels(
            analysis_type=AnalysisType.MALWARE_ANALYSIS.value
        ).inc()

        logger.info(f"Malware analysis completed for {request.evidence_id}")

        return result

    async def create_timeline(self, request: TimelineRequest) -> Dict:
        """Create investigation timeline"""
        logger.info(f"Creating timeline for incident {request.incident_id}")

        # Collect all evidence for this incident
        incident_evidence = [
            e for e in self.evidence_store.values()
            if e.incident_id == request.incident_id
        ]

        # In production, this would use Plaso/log2timeline
        # For now, return simulated timeline
        timeline_events = [
            {
                "timestamp": request.start_time.isoformat(),
                "source": "filesystem",
                "event": "File created: suspicious.exe",
                "details": {"path": "C:\\Users\\victim\\Downloads\\suspicious.exe"}
            },
            {
                "timestamp": (request.start_time + timedelta(minutes=5)).isoformat(),
                "source": "process",
                "event": "Process execution: suspicious.exe",
                "details": {"pid": 5678, "command_line": "suspicious.exe --install"}
            },
            {
                "timestamp": (request.start_time + timedelta(minutes=10)).isoformat(),
                "source": "network",
                "event": "Outbound connection to C2",
                "details": {"remote_ip": "93.184.216.34", "port": 443}
            },
        ]

        # Update metrics
        metrics_analyses_completed.labels(
            analysis_type=AnalysisType.TIMELINE_ANALYSIS.value
        ).inc()

        return {
            "incident_id": request.incident_id,
            "timeline_events": timeline_events,
            "event_count": len(timeline_events),
            "time_range": {
                "start": request.start_time.isoformat(),
                "end": request.end_time.isoformat()
            },
            "sources": request.sources,
            "evidence_count": len(incident_evidence)
        }


# FastAPI application
app = FastAPI(
    title="Forensics Evidence Collector",
    description="Forensic evidence collection and analysis service",
    version="1.0.0"
)

# Global service instance
collector = ForensicsCollector()


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    await collector.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    await collector.stop()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    return {"status": "ready", "evidence_count": len(collector.evidence_store)}


@app.get("/api/v1/evidence")
async def list_evidence(incident_id: Optional[str] = None):
    """List all evidence items"""
    evidence_list = list(collector.evidence_store.values())

    if incident_id:
        evidence_list = [e for e in evidence_list if e.incident_id == incident_id]

    return {
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type.value,
                "incident_id": e.incident_id,
                "collected_by": e.collected_by,
                "collected_at": e.collected_at.isoformat(),
                "status": e.status.value,
                "file_size": e.file_size,
                "sha256_hash": e.sha256_hash,
                "tags": e.tags
            }
            for e in evidence_list
        ],
        "count": len(evidence_list)
    }


@app.get("/api/v1/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """Get evidence details"""
    evidence = collector.evidence_store.get(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return {
        "id": evidence.id,
        "evidence_type": evidence.evidence_type.value,
        "incident_id": evidence.incident_id,
        "collected_by": evidence.collected_by,
        "collected_at": evidence.collected_at.isoformat(),
        "status": evidence.status.value,
        "file_path": evidence.file_path,
        "file_size": evidence.file_size,
        "sha256_hash": evidence.sha256_hash,
        "md5_hash": evidence.md5_hash,
        "description": evidence.description,
        "metadata": evidence.metadata,
        "tags": evidence.tags,
        "chain_of_custody": evidence.chain_of_custody
    }


@app.post("/api/v1/evidence")
async def create_evidence(
    evidence_type: str,
    incident_id: str,
    collected_by: str,
    description: str = "",
    file: Optional[UploadFile] = File(None)
):
    """Collect new evidence"""
    evidence_create = EvidenceCreate(
        evidence_type=EvidenceType(evidence_type),
        incident_id=incident_id,
        collected_by=collected_by,
        description=description
    )

    evidence = await collector.collect_evidence(evidence_create, file)

    return {
        "id": evidence.id,
        "evidence_type": evidence.evidence_type.value,
        "incident_id": evidence.incident_id,
        "status": evidence.status.value,
        "sha256_hash": evidence.sha256_hash
    }


@app.post("/api/v1/analyze/memory")
async def analyze_memory(request: MemoryAnalysisRequest):
    """Analyze memory dump"""
    result = await collector.analyze_memory_dump(request)

    return {
        "evidence_id": result.evidence_id,
        "volatility_profile": result.volatility_profile,
        "processes": result.processes,
        "network_connections": result.network_connections,
        "suspicious_findings": result.suspicious_findings,
        "analysis_timestamp": result.analysis_timestamp.isoformat()
    }


@app.post("/api/v1/analyze/malware")
async def analyze_malware(request: MalwareAnalysisRequest):
    """Analyze malware sample"""
    result = await collector.analyze_malware(request)

    return {
        "evidence_id": result.evidence_id,
        "file_hash": result.file_hash,
        "malware_family": result.malware_family,
        "threat_category": result.threat_category,
        "behavior": result.behavior,
        "network_iocs": result.network_iocs,
        "file_iocs": result.file_iocs,
        "yara_matches": result.yara_matches,
        "sandbox_url": result.sandbox_url,
        "analysis_timestamp": result.analysis_timestamp.isoformat()
    }


@app.post("/api/v1/timeline")
async def create_timeline(request: TimelineRequest):
    """Create investigation timeline"""
    timeline = await collector.create_timeline(request)
    return timeline


# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


def main():
    """Main entry point"""
    port = int(os.getenv("PORT", "8082"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
