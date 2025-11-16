"""
Phase 4 - Enterprise Integration Tests

Tests integrations with external enterprise systems including:
- SOAR platforms
- Ticketing systems (Jira, ServiceNow)
- EDR/XDR platforms (CrowdStrike, Microsoft Defender, SentinelOne)
- Cloud providers (AWS, Azure, GCP)
- Identity providers (Okta, Azure AD, Auth0)

Test Coverage:
- API connectivity and authentication
- Data transformation and mapping
- Bidirectional synchronization
- Error handling and retry logic
- Webhook delivery and processing
"""

import pytest
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestSOARIntegration:
    """Test SOAR platform integration."""

    def test_soar_alert_export(self, soar_client, sample_alert):
        """Test exporting alerts to SOAR platform."""
        result = soar_client.export_alert(
            alert_id=sample_alert.id,
            alert_data={
                "title": sample_alert.title,
                "severity": sample_alert.severity,
                "description": sample_alert.description,
                "indicators": sample_alert.indicators
            }
        )

        assert result.success is True
        assert result.soar_case_id is not None
        assert result.status == "created"

    def test_soar_bidirectional_sync(self, soar_client, sample_alert):
        """Test bidirectional sync between SIEM and SOAR."""
        # Export alert to SOAR
        soar_case = soar_client.export_alert(sample_alert.id)

        # Update case in SOAR
        soar_client.update_case(
            case_id=soar_case.id,
            status="in_progress",
            assignee="analyst@example.com"
        )

        # Sync back to SIEM
        time.sleep(2)  # Wait for webhook
        updated_alert = alert_service.get_alert(sample_alert.id)

        assert updated_alert.status == "in_progress"
        assert updated_alert.assignee == "analyst@example.com"

    def test_soar_playbook_trigger(self, soar_client, sample_alert):
        """Test triggering SOAR playbook from SIEM alert."""
        result = soar_client.trigger_playbook(
            playbook_name="Phishing Response",
            alert_id=sample_alert.id,
            parameters={
                "email_address": "phishing@example.com",
                "auto_quarantine": True
            }
        )

        assert result.execution_id is not None
        assert result.status == "running"

        # Wait for playbook completion
        execution = soar_client.wait_for_playbook(result.execution_id, timeout=30)
        assert execution.status == "completed"
        assert execution.actions_executed > 0

    def test_soar_connection_failure_retry(self, soar_client):
        """Test retry logic on connection failure."""
        with patch.object(soar_client, '_make_request') as mock_request:
            # Simulate connection failures followed by success
            mock_request.side_effect = [
                ConnectionError("Connection timeout"),
                ConnectionError("Connection timeout"),
                {"status": "success", "case_id": "12345"}
            ]

            result = soar_client.export_alert(alert_id="test-alert")

            # Should retry and eventually succeed
            assert mock_request.call_count == 3
            assert result["case_id"] == "12345"


