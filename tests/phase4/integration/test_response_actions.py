"""
Phase 4 - Automated Response Actions Tests

Tests automated response capabilities including:
- Firewall integration (IP blocking, rule management)
- Endpoint isolation
- Account management (disable, password reset, MFA)
- Email security actions
- Custom action framework

Test Coverage:
- Action execution and verification
- Idempotency
- Error recovery
- Audit trail
- State verification
- Rollback/undo operations
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, List


class TestFirewallActions:
    """Test firewall integration and blocking actions."""

    def test_block_ip_address(self, firewall_client):
        """Test blocking an IP address on the firewall."""
        result = firewall_client.block_ip(
            ip_address="192.0.2.100",
            reason="Brute force attack detected",
            duration_hours=24
        )

        assert result.success is True
        assert result.rule_id is not None
        assert result.status == "active"

        # Verify block is in place
        is_blocked = firewall_client.is_ip_blocked("192.0.2.100")
        assert is_blocked is True

    def test_block_ip_idempotency(self, firewall_client):
        """Test that blocking same IP multiple times is idempotent."""
        ip = "192.0.2.101"

        # Block first time
        result1 = firewall_client.block_ip(ip, "Test")
        rule_id_1 = result1.rule_id

        # Block again
        result2 = firewall_client.block_ip(ip, "Test")
        rule_id_2 = result2.rule_id

        # Should return same rule
        assert rule_id_1 == rule_id_2

    def test_unblock_ip_address(self, firewall_client):
        """Test unblocking an IP address."""
        ip = "192.0.2.102"

        # Block IP
        block_result = firewall_client.block_ip(ip, "Test")

        # Unblock IP
        unblock_result = firewall_client.unblock_ip(ip)

        assert unblock_result.success is True

        # Verify IP is no longer blocked
        is_blocked = firewall_client.is_ip_blocked(ip)
        assert is_blocked is False

    def test_create_firewall_rule(self, firewall_client):
        """Test creating a custom firewall rule."""
        rule = {
            "name": "Block suspicious subnet",
            "action": "deny",
            "source_network": "198.51.100.0/24",
            "destination_network": "any",
            "protocol": "any",
            "enabled": True
        }

        result = firewall_client.create_rule(rule)

        assert result.rule_id is not None
        assert result.status == "active"

    def test_temporary_ip_block_expiration(self, firewall_client):
        """Test that temporary IP blocks expire correctly."""
        ip = "192.0.2.103"

        # Block for 5 seconds
        firewall_client.block_ip(
            ip=ip,
            reason="Test",
            duration_seconds=5
        )

        # Verify blocked
        assert firewall_client.is_ip_blocked(ip) is True

        # Wait for expiration
        time.sleep(6)

        # Verify unblocked
        assert firewall_client.is_ip_blocked(ip) is False

    def test_block_ip_audit_trail(self, firewall_client, audit_service):
        """Test that IP blocking creates audit trail."""
        ip = "192.0.2.104"

        firewall_client.block_ip(
            ip=ip,
            reason="Malicious activity",
            requested_by="analyst@example.com"
        )

        # Check audit log
        audit_entries = audit_service.get_entries(
            action_type="firewall.block_ip",
            resource=ip
        )

        assert len(audit_entries) > 0
        assert audit_entries[0].ip_address == ip
        assert audit_entries[0].user == "analyst@example.com"


class TestEndpointActions:
    """Test endpoint isolation and containment actions."""

    def test_isolate_endpoint_full(self, endpoint_client):
        """Test full endpoint isolation (network disconnect)."""
        result = endpoint_client.isolate_endpoint(
            hostname="workstation-42",
            isolation_type="full",
            reason="Ransomware detected"
        )

        assert result.success is True
        assert result.isolation_status == "isolated"

        # Verify isolation
        endpoint = endpoint_client.get_endpoint("workstation-42")
        assert endpoint.network_status == "isolated"
        assert endpoint.can_communicate_external is False

    def test_isolate_endpoint_partial(self, endpoint_client):
        """Test partial endpoint isolation (allow auth only)."""
        result = endpoint_client.isolate_endpoint(
            hostname="server-01",
            isolation_type="partial",
            allowed_destinations=["dc01.example.com", "dns.example.com"],
            reason="Suspicious activity"
        )

        assert result.success is True
        assert result.isolation_status == "partially_isolated"

        # Verify can reach allowed destinations
        endpoint = endpoint_client.get_endpoint("server-01")
        assert "dc01.example.com" in endpoint.allowed_destinations

    def test_release_endpoint_isolation(self, endpoint_client):
        """Test releasing endpoint from isolation."""
        hostname = "workstation-43"

        # Isolate
        endpoint_client.isolate_endpoint(hostname, "full", "Test")

        # Release
        result = endpoint_client.release_isolation(
            hostname=hostname,
            reason="Investigation complete"
        )

        assert result.success is True

        # Verify released
        endpoint = endpoint_client.get_endpoint(hostname)
        assert endpoint.network_status == "normal"

    def test_endpoint_isolation_with_approval(self, endpoint_client, approval_service):
        """Test endpoint isolation requiring approval."""
        # Configure to require approval for critical servers
        endpoint_client.configure_approval_policy({
            "critical_servers": True,
            "approvers": ["manager@example.com"]
        })

        # Attempt isolation
        result = endpoint_client.isolate_endpoint(
            hostname="critical-server-01",
            isolation_type="full",
            reason="Security test"
        )

        assert result.status == "pending_approval"
        assert result.approval_id is not None

        # Approve
        approval_service.approve_action(
            action_id=result.approval_id,
            approver="manager@example.com"
        )

        # Verify isolation proceeds
        time.sleep(2)
        endpoint = endpoint_client.get_endpoint("critical-server-01")
        assert endpoint.network_status == "isolated"

    def test_bulk_endpoint_isolation(self, endpoint_client):
        """Test isolating multiple endpoints simultaneously."""
        hostnames = ["ws-01", "ws-02", "ws-03", "ws-04", "ws-05"]

        results = endpoint_client.bulk_isolate(
            hostnames=hostnames,
            isolation_type="full",
            reason="Lateral movement detected"
        )

        assert results.total == 5
        assert results.succeeded == 5
        assert results.failed == 0

        # Verify all isolated
        for hostname in hostnames:
            endpoint = endpoint_client.get_endpoint(hostname)
            assert endpoint.network_status == "isolated"


class TestAccountActions:
    """Test account management actions."""

    def test_disable_user_account(self, account_client):
        """Test disabling a user account."""
        result = account_client.disable_account(
            username="suspicious.user",
            reason="Compromised credentials detected"
        )

        assert result.success is True
        assert result.account_status == "disabled"

        # Verify account disabled
        account = account_client.get_account("suspicious.user")
        assert account.enabled is False

    def test_enable_user_account(self, account_client):
        """Test re-enabling a user account."""
        username = "test.user"

        # Disable
        account_client.disable_account(username, "Test")

        # Re-enable
        result = account_client.enable_account(
            username=username,
            reason="Investigation complete - false positive"
        )

        assert result.success is True

        # Verify enabled
        account = account_client.get_account(username)
        assert account.enabled is True

    def test_reset_user_password(self, account_client):
        """Test forcing password reset for user."""
        result = account_client.force_password_reset(
            username="john.doe",
            reason="Credential leak detected",
            notify_user=True
        )

        assert result.success is True
        assert result.temporary_password is not None

        # Verify user must change password
        account = account_client.get_account("john.doe")
        assert account.must_change_password is True

    def test_terminate_user_sessions(self, account_client):
        """Test terminating all active user sessions."""
        username = "compromised.user"

        result = account_client.terminate_sessions(
            username=username,
            reason="Account compromise"
        )

        assert result.success is True
        assert result.sessions_terminated > 0

        # Verify no active sessions
        sessions = account_client.get_active_sessions(username)
        assert len(sessions) == 0

    def test_enable_mfa_enforcement(self, account_client):
        """Test enforcing MFA for a user account."""
        result = account_client.enforce_mfa(
            username="high.privilege.user",
            reason="Security policy"
        )

        assert result.success is True

        # Verify MFA required
        account = account_client.get_account("high.privilege.user")
        assert account.mfa_required is True

    def test_revoke_user_permissions(self, account_client):
        """Test revoking specific permissions from user."""
        result = account_client.revoke_permissions(
            username="insider.threat",
            permissions=["admin_access", "data_export", "sensitive_data_access"],
            reason="Insider threat investigation"
        )

        assert result.success is True
        assert result.permissions_revoked == 3

        # Verify permissions removed
        account = account_client.get_account("insider.threat")
        assert "admin_access" not in account.permissions


class TestEmailSecurityActions:
    """Test email security actions."""

    def test_quarantine_email(self, email_client):
        """Test quarantining a malicious email."""
        result = email_client.quarantine_email(
            message_id="<abc123@example.com>",
            reason="Phishing email detected"
        )

        assert result.success is True
        assert result.quarantine_id is not None

        # Verify email quarantined
        email = email_client.get_email_status("<abc123@example.com>")
        assert email.status == "quarantined"

    def test_delete_email_from_mailboxes(self, email_client):
        """Test deleting email from multiple mailboxes."""
        result = email_client.delete_email(
            message_id="<malicious@attacker.com>",
            mailboxes=["user1@example.com", "user2@example.com", "user3@example.com"],
            reason="Confirmed malware"
        )

        assert result.success is True
        assert result.deleted_from_count == 3

    def test_block_sender(self, email_client):
        """Test blocking an email sender."""
        result = email_client.block_sender(
            sender_email="spammer@malicious.com",
            reason="Phishing campaign",
            scope="organization"
        )

        assert result.success is True
        assert result.rule_id is not None

        # Verify sender blocked
        is_blocked = email_client.is_sender_blocked("spammer@malicious.com")
        assert is_blocked is True

    def test_block_url_in_emails(self, email_client):
        """Test blocking URLs in emails."""
        urls = [
            "https://malicious-phishing.com",
            "https://fake-login.example",
            "https://credential-stealer.net"
        ]

        result = email_client.block_urls(
            urls=urls,
            reason="Phishing URLs"
        )

        assert result.success is True
        assert result.urls_blocked == 3

        # Verify URLs blocked
        for url in urls:
            assert email_client.is_url_blocked(url) is True

    def test_release_quarantined_email(self, email_client):
        """Test releasing email from quarantine."""
        message_id = "<false-positive@example.com>"

        # Quarantine
        email_client.quarantine_email(message_id, "Test")

        # Release
        result = email_client.release_from_quarantine(
            quarantine_id=message_id,
            reason="False positive",
            deliver_to=["user@example.com"]
        )

        assert result.success is True

        # Verify released
        email = email_client.get_email_status(message_id)
        assert email.status == "delivered"

    def test_create_email_transport_rule(self, email_client):
        """Test creating email transport rule."""
        rule = {
            "name": "Block attachments from external senders",
            "conditions": {
                "sender_domain_is_external": True,
                "attachment_extension_matches": [".exe", ".scr", ".bat"]
            },
            "actions": {
                "quarantine": True,
                "notify_admin": True
            }
        }

        result = email_client.create_transport_rule(rule)

        assert result.rule_id is not None
        assert result.status == "active"


class TestCustomActions:
    """Test custom action framework."""

    def test_register_custom_action(self, action_registry):
        """Test registering a custom action."""
        action_spec = {
            "name": "check_ip_reputation",
            "description": "Check IP reputation against external service",
            "parameters": [
                {"name": "ip_address", "type": "string", "required": True},
                {"name": "provider", "type": "string", "default": "virustotal"}
            ],
            "handler": "custom_actions.check_ip_reputation",
            "timeout": 30
        }

        result = action_registry.register_action(action_spec)

        assert result.success is True
        assert result.action_id is not None

    def test_execute_custom_action(self, action_executor):
        """Test executing a custom action."""
        result = action_executor.execute(
            action_name="check_ip_reputation",
            parameters={
                "ip_address": "192.0.2.100",
                "provider": "abuseipdb"
            }
        )

        assert result.success is True
        assert result.outputs.get("reputation_score") is not None

    def test_custom_action_with_validation(self, action_registry):
        """Test custom action parameter validation."""
        action_spec = {
            "name": "send_webhook",
            "parameters": [
                {
                    "name": "url",
                    "type": "string",
                    "required": True,
                    "validation": "^https://.*"
                },
                {
                    "name": "method",
                    "type": "string",
                    "enum": ["GET", "POST", "PUT"],
                    "default": "POST"
                }
            ],
            "handler": "custom_actions.send_webhook"
        }

        action_registry.register_action(action_spec)

        # Test valid execution
        result = action_executor.execute(
            action_name="send_webhook",
            parameters={
                "url": "https://api.example.com/webhook",
                "method": "POST"
            }
        )

        assert result.success is True

        # Test invalid URL
        with pytest.raises(ValueError, match="URL validation failed"):
            action_executor.execute(
                action_name="send_webhook",
                parameters={"url": "http://insecure.com"}
            )

    def test_custom_action_error_handling(self, action_executor):
        """Test custom action error handling."""
        # Register action that throws exception
        def failing_action(**kwargs):
            raise Exception("Simulated failure")

        action_registry.register_action({
            "name": "failing_action",
            "handler": failing_action
        })

        # Execute
        result = action_executor.execute(
            action_name="failing_action",
            parameters={}
        )

        assert result.success is False
        assert result.error_message == "Simulated failure"

    def test_custom_action_timeout(self, action_executor):
        """Test custom action timeout enforcement."""
        # Register action with timeout
        def slow_action(**kwargs):
            time.sleep(10)
            return {"result": "done"}

        action_registry.register_action({
            "name": "slow_action",
            "handler": slow_action,
            "timeout": 2  # 2 second timeout
        })

        # Execute - should timeout
        result = action_executor.execute(
            action_name="slow_action",
            parameters={}
        )

        assert result.success is False
        assert "timeout" in result.error_message.lower()


class TestActionAuditTrail:
    """Test audit trail for all response actions."""

    def test_action_execution_logged(self, audit_service):
        """Test that all action executions are logged."""
        # Execute various actions
        firewall_client.block_ip("192.0.2.200", "Test")
        endpoint_client.isolate_endpoint("ws-99", "full", "Test")
        account_client.disable_account("test.user", "Test")

        # Check audit log
        audit_entries = audit_service.get_entries(
            event_type="response_action",
            time_range=timedelta(minutes=5)
        )

        assert len(audit_entries) >= 3

        action_types = [entry.action_type for entry in audit_entries]
        assert "firewall.block_ip" in action_types
        assert "endpoint.isolate" in action_types
        assert "account.disable" in action_types

    def test_action_audit_includes_context(self, audit_service, firewall_client):
        """Test that audit entries include full context."""
        firewall_client.block_ip(
            ip="192.0.2.201",
            reason="Brute force attack",
            requested_by="analyst@example.com",
            alert_id="alert-12345"
        )

        audit_entry = audit_service.get_latest_entry(action_type="firewall.block_ip")

        assert audit_entry.ip_address == "192.0.2.201"
        assert audit_entry.reason == "Brute force attack"
        assert audit_entry.user == "analyst@example.com"
        assert audit_entry.alert_id == "alert-12345"
        assert audit_entry.timestamp is not None

    def test_failed_actions_logged(self, audit_service, firewall_client):
        """Test that failed actions are logged with error details."""
        # Attempt to block invalid IP
        try:
            firewall_client.block_ip("invalid-ip", "Test")
        except ValueError:
            pass

        # Check audit log
        audit_entry = audit_service.get_latest_entry(
            action_type="firewall.block_ip",
            status="failed"
        )

        assert audit_entry is not None
        assert audit_entry.error_message is not None
        assert "invalid" in audit_entry.error_message.lower()


# Pytest fixtures

@pytest.fixture
def firewall_client():
    """Provide firewall client instance."""
    pass

@pytest.fixture
def endpoint_client():
    """Provide endpoint management client."""
    pass

@pytest.fixture
def account_client():
    """Provide account management client."""
    pass

@pytest.fixture
def email_client():
    """Provide email security client."""
    pass

@pytest.fixture
def action_registry():
    """Provide custom action registry."""
    pass

@pytest.fixture
def action_executor():
    """Provide action executor service."""
    pass

@pytest.fixture
def audit_service():
    """Provide audit service instance."""
    pass

@pytest.fixture
def approval_service():
    """Provide approval workflow service."""
    pass
