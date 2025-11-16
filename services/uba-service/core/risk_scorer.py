"""
Risk Scorer Module

Calculates and manages user risk scores based on multiple risk factors.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    """Individual risk factor"""
    factor: str
    score: float  # 0-100
    weight: float  # 0-1
    details: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserRiskScore:
    """User risk score data structure"""
    user_id: str
    risk_score: float  # 0-100
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RiskScorer:
    """
    Calculates user risk scores based on multiple factors.

    Risk factors considered:
    - Behavioral anomalies
    - Policy violations
    - Unusual access patterns
    - Peer group deviation
    - Historical incidents
    - External threat intelligence
    """

    # Risk factor weights
    DEFAULT_WEIGHTS = {
        'behavioral_anomaly': 0.25,
        'policy_violation': 0.20,
        'unusual_access': 0.15,
        'peer_deviation': 0.15,
        'failed_auth': 0.10,
        'data_exfiltration': 0.10,
        'privilege_abuse': 0.05
    }

    # Risk level thresholds
    RISK_THRESHOLDS = {
        RiskLevel.CRITICAL: 85,
        RiskLevel.HIGH: 65,
        RiskLevel.MEDIUM: 40,
        RiskLevel.LOW: 0
    }

    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 alert_threshold: float = 65.0):
        """
        Initialize the risk scorer.

        Args:
            weights: Custom risk factor weights
            alert_threshold: Risk score threshold for alerting
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.alert_threshold = alert_threshold
        self.user_scores: Dict[str, UserRiskScore] = {}

    def calculate_risk_score(self,
                            user_id: str,
                            risk_factors: List[RiskFactor]) -> UserRiskScore:
        """
        Calculate overall risk score for a user.

        Args:
            user_id: User identifier
            risk_factors: List of risk factors

        Returns:
            UserRiskScore object
        """
        if not risk_factors:
            return UserRiskScore(
                user_id=user_id,
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
                risk_factors=[]
            )

        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0

        for factor in risk_factors:
            weight = self.weights.get(factor.factor, factor.weight)
            total_score += factor.score * weight
            total_weight += weight

        # Normalize score to 0-100 range
        if total_weight > 0:
            final_score = min(100.0, total_score / total_weight)
        else:
            final_score = 0.0

        # Determine risk level
        risk_level = self._determine_risk_level(final_score)

        user_risk = UserRiskScore(
            user_id=user_id,
            risk_score=final_score,
            risk_level=risk_level,
            risk_factors=risk_factors
        )

        self.user_scores[user_id] = user_risk
        return user_risk

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level based on score"""
        if score >= self.RISK_THRESHOLDS[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif score >= self.RISK_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif score >= self.RISK_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def create_behavioral_anomaly_factor(self,
                                        anomaly_score: float,
                                        anomaly_type: str) -> RiskFactor:
        """Create a risk factor for behavioral anomaly"""
        return RiskFactor(
            factor='behavioral_anomaly',
            score=anomaly_score * 100,
            weight=self.weights.get('behavioral_anomaly', 0.25),
            details=f"Behavioral anomaly detected: {anomaly_type}"
        )

    def create_policy_violation_factor(self,
                                      violation_severity: str,
                                      violation_details: str) -> RiskFactor:
        """Create a risk factor for policy violation"""
        severity_scores = {
            'low': 30,
            'medium': 60,
            'high': 85,
            'critical': 95
        }

        return RiskFactor(
            factor='policy_violation',
            score=severity_scores.get(violation_severity.lower(), 50),
            weight=self.weights.get('policy_violation', 0.20),
            details=violation_details
        )

    def create_unusual_access_factor(self,
                                    access_type: str,
                                    details: str) -> RiskFactor:
        """Create a risk factor for unusual access"""
        return RiskFactor(
            factor='unusual_access',
            score=65,
            weight=self.weights.get('unusual_access', 0.15),
            details=f"{access_type}: {details}"
        )

    def create_peer_deviation_factor(self,
                                    deviation_score: float,
                                    details: str) -> RiskFactor:
        """Create a risk factor for peer group deviation"""
        return RiskFactor(
            factor='peer_deviation',
            score=deviation_score * 100,
            weight=self.weights.get('peer_deviation', 0.15),
            details=details
        )

    def update_risk_score(self,
                         user_id: str,
                         new_factor: RiskFactor) -> UserRiskScore:
        """
        Update risk score with a new factor.

        Args:
            user_id: User identifier
            new_factor: New risk factor to add

        Returns:
            Updated UserRiskScore
        """
        current_score = self.user_scores.get(user_id)

        if current_score:
            # Add new factor and recalculate
            risk_factors = current_score.risk_factors + [new_factor]
        else:
            risk_factors = [new_factor]

        return self.calculate_risk_score(user_id, risk_factors)

    def get_risk_score(self, user_id: str) -> Optional[UserRiskScore]:
        """Get current risk score for a user"""
        return self.user_scores.get(user_id)

    def get_high_risk_users(self,
                           threshold: Optional[float] = None) -> List[UserRiskScore]:
        """
        Get list of high-risk users.

        Args:
            threshold: Risk score threshold (uses alert_threshold if not provided)

        Returns:
            List of UserRiskScore objects above threshold
        """
        threshold = threshold or self.alert_threshold
        high_risk_users = [
            score for score in self.user_scores.values()
            if score.risk_score >= threshold
        ]
        return sorted(high_risk_users,
                     key=lambda x: x.risk_score,
                     reverse=True)

    def should_alert(self, user_id: str) -> Tuple[bool, Optional[UserRiskScore]]:
        """
        Check if user risk score warrants an alert.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (should_alert, risk_score)
        """
        risk_score = self.user_scores.get(user_id)
        if risk_score and risk_score.risk_score >= self.alert_threshold:
            return True, risk_score
        return False, risk_score


# Example usage
if __name__ == "__main__":
    scorer = RiskScorer(alert_threshold=65.0)

    # Create sample risk factors
    factors = [
        scorer.create_behavioral_anomaly_factor(0.8, "unusual login time"),
        scorer.create_unusual_access_factor("sensitive_data", "Accessed 500+ files"),
        scorer.create_peer_deviation_factor(0.6, "Activity differs from peers")
    ]

    # Calculate risk score
    risk_score = scorer.calculate_risk_score("user123", factors)
    print(f"User: {risk_score.user_id}")
    print(f"Risk Score: {risk_score.risk_score:.2f}")
    print(f"Risk Level: {risk_score.risk_level.value}")
    print(f"Should Alert: {scorer.should_alert('user123')[0]}")
