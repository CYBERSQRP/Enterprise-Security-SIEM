#!/usr/bin/env python3
"""
Phase 7 Integration Tests

Tests for Phase 7 services including AI orchestration, quantum crypto,
edge security, blockchain audit, and deception platform.
"""

import pytest
import asyncio
import httpx
from datetime import datetime


class TestAISecurityOrchestrator:
    """Tests for AI Security Orchestrator service"""

    @pytest.fixture
    def base_url(self):
        return "http://ai-security-orchestrator:8085"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "models" in data

    @pytest.mark.asyncio
    async def test_autonomous_decision(self, base_url):
        """Test autonomous decision making"""
        async with httpx.AsyncClient() as client:
            decision_request = {
                "incident_id": "test-inc-001",
                "severity": "high",
                "threat_type": "malware",
                "affected_assets": ["server-01", "server-02"],
                "indicators": ["suspicious_process", "network_anomaly"],
                "require_approval": False
            }
            response = await client.post(
                f"{base_url}/api/v1/decide",
                json=decision_request,
                timeout=10.0
            )
            assert response.status_code == 200
            recommendation = response.json()
            assert "decision" in recommendation
            assert "actions" in recommendation
            assert "impact_analysis" in recommendation
            assert recommendation["decision"]["confidence"] > 0

    @pytest.mark.asyncio
    async def test_list_models(self, base_url):
        """Test listing ML models"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/models")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert data["count"] >= 3  # At least 3 models

    @pytest.mark.asyncio
    async def test_list_actions(self, base_url):
        """Test listing available actions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/actions")
            assert response.status_code == 200
            data = response.json()
            assert "actions" in data
            assert data["count"] >= 8  # At least 8 actions

    @pytest.mark.asyncio
    async def test_feedback_submission(self, base_url):
        """Test reinforcement learning feedback"""
        async with httpx.AsyncClient() as client:
            feedback = {
                "decision_id": "decision-12345",
                "effective": True,
                "reward": 1.0,
                "notes": "Successfully contained threat"
            }
            response = await client.post(
                f"{base_url}/api/v1/feedback",
                json=feedback
            )
            assert response.status_code == 200
            assert response.json()["status"] == "feedback_recorded"


class TestQuantumCryptoService:
    """Tests for Quantum Crypto Service"""

    @pytest.fixture
    def base_url(self):
        return "http://quantum-crypto-service:8086"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_list_algorithms(self, base_url):
        """Test listing supported PQC algorithms"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/algorithms")
            assert response.status_code == 200
            data = response.json()
            assert "algorithms" in data
            assert data["count"] >= 6  # At least 6 PQC algorithms

    @pytest.mark.asyncio
    async def test_generate_key(self, base_url):
        """Test PQC key generation"""
        async with httpx.AsyncClient() as client:
            key_request = {
                "algorithm": "CRYSTALS-Dilithium",
                "usage": "signing",
                "mode": "quantum_only",
                "validity_days": 365
            }
            response = await client.post(
                f"{base_url}/api/v1/keys/generate",
                json=key_request,
                timeout=10.0
            )
            assert response.status_code == 200
            key_data = response.json()
            assert "key_id" in key_data
            assert "public_key" in key_data
            assert key_data["algorithm"] == "CRYSTALS-Dilithium"

    @pytest.mark.asyncio
    async def test_sign_and_verify(self, base_url):
        """Test PQC signing and verification"""
        async with httpx.AsyncClient() as client:
            # Generate key
            key_request = {
                "algorithm": "CRYSTALS-Dilithium",
                "usage": "signing",
                "mode": "quantum_only"
            }
            key_response = await client.post(
                f"{base_url}/api/v1/keys/generate",
                json=key_request,
                timeout=10.0
            )
            key_id = key_response.json()["key_id"]

            # Sign data
            sign_request = {
                "key_id": key_id,
                "data": "Important security message",
                "mode": "quantum_only"
            }
            sign_response = await client.post(
                f"{base_url}/api/v1/sign",
                json=sign_request,
                timeout=10.0
            )
            assert sign_response.status_code == 200
            signature_id = sign_response.json()["signature_id"]

            # Verify signature
            verify_request = {
                "signature_id": signature_id,
                "data": "Important security message",
                "public_key_id": key_id
            }
            verify_response = await client.post(
                f"{base_url}/api/v1/verify",
                json=verify_request,
                timeout=10.0
            )
            assert verify_response.status_code == 200
            assert verify_response.json()["valid"] == True

    @pytest.mark.asyncio
    async def test_quantum_readiness(self, base_url):
        """Test quantum readiness assessment"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/quantum-readiness")
            assert response.status_code == 200
            data = response.json()
            assert "readiness_score" in data
            assert "total_keys" in data
            assert "status" in data