class TestTicketingIntegration:
    """Test ticketing system integrations."""

    def test_jira_ticket_creation(self, jira_client, sample_alert):
        """Test automatic Jira ticket creation from alert."""
        ticket = jira_client.create_ticket(
            project="SEC",
            issue_type="Security Incident",
            summary=sample_alert.title,
            description=sample_alert.description,
            priority=map_severity_to_priority(sample_alert.severity),
            labels=["security", "siem", sample_alert.category]
        )

        assert ticket.key is not None
        assert ticket.key.startswith("SEC-")
        assert ticket.status == "Open"

    def test_jira_status_sync(self, jira_client, sample_alert):
        """Test bidirectional status synchronization with Jira."""
        # Create ticket from alert
        ticket = jira_client.create_ticket_from_alert(sample_alert.id)

        # Update ticket status in Jira
        jira_client.transition_issue(
            issue_key=ticket.key,
            transition="In Progress"
        )

        # Verify alert status updated
        time.sleep(2)
        updated_alert = alert_service.get_alert(sample_alert.id)
        assert updated_alert.ticket_status == "In Progress"

    def test_jira_comment_sync(self, jira_client, sample_alert):
        """Test comment synchronization between SIEM and Jira."""
        ticket = jira_client.create_ticket_from_alert(sample_alert.id)

        # Add comment in SIEM
        alert_service.add_comment(
            alert_id=sample_alert.id,
            comment="Initial investigation shows false positive",
            author="analyst@example.com"
        )

        # Verify comment appears in Jira
        time.sleep(2)
        jira_comments = jira_client.get_comments(ticket.key)
        assert len(jira_comments) > 0
        assert "false positive" in jira_comments[-1].body

    def test_servicenow_incident_creation(self, snow_client, sample_alert):
        """Test ServiceNow incident creation."""
        incident = snow_client.create_incident(
            short_description=sample_alert.title,
            description=sample_alert.description,
            urgency=map_severity_to_urgency(sample_alert.severity),
            impact="2",
            category="Security",
            assignment_group="Security Operations"
        )

        assert incident.number is not None
        assert incident.state == "New"
        assert incident.assignment_group == "Security Operations"

    def test_servicenow_cmdb_integration(self, snow_client, sample_alert):
        """Test integration with ServiceNow CMDB."""
        # Get asset information from alert
        asset_ip = sample_alert.source_ip

        # Query CMDB for asset details
        ci = snow_client.get_configuration_item(ip_address=asset_ip)

        assert ci is not None
        assert ci.ip_address == asset_ip
        assert ci.managed_by is not None

        # Enrich alert with CMDB data
        enriched_alert = alert_service.enrich_with_cmdb(
            alert_id=sample_alert.id,
            cmdb_data=ci
        )

        assert enriched_alert.asset_owner == ci.managed_by
        assert enriched_alert.asset_criticality == ci.business_criticality


class TestEDRIntegration:
    """Test EDR/XDR platform integrations."""

    def test_crowdstrike_detection_ingestion(self, crowdstrike_client):
        """Test ingesting detections from CrowdStrike."""
        detections = crowdstrike_client.get_detections(
            filter="status:'new'",
            limit=100
        )

        assert len(detections) > 0

        for detection in detections:
            # Ingest into SIEM
            event = event_service.ingest_edr_detection(
                source="crowdstrike",
                detection_id=detection.id,
                severity=detection.severity,
                hostname=detection.device.hostname,
                process=detection.behaviors[0].process_name,
                command_line=detection.behaviors[0].command_line
            )

            assert event.id is not None
            assert event.source == "crowdstrike"

    def test_crowdstrike_endpoint_isolation(self, crowdstrike_client):
        """Test endpoint isolation via CrowdStrike."""
        result = crowdstrike_client.contain_host(
            device_id="abc123def456",
            reason="Malware detected by SIEM correlation"
        )

        assert result.success is True
        assert result.action == "contained"

        # Verify isolation status
        device = crowdstrike_client.get_device("abc123def456")
        assert device.status == "containment_pending" or device.status == "contained"

    def test_crowdstrike_ioc_upload(self, crowdstrike_client, sample_iocs):
        """Test uploading IOCs to CrowdStrike."""
        result = crowdstrike_client.upload_iocs(
            iocs=sample_iocs,
            source="SIEM Threat Intelligence",
            action="detect",
            severity="high"
        )

        assert result.uploaded_count == len(sample_iocs)
        assert result.failed_count == 0

    def test_microsoft_defender_alert_ingestion(self, defender_client):
        """Test ingesting alerts from Microsoft Defender."""
        alerts = defender_client.get_alerts(
            filter="status eq 'New'",
            top=50
        )

        for alert in alerts:
            event = event_service.ingest_edr_detection(
                source="microsoft_defender",
                detection_id=alert.id,
                severity=alert.severity,
                hostname=alert.machineId,
                threat_family=alert.threatFamilyName,
                category=alert.category
            )

            assert event.normalized_severity in ["low", "medium", "high", "critical"]

    def test_sentinelone_threat_intelligence_sharing(self, sentinelone_client):
        """Test sharing threat intelligence with SentinelOne."""
        # Get IOCs from SIEM threat intel
        iocs = threat_intel_service.get_iocs(
            types=["sha256", "md5", "domain"],
            min_confidence=80
        )

        # Upload to SentinelOne
        result = sentinelone_client.create_threat_intelligence(
            indicators=iocs,
            source="Enterprise SIEM",
            validity_period_days=30
        )

        assert result.indicators_added > 0


