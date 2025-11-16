"""
AI Security Analyst Assistant

This service provides an intelligent AI assistant to help security analysts
with investigation, threat analysis, and decision-making.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatSeverity(Enum):
    """Threat severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InvestigationStatus(Enum):
    """Investigation status."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class SecurityEvent:
    """Represents a security event."""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: ThreatSeverity
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    user: Optional[str] = None
    process: Optional[str] = None
    raw_log: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatContext:
    """Context information about a threat."""
    threat_type: str
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    iocs: List[str]
    related_events: List[str]
    confidence_score: float
    risk_score: float
    affected_assets: List[str]
    timeline: List[Dict]


@dataclass
class InvestigationRecommendation:
    """AI-generated recommendation for investigation."""
    recommendation_type: str
    priority: int
    description: str
    action_items: List[str]
    rationale: str
    estimated_impact: str
    confidence: float


class AISecurityAnalyst:
    """
    AI-powered security analyst assistant that provides intelligent
    recommendations, automated triage, and investigation guidance.
    """

    def __init__(self):
        self.knowledge_base = ThreatKnowledgeBase()
        self.event_correlator = EventCorrelator()
        self.risk_calculator = RiskCalculator()
        self.investigation_engine = InvestigationEngine()

    async def analyze_alert(self, event: SecurityEvent) -> Dict[str, Any]:
        """
        Analyze a security alert and provide comprehensive insights.

        Args:
            event: The security event to analyze

        Returns:
            Comprehensive analysis including context, recommendations, and actions
        """
        logger.info(f"Analyzing alert {event.event_id}")

        # Gather threat context
        threat_context = await self._gather_threat_context(event)

        # Calculate risk score
        risk_assessment = self.risk_calculator.calculate_risk(event, threat_context)

        # Find related events
        related_events = await self.event_correlator.find_related_events(event)

        # Generate investigation recommendations
        recommendations = await self._generate_recommendations(
            event,
            threat_context,
            related_events
        )

        # Suggest next steps
        next_steps = self._suggest_next_steps(event, threat_context, recommendations)

        # Auto-triage
        triage_decision = self._auto_triage(event, threat_context, risk_assessment)

        analysis = {
            'event_id': event.event_id,
            'threat_context': threat_context,
            'risk_assessment': risk_assessment,
            'related_events': related_events,
            'recommendations': recommendations,
            'next_steps': next_steps,
            'triage_decision': triage_decision,
            'timestamp': datetime.utcnow().isoformat()
        }

        return analysis

    async def _gather_threat_context(self, event: SecurityEvent) -> ThreatContext:
        """Gather contextual information about the threat."""
        # Query threat intelligence
        threat_intel = await self.knowledge_base.query_threat_intel(event)

        # Map to MITRE ATT&CK
        mitre_mapping = self.knowledge_base.map_to_mitre(event.event_type)

        # Extract IOCs
        iocs = self._extract_iocs(event)

        # Build timeline
        timeline = await self._build_event_timeline(event)

        # Identify affected assets
        affected_assets = self._identify_affected_assets(event)

        # Calculate confidence and risk scores
        confidence_score = self._calculate_confidence(event, threat_intel)
        risk_score = self.risk_calculator.calculate_event_risk(event)

        context = ThreatContext(
            threat_type=threat_intel.get('threat_type', 'Unknown'),
            mitre_tactics=mitre_mapping.get('tactics', []),
            mitre_techniques=mitre_mapping.get('techniques', []),
            iocs=iocs,
            related_events=[],
            confidence_score=confidence_score,
            risk_score=risk_score,
            affected_assets=affected_assets,
            timeline=timeline
        )

        return context

    async def _generate_recommendations(
        self,
        event: SecurityEvent,
        context: ThreatContext,
        related_events: List[SecurityEvent]
    ) -> List[InvestigationRecommendation]:
        """Generate intelligent investigation recommendations."""
        recommendations = []

        # Immediate response recommendations
        if context.risk_score > 0.8:
            recommendations.append(InvestigationRecommendation(
                recommendation_type="immediate_containment",
                priority=1,
                description="Immediately isolate affected systems",
                action_items=[
                    "Isolate host from network",
                    "Disable compromised user account",
                    "Block malicious IPs at firewall"
                ],
                rationale=f"High risk score ({context.risk_score:.2f}) indicates active threat",
                estimated_impact="Prevents further lateral movement",
                confidence=0.9
            ))

        # Investigation recommendations
        if len(related_events) > 5:
            recommendations.append(InvestigationRecommendation(
                recommendation_type="deep_investigation",
                priority=2,
                description="Conduct deep investigation of correlated events",
                action_items=[
                    f"Review {len(related_events)} correlated events",
                    "Analyze attack timeline",
                    "Check for data exfiltration",
                    "Review authentication logs"
                ],
                rationale=f"Found {len(related_events)} related events suggesting coordinated attack",
                estimated_impact="Reveals full scope of compromise",
                confidence=0.85
            ))

        # Threat hunting recommendations
        if context.mitre_techniques:
            recommendations.append(InvestigationRecommendation(
                recommendation_type="proactive_hunting",
                priority=3,
                description="Hunt for similar threats across environment",
                action_items=[
                    f"Search for {', '.join(context.mitre_techniques[:3])} TTPs",
                    "Review other systems for similar patterns",
                    "Check for persistence mechanisms"
                ],
                rationale=f"Detected MITRE techniques: {', '.join(context.mitre_techniques[:3])}",
                estimated_impact="Identifies additional compromises",
                confidence=0.75
            ))

        # Forensics recommendations
        if event.severity in [ThreatSeverity.CRITICAL, ThreatSeverity.HIGH]:
            recommendations.append(InvestigationRecommendation(
                recommendation_type="forensics",
                priority=4,
                description="Collect forensic evidence",
                action_items=[
                    "Capture memory dump",
                    "Collect disk images",
                    "Preserve network traffic captures",
                    "Document chain of custody"
                ],
                rationale="High severity event requires forensic analysis",
                estimated_impact="Enables detailed post-incident analysis",
                confidence=0.8
            ))

        return sorted(recommendations, key=lambda x: x.priority)

    def _suggest_next_steps(
        self,
        event: SecurityEvent,
        context: ThreatContext,
        recommendations: List[InvestigationRecommendation]
    ) -> List[str]:
        """Suggest immediate next steps for the analyst."""
        next_steps = []

        # Prioritize based on risk
        if context.risk_score > 0.8:
            next_steps.append("🚨 CRITICAL: Immediately escalate to incident response team")
            next_steps.append("Activate incident response playbook")

        # Add top recommendations
        for rec in recommendations[:3]:
            next_steps.extend(rec.action_items[:2])

        # Add investigation queries
        next_steps.append(f"Run query: Find all events from {event.source_ip} in last 24h")

        if event.user:
            next_steps.append(f"Check recent activity for user: {event.user}")

        return next_steps

    def _auto_triage(
        self,
        event: SecurityEvent,
        context: ThreatContext,
        risk_assessment: Dict
    ) -> Dict[str, Any]:
        """Automatically triage the alert."""
        # Calculate triage score
        triage_score = self._calculate_triage_score(event, context, risk_assessment)

        # Determine priority
        if triage_score > 0.9:
            priority = "P1 - Critical"
            auto_action = "escalate_to_ir"
        elif triage_score > 0.7:
            priority = "P2 - High"
            auto_action = "assign_to_analyst"
        elif triage_score > 0.5:
            priority = "P3 - Medium"
            auto_action = "queue_for_review"
        else:
            priority = "P4 - Low"
            auto_action = "auto_close_if_no_correlation"

        return {
            'triage_score': triage_score,
            'priority': priority,
            'recommended_action': auto_action,
            'rationale': self._explain_triage_decision(event, context, triage_score),
            'requires_human_review': triage_score > 0.6
        }

    def _calculate_triage_score(
        self,
        event: SecurityEvent,
        context: ThreatContext,
        risk_assessment: Dict
    ) -> float:
        """Calculate automated triage score."""
        score = 0.0

        # Severity weight (30%)
        severity_weights = {
            ThreatSeverity.CRITICAL: 1.0,
            ThreatSeverity.HIGH: 0.7,
            ThreatSeverity.MEDIUM: 0.4,
            ThreatSeverity.LOW: 0.2,
            ThreatSeverity.INFO: 0.1
        }
        score += severity_weights.get(event.severity, 0.5) * 0.3

        # Confidence score (20%)
        score += context.confidence_score * 0.2

        # Risk score (30%)
        score += context.risk_score * 0.3

        # MITRE mapping (10%)
        if context.mitre_techniques:
            score += min(len(context.mitre_techniques) * 0.1, 1.0) * 0.1

        # IOC presence (10%)
        if context.iocs:
            score += min(len(context.iocs) * 0.2, 1.0) * 0.1

        return min(score, 1.0)

    def _explain_triage_decision(
        self,
        event: SecurityEvent,
        context: ThreatContext,
        score: float
    ) -> str:
        """Explain the triage decision in natural language."""
        explanations = []

        explanations.append(f"Event severity: {event.severity.value}")
        explanations.append(f"Risk score: {context.risk_score:.2f}")
        explanations.append(f"Confidence: {context.confidence_score:.2f}")

        if context.mitre_techniques:
            explanations.append(
                f"Mapped to {len(context.mitre_techniques)} MITRE techniques"
            )

        if context.iocs:
            explanations.append(f"Contains {len(context.iocs)} IOCs")

        return " | ".join(explanations)

    def _extract_iocs(self, event: SecurityEvent) -> List[str]:
        """Extract indicators of compromise from event."""
        iocs = []

        if event.source_ip:
            iocs.append(f"ip:{event.source_ip}")

        if event.dest_ip:
            iocs.append(f"ip:{event.dest_ip}")

        # Extract from raw log using regex
        import re

        # File hashes
        hashes = re.findall(r'\b[a-fA-F0-9]{32,64}\b', event.raw_log)
        iocs.extend([f"hash:{h}" for h in hashes])

        # URLs
        urls = re.findall(r'https?://[^\s]+', event.raw_log)
        iocs.extend([f"url:{u}" for u in urls])

        return iocs

    async def _build_event_timeline(self, event: SecurityEvent) -> List[Dict]:
        """Build a timeline of related events."""
        timeline = []

        # Add the current event
        timeline.append({
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'description': f"{event.event_type} detected"
        })

        # TODO: Query for related events and build timeline
        # This would query the event database

        return timeline

    def _identify_affected_assets(self, event: SecurityEvent) -> List[str]:
        """Identify assets affected by the event."""
        assets = []

        if event.source_ip:
            assets.append(f"host:{event.source_ip}")

        if event.user:
            assets.append(f"user:{event.user}")

        return assets

    def _calculate_confidence(
        self,
        event: SecurityEvent,
        threat_intel: Dict
    ) -> float:
        """Calculate confidence score for the threat assessment."""
        confidence = 0.5  # Base confidence

        # Increase confidence if we have threat intel
        if threat_intel.get('known_threat'):
            confidence += 0.3

        # Increase confidence based on severity
        if event.severity == ThreatSeverity.CRITICAL:
            confidence += 0.2

        return min(confidence, 1.0)


class ThreatKnowledgeBase:
    """Knowledge base for threat intelligence and MITRE ATT&CK mapping."""

    def __init__(self):
        self.threat_intel_db = {}
        self.mitre_mappings = self._load_mitre_mappings()

    async def query_threat_intel(self, event: SecurityEvent) -> Dict:
        """Query threat intelligence databases."""
        # Simulate threat intel lookup
        threat_info = {
            'known_threat': False,
            'threat_type': 'Unknown',
            'first_seen': None,
            'last_seen': None,
            'prevalence': 0
        }

        # TODO: Integrate with actual threat intel feeds
        # - VirusTotal
        # - AlienVault OTX
        # - MISP
        # - Custom feeds

        return threat_info

    def map_to_mitre(self, event_type: str) -> Dict[str, List[str]]:
        """Map event type to MITRE ATT&CK framework."""
        return self.mitre_mappings.get(event_type, {
            'tactics': [],
            'techniques': []
        })

    def _load_mitre_mappings(self) -> Dict:
        """Load MITRE ATT&CK mappings."""
        return {
            'brute_force_attack': {
                'tactics': ['Credential Access'],
                'techniques': ['T1110 - Brute Force', 'T1110.001 - Password Guessing']
            },
            'lateral_movement': {
                'tactics': ['Lateral Movement'],
                'techniques': ['T1021 - Remote Services', 'T1570 - Lateral Tool Transfer']
            },
            'data_exfiltration': {
                'tactics': ['Exfiltration'],
                'techniques': ['T1041 - Exfiltration Over C2 Channel', 'T1048 - Exfiltration Over Alternative Protocol']
            },
            'privilege_escalation': {
                'tactics': ['Privilege Escalation'],
                'techniques': ['T1068 - Exploitation for Privilege Escalation', 'T1134 - Access Token Manipulation']
            },
            'malware_execution': {
                'tactics': ['Execution'],
                'techniques': ['T1204 - User Execution', 'T1059 - Command and Scripting Interpreter']
            }
        }


class EventCorrelator:
    """Correlates related security events."""

    async def find_related_events(
        self,
        event: SecurityEvent,
        time_window: timedelta = timedelta(hours=1)
    ) -> List[SecurityEvent]:
        """Find events related to the given event."""
        related_events = []

        # TODO: Query event database for related events
        # Correlation criteria:
        # - Same source/dest IP
        # - Same user
        # - Similar event type
        # - Within time window

        return related_events


class RiskCalculator:
    """Calculates risk scores for events and assets."""

    def calculate_risk(
        self,
        event: SecurityEvent,
        context: ThreatContext
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk assessment."""
        # Event risk score
        event_risk = self.calculate_event_risk(event)

        # Asset risk score
        asset_risk = self._calculate_asset_risk(context.affected_assets)

        # Overall risk score
        overall_risk = (event_risk * 0.6 + asset_risk * 0.4)

        return {
            'event_risk': event_risk,
            'asset_risk': asset_risk,
            'overall_risk': overall_risk,
            'risk_factors': self._identify_risk_factors(event, context)
        }

    def calculate_event_risk(self, event: SecurityEvent) -> float:
        """Calculate risk score for an individual event."""
        risk = 0.0

        # Severity contribution
        severity_scores = {
            ThreatSeverity.CRITICAL: 0.9,
            ThreatSeverity.HIGH: 0.7,
            ThreatSeverity.MEDIUM: 0.5,
            ThreatSeverity.LOW: 0.3,
            ThreatSeverity.INFO: 0.1
        }
        risk += severity_scores.get(event.severity, 0.5)

        return min(risk, 1.0)

    def _calculate_asset_risk(self, assets: List[str]) -> float:
        """Calculate risk based on affected assets."""
        # Simplified asset risk calculation
        return min(len(assets) * 0.2, 1.0)

    def _identify_risk_factors(
        self,
        event: SecurityEvent,
        context: ThreatContext
    ) -> List[str]:
        """Identify specific risk factors."""
        factors = []

        if event.severity in [ThreatSeverity.CRITICAL, ThreatSeverity.HIGH]:
            factors.append("High severity event")

        if context.iocs:
            factors.append(f"Contains {len(context.iocs)} IOCs")

        if context.mitre_techniques:
            factors.append(f"Maps to {len(context.mitre_techniques)} attack techniques")

        return factors


class InvestigationEngine:
    """Engine for automated investigation."""

    async def auto_investigate(
        self,
        event: SecurityEvent
    ) -> Dict[str, Any]:
        """Perform automated investigation."""
        investigation_results = {
            'event_id': event.event_id,
            'investigation_steps': [],
            'findings': [],
            'evidence_collected': []
        }

        # TODO: Implement automated investigation logic
        # - Query related logs
        # - Check threat intel
        # - Analyze network traffic
        # - Check endpoint telemetry

        return investigation_results
