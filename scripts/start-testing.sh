#!/bin/bash
# PondMonitor Testing Mode Startup Script

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

echo "🧪 PondMonitor Testing Mode Setup"
echo "================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available (try both modern and legacy)
DOCKER_COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "✅ Found Docker Compose (plugin): $(docker compose version --short)"
elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "✅ Found Docker Compose (standalone): $(docker-compose version --short)"
else
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    echo "💡 Try: sudo apt install docker-compose-plugin"
    exit 1
fi

# Create .env file for testing if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file for testing..."
    cat > .env << EOF
# Database Configuration
POSTGRES_USER=pond_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=pond_data
POSTGRES_PORT=5432
PG_HOST=timescaledb

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Serial/LoRa Configuration - TESTING MODE
SERIAL_PORT=/dev/ttyUSB0
BAUD_RATE=9600
TESTING_MODE=true
SIMULATE_DATA=true

# Application Configuration
FLASK_PORT=5000
FLASK_ENV=development
FLASK_SECRET_KEY=testing_secret_key_change_in_production

# Weather API Configuration (Palkovice, Czech Republic)
WEATHER_LAT=49.6265900
WEATHER_LON=18.3016172
WEATHER_ALT=350
WEATHER_CACHE_DURATION=3600
USER_AGENT=PondMonitor/1.0 (pond@monitor.cz)

# Gateway Configuration
RETRY_DELAY=5
MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env file with testing configuration"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p db/backups
mkdir -p monitoring

echo "🏗️ Building Docker images..."
$DOCKER_COMPOSE_CMD build

echo "🚀 Starting services..."
$DOCKER_COMPOSE_CMD up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo "✅ Services are healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️ Services may still be starting up..."
    fi
    sleep 2
done

echo ""
echo "🎉 PondMonitor is now running in testing mode!"
echo ""
echo "📊 Features available:"
echo "  • Web Interface: http://localhost:5000"
echo "  • Simulated sensor data (updated every 30 seconds)"
echo "  • Weather data from met.no API"
echo "  • Real-time charts and diagnostics"
echo ""
echo "🔧 Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Check status: docker-compose ps"
echo "  • Stop services: docker-compose down"
echo "  • Show recent data: make show-data"
echo ""
echo "🧪 Testing Notes:"
echo "  • No USB device required"
echo "  • Data is simulated but realistic"
echo "  • Database persists between restarts"
echo ""

# Show current status
echo "📋 Current Service Status:"
$DOCKER_COMPOSE_CMD ps

echo ""
echo "🌐 Open http://localhost:5000 in your browser to see the dashboard!"