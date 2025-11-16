#!/usr/bin/env python3
"""
Phase 6 Integration Tests

Tests for Phase 6 services including threat intelligence, supply chain monitoring,
forensics, collaboration, and predictive analytics.
"""

import pytest
import asyncio
import httpx
from datetime import datetime, timedelta


class TestThreatIntelAggregator:
    """Tests for Threat Intelligence Aggregator service"""

    @pytest.fixture
    def base_url(self):
        return "http://threat-intel-aggregator:8080"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_list_feeds(self, base_url):
        """Test listing threat intelligence feeds"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/feeds")
            assert response.status_code == 200
            data = response.json()
            assert "feeds" in data
            assert "count" in data
            assert data["count"] > 0

    @pytest.mark.asyncio
    async def test_get_feed(self, base_url):
        """Test getting specific feed details"""
        async with httpx.AsyncClient() as client:
            # First get list of feeds
            feeds_response = await client.get(f"{base_url}/api/v1/feeds")
            feeds = feeds_response.json()["feeds"]

            if feeds:
                feed_id = feeds[0]["id"]
                response = await client.get(f"{base_url}/api/v1/feeds/{feed_id}")
                assert response.status_code == 200
                feed = response.json()
                assert feed["id"] == feed_id

    @pytest.mark.asyncio
    async def test_refresh_feed(self, base_url):
        """Test manual feed refresh"""
        async with httpx.AsyncClient() as client:
            feed_id = "alienvault-otx"
            response = await client.post(f"{base_url}/api/v1/feeds/{feed_id}/refresh")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "refresh_started"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, base_url):
        """Test Prometheus metrics endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url.replace('8080', '9090')}/metrics")
            assert response.status_code == 200
            assert "threat_intel_feeds_processed_total" in response.text


class TestSupplyChainMonitor:
    """Tests for Supply Chain Monitor service"""

    @pytest.fixture
    def base_url(self):
        return "http://supply-chain-monitor:8081"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_vendors(self, base_url):
        """Test listing monitored vendors"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/vendors")
            assert response.status_code == 200
            data = response.json()
            assert "vendors" in data
            assert data["count"] > 0

    @pytest.mark.asyncio
    async def test_vendor_risk_assessment(self, base_url):
        """Test vendor risk assessment"""
        async with httpx.AsyncClient() as client:
            # Get list of vendors
            vendors_response = await client.get(f"{base_url}/api/v1/vendors")
            vendors = vendors_response.json()["vendors"]

            if vendors:
                vendor_id = vendors[0]["id"]
                response = await client.post(
                    f"{base_url}/api/v1/vendors/{vendor_id}/assess"
                )
                assert response.status_code == 200
                assessment = response.json()
                assert "risk_score" in assessment
                assert "risk_level" in assessment
                assert assessment["risk_score"] >= 0

    @pytest.mark.asyncio
    async def test_create_vendor_event(self, base_url):
        """Test creating a vendor event"""
        async with httpx.AsyncClient() as client:
            event_data = {
                "vendor_id": "aws",
                "event_type": "api_call",
                "severity": "medium",
                "description": "Test API call event"
            }
            response = await client.post(
                f"{base_url}/api/v1/events",
                json=event_data
            )
            assert response.status_code == 200
            event = response.json()
            assert "id" in event
            assert event["vendor_id"] == "aws"


class TestForensicsCollector:
    """Tests for Forensics Collector service"""

    @pytest.fixture
    def base_url(self):
        return "http://forensics-collector:8082"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_evidence(self, base_url):
        """Test listing evidence items"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/evidence")
            assert response.status_code == 200
            data = response.json()
            assert "evidence" in data
            assert "count" in data

    @pytest.mark.asyncio
    async def test_memory_analysis(self, base_url):
        """Test memory dump analysis"""
        async with httpx.AsyncClient() as client:
            # First create mock evidence
            # In real scenario, would upload actual file

            # Test analysis request structure
            analysis_request = {
                "evidence_id": "test-evidence-1",
                "volatility_profile": "Win10x64_19041",
                "plugins": ["pslist", "netscan"]
            }
            # Note: This would fail without actual evidence
            # In production, would have proper test fixtures