class TestCloudProviderIntegration:
    """Test cloud provider integrations."""

    def test_aws_cloudtrail_ingestion(self, aws_client):
        """Test ingesting AWS CloudTrail logs."""
        # Configure CloudTrail integration
        integration = aws_client.setup_cloudtrail_integration(
            trail_name="enterprise-cloudtrail",
            s3_bucket="cloudtrail-logs-bucket",
            region="us-east-1"
        )

        assert integration.status == "active"

        # Fetch and ingest events
        events = aws_client.fetch_cloudtrail_events(
            start_time=datetime.now().replace(hour=0, minute=0),
            end_time=datetime.now()
        )

        ingested_count = 0
        for event in events:
            normalized_event = normalize_aws_event(event)
            event_service.ingest_event(normalized_event)
            ingested_count += 1

        assert ingested_count > 0

    def test_aws_guardduty_integration(self, aws_client):
        """Test AWS GuardDuty findings integration."""
        findings = aws_client.get_guardduty_findings(
            detector_id="abc123",
            filter={"severity": {"gte": 7}}
        )

        for finding in findings:
            alert = alert_service.create_alert(
                title=finding.title,
                description=finding.description,
                severity=map_guardduty_severity(finding.severity),
                source="aws_guardduty",
                aws_account_id=finding.accountId,
                aws_region=finding.region,
                resource=finding.resource
            )

            assert alert.id is not None

    def test_azure_monitor_log_ingestion(self, azure_client):
        """Test ingesting Azure Monitor logs."""
        # Query Azure activity logs
        logs = azure_client.query_logs(
            workspace_id="azure-workspace-id",
            query="""
                AzureActivity
                | where TimeGenerated > ago(1h)
                | where CategoryValue == "Security"
            """,
            timespan="PT1H"
        )

        for log in logs:
            event = event_service.ingest_event({
                "source": "azure_monitor",
                "timestamp": log.TimeGenerated,
                "user": log.Caller,
                "action": log.OperationNameValue,
                "resource": log.ResourceId,
                "status": log.ActivityStatusValue
            })

            assert event.id is not None

    def test_azure_sentinel_bidirectional_sync(self, azure_sentinel_client):
        """Test bidirectional sync with Azure Sentinel."""
        # Export incident to Sentinel
        incident = incident_service.get_incident("incident-123")

        sentinel_incident = azure_sentinel_client.create_incident(
            title=incident.title,
            description=incident.description,
            severity=incident.severity,
            status=incident.status
        )

        assert sentinel_incident.incident_number is not None

        # Update in Sentinel
        azure_sentinel_client.update_incident(
            incident_id=sentinel_incident.id,
            status="Active",
            owner="analyst@example.com"
        )

        # Sync back
        time.sleep(3)
        updated_incident = incident_service.get_incident("incident-123")
        assert updated_incident.assignee == "analyst@example.com"

    def test_gcp_logging_integration(self, gcp_client):
        """Test Google Cloud Platform logging integration."""
        # Set up log sink
        sink = gcp_client.create_log_sink(
            sink_name="siem-integration",
            destination="pubsub.googleapis.com/projects/my-project/topics/siem-logs",
            filter='severity >= "WARNING"'
        )

        assert sink.name == "siem-integration"

        # Subscribe to Pub/Sub topic
        messages = gcp_client.pull_pubsub_messages(
            subscription="siem-logs-sub",
            max_messages=100
        )

        for message in messages:
            log_entry = json.loads(message.data)
            event = event_service.ingest_event({
                "source": "gcp_logging",
                "timestamp": log_entry.get("timestamp"),
                "severity": log_entry.get("severity"),
                "log_name": log_entry.get("logName"),
                "resource": log_entry.get("resource"),
                "message": log_entry.get("textPayload")
            })

            assert event.id is not None

            # Acknowledge message
            gcp_client.acknowledge_message(message.ack_id)


