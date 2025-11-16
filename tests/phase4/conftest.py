"""
Phase 4 Test Configuration and Fixtures

Provides pytest configuration and shared fixtures for Phase 4 tests.
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, List


# Pytest configuration

def pytest_configure(config):
    """Configure pytest for Phase 4 tests."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring external services"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to execute"
    )
    config.addinivalue_line(
        "markers", "multi_tenant: Multi-tenancy specific tests"
    )
    config.addinivalue_line(
        "markers", "compliance: Compliance framework tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


# Environment configuration

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "database": {
            "host": os.getenv("TEST_DB_HOST", "localhost"),
            "port": int(os.getenv("TEST_DB_PORT", "5432")),
            "database": os.getenv("TEST_DB_NAME", "siem_test"),
            "username": os.getenv("TEST_DB_USER", "test_user"),
            "password": os.getenv("TEST_DB_PASSWORD", "test_password")
        },
        "elasticsearch": {
            "hosts": os.getenv("TEST_ES_HOSTS", "localhost:9200").split(","),
            "index_prefix": "test_siem"
        },
        "kafka": {
            "bootstrap_servers": os.getenv("TEST_KAFKA_BROKERS", "localhost:9092").split(","),
            "topic_prefix": "test_siem"
        },
        "redis": {
            "host": os.getenv("TEST_REDIS_HOST", "localhost"),
            "port": int(os.getenv("TEST_REDIS_PORT", "6379")),
            "db": int(os.getenv("TEST_REDIS_DB", "1"))
        },
        "test_data": {
            "generate_sample_data": os.getenv("GENERATE_TEST_DATA", "true").lower() == "true",
            "sample_events_count": int(os.getenv("SAMPLE_EVENTS_COUNT", "1000")),
            "sample_tenants_count": int(os.getenv("SAMPLE_TENANTS_COUNT", "5"))
        },
        "integrations": {
            "mock_external_services": os.getenv("MOCK_INTEGRATIONS", "true").lower() == "true",
            "soar_api_url": os.getenv("TEST_SOAR_URL", "http://localhost:8080"),
            "jira_api_url": os.getenv("TEST_JIRA_URL", "http://localhost:8081"),
            "edr_api_url": os.getenv("TEST_EDR_URL", "http://localhost:8082")
        }
    }


# Database fixtures

