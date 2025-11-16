"""
Behavior Profiler Module

Creates and maintains behavioral profiles for users based on their historical activities.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np


@dataclass
class UserBehaviorProfile:
    """User behavior profile data structure"""
    user_id: str
    typical_login_hours: Set[int] = field(default_factory=set)
    typical_login_locations: Set[str] = field(default_factory=set)
    typical_applications: Set[str] = field(default_factory=set)
    average_files_accessed_per_day: float = 0.0
    average_data_downloaded_mb: float = 0.0
    average_session_duration_minutes: float = 0.0
    peer_group_id: Optional[str] = None
    baseline_start_date: Optional[datetime] = None
    baseline_end_date: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


class BehaviorProfiler:
    """
    Creates and maintains behavioral profiles for users.

    Analyzes historical user activity to establish baselines for:
    - Login patterns (time, location, frequency)
    - Resource access patterns
    - Application usage
    - Data transfer patterns
    - Session characteristics
    """

    def __init__(self, baseline_period_days: int = 30, min_events: int = 100):
        """
        Initialize the behavior profiler.

        Args:
            baseline_period_days: Number of days to use for baseline
            min_events: Minimum events required to create a profile
        """
        self.baseline_period_days = baseline_period_days
        self.min_events = min_events
        self.profiles: Dict[str, UserBehaviorProfile] = {}

    def create_profile(self,
                      user_id: str,
                      historical_events: List[Dict]) -> UserBehaviorProfile:
        """
        Create a behavioral profile for a user.

        Args:
            user_id: User identifier
            historical_events: List of user activity events

        Returns:
            UserBehaviorProfile object
        """
        if len(historical_events) < self.min_events:
            raise ValueError(
                f"Insufficient events ({len(historical_events)}) "
                f"to create profile. Minimum: {self.min_events}"
            )

        profile = UserBehaviorProfile(user_id=user_id)

        # Extract temporal patterns
        profile.typical_login_hours = self._extract_login_hours(historical_events)

        # Extract location patterns
        profile.typical_login_locations = self._extract_locations(historical_events)

        # Extract application usage
        profile.typical_applications = self._extract_applications(historical_events)

        # Calculate statistics
        profile.average_files_accessed_per_day = self._calculate_avg_files_accessed(
            historical_events
        )
        profile.average_data_downloaded_mb = self._calculate_avg_data_downloaded(
            historical_events
        )
        profile.average_session_duration_minutes = self._calculate_avg_session_duration(
            historical_events
        )

        # Set baseline dates
        profile.baseline_start_date = datetime.utcnow() - timedelta(
            days=self.baseline_period_days
        )
        profile.baseline_end_date = datetime.utcnow()
        profile.last_updated = datetime.utcnow()

        self.profiles[user_id] = profile
        return profile

    def _extract_login_hours(self, events: List[Dict]) -> Set[int]:
        """Extract typical login hours from events"""
        login_hours = []
        for event in events:
            if event.get('event_type') == 'login':
                timestamp = event.get('timestamp')
                if timestamp:
                    hour = datetime.fromisoformat(timestamp).hour
                    login_hours.append(hour)

        # Find hours that account for 90% of logins
        if login_hours:
            hour_counts = {}
            for hour in login_hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

            total = len(login_hours)
            sorted_hours = sorted(hour_counts.items(),
                                 key=lambda x: x[1],
                                 reverse=True)

            cumulative = 0
            typical_hours = set()
            for hour, count in sorted_hours:
                typical_hours.add(hour)
                cumulative += count
                if cumulative / total >= 0.9:
                    break

            return typical_hours

        return set()

    def _extract_locations(self, events: List[Dict]) -> Set[str]:
        """Extract typical login locations from events"""
        locations = set()
        for event in events:
            if event.get('event_type') == 'login':
                location = event.get('source_ip') or event.get('location')
                if location:
                    locations.add(location)
        return locations

    def _extract_applications(self, events: List[Dict]) -> Set[str]:
        """Extract typical applications used"""
        applications = set()
        for event in events:
            app = event.get('application')
            if app:
                applications.add(app)
        return applications

    def _calculate_avg_files_accessed(self, events: List[Dict]) -> float:
        """Calculate average files accessed per day"""
        file_access_events = [
            e for e in events
            if e.get('event_type') == 'file_access'
        ]
        if not file_access_events:
            return 0.0

        days = (
            max(datetime.fromisoformat(e['timestamp']) for e in file_access_events) -
            min(datetime.fromisoformat(e['timestamp']) for e in file_access_events)
        ).days or 1

        return len(file_access_events) / days

    def _calculate_avg_data_downloaded(self, events: List[Dict]) -> float:
        """Calculate average data downloaded per day in MB"""
        # TODO: Implement data download calculation
        return 0.0

    def _calculate_avg_session_duration(self, events: List[Dict]) -> float:
        """Calculate average session duration in minutes"""
        # TODO: Implement session duration calculation
        return 0.0

    def update_profile(self,
                      user_id: str,
                      recent_events: List[Dict]) -> UserBehaviorProfile:
        """
        Update an existing profile with recent events.

        Args:
            user_id: User identifier
            recent_events: Recent user activity events

        Returns:
            Updated UserBehaviorProfile
        """
        if user_id not in self.profiles:
            return self.create_profile(user_id, recent_events)

        # TODO: Implement incremental profile update
        profile = self.profiles[user_id]
        profile.last_updated = datetime.utcnow()
        return profile

    def get_profile(self, user_id: str) -> Optional[UserBehaviorProfile]:
        """Get the behavior profile for a user"""
        return self.profiles.get(user_id)

    def is_profile_stale(self,
                        user_id: str,
                        staleness_days: int = 7) -> bool:
        """
        Check if a profile is stale and needs updating.

        Args:
            user_id: User identifier
            staleness_days: Days before profile is considered stale

        Returns:
            True if profile is stale
        """
        profile = self.profiles.get(user_id)
        if not profile:
            return True

        days_since_update = (datetime.utcnow() - profile.last_updated).days
        return days_since_update >= staleness_days


# Example usage
if __name__ == "__main__":
    profiler = BehaviorProfiler(baseline_period_days=30, min_events=100)
    print("Behavior Profiler initialized")
    print(f"Baseline period: {profiler.baseline_period_days} days")
    print(f"Minimum events: {profiler.min_events}")
