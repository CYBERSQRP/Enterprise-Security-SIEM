"""
Intelligent Alert Prioritization Service

This service uses machine learning to intelligently prioritize security alerts
based on context, severity, asset criticality, and historical patterns.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import json


class AlertPriority(Enum):
    """Alert priority levels."""
    P0_CRITICAL = 0  # Immediate response required
    P1_HIGH = 1      # Response within 1 hour
    P2_MEDIUM = 2    # Response within 4 hours
    P3_LOW = 3       # Response within 24 hours
    P4_INFO = 4      # Review when possible


@dataclass
class Alert:
    """Represents a security alert."""
    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    source_ip: Optional[str]
    dest_ip: Optional[str]
    user: Optional[str]
    asset: Optional[str]
    description: str
    raw_score: float = 0.5
    metadata: Dict = None


@dataclass
class PrioritizationResult:
    """Result of alert prioritization."""
    alert_id: str
    priority: AlertPriority
    priority_score: float
    factors: Dict[str, float]
    recommended_sla: timedelta
    reasoning: List[str]
    auto_actions: List[str]


class AlertPrioritizationModel(nn.Module):
    """
    Neural network model for alert prioritization.
    Uses multiple features to predict alert priority.
    """

    def __init__(
        self,
        input_dim: int = 50,
        hidden_dims: List[int] = [256, 128, 64],
        num_priority_levels: int = 5
    ):
        super(AlertPrioritizationModel, self).__init__()

        layers = []
        prev_dim = input_dim

        # Hidden layers
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim

        # Output layer
        layers.append(nn.Linear(prev_dim, num_priority_levels))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.network(x)


class FeatureExtractor:
    """Extracts features from alerts for ML model."""

    def __init__(self):
        self.severity_mapping = {
            'critical': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25,
            'info': 0.1
        }

        self.alert_type_importance = self._load_alert_type_importance()
        self.asset_criticality = self._load_asset_criticality()

    def extract_features(self, alert: Alert) -> np.ndarray:
        """Extract feature vector from alert."""
        features = []

        # Basic severity (1 feature)
        features.append(self.severity_mapping.get(alert.severity.lower(), 0.5))

        # Alert type importance (1 feature)
        features.append(self.alert_type_importance.get(alert.alert_type, 0.5))

        # Asset criticality (1 feature)
        asset_crit = 0.5
        if alert.asset:
            asset_crit = self.asset_criticality.get(alert.asset, 0.5)
        features.append(asset_crit)

        # Time-based features (4 features)
        hour = alert.timestamp.hour
        is_business_hours = 1.0 if 9 <= hour <= 17 else 0.0
        is_weekend = 1.0 if alert.timestamp.weekday() >= 5 else 0.0
        hour_normalized = hour / 24.0

        features.extend([
            is_business_hours,
            is_weekend,
            hour_normalized,
            alert.timestamp.weekday() / 7.0
        ])

        # User features (3 features)
        is_privileged_user = self._is_privileged_user(alert.user)
        is_service_account = self._is_service_account(alert.user)
        user_risk_score = self._get_user_risk_score(alert.user)

        features.extend([
            1.0 if is_privileged_user else 0.0,
            1.0 if is_service_account else 0.0,
            user_risk_score
        ])

        # IP reputation features (2 features)
        source_reputation = self._get_ip_reputation(alert.source_ip)
        dest_reputation = self._get_ip_reputation(alert.dest_ip)

        features.extend([source_reputation, dest_reputation])

        # Historical features (5 features)
        alert_frequency = self._get_alert_frequency(alert.alert_type)
        false_positive_rate = self._get_false_positive_rate(alert.alert_type)
        user_alert_history = self._get_user_alert_history(alert.user)
        asset_alert_history = self._get_asset_alert_history(alert.asset)
        similar_alerts_count = self._count_similar_alerts(alert)

        features.extend([
            alert_frequency,
            false_positive_rate,
            user_alert_history,
            asset_alert_history,
            min(similar_alerts_count / 100.0, 1.0)
        ])

        # Contextual features (5 features)
        has_known_iocs = 1.0 if self._has_known_iocs(alert) else 0.0
        matches_attack_pattern = 1.0 if self._matches_attack_pattern(alert) else 0.0
        is_lateral_movement = 1.0 if 'lateral' in alert.description.lower() else 0.0
        is_data_exfil = 1.0 if 'exfil' in alert.description.lower() else 0.0
        is_persistence = 1.0 if 'persistence' in alert.description.lower() else 0.0

        features.extend([
            has_known_iocs,
            matches_attack_pattern,
            is_lateral_movement,
            is_data_exfil,
            is_persistence
        ])

        # Pad to 50 features
        while len(features) < 50:
            features.append(0.0)

        return np.array(features[:50], dtype=np.float32)

    def _load_alert_type_importance(self) -> Dict[str, float]:
        """Load importance scores for different alert types."""
        return {
            'ransomware': 1.0,
            'data_exfiltration': 0.95,
            'privilege_escalation': 0.9,
            'lateral_movement': 0.85,
            'malware_execution': 0.8,
            'brute_force': 0.6,
            'failed_login': 0.3,
            'policy_violation': 0.4
        }

    def _load_asset_criticality(self) -> Dict[str, float]:
        """Load criticality scores for assets."""
        # Placeholder - would be loaded from CMDB
        return {}

    def _is_privileged_user(self, user: Optional[str]) -> bool:
        """Check if user is privileged."""
        if not user:
            return False
        privileged_keywords = ['admin', 'root', 'system', 'service']
        return any(kw in user.lower() for kw in privileged_keywords)

    def _is_service_account(self, user: Optional[str]) -> bool:
        """Check if user is a service account."""
        if not user:
            return False
        return 'svc-' in user.lower() or 'service' in user.lower()

    def _get_user_risk_score(self, user: Optional[str]) -> float:
        """Get user risk score from UBA system."""
        # Placeholder - would query UBA system
        return 0.5

    def _get_ip_reputation(self, ip: Optional[str]) -> float:
        """Get IP reputation score."""
        if not ip:
            return 0.5
        # Placeholder - would query threat intel
        return 0.5

    def _get_alert_frequency(self, alert_type: str) -> float:
        """Get normalized alert frequency."""
        # Placeholder - would query historical data
        return 0.5

    def _get_false_positive_rate(self, alert_type: str) -> float:
        """Get historical false positive rate for alert type."""
        # Placeholder - would query historical data
        return 0.3

    def _get_user_alert_history(self, user: Optional[str]) -> float:
        """Get user's alert history score."""
        # Placeholder
        return 0.5

    def _get_asset_alert_history(self, asset: Optional[str]) -> float:
        """Get asset's alert history score."""
        # Placeholder
        return 0.5

    def _count_similar_alerts(self, alert: Alert) -> int:
        """Count similar recent alerts."""
        # Placeholder - would query recent alerts
        return 0

    def _has_known_iocs(self, alert: Alert) -> bool:
        """Check if alert contains known IOCs."""
        # Placeholder - would check threat intel
        return False

    def _matches_attack_pattern(self, alert: Alert) -> bool:
        """Check if alert matches known attack patterns."""
        # Placeholder - would check attack patterns
        return False