class TestEdgeSecurityGateway:
    """Tests for Edge Security Gateway"""

    @pytest.fixture
    def base_url(self):
        return "http://edge-security-gateway:8087"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_register_device(self, base_url):
        """Test IoT device registration"""
        async with httpx.AsyncClient() as client:
            device_data = {
                "device_id": "iot-test-camera-01",
                "device_type": "camera",
                "location": "Test Lab",
                "ip_address": "192.168.1.100",
                "mac_address": "00:11:22:33:44:55",
                "firmware": "v2.1.0",
                "capabilities": ["motion_detection", "night_vision"]
            }
            response = await client.post(
                f"{base_url}/api/v1/devices/register",
                json=device_data
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "registered"
            assert "device" in data

    @pytest.mark.asyncio
    async def test_send_telemetry(self, base_url):
        """Test device telemetry submission"""
        async with httpx.AsyncClient() as client:
            # First register a device
            device_data = {
                "device_id": "iot-test-sensor-01",
                "device_type": "sensor",
                "location": "Test Lab",
                "ip_address": "192.168.1.101",
                "mac_address": "00:11:22:33:44:66",
                "firmware": "v1.0.0"
            }
            await client.post(f"{base_url}/api/v1/devices/register", json=device_data)

            # Send telemetry
            telemetry = {
                "device_id": "iot-test-sensor-01",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 62.5,
                    "network_traffic": 2048,
                    "temperature": 42.5
                }
            }
            response = await client.post(
                f"{base_url}/api/v1/telemetry",
                json=telemetry
            )
            assert response.status_code == 200
            assert response.json()["status"] == "received"

    @pytest.mark.asyncio
    async def test_list_devices(self, base_url):
        """Test listing registered devices"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/devices")
            assert response.status_code == 200
            data = response.json()
            assert "devices" in data
            assert "count" in data

    @pytest.mark.asyncio
    async def test_list_rules(self, base_url):
        """Test listing edge security rules"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/rules")
            assert response.status_code == 200
            data = response.json()
            assert "rules" in data
            assert data["count"] >= 3  # At least 3 default rules


