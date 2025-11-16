"""
Digital Forensics and Investigation Tools

This module provides advanced forensic investigation capabilities including
evidence collection, timeline analysis, and chain of custody management.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of digital evidence."""
    MEMORY_DUMP = "memory_dump"
    DISK_IMAGE = "disk_image"
    NETWORK_PCAP = "network_pcap"
    LOG_FILE = "log_file"
    REGISTRY_HIVE = "registry_hive"
    FILE_ARTIFACT = "file_artifact"
    PROCESS_DUMP = "process_dump"
    BROWSER_ARTIFACT = "browser_artifact"
    EMAIL = "email"
    DATABASE_EXPORT = "database_export"


class ForensicState(Enum):
    """States in forensic investigation."""
    INITIAL = "initial"
    COLLECTION = "collection"
    PRESERVATION = "preservation"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    CLOSED = "closed"


@dataclass
class Evidence:
    """Represents a piece of digital evidence."""
    evidence_id: str
    evidence_type: EvidenceType
    description: str
    source_system: str
    collection_timestamp: datetime
    collector: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    hash_md5: Optional[str] = None
    hash_sha256: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    chain_of_custody: List[Dict] = field(default_factory=list)


@dataclass
class ForensicTimeline:
    """Timeline of events for forensic analysis."""
    timeline_id: str
    case_id: str
    events: List[Dict] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class ForensicCase:
    """Represents a forensic investigation case."""
    case_id: str
    case_name: str
    incident_id: str
    investigator: str
    created_at: datetime
    state: ForensicState
    evidence_items: List[Evidence] = field(default_factory=list)
    timeline: Optional[ForensicTimeline] = None
    findings: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class EvidenceCollector:
    """Collects and preserves digital evidence."""

    def __init__(self, evidence_storage_path: str = "/forensics/evidence"):
        self.storage_path = Path(evidence_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def collect_memory_dump(
        self,
        target_system: str,
        case_id: str,
        collector: str
    ) -> Evidence:
        """Collect memory dump from target system."""
        logger.info(f"Collecting memory dump from {target_system}")

        evidence_id = f"MEM-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # In production, this would:
        # 1. Connect to target system
        # 2. Use tools like WinPmem, LiME, or FTK Imager
        # 3. Stream memory dump to secure storage
        # 4. Calculate hashes during collection

        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type=EvidenceType.MEMORY_DUMP,
            description=f"Memory dump from {target_system}",
            source_system=target_system,
            collection_timestamp=datetime.utcnow(),
            collector=collector,
            metadata={
                'collection_method': 'winpmem',
                'system_info': self._get_system_info(target_system)
            }
        )

        # Add to chain of custody
        self._update_chain_of_custody(
            evidence,
            action="collected",
            performer=collector,
            notes=f"Memory dump collected from {target_system}"
        )

        return evidence

    def collect_disk_image(
        self,
        target_system: str,
        drive: str,
        case_id: str,
        collector: str
    ) -> Evidence:
        """Collect disk image from target system."""
        logger.info(f"Collecting disk image from {target_system}:{drive}")

        evidence_id = f"DISK-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # In production, this would:
        # 1. Use dd, FTK Imager, or EnCase
        # 2. Create forensically sound image (E01 or raw)
        # 3. Verify image integrity
        # 4. Calculate hashes

        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type=EvidenceType.DISK_IMAGE,
            description=f"Disk image of {drive} from {target_system}",
            source_system=target_system,
            collection_timestamp=datetime.utcnow(),
            collector=collector,
            metadata={
                'drive': drive,
                'imaging_tool': 'dd',
                'compression': 'none',
                'encryption': 'AES-256'
            }
        )

        self._update_chain_of_custody(
            evidence,
            action="collected",
            performer=collector,
            notes=f"Disk image collected from {target_system}:{drive}"
        )

        return evidence

    def collect_network_capture(
        self,
        target_interface: str,
        duration_seconds: int,
        case_id: str,
        collector: str,
        filter_expression: Optional[str] = None
    ) -> Evidence:
        """Collect network traffic capture."""
        logger.info(f"Collecting network capture on {target_interface}")

        evidence_id = f"PCAP-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # In production, this would:
        # 1. Use tcpdump or Wireshark
        # 2. Apply BPF filter if specified
        # 3. Capture for specified duration
        # 4. Save PCAP file

        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type=EvidenceType.NETWORK_PCAP,
            description=f"Network capture from {target_interface}",
            source_system=target_interface,
            collection_timestamp=datetime.utcnow(),
            collector=collector,
            metadata={
                'duration_seconds': duration_seconds,
                'filter': filter_expression,
                'capture_tool': 'tcpdump'
            }
        )

        self._update_chain_of_custody(
            evidence,
            action="collected",
            performer=collector,
            notes=f"Network capture collected for {duration_seconds}s"
        )

        return evidence

    def collect_logs(
        self,
        target_system: str,
        log_paths: List[str],
        start_time: datetime,
        end_time: datetime,
        case_id: str,
        collector: str
    ) -> Evidence:
        """Collect relevant log files."""
        logger.info(f"Collecting logs from {target_system}")

        evidence_id = f"LOG-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type=EvidenceType.LOG_FILE,
            description=f"Log files from {target_system}",
            source_system=target_system,
            collection_timestamp=datetime.utcnow(),
            collector=collector,
            metadata={
                'log_paths': log_paths,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        )

        self._update_chain_of_custody(
            evidence,
            action="collected",
            performer=collector,
            notes=f"Collected {len(log_paths)} log files"
        )

        return evidence

    def preserve_evidence(self, evidence: Evidence, storage_location: str) -> bool:
        """
        Preserve evidence with cryptographic hashing and secure storage.

        Args:
            evidence: Evidence object to preserve
            storage_location: Path to store evidence

        Returns:
            True if preservation successful
        """
        logger.info(f"Preserving evidence {evidence.evidence_id}")

        # Calculate hashes
        if evidence.file_path:
            evidence.hash_md5 = self._calculate_hash(evidence.file_path, 'md5')
            evidence.hash_sha256 = self._calculate_hash(evidence.file_path, 'sha256')

        # Update chain of custody
        self._update_chain_of_custody(
            evidence,
            action="preserved",
            performer="system",
            notes=f"Evidence preserved at {storage_location}"
        )

        # In production, this would:
        # 1. Encrypt evidence file
        # 2. Store in secure evidence locker
        # 3. Create write-protect flag
        # 4. Log to audit trail

        return True

    def _calculate_hash(self, file_path: str, algorithm: str) -> str:
        """Calculate cryptographic hash of file."""
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash: {e}")
            return ""

    def _update_chain_of_custody(
        self,
        evidence: Evidence,
        action: str,
        performer: str,
        notes: str
    ):
        """Update chain of custody for evidence."""
        custody_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'performer': performer,
            'notes': notes
        }
        evidence.chain_of_custody.append(custody_entry)

    def _get_system_info(self, target_system: str) -> Dict:
        """Get system information from target."""
        # Placeholder - would collect actual system info
        return {
            'hostname': target_system,
            'os': 'Windows 10',
            'os_version': '10.0.19044',
            'architecture': 'x86_64'
        }