class IntelligentAlertPrioritizer:
    """
    Main alert prioritization service using ML and rule-based logic.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.feature_extractor = FeatureExtractor()
        self.model = AlertPrioritizationModel()

        if model_path:
            self._load_model(model_path)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()

    def prioritize_alert(self, alert: Alert) -> PrioritizationResult:
        """
        Prioritize a single alert.

        Args:
            alert: The alert to prioritize

        Returns:
            PrioritizationResult with priority level and reasoning
        """
        # Extract features
        features = self.feature_extractor.extract_features(alert)
        features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)

        # Get ML prediction
        with torch.no_grad():
            logits = self.model(features_tensor)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]
            ml_priority = int(np.argmax(probabilities))
            ml_confidence = float(probabilities[ml_priority])

        # Apply rule-based adjustments
        adjusted_priority, rule_factors = self._apply_priority_rules(alert, ml_priority)

        # Calculate final priority score
        priority_score = self._calculate_priority_score(
            alert,
            ml_priority,
            ml_confidence,
            rule_factors
        )

        # Determine priority level
        priority_level = self._score_to_priority_level(priority_score)

        # Get SLA recommendation
        recommended_sla = self._get_recommended_sla(priority_level)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            alert,
            priority_level,
            ml_confidence,
            rule_factors
        )

        # Suggest automated actions
        auto_actions = self._suggest_auto_actions(alert, priority_level)

        return PrioritizationResult(
            alert_id=alert.alert_id,
            priority=priority_level,
            priority_score=priority_score,
            factors=rule_factors,
            recommended_sla=recommended_sla,
            reasoning=reasoning,
            auto_actions=auto_actions
        )

    def prioritize_batch(self, alerts: List[Alert]) -> List[PrioritizationResult]:
        """Prioritize multiple alerts efficiently."""
        return [self.prioritize_alert(alert) for alert in alerts]

    def _apply_priority_rules(
        self,
        alert: Alert,
        ml_priority: int
    ) -> Tuple[int, Dict[str, float]]:
        """Apply business rules to adjust ML priority."""
        adjusted_priority = ml_priority
        factors = {}

        # Critical asset rule
        if alert.asset and self._is_critical_asset(alert.asset):
            adjusted_priority = min(adjusted_priority, 1)
            factors['critical_asset'] = 1.0

        # Known attack pattern rule
        if self._is_known_attack_pattern(alert):
            adjusted_priority = min(adjusted_priority, 1)
            factors['known_attack_pattern'] = 0.9

        # Multiple correlated alerts rule
        correlation_score = self._get_correlation_score(alert)
        if correlation_score > 0.7:
            adjusted_priority = min(adjusted_priority, 1)
            factors['correlated_alerts'] = correlation_score

        # Business hours adjustment
        if not self._is_business_hours(alert.timestamp):
            factors['off_hours'] = 0.3

        # False positive history
        fp_rate = self.feature_extractor._get_false_positive_rate(alert.alert_type)
        if fp_rate > 0.8:
            adjusted_priority = min(adjusted_priority + 1, 4)
            factors['high_false_positive_rate'] = fp_rate

        return adjusted_priority, factors

    def _calculate_priority_score(
        self,
        alert: Alert,
        ml_priority: int,
        ml_confidence: float,
        rule_factors: Dict[str, float]
    ) -> float:
        """Calculate final priority score."""
        # Convert priority to score (0-1, where 1 is highest priority)
        base_score = (4 - ml_priority) / 4.0

        # Apply confidence weighting
        score = base_score * ml_confidence

        # Apply rule factor adjustments
        for factor_name, factor_value in rule_factors.items():
            if factor_name in ['critical_asset', 'known_attack_pattern', 'correlated_alerts']:
                score = min(score + factor_value * 0.2, 1.0)
            elif factor_name == 'high_false_positive_rate':
                score *= (1 - factor_value * 0.3)

        return score

    def _score_to_priority_level(self, score: float) -> AlertPriority:
        """Convert priority score to priority level."""
        if score >= 0.9:
            return AlertPriority.P0_CRITICAL
        elif score >= 0.7:
            return AlertPriority.P1_HIGH
        elif score >= 0.5:
            return AlertPriority.P2_MEDIUM
        elif score >= 0.3:
            return AlertPriority.P3_LOW
        else:
            return AlertPriority.P4_INFO

    def _get_recommended_sla(self, priority: AlertPriority) -> timedelta:
        """Get recommended SLA for priority level."""
        sla_map = {
            AlertPriority.P0_CRITICAL: timedelta(minutes=15),
            AlertPriority.P1_HIGH: timedelta(hours=1),
            AlertPriority.P2_MEDIUM: timedelta(hours=4),
            AlertPriority.P3_LOW: timedelta(hours=24),
            AlertPriority.P4_INFO: timedelta(days=7)
        }
        return sla_map[priority]

    def _generate_reasoning(
        self,
        alert: Alert,
        priority: AlertPriority,
        ml_confidence: float,
        rule_factors: Dict[str, float]
    ) -> List[str]:
        """Generate human-readable reasoning for prioritization."""
        reasoning = []

        reasoning.append(f"Alert classified as {priority.name} (confidence: {ml_confidence:.2f})")

        if 'critical_asset' in rule_factors:
            reasoning.append("Alert involves critical asset")

        if 'known_attack_pattern' in rule_factors:
            reasoning.append("Matches known attack pattern")

        if 'correlated_alerts' in rule_factors:
            reasoning.append(
                f"Part of correlated attack sequence (score: {rule_factors['correlated_alerts']:.2f})"
            )

        if 'high_false_positive_rate' in rule_factors:
            reasoning.append(
                f"High historical false positive rate ({rule_factors['high_false_positive_rate']:.0%})"
            )

        return reasoning

    def _suggest_auto_actions(
        self,
        alert: Alert,
        priority: AlertPriority
    ) -> List[str]:
        """Suggest automated actions based on priority."""
        actions = []

        if priority == AlertPriority.P0_CRITICAL:
            actions.extend([
                "Immediately notify on-call security engineer",
                "Create incident ticket",
                "Begin automated containment procedures",
                "Escalate to SOC manager"
            ])
        elif priority == AlertPriority.P1_HIGH:
            actions.extend([
                "Assign to senior analyst",
                "Create incident ticket",
                "Gather additional context"
            ])
        elif priority == AlertPriority.P2_MEDIUM:
            actions.extend([
                "Add to analyst queue",
                "Enrich with threat intelligence"
            ])
        else:
            actions.extend([
                "Queue for review",
                "Consider for automated closure if no correlation"
            ])

        return actions

    def _is_critical_asset(self, asset: str) -> bool:
        """Check if asset is critical."""
        # Placeholder - would check CMDB
        critical_keywords = ['dc', 'domain', 'prod', 'database', 'payment']
        return any(kw in asset.lower() for kw in critical_keywords)

    def _is_known_attack_pattern(self, alert: Alert) -> bool:
        """Check if alert matches known attack pattern."""
        # Placeholder - would check attack pattern database
        return False

    def _get_correlation_score(self, alert: Alert) -> float:
        """Get correlation score with other recent alerts."""
        # Placeholder - would query correlation engine
        return 0.0

    def _is_business_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during business hours."""
        return 9 <= timestamp.hour <= 17 and timestamp.weekday() < 5

    def _load_model(self, model_path: str):
        """Load trained model from disk."""
        checkpoint = torch.load(model_path, map_location='cpu')
        self.model.load_state_dict(checkpoint['model_state_dict'])
