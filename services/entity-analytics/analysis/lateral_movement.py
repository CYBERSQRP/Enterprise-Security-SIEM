"""
Lateral Movement Detection

Detects lateral movement patterns in the network using graph analysis.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


@dataclass
class LateralMovementAlert:
    """Lateral movement detection alert"""
    alert_id: str
    user_id: str
    username: str
    source_hosts: List[str]
    target_hosts: List[str]
    technique: str  # MITRE ATT&CK technique
    confidence: float  # 0-1
    severity: str  # low, medium, high, critical
    details: Dict
    timestamp: datetime


class LateralMovementDetector:
    """
    Detects lateral movement patterns using graph analytics.

    Techniques detected:
    - Remote Desktop (RDP)
    - PsExec and remote execution
    - WMI remote execution
    - Pass-the-Hash (PtH)
    - Pass-the-Ticket (PtT)
    - Windows Admin Shares
    - Remote Services
    """

    # MITRE ATT&CK technique mappings
    TECHNIQUES = {
        'T1021.001': 'Remote Desktop Protocol',
        'T1021.002': 'SMB/Windows Admin Shares',
        'T1021.003': 'Distributed Component Object Model',
        'T1021.006': 'Windows Remote Management',
        'T1047': 'Windows Management Instrumentation',
        'T1550.002': 'Pass the Hash',
        'T1550.003': 'Pass the Ticket'
    }

    def __init__(self,
                 min_hosts_threshold: int = 3,
                 time_window_minutes: int = 60):
        """
        Initialize lateral movement detector.

        Args:
            min_hosts_threshold: Minimum hosts for lateral movement alert
            time_window_minutes: Time window for detection
        """
        self.min_hosts_threshold = min_hosts_threshold
        self.time_window_minutes = time_window_minutes

    def detect_rdp_lateral_movement(self,
                                   auth_events: List[Dict]) -> List[LateralMovementAlert]:
        """
        Detect RDP-based lateral movement.

        Args:
            auth_events: List of authentication events

        Returns:
            List of lateral movement alerts
        """
        alerts = []

        # Filter RDP authentications
        rdp_auths = [
            e for e in auth_events
            if e.get('auth_type') == 'RDP' or e.get('port') == 3389
        ]

        # Group by user
        user_auths = {}
        for auth in rdp_auths:
            user_id = auth.get('user_id')
            if user_id:
                if user_id not in user_auths:
                    user_auths[user_id] = []
                user_auths[user_id].append(auth)

        # Detect multiple RDP sessions in time window
        for user_id, auths in user_auths.items():
            # Sort by timestamp
            sorted_auths = sorted(auths, key=lambda x: x['timestamp'])

            # Check for multiple distinct hosts in time window
            time_window = timedelta(minutes=self.time_window_minutes)
            hosts_accessed = set()

            for i, auth in enumerate(sorted_auths):
                current_time = datetime.fromisoformat(auth['timestamp'])
                current_host = auth.get('target_host')

                if current_host:
                    hosts_accessed.add(current_host)

                # Check if we exceeded threshold
                if len(hosts_accessed) >= self.min_hosts_threshold:
                    alert = LateralMovementAlert(
                        alert_id=f"lm_{user_id}_{int(current_time.timestamp())}",
                        user_id=user_id,
                        username=auth.get('username', 'unknown'),
                        source_hosts=[auth.get('source_host')],
                        target_hosts=list(hosts_accessed),
                        technique='T1021.001',
                        confidence=0.85,
                        severity='high',
                        details={
                            'method': 'RDP',
                            'host_count': len(hosts_accessed),
                            'time_window_minutes': self.time_window_minutes
                        },
                        timestamp=current_time
                    )
                    alerts.append(alert)
                    break

        return alerts

    def detect_psexec_lateral_movement(self,
                                      process_events: List[Dict]) -> List[LateralMovementAlert]:
        """
        Detect PsExec-based lateral movement.

        Args:
            process_events: List of process execution events

        Returns:
            List of lateral movement alerts
        """
        alerts = []

        # Look for PsExec service executions
        psexec_indicators = ['psexesvc.exe', 'psexec.exe', 'PSEXESVC']

        psexec_events = [
            e for e in process_events
            if any(ind in e.get('process_name', '').lower() for ind in
                   [i.lower() for i in psexec_indicators])
        ]

        # TODO: Implement PsExec detection logic
        # Group by user and check for multiple hosts

        return alerts

    def detect_wmi_lateral_movement(self,
                                   wmi_events: List[Dict]) -> List[LateralMovementAlert]:
        """
        Detect WMI-based lateral movement.

        Args:
            wmi_events: List of WMI execution events

        Returns:
            List of lateral movement alerts
        """
        alerts = []

        # Look for WMI remote execution
        # TODO: Implement WMI detection logic

        return alerts

    def detect_pass_the_hash(self,
                           auth_events: List[Dict]) -> List[LateralMovementAlert]:
        """
        Detect Pass-the-Hash attacks.

        Args:
            auth_events: List of authentication events

        Returns:
            List of lateral movement alerts
        """
        alerts = []

        # Look for NTLM authentication patterns
        ntlm_auths = [
            e for e in auth_events
            if e.get('auth_method') == 'NTLM'
        ]

        # Group by user
        user_auths = {}
        for auth in ntlm_auths:
            user_id = auth.get('user_id')
            if user_id:
                if user_id not in user_auths:
                    user_auths[user_id] = []
                user_auths[user_id].append(auth)

        # Detect multiple NTLM auths to different hosts in short time
        for user_id, auths in user_auths.items():
            sorted_auths = sorted(auths, key=lambda x: x['timestamp'])

            # Check for rapid authentication to multiple hosts
            for i in range(len(sorted_auths) - 1):
                current = sorted_auths[i]
                next_auth = sorted_auths[i + 1]

                current_time = datetime.fromisoformat(current['timestamp'])
                next_time = datetime.fromisoformat(next_auth['timestamp'])

                # If authentications are within 5 minutes to different hosts
                if (next_time - current_time).total_seconds() < 300:
                    if current.get('target_host') != next_auth.get('target_host'):
                        alert = LateralMovementAlert(
                            alert_id=f"pth_{user_id}_{int(current_time.timestamp())}",
                            user_id=user_id,
                            username=current.get('username', 'unknown'),
                            source_hosts=[current.get('source_host')],
                            target_hosts=[current.get('target_host'),
                                        next_auth.get('target_host')],
                            technique='T1550.002',
                            confidence=0.75,
                            severity='high',
                            details={
                                'method': 'Pass-the-Hash',
                                'auth_method': 'NTLM',
                                'time_delta_seconds': (next_time - current_time).total_seconds()
                            },
                            timestamp=current_time
                        )
                        alerts.append(alert)

        return alerts

    def detect_admin_share_access(self,
                                 file_events: List[Dict]) -> List[LateralMovementAlert]:
        """
        Detect lateral movement via Windows Admin Shares (C$, ADMIN$, etc).

        Args:
            file_events: List of file access events

        Returns:
            List of lateral movement alerts
        """
        alerts = []

        admin_shares = ['C$', 'ADMIN$', 'IPC$']

        # Filter admin share access
        admin_share_access = [
            e for e in file_events
            if any(share in e.get('path', '') for share in admin_shares)
        ]

        # TODO: Implement admin share detection logic

        return alerts

    def analyze_attack_path(self,
                          source_host: str,
                          target_host: str,
                          events: List[Dict]) -> Dict:
        """
        Analyze the attack path between two hosts.

        Args:
            source_host: Source hostname
            target_host: Target hostname
            events: Related events

        Returns:
            Attack path analysis
        """
        # TODO: Implement attack path analysis
        # Use graph database to find intermediate hops

        return {
            'source': source_host,
            'target': target_host,
            'intermediate_hops': [],
            'techniques_used': [],
            'timeline': []
        }


# Example usage
if __name__ == "__main__":
    detector = LateralMovementDetector(
        min_hosts_threshold=3,
        time_window_minutes=60
    )

    # Sample authentication events
    sample_events = [
        {
            'user_id': 'user123',
            'username': 'attacker',
            'auth_type': 'RDP',
            'target_host': 'HOST-A',
            'source_host': 'HOST-INITIAL',
            'timestamp': '2024-01-15T10:00:00Z'
        },
        {
            'user_id': 'user123',
            'username': 'attacker',
            'auth_type': 'RDP',
            'target_host': 'HOST-B',
            'source_host': 'HOST-A',
            'timestamp': '2024-01-15T10:15:00Z'
        },
        {
            'user_id': 'user123',
            'username': 'attacker',
            'auth_type': 'RDP',
            'target_host': 'HOST-C',
            'source_host': 'HOST-B',
            'timestamp': '2024-01-15T10:30:00Z'
        }
    ]

    alerts = detector.detect_rdp_lateral_movement(sample_events)
    print(f"Detected {len(alerts)} lateral movement alerts")
    for alert in alerts:
        print(f"Alert: {alert.technique} - {alert.details}")