class TimelineAnalyzer:
    """Analyzes and reconstructs timeline of events."""

    def __init__(self):
        self.timeline_events = []

    def create_timeline(
        self,
        case_id: str,
        evidence_items: List[Evidence],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> ForensicTimeline:
        """
        Create forensic timeline from evidence.

        Args:
            case_id: Case identifier
            evidence_items: List of evidence to analyze
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            ForensicTimeline object
        """
        logger.info(f"Creating timeline for case {case_id}")

        timeline_id = f"TL-{case_id}"
        timeline = ForensicTimeline(
            timeline_id=timeline_id,
            case_id=case_id,
            start_time=start_time,
            end_time=end_time
        )

        # Extract events from each evidence item
        for evidence in evidence_items:
            events = self._extract_events_from_evidence(evidence)
            timeline.events.extend(events)

        # Sort events chronologically
        timeline.events.sort(key=lambda x: x['timestamp'])

        # Set timeline bounds
        if timeline.events:
            timeline.start_time = datetime.fromisoformat(timeline.events[0]['timestamp'])
            timeline.end_time = datetime.fromisoformat(timeline.events[-1]['timestamp'])

        return timeline

    def _extract_events_from_evidence(self, evidence: Evidence) -> List[Dict]:
        """Extract timeline events from evidence."""
        events = []

        # Add evidence collection as an event
        events.append({
            'timestamp': evidence.collection_timestamp.isoformat(),
            'event_type': 'evidence_collection',
            'description': f"Evidence collected: {evidence.description}",
            'source': evidence.source_system,
            'evidence_id': evidence.evidence_id
        })

        # In production, this would parse evidence files to extract events:
        # - Parse Windows Event Logs (EVTX)
        # - Parse Linux syslogs
        # - Extract filesystem timestamps (MFT, journal)
        # - Parse browser history
        # - Extract registry modifications
        # - Parse email headers

        return events

    def visualize_timeline(
        self,
        timeline: ForensicTimeline,
        output_format: str = 'json'
    ) -> str:
        """Generate visualization of timeline."""
        if output_format == 'json':
            return json.dumps({
                'timeline_id': timeline.timeline_id,
                'case_id': timeline.case_id,
                'event_count': len(timeline.events),
                'start_time': timeline.start_time.isoformat() if timeline.start_time else None,
                'end_time': timeline.end_time.isoformat() if timeline.end_time else None,
                'events': timeline.events
            }, indent=2)

        # Could also generate HTML, CSV, or other formats
        return ""


class ArtifactAnalyzer:
    """Analyzes forensic artifacts for evidence."""

    def analyze_windows_artifacts(
        self,
        evidence: Evidence
    ) -> Dict[str, List[Dict]]:
        """Analyze Windows-specific artifacts."""
        artifacts = {
            'registry_keys': [],
            'event_logs': [],
            'prefetch': [],
            'amcache': [],
            'shimcache': [],
            'user_profiles': [],
            'scheduled_tasks': [],
            'services': []
        }

        # In production, this would:
        # 1. Parse registry hives (NTUSER.DAT, SOFTWARE, SYSTEM, etc.)
        # 2. Extract Windows Event Logs
        # 3. Parse Prefetch files
        # 4. Analyze AmCache.hve
        # 5. Extract ShimCache entries
        # 6. Analyze user profiles
        # 7. Extract scheduled tasks
        # 8. Enumerate services

        return artifacts

    def analyze_linux_artifacts(
        self,
        evidence: Evidence
    ) -> Dict[str, List[Dict]]:
        """Analyze Linux-specific artifacts."""
        artifacts = {
            'bash_history': [],
            'auth_logs': [],
            'cron_jobs': [],
            'systemd_services': [],
            'network_connections': [],
            'user_accounts': [],
            'sudo_logs': []
        }

        # In production, this would parse Linux artifacts

        return artifacts

    def analyze_network_traffic(
        self,
        pcap_evidence: Evidence
    ) -> Dict[str, any]:
        """Analyze network traffic from PCAP."""
        analysis = {
            'total_packets': 0,
            'protocols': {},
            'conversations': [],
            'dns_queries': [],
            'http_requests': [],
            'suspicious_ips': [],
            'data_transferred': 0
        }

        # In production, this would:
        # 1. Use dpkt, scapy, or pyshark to parse PCAP
        # 2. Extract protocols and conversations
        # 3. Identify suspicious patterns
        # 4. Extract IOCs
        # 5. Calculate data transfer volumes

        return analysis

    def analyze_memory_dump(
        self,
        memory_evidence: Evidence
    ) -> Dict[str, any]:
        """Analyze memory dump for artifacts."""
        analysis = {
            'processes': [],
            'network_connections': [],
            'loaded_dlls': [],
            'registry_in_memory': [],
            'injected_code': [],
            'suspicious_strings': [],
            'malware_detected': []
        }

        # In production, this would use Volatility framework:
        # 1. List processes (pslist, pstree)
        # 2. Extract network connections (netscan)
        # 3. List loaded DLLs (dlllist)
        # 4. Detect code injection (malfind)
        # 5. Extract strings
        # 6. Scan for malware signatures

        return analysis


class ForensicInvestigator:
    """Main forensic investigation orchestrator."""

    def __init__(self):
        self.evidence_collector = EvidenceCollector()
        self.timeline_analyzer = TimelineAnalyzer()
        self.artifact_analyzer = ArtifactAnalyzer()
        self.cases: Dict[str, ForensicCase] = {}

    def create_case(
        self,
        case_name: str,
        incident_id: str,
        investigator: str
    ) -> ForensicCase:
        """Create new forensic investigation case."""
        case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        case = ForensicCase(
            case_id=case_id,
            case_name=case_name,
            incident_id=incident_id,
            investigator=investigator,
            created_at=datetime.utcnow(),
            state=ForensicState.INITIAL
        )

        self.cases[case_id] = case
        logger.info(f"Created forensic case {case_id}: {case_name}")

        return case

    def conduct_investigation(
        self,
        case: ForensicCase,
        target_systems: List[str]
    ) -> Dict[str, any]:
        """
        Conduct comprehensive forensic investigation.

        Args:
            case: Forensic case object
            target_systems: List of systems to investigate

        Returns:
            Investigation results
        """
        logger.info(f"Starting investigation for case {case.case_id}")

        # Update case state
        case.state = ForensicState.COLLECTION

        # Collect evidence from all target systems
        for system in target_systems:
            # Collect memory
            mem_evidence = self.evidence_collector.collect_memory_dump(
                system,
                case.case_id,
                case.investigator
            )
            case.evidence_items.append(mem_evidence)

            # Collect logs
            log_evidence = self.evidence_collector.collect_logs(
                system,
                ['/var/log/syslog', '/var/log/auth.log'],
                datetime.utcnow() - timedelta(days=7),
                datetime.utcnow(),
                case.case_id,
                case.investigator
            )
            case.evidence_items.append(log_evidence)

        # Create timeline
        case.state = ForensicState.ANALYSIS
        case.timeline = self.timeline_analyzer.create_timeline(
            case.case_id,
            case.evidence_items
        )

        # Generate findings
        findings = self._generate_findings(case)
        case.findings = findings

        # Generate recommendations
        case.recommendations = self._generate_recommendations(findings)

        # Update state
        case.state = ForensicState.REPORTING

        return {
            'case_id': case.case_id,
            'evidence_count': len(case.evidence_items),
            'timeline_events': len(case.timeline.events) if case.timeline else 0,
            'findings_count': len(case.findings),
            'recommendations': case.recommendations
        }

    def _generate_findings(self, case: ForensicCase) -> List[Dict]:
        """Generate investigation findings."""
        findings = []

        # Analyze each evidence item
        for evidence in case.evidence_items:
            if evidence.evidence_type == EvidenceType.MEMORY_DUMP:
                mem_analysis = self.artifact_analyzer.analyze_memory_dump(evidence)
                if mem_analysis['malware_detected']:
                    findings.append({
                        'severity': 'critical',
                        'type': 'malware_detection',
                        'description': 'Malware detected in memory dump',
                        'evidence_id': evidence.evidence_id,
                        'details': mem_analysis['malware_detected']
                    })

        return findings

    def _generate_recommendations(self, findings: List[Dict]) -> List[str]:
        """Generate remediation recommendations."""
        recommendations = []

        for finding in findings:
            if finding['type'] == 'malware_detection':
                recommendations.append("Isolate affected systems immediately")
                recommendations.append("Run antimalware scan on all systems")
                recommendations.append("Reset credentials for affected users")

        return recommendations

    def generate_report(self, case: ForensicCase) -> str:
        """Generate forensic investigation report."""
        report = {
            'case_information': {
                'case_id': case.case_id,
                'case_name': case.case_name,
                'investigator': case.investigator,
                'created_at': case.created_at.isoformat(),
                'state': case.state.value
            },
            'evidence_summary': {
                'total_items': len(case.evidence_items),
                'items': [
                    {
                        'evidence_id': e.evidence_id,
                        'type': e.evidence_type.value,
                        'source': e.source_system,
                        'hash_sha256': e.hash_sha256
                    }
                    for e in case.evidence_items
                ]
            },
            'timeline_summary': {
                'total_events': len(case.timeline.events) if case.timeline else 0,
                'start_time': case.timeline.start_time.isoformat() if case.timeline and case.timeline.start_time else None,
                'end_time': case.timeline.end_time.isoformat() if case.timeline and case.timeline.end_time else None
            },
            'findings': case.findings,
            'recommendations': case.recommendations
        }

        return json.dumps(report, indent=2)
