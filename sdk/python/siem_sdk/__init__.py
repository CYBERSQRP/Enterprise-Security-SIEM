"""
Enterprise SIEM Python SDK

Official Python SDK for interacting with the Enterprise SIEM platform.

Example usage:
    from siem_sdk import SIEMClient

    client = SIEMClient(
        api_url="https://siem.example.com/api",
        api_key="your-api-key"
    )

    # Search for events
    events = client.events.search(
        query="failed_login AND user:admin",
        time_range="last_24h"
    )

    # Create an alert
    alert = client.alerts.create(
        severity="high",
        title="Suspicious Activity Detected",
        description="Multiple failed login attempts"
    )
"""

import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
from dataclasses import dataclass


__version__ = "1.0.0"


@dataclass
class Event:
    """Represents a security event."""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    user: Optional[str] = None
    message: str = ""
    raw_data: Dict = None


@dataclass
class Alert:
    """Represents a security alert."""
    alert_id: str
    title: str
    severity: str
    status: str
    created_at: datetime
    description: str = ""
    assigned_to: Optional[str] = None


class SIEMException(Exception):
    """Base exception for SIEM SDK."""
    pass


class APIException(SIEMException):
    """Exception for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class EventsAPI:
    """API client for event operations."""

    def __init__(self, client):
        self.client = client

    def search(
        self,
        query: Optional[str] = None,
        time_range: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        filters: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Event]:
        """
        Search for security events.

        Args:
            query: Search query string
            time_range: Time range (e.g., "last_24h", "last_7d")
            start_time: Start of time range
            end_time: End of time range
            filters: Additional filters
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of Event objects
        """
        params = {
            'limit': limit,
            'offset': offset
        }

        if query:
            params['query'] = query

        if time_range:
            params['time_range'] = time_range
        elif start_time and end_time:
            params['start_time'] = start_time.isoformat()
            params['end_time'] = end_time.isoformat()

        if filters:
            params['filters'] = json.dumps(filters)

        response = self.client._request('GET', '/events/search', params=params)

        events = []
        for event_data in response.get('events', []):
            events.append(Event(
                event_id=event_data['event_id'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                event_type=event_data['event_type'],
                severity=event_data['severity'],
                source_ip=event_data.get('source_ip'),
                dest_ip=event_data.get('dest_ip'),
                user=event_data.get('user'),
                message=event_data.get('message', ''),
                raw_data=event_data
            ))

        return events

    def get(self, event_id: str) -> Event:
        """
        Get a specific event by ID.

        Args:
            event_id: Event identifier

        Returns:
            Event object
        """
        response = self.client._request('GET', f'/events/{event_id}')

        return Event(
            event_id=response['event_id'],
            timestamp=datetime.fromisoformat(response['timestamp']),
            event_type=response['event_type'],
            severity=response['severity'],
            source_ip=response.get('source_ip'),
            dest_ip=response.get('dest_ip'),
            user=response.get('user'),
            message=response.get('message', ''),
            raw_data=response
        )

    def aggregate(
        self,
        field: str,
        query: Optional[str] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Aggregate events by a field.

        Args:
            field: Field to aggregate by
            query: Optional query filter
            time_range: Optional time range

        Returns:
            Dictionary of aggregated counts
        """
        params = {'field': field}

        if query:
            params['query'] = query
        if time_range:
            params['time_range'] = time_range

        response = self.client._request('GET', '/events/aggregate', params=params)
        return response.get('aggregations', {})


