"""
Comprehensive Module Configuration Tests

Tests to verify proper configuration of all SIEM modules including:
- Alert Prioritization
- AI Analyst
- Forensics Investigation
- Performance Optimizer
- Visualization Engine
- All Phase 6 and Phase 7 services
"""

import pytest
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List


# Base path
BASE_PATH = Path(__file__).parent.parent


class TestServiceConfigurations:
    """Test service configuration files exist and are valid."""

    def test_alert_prioritization_config(self):
        """Test Alert Prioritization service configuration."""
        service_path = BASE_PATH / "services" / "alert-prioritization"

        # Check Dockerfile exists
        assert (service_path / "Dockerfile").exists(), "Dockerfile missing"

        # Check requirements.txt exists and has content
        requirements = service_path / "requirements.txt"
        assert requirements.exists(), "requirements.txt missing"

        with open(requirements) as f:
            content = f.read()
            assert "fastapi" in content, "FastAPI dependency missing"
            assert "torch" in content, "PyTorch dependency missing"
            assert "prometheus-client" in content, "Prometheus client missing"

        # Check main.py exists
        assert (service_path / "main.py").exists(), "main.py missing"

        # Check prioritizer.py exists
        assert (service_path / "prioritizer.py").exists(), "prioritizer.py missing"

        # Check README exists
        assert (service_path / "README.md").exists(), "README.md missing"

    def test_ai_analyst_config(self):
        """Test AI Analyst service configuration."""
        service_path = BASE_PATH / "services" / "ai-analyst"

        # Check Dockerfile exists
        assert (service_path / "Dockerfile").exists(), "Dockerfile missing"

        # Check requirements.txt exists and has content
        requirements = service_path / "requirements.txt"
        assert requirements.exists(), "requirements.txt missing"

        with open(requirements) as f:
            content = f.read()
            assert "fastapi" in content, "FastAPI dependency missing"
            assert "elasticsearch" in content, "Elasticsearch dependency missing"

        # Check main.py exists
        assert (service_path / "main.py").exists(), "main.py missing"

        # Check assistant.py exists
        assert (service_path / "assistant.py").exists(), "assistant.py missing"

        # Check README exists
        assert (service_path / "README.md").exists(), "README.md missing"

    def test_forensics_config(self):
        """Test Forensics Investigation service configuration."""
        service_path = BASE_PATH / "services" / "forensics"

        # Check Dockerfile exists
        assert (service_path / "Dockerfile").exists(), "Dockerfile missing"

        # Check requirements.txt exists and has content
        requirements = service_path / "requirements.txt"
        assert requirements.exists(), "requirements.txt missing"

        with open(requirements) as f:
            content = f.read()
            assert "fastapi" in content, "FastAPI dependency missing"

        # Check main.py exists
        assert (service_path / "main.py").exists(), "main.py missing"

        # Check investigator.py exists
        assert (service_path / "investigator.py").exists(), "investigator.py missing"

        # Check README exists
        assert (service_path / "README.md").exists(), "README.md missing"

    def test_performance_optimizer_config(self):
        """Test Performance Optimizer service configuration."""
        service_path = BASE_PATH / "services" / "performance-optimizer"

        # Check Dockerfile exists
        assert (service_path / "Dockerfile").exists(), "Dockerfile missing"

        # Check requirements.txt exists and has content
        requirements = service_path / "requirements.txt"
        assert requirements.exists(), "requirements.txt missing"

        with open(requirements) as f:
            content = f.read()
            assert "fastapi" in content, "FastAPI dependency missing"

        # Check main.py exists
        assert (service_path / "main.py").exists(), "main.py missing"

        # Check optimizer.py exists
        assert (service_path / "optimizer.py").exists(), "optimizer.py missing"

        # Check README exists
        assert (service_path / "README.md").exists(), "README.md missing"

    def test_visualization_engine_config(self):
        """Test Visualization Engine service configuration."""
        service_path = BASE_PATH / "services" / "visualization-engine"

        # Check Dockerfile exists
        assert (service_path / "Dockerfile").exists(), "Dockerfile missing"

        # Check package.json exists and has content
        package_json = service_path / "package.json"
        assert package_json.exists(), "package.json missing"

        with open(package_json) as f:
            package_data = json.load(f)
            assert "express" in package_data.get("dependencies", {}), "Express dependency missing"
            assert "d3" in package_data.get("dependencies", {}), "D3.js dependency missing"
            assert "three" in package_data.get("dependencies", {}), "Three.js dependency missing"

        # Check server.js exists
        assert (service_path / "server.js").exists(), "server.js missing"

        # Check visualizer.tsx exists
        assert (service_path / "visualizer.tsx").exists(), "visualizer.tsx missing"

        # Check README exists
        assert (service_path / "README.md").exists(), "README.md missing"