class TestIdentityProviderIntegration:
    """Test identity provider integrations."""

    def test_okta_user_provisioning(self, okta_client):
        """Test user provisioning from Okta."""
        # Fetch users from Okta
        okta_users = okta_client.list_users(
            filter='status eq "ACTIVE"',
            limit=200
        )

        for okta_user in okta_users:
            # Provision user in SIEM
            user = user_service.provision_user(
                email=okta_user.profile.email,
                first_name=okta_user.profile.firstName,
                last_name=okta_user.profile.lastName,
                external_id=okta_user.id,
                source="okta"
            )

            assert user.id is not None
            assert user.email == okta_user.profile.email

    def test_okta_group_sync(self, okta_client):
        """Test syncing Okta groups to SIEM roles."""
        # Map Okta groups to SIEM roles
        group_mapping = {
            "Security-Analysts": "analyst",
            "Security-Admin": "admin",
            "Security-Viewers": "viewer"
        }

        for okta_group_name, siem_role in group_mapping.items():
            # Get Okta group members
            group = okta_client.get_group_by_name(okta_group_name)
            members = okta_client.list_group_members(group.id)

            # Assign SIEM role to members
            for member in members:
                user = user_service.get_user_by_email(member.profile.email)
                if user:
                    rbac_service.assign_role(user.id, siem_role)

    def test_azure_ad_sso_authentication(self, azure_ad_client):
        """Test SSO authentication via Azure AD."""
        # Simulate SAML authentication flow
        saml_response = azure_ad_client.generate_saml_response(
            user_email="user@example.com",
            attributes={
                "firstName": "John",
                "lastName": "Doe",
                "groups": ["Security-Team"]
            }
        )

        # Process SAML response
        session = auth_service.process_saml_response(saml_response)

        assert session.user_id is not None
        assert session.authenticated is True
        assert "Security-Team" in session.user.groups

    def test_azure_ad_user_sync(self, azure_ad_client):
        """Test user synchronization from Azure AD."""
        # Fetch users from Azure AD
        ad_users = azure_ad_client.list_users(
            filter="accountEnabled eq true"
        )

        synced_count = 0
        for ad_user in ad_users:
            user = user_service.sync_user_from_azure_ad(
                upn=ad_user.userPrincipalName,
                display_name=ad_user.displayName,
                job_title=ad_user.jobTitle,
                department=ad_user.department
            )

            if user:
                synced_count += 1

        assert synced_count > 0

    def test_auth0_integration(self, auth0_client):
        """Test Auth0 integration for authentication."""
        # Configure Auth0 connection
        config = auth0_client.configure_connection(
            connection_name="enterprise-siem",
            strategy="auth0",
            enabled_clients=["siem-web-app", "siem-api"]
        )

        assert config.status == "active"

        # Test authentication
        token = auth0_client.authenticate(
            username="analyst@example.com",
            password="test-password",
            client_id="siem-web-app"
        )

        assert token.access_token is not None
        assert token.token_type == "Bearer"


class TestIntegrationErrorHandling:
    """Test error handling across integrations."""

    def test_api_rate_limiting(self, integration_client):
        """Test handling of API rate limiting."""
        with patch.object(integration_client, '_make_request') as mock_request:
            # Simulate rate limit response
            mock_request.return_value = Mock(
                status_code=429,
                headers={"Retry-After": "60"}
            )

            with pytest.raises(RateLimitError) as exc_info:
                integration_client.fetch_data()

            assert exc_info.value.retry_after == 60

    def test_authentication_failure_handling(self, integration_client):
        """Test handling of authentication failures."""
        with patch.object(integration_client, 'authenticate') as mock_auth:
            mock_auth.side_effect = AuthenticationError("Invalid credentials")

            with pytest.raises(AuthenticationError):
                integration_client.fetch_data()

            # Verify retry with token refresh
            assert mock_auth.call_count > 1

    def test_data_transformation_error(self, integration_client):
        """Test handling of data transformation errors."""
        malformed_data = {
            "invalid_field": "value",
            "missing_required_field": None
        }

        with pytest.raises(DataTransformationError) as exc_info:
            integration_client.transform_data(malformed_data)

        assert "required field" in str(exc_info.value).lower()

    def test_webhook_delivery_failure_retry(self, webhook_service):
        """Test retry logic for failed webhook deliveries."""
        webhook_url = "https://external-system.example.com/webhook"

        with patch('requests.post') as mock_post:
            # Simulate failures then success
            mock_post.side_effect = [
                Mock(status_code=500),
                Mock(status_code=503),
                Mock(status_code=200, json=lambda: {"status": "ok"})
            ]

            result = webhook_service.deliver_webhook(
                url=webhook_url,
                payload={"event": "alert.created"},
                max_retries=3
            )

            assert result.success is True
            assert mock_post.call_count == 3