@pytest.fixture(scope="session")
def db_engine(test_config):
    """Create database engine for tests."""
    from sqlalchemy import create_engine

    db_config = test_config["database"]
    connection_string = (
        f"postgresql://{db_config['username']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )

    engine = create_engine(connection_string, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide database session with automatic rollback."""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


# Service fixtures

@pytest.fixture
def tenant_service():
    """Provide tenant service instance."""
    from services.tenant_service import TenantService
    return TenantService()


@pytest.fixture
def user_service():
    """Provide user service instance."""
    from services.user_service import UserService
    return UserService()


@pytest.fixture
def alert_service():
    """Provide alert service instance."""
    from services.alert_service import AlertService
    return AlertService()


@pytest.fixture
def event_service():
    """Provide event service instance."""
    from services.event_service import EventService
    return EventService()


@pytest.fixture
def incident_service():
    """Provide incident service instance."""
    from services.incident_service import IncidentService
    return IncidentService()


@pytest.fixture
def rbac_service():
    """Provide RBAC service instance."""
    from services.rbac_service import RBACService
    return RBACService()


@pytest.fixture
def audit_service():
    """Provide audit service instance."""
    from services.audit_service import AuditService
    return AuditService()


@pytest.fixture
def auth_service():
    """Provide authentication service instance."""
    from services.auth_service import AuthService
    return AuthService()


@pytest.fixture
def playbook_engine():
    """Provide playbook engine instance."""
    from services.playbook_engine import PlaybookEngine
    return PlaybookEngine()


@pytest.fixture
def compliance_service():
    """Provide compliance service instance."""
    from services.compliance_service import ComplianceService
    return ComplianceService()


# Test data fixtures

@pytest.fixture
def sample_tenant(tenant_service):
    """Create a sample tenant for testing."""
    tenant = tenant_service.create_tenant({
        "name": "Test Tenant",
        "domain": "test.example.com",
        "admin_email": "admin@test.example.com",
        "max_users": 100,
        "max_events_per_day": 1000000
    })

    yield tenant

    # Cleanup
    try:
        tenant_service.delete_tenant(tenant.id)
    except:
        pass


@pytest.fixture
def sample_user(user_service, sample_tenant):
    """Create a sample user for testing."""
    user = user_service.create_user({
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "tenant_id": sample_tenant.id,
        "role": "analyst"
    })

    yield user

    # Cleanup
    try:
        user_service.delete_user(user.id)
    except:
        pass


@pytest.fixture
def sample_alert(alert_service, sample_tenant):
    """Create a sample alert for testing."""
    alert = alert_service.create_alert({
        "tenant_id": sample_tenant.id,
        "title": "Test Alert",
        "description": "This is a test alert",
        "severity": "medium",
        "source_ip": "192.0.2.100",
        "destination_ip": "10.0.0.50",
        "category": "network_intrusion"
    })

    yield alert

    # Cleanup
    try:
        alert_service.delete_alert(alert.id)
    except:
        pass


@pytest.fixture
def sample_playbook(playbook_engine):
    """Create a sample playbook for testing."""
    playbook = {
        "name": "Test Playbook",
        "description": "Test playbook for unit tests",
        "trigger": "manual",
        "steps": [
            {
                "id": "step1",
                "action": "log_message",
                "inputs": {"message": "Test step 1"}
            },
            {
                "id": "step2",
                "action": "log_message",
                "inputs": {"message": "Test step 2"}
            }
        ]
    }

    created_playbook = playbook_engine.create_playbook(playbook)

    yield created_playbook

    # Cleanup
    try:
        playbook_engine.delete_playbook(created_playbook.id)
    except:
        pass


# Integration client fixtures (with mocking option)

@pytest.fixture
def soar_client(test_config):
    """Provide SOAR client instance (mocked or real based on config)."""
    if test_config["integrations"]["mock_external_services"]:
        from unittest.mock import MagicMock
        client = MagicMock()
        client.export_alert.return_value = {"success": True, "soar_case_id": "CASE-123"}
        return client
    else:
        from integrations.soar_client import SOARClient
        return SOARClient(api_url=test_config["integrations"]["soar_api_url"])


@pytest.fixture
def jira_client(test_config):
    """Provide Jira client instance (mocked or real based on config)."""
    if test_config["integrations"]["mock_external_services"]:
        from unittest.mock import MagicMock
        client = MagicMock()
        client.create_ticket.return_value = {"key": "SEC-123", "status": "Open"}
        return client
    else:
        from integrations.jira_client import JiraClient
        return JiraClient(api_url=test_config["integrations"]["jira_api_url"])


@pytest.fixture
def edr_client(test_config):
    """Provide EDR client instance (mocked or real based on config)."""
    if test_config["integrations"]["mock_external_services"]:
        from unittest.mock import MagicMock
        client = MagicMock()
        client.isolate_endpoint.return_value = {"success": True, "status": "isolated"}
        return client
    else:
        from integrations.edr_client import EDRClient
        return EDRClient(api_url=test_config["integrations"]["edr_api_url"])


# Elasticsearch fixtures

@pytest.fixture(scope="session")
def es_client(test_config):
    """Provide Elasticsearch client."""
    from elasticsearch import Elasticsearch

    es = Elasticsearch(
        hosts=test_config["elasticsearch"]["hosts"],
        verify_certs=False
    )

    yield es

    # Cleanup test indices
    test_indices = es.indices.get(index=f"{test_config['elasticsearch']['index_prefix']}*")
    for index_name in test_indices.keys():
        es.indices.delete(index=index_name)


# Kafka fixtures

@pytest.fixture(scope="session")
def kafka_admin(test_config):
    """Provide Kafka admin client."""
    from kafka.admin import KafkaAdminClient

    admin = KafkaAdminClient(
        bootstrap_servers=test_config["kafka"]["bootstrap_servers"]
    )

    yield admin

    admin.close()


# Redis fixtures

@pytest.fixture(scope="session")
def redis_client(test_config):
    """Provide Redis client."""
    import redis

    client = redis.Redis(
        host=test_config["redis"]["host"],
        port=test_config["redis"]["port"],
        db=test_config["redis"]["db"],
        decode_responses=True
    )

    yield client

    # Cleanup
    client.flushdb()
    client.close()


# Mock fixtures for external services

@pytest.fixture
def mock_firewall_client():
    """Provide mock firewall client."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.block_ip.return_value = {
        "success": True,
        "rule_id": "rule-123",
        "status": "active"
    }
    client.is_ip_blocked.return_value = True
    client.unblock_ip.return_value = {"success": True}

    return client


@pytest.fixture
def mock_endpoint_client():
    """Provide mock endpoint management client."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.isolate_endpoint.return_value = {
        "success": True,
        "isolation_status": "isolated"
    }
    client.get_endpoint.return_value = MagicMock(
        network_status="isolated",
        can_communicate_external=False
    )

    return client


@pytest.fixture
def mock_account_client():
    """Provide mock account management client."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.disable_account.return_value = {
        "success": True,
        "account_status": "disabled"
    }
    client.get_account.return_value = MagicMock(enabled=False)

    return client


# Performance monitoring fixtures

@pytest.fixture
def performance_monitor():
    """Provide performance monitoring utilities."""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}

        def start_timer(self, name: str):
            import time
            self.metrics[name] = {"start": time.time()}

        def stop_timer(self, name: str):
            import time
            if name in self.metrics:
                self.metrics[name]["end"] = time.time()
                self.metrics[name]["duration"] = (
                    self.metrics[name]["end"] - self.metrics[name]["start"]
                )

        def get_duration(self, name: str) -> float:
            if name in self.metrics and "duration" in self.metrics[name]:
                return self.metrics[name]["duration"]
            return 0.0

    return PerformanceMonitor()


# Cleanup hooks

@pytest.fixture(autouse=True, scope="function")
def cleanup_test_data(request):
    """Automatically cleanup test data after each test."""
    yield

    # Add cleanup logic here if needed
    # For example: delete temporary files, clear caches, etc.
    pass


# Test markers for selective execution

pytestmark = pytest.mark.phase4