class TestBlockchainAuditService:
    """Tests for Blockchain Audit Service"""

    @pytest.fixture
    def base_url(self):
        return "http://blockchain-audit-service:8088"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "chain_length" in data

    @pytest.mark.asyncio
    async def test_record_audit_event(self, base_url):
        """Test recording an audit event"""
        async with httpx.AsyncClient() as client:
            audit_event = {
                "event_type": "user_login",
                "user": "test@company.com",
                "action": "login",
                "resource": "/api/admin",
                "details": {"method": "password", "mfa": True},
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 Test",
                "outcome": "success"
            }
            response = await client.post(
                f"{base_url}/api/v1/audit/record",
                json=audit_event,
                timeout=10.0
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "recorded"
            assert "transaction_id" in data
            assert data["immutable"] == True

    @pytest.mark.asyncio
    async def test_verify_transaction(self, base_url):
        """Test transaction verification"""
        async with httpx.AsyncClient() as client:
            # Record an event
            audit_event = {
                "event_type": "data_access",
                "user": "analyst@company.com",
                "action": "read",
                "resource": "/data/customer",
                "details": {"record_count": 100},
                "ip_address": "192.168.1.101",
                "user_agent": "API Client",
                "outcome": "success"
            }
            record_response = await client.post(
                f"{base_url}/api/v1/audit/record",
                json=audit_event,
                timeout=10.0
            )
            transaction_id = record_response.json()["transaction_id"]

            # Give it a moment to be processed
            await asyncio.sleep(0.5)

            # Verify the transaction
            verify_request = {"transaction_id": transaction_id}
            verify_response = await client.post(
                f"{base_url}/api/v1/audit/verify",
                json=verify_request,
                timeout=10.0
            )

            if verify_response.status_code == 200:
                data = verify_response.json()
                assert "valid" in data
                assert "checks" in data

    @pytest.mark.asyncio
    async def test_get_chain(self, base_url):
        """Test retrieving the blockchain"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/chain")
            assert response.status_code == 200
            data = response.json()
            assert "chain" in data
            assert "length" in data
            assert data["length"] >= 1  # At least genesis block

    @pytest.mark.asyncio
    async def test_verify_chain(self, base_url):
        """Test blockchain integrity verification"""
        async with httpx.AsyncClient() as client:
            verify_request = {
                "start_block": 0,
                "end_block": None
            }
            response = await client.post(
                f"{base_url}/api/v1/audit/verify-chain",
                json=verify_request,
                timeout=10.0
            )
            assert response.status_code == 200
            data = response.json()
            assert "valid" in data
            assert data["valid"] == True


class TestDeceptionPlatform:
    """Tests for Deception Platform"""

    @pytest.fixture
    def base_url(self):
        return "http://deception-platform:8089"

    @pytest.mark.asyncio
    async def test_health_check(self, base_url):
        """Test service health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_create_honeypot(self, base_url):
        """Test honeypot creation"""
        async with httpx.AsyncClient() as client:
            honeypot_data = {
                "name": "Test SSH Honeypot",
                "type": "ssh_server",
                "interaction_level": "medium",
                "ip_address": "10.0.1.200",
                "port": 22,
                "protocol": "TCP",
                "services": ["ssh"],
                "decoy_data": {"banner": "Ubuntu Test SSH"}
            }
            response = await client.post(
                f"{base_url}/api/v1/honeypots",
                json=honeypot_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deployed"
            assert "honeypot" in data

    @pytest.mark.asyncio
    async def test_create_honeytoken(self, base_url):
        """Test honeytoken creation"""
        async with httpx.AsyncClient() as client:
            honeytoken_data = {
                "name": "Test API Key",
                "type": "api_key",
                "location": "/config/secrets.yaml",
                "auto_generate": True
            }
            response = await client.post(
                f"{base_url}/api/v1/honeytokens",
                json=honeytoken_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "created"
            assert "honeytoken" in data

    @pytest.mark.asyncio
    async def test_report_interaction(self, base_url):
        """Test reporting deception interaction"""
        async with httpx.AsyncClient() as client:
            # First list honeypots to get an ID
            honeypots_response = await client.get(f"{base_url}/api/v1/honeypots")
            honeypots = honeypots_response.json()["honeypots"]

            if honeypots:
                honeypot_id = honeypots[0]["honeypot_id"]

                # Report interaction
                interaction_data = {
                    "asset_id": honeypot_id,
                    "asset_type": "honeypot",
                    "source_ip": "192.168.100.50",
                    "source_port": 54321,
                    "destination_port": 22,
                    "protocol": "TCP",
                    "payload": "admin:password123"
                }
                response = await client.post(
                    f"{base_url}/api/v1/interactions",
                    json=interaction_data
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "recorded"
                assert "interaction" in data

    @pytest.mark.asyncio
    async def test_get_stats(self, base_url):
        """Test getting deception statistics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_honeypots" in data
            assert "total_honeytokens" in data
            assert "total_interactions" in data

    @pytest.mark.asyncio
    async def test_get_threat_intel(self, base_url):
        """Test threat intelligence extraction"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/threat-intel")
            assert response.status_code == 200
            data = response.json()
            assert "malicious_ips" in data
            assert "attack_patterns" in data


class TestPhase7Performance:
    """Performance tests for Phase 7 services"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_ai_decisions(self):
        """Test concurrent AI decision making"""
        base_url = "http://ai-security-orchestrator:8085"

        async def make_decision():
            async with httpx.AsyncClient() as client:
                decision_request = {
                    "incident_id": f"test-{asyncio.current_task().get_name()}",
                    "severity": "medium",
                    "threat_type": "phishing",
                    "affected_assets": ["user-01"],
                    "indicators": ["suspicious_email"],
                    "require_approval": False
                }
                return await client.post(
                    f"{base_url}/api/v1/decide",
                    json=decision_request,
                    timeout=30.0
                )

        # Make 10 concurrent decisions
        tasks = [make_decision() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful responses
        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        assert successful >= 8  # At least 80% success rate

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_blockchain_throughput(self):
        """Test blockchain audit event throughput"""
        base_url = "http://blockchain-audit-service:8088"

        async def record_event(index):
            async with httpx.AsyncClient() as client:
                audit_event = {
                    "event_type": "data_access",
                    "user": f"user{index}@company.com",
                    "action": "read",
                    "resource": "/data/test",
                    "details": {"test": True},
                    "ip_address": "192.168.1.100",
                    "user_agent": "Test",
                    "outcome": "success"
                }
                return await client.post(
                    f"{base_url}/api/v1/audit/record",
                    json=audit_event,
                    timeout=30.0
                )

        # Record 20 events concurrently
        tasks = [record_event(i) for i in range(20)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        assert successful >= 18  # At least 90% success rate


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