# Helper functions

def map_severity_to_priority(severity: str) -> str:
    """Map SIEM severity to Jira priority."""
    mapping = {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low"
    }
    return mapping.get(severity, "Medium")

def map_severity_to_urgency(severity: str) -> str:
    """Map SIEM severity to ServiceNow urgency."""
    mapping = {
        "critical": "1",
        "high": "2",
        "medium": "3",
        "low": "4"
    }
    return mapping.get(severity, "3")

def map_guardduty_severity(severity: float) -> str:
    """Map GuardDuty severity to SIEM severity."""
    if severity >= 7.0:
        return "critical"
    elif severity >= 4.0:
        return "high"
    elif severity >= 1.0:
        return "medium"
    else:
        return "low"

def normalize_aws_event(event: dict) -> dict:
    """Normalize AWS CloudTrail event to SIEM format."""
    return {
        "timestamp": event.get("eventTime"),
        "source": "aws_cloudtrail",
        "event_type": event.get("eventName"),
        "user": event.get("userIdentity", {}).get("userName"),
        "source_ip": event.get("sourceIPAddress"),
        "aws_region": event.get("awsRegion"),
        "user_agent": event.get("userAgent"),
        "resource": event.get("resources", []),
        "raw": event
    }


# Custom exceptions

class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class DataTransformationError(Exception):
    """Raised when data transformation fails."""
    pass


# Pytest fixtures

@pytest.fixture
def soar_client():
    """Provide SOAR client instance."""
    pass

@pytest.fixture
def sample_alert():
    """Create a sample alert for testing."""
    pass

@pytest.fixture
def alert_service():
    """Provide alert service instance."""
    pass

@pytest.fixture
def jira_client():
    """Provide Jira client instance."""
    pass

@pytest.fixture
def snow_client():
    """Provide ServiceNow client instance."""
    pass

@pytest.fixture
def crowdstrike_client():
    """Provide CrowdStrike client instance."""
    pass

@pytest.fixture
def defender_client():
    """Provide Microsoft Defender client instance."""
    pass

@pytest.fixture
def sentinelone_client():
    """Provide SentinelOne client instance."""
    pass

@pytest.fixture
def aws_client():
    """Provide AWS client instance."""
    pass

@pytest.fixture
def azure_client():
    """Provide Azure client instance."""
    pass

@pytest.fixture
def azure_sentinel_client():
    """Provide Azure Sentinel client instance."""
    pass

@pytest.fixture
def gcp_client():
    """Provide GCP client instance."""
    pass

@pytest.fixture
def okta_client():
    """Provide Okta client instance."""
    pass

@pytest.fixture
def azure_ad_client():
    """Provide Azure AD client instance."""
    pass

@pytest.fixture
def auth0_client():
    """Provide Auth0 client instance."""
    pass

@pytest.fixture
def event_service():
    """Provide event service instance."""
    pass

@pytest.fixture
def incident_service():
    """Provide incident service instance."""
    pass

@pytest.fixture
def user_service():
    """Provide user service instance."""
    pass

@pytest.fixture
def rbac_service():
    """Provide RBAC service instance."""
    pass

@pytest.fixture
def auth_service():
    """Provide authentication service instance."""
    pass

@pytest.fixture
def threat_intel_service():
    """Provide threat intelligence service instance."""
    pass

@pytest.fixture
def sample_iocs():
    """Provide sample IOCs for testing."""
    return [
        {"type": "sha256", "value": "abc123..."},
        {"type": "domain", "value": "malicious.example.com"},
        {"type": "ip", "value": "192.0.2.100"}
    ]

@pytest.fixture
def integration_client():
    """Provide generic integration client for error testing."""
    pass

@pytest.fixture
def webhook_service():
    """Provide webhook service instance."""
    pass
