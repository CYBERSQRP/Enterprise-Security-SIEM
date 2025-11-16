"""
Hypothesis Manager

Manages threat hunting hypotheses and tracks validation results.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class HypothesisStatus(Enum):
    """Hypothesis status"""
    DRAFT = "draft"
    ACTIVE = "active"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


class Severity(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HuntingQuery:
    """Hunting query for hypothesis testing"""
    name: str
    query: str
    data_source: str  # elasticsearch, neo4j, etc.
    expected_result_count: Optional[int] = None


@dataclass
class HuntingHypothesis:
    """Threat hunting hypothesis"""
    hypothesis_id: str
    name: str
    description: str
    mitre_technique: str
    severity: Severity
    status: HypothesisStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    indicators: List[str]
    queries: List[HuntingQuery]
    expected_findings: str
    validation_criteria: List[str]
    findings: List[Dict] = field(default_factory=list)
    notes: str = ""


class HypothesisManager:
    """
    Manages threat hunting hypotheses.

    Provides functionality to:
    - Create and manage hypotheses
    - Track hypothesis validation
    - Generate hypothesis templates
    - Link hypotheses to MITRE ATT&CK
    """

    def __init__(self):
        self.hypotheses: Dict[str, HuntingHypothesis] = {}

    def create_hypothesis(self,
                         name: str,
                         description: str,
                         mitre_technique: str,
                         severity: Severity,
                         created_by: str,
                         indicators: List[str],
                         queries: List[HuntingQuery],
                         expected_findings: str,
                         validation_criteria: List[str]) -> HuntingHypothesis:
        """
        Create a new hunting hypothesis.

        Args:
            name: Hypothesis name
            description: Detailed description
            mitre_technique: MITRE ATT&CK technique ID
            severity: Threat severity
            created_by: Creator email/username
            indicators: List of threat indicators
            queries: List of hunting queries
            expected_findings: Expected findings description
            validation_criteria: Criteria for validation

        Returns:
            Created HuntingHypothesis
        """
        hypothesis_id = f"HYPO-{datetime.utcnow().year}-{str(uuid.uuid4())[:8].upper()}"

        hypothesis = HuntingHypothesis(
            hypothesis_id=hypothesis_id,
            name=name,
            description=description,
            mitre_technique=mitre_technique,
            severity=severity,
            status=HypothesisStatus.DRAFT,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            indicators=indicators,
            queries=queries,
            expected_findings=expected_findings,
            validation_criteria=validation_criteria
        )

        self.hypotheses[hypothesis_id] = hypothesis
        return hypothesis

    def activate_hypothesis(self, hypothesis_id: str) -> HuntingHypothesis:
        """Activate a hypothesis for testing"""
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        hypothesis.status = HypothesisStatus.ACTIVE
        hypothesis.updated_at = datetime.utcnow()
        return hypothesis

    def add_finding(self,
                   hypothesis_id: str,
                   finding: Dict) -> HuntingHypothesis:
        """
        Add a finding to a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            finding: Finding details

        Returns:
            Updated hypothesis
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        hypothesis.findings.append({
            **finding,
            'timestamp': datetime.utcnow().isoformat()
        })
        hypothesis.updated_at = datetime.utcnow()
        return hypothesis

    def validate_hypothesis(self,
                          hypothesis_id: str,
                          validation_result: bool,
                          notes: str = "") -> HuntingHypothesis:
        """
        Mark hypothesis as validated or invalidated.

        Args:
            hypothesis_id: Hypothesis ID
            validation_result: True if validated, False if invalidated
            notes: Validation notes

        Returns:
            Updated hypothesis
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        if validation_result:
            hypothesis.status = HypothesisStatus.VALIDATED
        else:
            hypothesis.status = HypothesisStatus.INVALIDATED

        hypothesis.notes = notes
        hypothesis.updated_at = datetime.utcnow()
        return hypothesis

    def get_hypothesis(self, hypothesis_id: str) -> Optional[HuntingHypothesis]:
        """Get hypothesis by ID"""
        return self.hypotheses.get(hypothesis_id)

    def list_hypotheses(self,
                       status: Optional[HypothesisStatus] = None,
                       mitre_technique: Optional[str] = None) -> List[HuntingHypothesis]:
        """
        List hypotheses with optional filtering.

        Args:
            status: Filter by status
            mitre_technique: Filter by MITRE technique

        Returns:
            List of matching hypotheses
        """
        results = list(self.hypotheses.values())

        if status:
            results = [h for h in results if h.status == status]

        if mitre_technique:
            results = [h for h in results if h.mitre_technique == mitre_technique]

        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def create_kerberoasting_hypothesis(self, created_by: str) -> HuntingHypothesis:
        """Create a pre-built Kerberoasting hypothesis"""
        return self.create_hypothesis(
            name="Detect Kerberoasting Activity",
            description="Hunt for potential Kerberoasting attacks targeting service accounts",
            mitre_technique="T1558.003",
            severity=Severity.HIGH,
            created_by=created_by,
            indicators=[
                "Unusual Kerberos TGS requests",
                "Requests for RC4 encrypted tickets",
                "Multiple SPN requests in short time"
            ],
            queries=[
                HuntingQuery(
                    name="Find TGS requests with RC4",
                    query='event.code:4769 AND service_ticket_encryption:0x17',
                    data_source="elasticsearch"
                ),
                HuntingQuery(
                    name="Multiple SPN requests",
                    query="""
                    {
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"event.code": "4769"}},
                                    {"range": {"@timestamp": {"gte": "now-1h"}}}
                                ]
                            }
                        },
                        "aggs": {
                            "by_user": {
                                "terms": {"field": "user.name"},
                                "aggs": {
                                    "unique_spns": {
                                        "cardinality": {"field": "service_name"}
                                    }
                                }
                            }
                        }
                    }
                    """,
                    data_source="elasticsearch"
                )
            ],
            expected_findings="Service accounts with unusual TGS request patterns",
            validation_criteria=[
                "Multiple TGS requests from single user",
                "RC4 encryption requested",
                "Service account targeted",
                "No legitimate business reason"
            ]
        )

    def create_powershell_obfuscation_hypothesis(self,
                                                created_by: str) -> HuntingHypothesis:
        """Create a pre-built PowerShell obfuscation hypothesis"""
        return self.create_hypothesis(
            name="Detect Obfuscated PowerShell",
            description="Hunt for obfuscated or encoded PowerShell commands",
            mitre_technique="T1059.001",
            severity=Severity.MEDIUM,
            created_by=created_by,
            indicators=[
                "Base64 encoded commands",
                "String concatenation",
                "Character substitution",
                "Multiple layers of encoding"
            ],
            queries=[
                HuntingQuery(
                    name="Base64 encoded PowerShell",
                    query="""
                    event.category:process AND
                    process.name:powershell.exe AND
                    process.command_line:(*-enc* OR *-encodedcommand* OR
                                          *FromBase64String*)
                    """,
                    data_source="elasticsearch"
                )
            ],
            expected_findings="PowerShell commands with suspicious obfuscation",
            validation_criteria=[
                "Base64 or other encoding detected",
                "Unusual command structure",
                "Known malicious patterns",
                "No legitimate automation reason"
            ]
        )


# Example usage
if __name__ == "__main__":
    manager = HypothesisManager()

    # Create Kerberoasting hypothesis
    hypo = manager.create_kerberoasting_hypothesis("analyst@company.com")
    print(f"Created hypothesis: {hypo.hypothesis_id}")
    print(f"Name: {hypo.name}")
    print(f"Status: {hypo.status.value}")
    print(f"MITRE: {hypo.mitre_technique}")
    print(f"Queries: {len(hypo.queries)}")

    # Activate hypothesis
    manager.activate_hypothesis(hypo.hypothesis_id)
    print(f"\nActivated hypothesis: {hypo.hypothesis_id}")

    # Add finding
    manager.add_finding(hypo.hypothesis_id, {
        "user": "suspicious.user",
        "spn_count": 15,
        "details": "User requested 15 SPNs in 10 minutes"
    })

    # Validate hypothesis
    manager.validate_hypothesis(
        hypo.hypothesis_id,
        True,
        "Confirmed Kerberoasting attack. User account compromised."
    )

    print(f"\nFinal status: {hypo.status.value}")
    print(f"Findings: {len(hypo.findings)}")
