# Enterprise SIEM Makefile

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ====================================
# Development
# ====================================

.PHONY: dev-setup
dev-setup: ## Set up development environment
	@echo "Setting up development environment..."
	cp .env.example .env
	docker-compose pull
	@echo "Development environment ready!"
	@echo "Run 'make up' to start services"

.PHONY: up
up: ## Start all services
	docker-compose up -d

.PHONY: down
down: ## Stop all services
	docker-compose down

.PHONY: restart
restart: down up ## Restart all services

.PHONY: logs
logs: ## Show logs for all services
	docker-compose logs -f

.PHONY: ps
ps: ## Show status of all services
	docker-compose ps

.PHONY: clean
clean: ## Stop services and remove volumes (WARNING: deletes data)
	docker-compose down -v
	rm -rf data/ volumes/

# ====================================
# Building
# ====================================

.PHONY: build
build: ## Build all services
	docker-compose build

.PHONY: build-collector
build-collector: ## Build collector service
	docker-compose build collector

.PHONY: build-api
build-api: ## Build API gateway
	docker-compose build api-gateway

.PHONY: build-ui
build-ui: ## Build web UI
	docker-compose build web-ui

# ====================================
# Testing
# ====================================

.PHONY: test
test: test-go test-python test-frontend ## Run all tests

.PHONY: test-go
test-go: ## Run Go tests
	@echo "Running Go tests..."
	@find services -name go.mod -execdir go test -v ./... \;

.PHONY: test-python
test-python: ## Run Python tests
	@echo "Running Python tests..."
	@find services -name pytest.ini -execdir pytest -v \;

.PHONY: test-frontend
test-frontend: ## Run frontend tests
	@echo "Running frontend tests..."
	cd web-ui && npm test

.PHONY: test-coverage
test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	@find services -name go.mod -execdir go test -coverprofile=coverage.out ./... \;
	@find services -name pytest.ini -execdir pytest --cov --cov-report=html \;

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "Running integration tests..."
	cd tests/integration && go test -v ./...

# ====================================
# Code Quality
# ====================================

.PHONY: lint
lint: lint-go lint-python lint-frontend ## Run all linters

.PHONY: lint-go
lint-go: ## Run Go linters
	@echo "Running Go linters..."
	@find services -name go.mod -execdir golangci-lint run \;

.PHONY: lint-python
lint-python: ## Run Python linters
	@echo "Running Python linters..."
	@find services -name "*.py" -exec pylint {} \;

.PHONY: lint-frontend
lint-frontend: ## Run frontend linters
	@echo "Running frontend linters..."
	cd web-ui && npm run lint

.PHONY: format
format: format-go format-python format-frontend ## Format all code

.PHONY: format-go
format-go: ## Format Go code
	@echo "Formatting Go code..."
	@find services -name "*.go" -exec gofmt -w {} \;

.PHONY: format-python
format-python: ## Format Python code
	@echo "Formatting Python code..."
	@find services -name "*.py" -exec black {} \;

.PHONY: format-frontend
format-frontend: ## Format frontend code
	@echo "Formatting frontend code..."
	cd web-ui && npm run format

# ====================================
# Database
# ====================================

.PHONY: db-migrate
db-migrate: ## Run database migrations
	docker-compose exec api-gateway ./bin/migrate up

.PHONY: db-rollback
db-rollback: ## Rollback last database migration
	docker-compose exec api-gateway ./bin/migrate down

.PHONY: db-seed
db-seed: ## Seed database with sample data
	docker-compose exec api-gateway ./scripts/seed-database.sh

.PHONY: db-reset
db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose exec postgresql psql -U siem_user -d siem -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) db-migrate
	$(MAKE) db-seed

# ====================================
# Development Tools
# ====================================

.PHONY: shell-api
shell-api: ## Open shell in API gateway container
	docker-compose exec api-gateway sh

.PHONY: shell-db
shell-db: ## Open PostgreSQL shell
	docker-compose exec postgresql psql -U siem_user -d siem

.PHONY: kafka-topics
kafka-topics: ## List Kafka topics
	docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

.PHONY: kafka-consume
kafka-consume: ## Consume from Kafka topic (usage: make kafka-consume TOPIC=raw-events)
	docker-compose exec kafka kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic $(TOPIC) \
		--from-beginning

.PHONY: es-indices
es-indices: ## List Elasticsearch indices
	curl -s http://localhost:9200/_cat/indices?v

.PHONY: es-health
es-health: ## Check Elasticsearch health
	curl -s http://localhost:9200/_cluster/health?pretty

# ====================================
# Sample Data
# ====================================

.PHONY: generate-events
generate-events: ## Generate sample events
	docker-compose exec api-gateway ./scripts/generate-sample-events.sh

.PHONY: load-rules
load-rules: ## Load default detection rules
	docker-compose exec api-gateway ./scripts/load-default-rules.sh

# ====================================
# Monitoring
# ====================================

.PHONY: metrics
metrics: ## Open Prometheus UI
	@echo "Opening Prometheus at http://localhost:9090"
	open http://localhost:9090 || xdg-open http://localhost:9090

.PHONY: dashboards
dashboards: ## Open Grafana dashboards
	@echo "Opening Grafana at http://localhost:3001"
	@echo "Username: admin, Password: admin_change_me"
	open http://localhost:3001 || xdg-open http://localhost:3001

.PHONY: traces
traces: ## Open Jaeger tracing UI
	@echo "Opening Jaeger at http://localhost:16686"
	open http://localhost:16686 || xdg-open http://localhost:16686

# ====================================
# Documentation
# ====================================

.PHONY: docs
docs: ## Generate documentation
	@echo "Generating documentation..."
	cd docs && make html

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	cd docs && make serve

# ====================================
# Deployment
# ====================================

.PHONY: k8s-deploy
k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f infrastructure/kubernetes/

.PHONY: k8s-delete
k8s-delete: ## Delete from Kubernetes
	kubectl delete -f infrastructure/kubernetes/

.PHONY: helm-install
helm-install: ## Install with Helm
	helm install siem ./charts/enterprise-siem -f values-production.yaml

.PHONY: helm-upgrade
helm-upgrade: ## Upgrade Helm deployment
	helm upgrade siem ./charts/enterprise-siem -f values-production.yaml

# ====================================
# CI/CD
# ====================================

.PHONY: ci
ci: lint test ## Run CI checks locally

.PHONY: security-scan
security-scan: ## Run security scans
	@echo "Running security scans..."
	docker scan siem-api-gateway
	docker scan siem-collector

# ====================================
# Utilities
# ====================================

.PHONY: version
version: ## Show version information
	@echo "SIEM Platform Version: 0.1.0"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@echo "Kubernetes: $$(kubectl version --client --short 2>/dev/null || echo 'Not installed')"

.PHONY: health
health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps
	@echo "\nElasticsearch:"
	@curl -s http://localhost:9200/_cluster/health | grep status || echo "Not available"
	@echo "\nKafka:"
	@docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null | head -1 || echo "Not available"
	@echo "\nPostgreSQL:"
	@docker-compose exec postgresql pg_isready || echo "Not available"
	@echo "\nRedis:"
	@docker-compose exec redis redis-cli ping || echo "Not available"
