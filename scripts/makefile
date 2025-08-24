.PHONY: help build up down logs test lint format clean test-mode prod-mode

# Detect Docker Compose command
DOCKER_COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Using: $(DOCKER_COMPOSE)'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $1, $2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d

down: ## Stop all services
	$(DOCKER_COMPOSE) down

logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

# Testing mode commands
test-mode: ## Start in testing mode (no USB device required)
	@echo "🧪 Starting in TESTING MODE (no physical hardware required)"
	@cp config/.env.testing .env
	$(DOCKER_COMPOSE) up -d
	@echo "✅ PondMonitor is running in testing mode!"
	@echo "📊 Simulated data is being generated every 30 seconds"
	@echo "🌐 Web interface: http://localhost:5000"

test-logs: ## Show logs in testing mode
	$(DOCKER_COMPOSE) logs -f lora_gateway flask_ui

test-status: ## Check status of testing services
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "🔍 Checking service health..."
	@curl -s http://localhost:5000/health | python3 -m json.tool || echo "❌ Flask UI not responding"

# Production mode commands  
prod-mode: ## Switch to production mode (USB device required)
	@echo "🏭 Switching to PRODUCTION MODE"
	@cp .env .env.backup 2>/dev/null || true
	@echo "TESTING_MODE=false" > .env.prod
	@echo "SIMULATE_DATA=false" >> .env.prod
	@cat config/.env.testing >> .env.prod
	@sed -i 's/TESTING_MODE=true/TESTING_MODE=false/' .env.prod
	@sed -i 's/SIMULATE_DATA=true/SIMULATE_DATA=false/' .env.prod
	@cp .env.prod .env
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ PondMonitor is running in production mode!"
	@echo "⚠️  Make sure your USB device is connected to ${SERIAL_PORT:-/dev/ttyUSB0}"

# Development and testing
test: ## Run tests
	python -m pytest tests/ -v --cov=.

lint: ## Run linting
	flake8 src/
	mypy src/

format: ## Format code
	black src/

# Cleanup
clean: ## Clean up Docker resources
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

reset-db: ## Reset database (WARNING: deletes all data)
	@echo "⚠️  WARNING: This will delete ALL data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $REPLY =~ ^[Yy]$ ]]; then \
		$(DOCKER_COMPOSE) down -v; \
		docker volume rm pondmonitor_timescale_data pondmonitor_redis_data 2>/dev/null || true; \
		echo "🗑️  Database reset complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

# Monitoring
monitoring: ## Start with monitoring stack
	$(DOCKER_COMPOSE) --profile monitoring up -d

# Quick access to services
shell-db: ## Connect to database shell
	$(DOCKER_COMPOSE) exec timescaledb psql -U pond_user -d pond_data

shell-redis: ## Connect to Redis shell
	$(DOCKER_COMPOSE) exec redis redis-cli

# Backup and restore
backup: ## Backup database
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec timescaledb pg_dump -U pond_user pond_data > backups/pond_data_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up to backups/"

# Health checks
health: ## Check health of all services
	@echo "🔍 Checking service health..."
	@curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "❌ Flask UI not responding"
	@$(DOCKER_COMPOSE) ps

# Data inspection
show-data: ## Show recent data from database
	@echo "📊 Recent sensor data:"
	$(DOCKER_COMPOSE) exec timescaledb psql -U pond_user -d pond_data -c "\
		SELECT timestamp, temperature_c, battery_v, solar_v, signal_dbm \
		FROM station_metrics \
		ORDER BY timestamp DESC \
		LIMIT 10;"
	@echo ""
	@echo "🌊 Recent pond data:"
	$(DOCKER_COMPOSE) exec timescaledb psql -U pond_user -d pond_data -c "\
		SELECT timestamp, level_cm, outflow_lps \
		FROM pond_metrics \
		ORDER BY timestamp DESC \
		LIMIT 10;"

show-redis: ## Show current Redis data
	@echo "📋 Current status in Redis:"
	$(DOCKER_COMPOSE) exec redis redis-cli get latest_status | python3 -m json.tool 2>/dev/null || echo "❌ No data in Redis"

# Development shortcuts
dev: test-mode ## Alias for test-mode
	@echo "🚀 Development environment ready!"

quick-start: build test-mode ## Build and start in testing mode
	@echo "⚡ Quick start complete!"

# Troubleshooting
debug: ## Show debugging information
	@echo "🐛 Debug Information:"
	@echo "===================="
	@echo "Docker Compose Command: $(DOCKER_COMPOSE)"
	@echo ""
	@echo "Docker Compose Status:"
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "Docker Images:"
	docker images | grep -E "(pondmonitor|timescale|redis)"
	@echo ""
	@echo "Docker Volumes:"
	docker volume ls | grep pondmonitor
	@echo ""
	@echo "Environment Variables:"
	@grep -E "^[A-Z]" .env 2>/dev/null || echo "No .env file found"
	@echo ""
	@echo "Recent Gateway Logs:"
	$(DOCKER_COMPOSE) logs --tail=20 lora_gateway
	@echo ""
	@echo "Recent Flask Logs:"
	$(DOCKER_COMPOSE) logs --tail=20 flask_ui