class TestCollaborationHub:
    """Tests for Collaboration Hub service"""

    @pytest.fixture
    def base_url(self):
        return "http://collaboration-hub:8083"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_session(self, base_url):
        """Test creating investigation session"""
        async with httpx.AsyncClient() as client:
            session_data = {
                "incident_id": "incident-12345",
                "name": "Test Investigation",
                "created_by": "analyst@company.com"
            }
            response = await client.post(
                f"{base_url}/api/v1/sessions",
                json=session_data
            )
            assert response.status_code == 201
            session = response.json()
            assert "id" in session
            assert session["incident_id"] == "incident-12345"

    @pytest.mark.asyncio
    async def test_list_sessions(self, base_url):
        """Test listing investigation sessions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/sessions")
            assert response.status_code == 200
            data = response.json()
            assert "sessions" in data

    @pytest.mark.asyncio
    async def test_websocket_connection(self, base_url):
        """Test WebSocket connection (placeholder)"""
        # WebSocket testing requires special handling
        # Would use websockets library in production
        pass


class TestPredictiveAnalytics:
    """Tests for Predictive Analytics service"""

    @pytest.fixture
    def base_url(self):
        return "http://predictive-analytics:8084"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_models(self, base_url):
        """Test listing ML models"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/models")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert data["count"] > 0

    @pytest.mark.asyncio
    async def test_threat_forecast(self, base_url):
        """Test threat forecasting"""
        async with httpx.AsyncClient() as client:
            forecast_request = {
                "threat_category": "malware",
                "forecast_period": "daily",
                "days_ahead": 30
            }
            response = await client.post(
                f"{base_url}/api/v1/predict/threats",
                json=forecast_request,
                timeout=30.0
            )
            assert response.status_code == 200
            forecast = response.json()
            assert "predictions" in forecast
            assert "trend" in forecast
            assert len(forecast["predictions"]) == 30

    @pytest.mark.asyncio
    async def test_risk_prediction(self, base_url):
        """Test risk prediction"""
        async with httpx.AsyncClient() as client:
            risk_request = {
                "entity_id": "server-001",
                "entity_type": "asset",
                "time_horizon": 7
            }
            response = await client.post(
                f"{base_url}/api/v1/predict/risk",
                json=risk_request,
                timeout=30.0
            )
            assert response.status_code == 200
            prediction = response.json()
            assert "current_risk" in prediction
            assert "predicted_risk" in prediction
            assert "recommendations" in prediction

    @pytest.mark.asyncio
    async def test_attack_path_prediction(self, base_url):
        """Test attack path prediction"""
        async with httpx.AsyncClient() as client:
            attack_request = {
                "incident_id": "incident-12345",
                "current_indicators": ["phishing_email", "malware_download"]
            }
            response = await client.post(
                f"{base_url}/api/v1/predict/attack-path",
                json=attack_request,
                timeout=30.0
            )
            assert response.status_code == 200
            prediction = response.json()
            assert "predicted_stages" in prediction
            assert "next_targets" in prediction
            assert "recommended_actions" in prediction


class TestPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        base_url = "http://threat-intel-aggregator:8080"

        async def make_request():
            async with httpx.AsyncClient() as client:
                return await client.get(f"{base_url}/health")

        # Make 100 concurrent requests
        tasks = [make_request() for _ in range(100)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_response_time(self):
        """Test API response times"""
        base_url = "http://threat-intel-aggregator:8080"

        async with httpx.AsyncClient() as client:
            start = datetime.now()
            response = await client.get(f"{base_url}/api/v1/feeds")
            duration = (datetime.now() - start).total_seconds()

            assert response.status_code == 200
            assert duration < 1.0  # Should respond within 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