class TestDockerComposeConfigurations:
    """Test Docker Compose configurations."""

    def test_docker_compose_phase7_exists(self):
        """Test that docker-compose-phase7.yaml exists."""
        compose_file = BASE_PATH / "docker-compose-phase7.yaml"
        assert compose_file.exists(), "docker-compose-phase7.yaml missing"

    def test_docker_compose_phase7_valid(self):
        """Test that docker-compose-phase7.yaml is valid YAML."""
        compose_file = BASE_PATH / "docker-compose-phase7.yaml"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Invalid YAML"
        assert "services" in config, "Services section missing"
        assert "networks" in config, "Networks section missing"
        assert "volumes" in config, "Volumes section missing"

    def test_phase7_services_included(self):
        """Test that all Phase 7 services are in docker-compose-phase7.yaml."""
        compose_file = BASE_PATH / "docker-compose-phase7.yaml"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        services = config.get("services", {})

        # Phase 7 services
        assert "ai-security-orchestrator" in services, "AI Security Orchestrator missing"
        assert "quantum-crypto-service" in services, "Quantum Crypto Service missing"
        assert "edge-security-gateway" in services, "Edge Security Gateway missing"
        assert "blockchain-audit-service" in services, "Blockchain Audit Service missing"
        assert "deception-platform" in services, "Deception Platform missing"

        # Newly completed services
        assert "alert-prioritization" in services, "Alert Prioritization missing"
        assert "ai-analyst" in services, "AI Analyst missing"
        assert "forensics" in services, "Forensics Investigation missing"
        assert "performance-optimizer" in services, "Performance Optimizer missing"
        assert "visualization-engine" in services, "Visualization Engine missing"

    def test_service_health_checks(self):
        """Test that all services have health checks configured."""
        compose_file = BASE_PATH / "docker-compose-phase7.yaml"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        services = config.get("services", {})

        # Services that should have health checks
        services_to_check = [
            "ai-security-orchestrator",
            "quantum-crypto-service",
            "edge-security-gateway",
            "blockchain-audit-service",
            "deception-platform",
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service_name in services_to_check:
            if service_name in services:
                service = services[service_name]
                assert "healthcheck" in service, f"{service_name} missing health check"

    def test_service_ports_configured(self):
        """Test that all services have ports configured."""
        compose_file = BASE_PATH / "docker-compose-phase7.yaml"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        services = config.get("services", {})

        # Expected port mappings
        expected_ports = {
            "ai-security-orchestrator": "8085",
            "quantum-crypto-service": "8086",
            "edge-security-gateway": "8087",
            "blockchain-audit-service": "8088",
            "deception-platform": "8089",
            "alert-prioritization": "8090",
            "ai-analyst": "8091",
            "forensics": "8092",
            "performance-optimizer": "8093",
            "visualization-engine": "8094"
        }

        for service_name, expected_port in expected_ports.items():
            if service_name in services:
                service = services[service_name]
                assert "ports" in service, f"{service_name} missing ports"
                ports = service["ports"]
                assert any(expected_port in str(port) for port in ports), \
                    f"{service_name} port {expected_port} not configured"


class TestModuleImports:
    """Test that Python modules can be imported."""

    def test_alert_prioritization_imports(self):
        """Test Alert Prioritization module imports."""
        import sys
        sys.path.insert(0, str(BASE_PATH / "services" / "alert-prioritization"))

        try:
            from prioritizer import IntelligentAlertPrioritizer, AlertPriority
            assert IntelligentAlertPrioritizer is not None
            assert AlertPriority is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Alert Prioritization modules: {e}")

    def test_ai_analyst_imports(self):
        """Test AI Analyst module imports."""
        import sys
        sys.path.insert(0, str(BASE_PATH / "services" / "ai-analyst"))

        try:
            from assistant import AISecurityAnalyst, ThreatSeverity
            assert AISecurityAnalyst is not None
            assert ThreatSeverity is not None
        except ImportError as e:
            pytest.fail(f"Failed to import AI Analyst modules: {e}")

    def test_forensics_imports(self):
        """Test Forensics module imports."""
        import sys
        sys.path.insert(0, str(BASE_PATH / "services" / "forensics"))

        try:
            from investigator import ForensicInvestigator, EvidenceType
            assert ForensicInvestigator is not None
            assert EvidenceType is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Forensics modules: {e}")

    def test_performance_optimizer_imports(self):
        """Test Performance Optimizer module imports."""
        import sys
        sys.path.insert(0, str(BASE_PATH / "services" / "performance-optimizer"))

        try:
            from optimizer import PerformanceOptimizer, StorageTier
            assert PerformanceOptimizer is not None
            assert StorageTier is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Performance Optimizer modules: {e}")


class TestDockerfileValidity:
    """Test that Dockerfiles are valid."""

    def test_dockerfiles_exist(self):
        """Test that all service Dockerfiles exist."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            dockerfile = BASE_PATH / "services" / service / "Dockerfile"
            assert dockerfile.exists(), f"Dockerfile missing for {service}"

    def test_dockerfiles_have_from(self):
        """Test that Dockerfiles have FROM statement."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            dockerfile = BASE_PATH / "services" / service / "Dockerfile"
            with open(dockerfile) as f:
                content = f.read()
                assert "FROM" in content, f"Dockerfile for {service} missing FROM statement"

    def test_dockerfiles_have_healthcheck(self):
        """Test that Dockerfiles have HEALTHCHECK statement."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            dockerfile = BASE_PATH / "services" / service / "Dockerfile"
            with open(dockerfile) as f:
                content = f.read()
                assert "HEALTHCHECK" in content, f"Dockerfile for {service} missing HEALTHCHECK"

    def test_dockerfiles_have_expose(self):
        """Test that Dockerfiles have EXPOSE statement."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            dockerfile = BASE_PATH / "services" / service / "Dockerfile"
            with open(dockerfile) as f:
                content = f.read()
                assert "EXPOSE" in content, f"Dockerfile for {service} missing EXPOSE"


class TestREADMEDocumentation:
    """Test that README files contain required documentation."""

    def test_readmes_have_features_section(self):
        """Test that READMEs have Features section."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            readme = BASE_PATH / "services" / service / "README.md"
            with open(readme) as f:
                content = f.read()
                assert "## Features" in content or "# Features" in content, \
                    f"README for {service} missing Features section"

    def test_readmes_have_api_endpoints(self):
        """Test that READMEs document API endpoints."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            readme = BASE_PATH / "services" / service / "README.md"
            with open(readme) as f:
                content = f.read()
                # Should have either "API Endpoints" or endpoint examples
                has_endpoints = ("## API Endpoints" in content or
                               "/api/v1/" in content or
                               "GET /" in content or
                               "POST /" in content)
                assert has_endpoints, f"README for {service} missing API endpoints documentation"

    def test_readmes_have_running_instructions(self):
        """Test that READMEs have running instructions."""
        services = [
            "alert-prioritization",
            "ai-analyst",
            "forensics",
            "performance-optimizer",
            "visualization-engine"
        ]

        for service in services:
            readme = BASE_PATH / "services" / service / "README.md"
            with open(readme) as f:
                content = f.read()
                assert "docker" in content.lower() or "Docker" in content, \
                    f"README for {service} missing Docker instructions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