class AlertsAPI:
    """API client for alert operations."""

    def __init__(self, client):
        self.client = client

    def list(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        List alerts.

        Args:
            status: Filter by status
            severity: Filter by severity
            limit: Maximum number of results

        Returns:
            List of Alert objects
        """
        params = {'limit': limit}

        if status:
            params['status'] = status
        if severity:
            params['severity'] = severity

        response = self.client._request('GET', '/alerts', params=params)

        alerts = []
        for alert_data in response.get('alerts', []):
            alerts.append(Alert(
                alert_id=alert_data['alert_id'],
                title=alert_data['title'],
                severity=alert_data['severity'],
                status=alert_data['status'],
                created_at=datetime.fromisoformat(alert_data['created_at']),
                description=alert_data.get('description', ''),
                assigned_to=alert_data.get('assigned_to')
            ))

        return alerts

    def create(
        self,
        title: str,
        severity: str,
        description: str,
        event_ids: Optional[List[str]] = None
    ) -> Alert:
        """
        Create a new alert.

        Args:
            title: Alert title
            severity: Severity level
            description: Alert description
            event_ids: Related event IDs

        Returns:
            Created Alert object
        """
        data = {
            'title': title,
            'severity': severity,
            'description': description
        }

        if event_ids:
            data['event_ids'] = event_ids

        response = self.client._request('POST', '/alerts', json=data)

        return Alert(
            alert_id=response['alert_id'],
            title=response['title'],
            severity=response['severity'],
            status=response['status'],
            created_at=datetime.fromisoformat(response['created_at']),
            description=response.get('description', ''),
            assigned_to=response.get('assigned_to')
        )

    def update(self, alert_id: str, **kwargs) -> Alert:
        """Update an alert."""
        response = self.client._request('PATCH', f'/alerts/{alert_id}', json=kwargs)

        return Alert(
            alert_id=response['alert_id'],
            title=response['title'],
            severity=response['severity'],
            status=response['status'],
            created_at=datetime.fromisoformat(response['created_at']),
            description=response.get('description', ''),
            assigned_to=response.get('assigned_to')
        )


class ThreatIntelAPI:
    """API client for threat intelligence operations."""

    def __init__(self, client):
        self.client = client

    def lookup_ioc(self, ioc: str, ioc_type: str) -> Dict:
        """
        Lookup an indicator of compromise.

        Args:
            ioc: The IOC value
            ioc_type: Type of IOC (ip, domain, hash, etc.)

        Returns:
            Threat intelligence data
        """
        params = {
            'ioc': ioc,
            'type': ioc_type
        }

        return self.client._request('GET', '/threat-intel/lookup', params=params)

    def add_ioc(self, ioc: str, ioc_type: str, threat_type: str, **metadata) -> Dict:
        """Add a new IOC to the threat intelligence database."""
        data = {
            'ioc': ioc,
            'type': ioc_type,
            'threat_type': threat_type,
            **metadata
        }

        return self.client._request('POST', '/threat-intel/iocs', json=data)


class AIAPI:
    """API client for AI-powered features."""

    def __init__(self, client):
        self.client = client

    def analyze_alert(self, alert_id: str) -> Dict:
        """
        Use AI to analyze an alert.

        Args:
            alert_id: Alert to analyze

        Returns:
            AI analysis results
        """
        return self.client._request('POST', f'/ai/analyze/alert/{alert_id}')

    def investigate(self, event_ids: List[str]) -> Dict:
        """
        Run automated investigation on events.

        Args:
            event_ids: List of event IDs to investigate

        Returns:
            Investigation results
        """
        data = {'event_ids': event_ids}
        return self.client._request('POST', '/ai/investigate', json=data)

    def prioritize_alerts(self, alert_ids: List[str]) -> List[Dict]:
        """
        Get AI-powered alert prioritization.

        Args:
            alert_ids: List of alert IDs to prioritize

        Returns:
            Prioritized alerts with scores
        """
        data = {'alert_ids': alert_ids}
        response = self.client._request('POST', '/ai/prioritize', json=data)
        return response.get('prioritized_alerts', [])


class SIEMClient:
    """
    Main SIEM SDK client.

    Example:
        client = SIEMClient(
            api_url="https://siem.example.com/api",
            api_key="your-api-key"
        )

        events = client.events.search(query="failed_login")
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize SIEM client.

        Args:
            api_url: Base URL of SIEM API
            api_key: API authentication key
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'SIEM-Python-SDK/{__version__}'
        })

        # Initialize API clients
        self.events = EventsAPI(self)
        self.alerts = AlertsAPI(self)
        self.threat_intel = ThreatIntelAPI(self)
        self.ai = AIAPI(self)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict:
        """
        Make an API request.

        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            json: JSON body

        Returns:
            Response data

        Raises:
            APIException: If the API returns an error
        """
        url = f"{self.api_url}{path}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                message = error_data.get('error', str(e))
            except:
                message = str(e)

            raise APIException(e.response.status_code, message)

        except requests.exceptions.RequestException as e:
            raise SIEMException(f"Request failed: {str(e)}")

    def health_check(self) -> Dict:
        """Check API health status."""
        return self._request('GET', '/health')


# Convenience exports
__all__ = [
    'SIEMClient',
    'Event',
    'Alert',
    'SIEMException',
    'APIException'
]
