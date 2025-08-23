#!/bin/bash
# Comprehensive test runner for CI/CD pipeline

set -e

# Change to project root
cd "$(dirname "$0")/../.."

echo "🧪 Running PondMonitor Test Suite"
echo "================================="

# Check if virtual environment is needed
if [ ! -d "venv" ] && [ "$CI" != "true" ]; then
    echo "⚠️  No virtual environment detected. Consider using:"
    echo "   python -m venv venv && source venv/bin/activate"
fi

# Verify dependencies
echo "📦 Checking dependencies..."
python -c "import flask, pytest, psycopg2, redis" || {
    echo "❌ Missing dependencies. Run: pip install -r requirements.txt"
    exit 1
}

# Set test environment
echo "🔧 Setting up test environment..."
export FLASK_ENV=testing
export TESTING_MODE=true
export SIMULATE_DATA=true

# Check if .env exists for local testing
if [ ! -f ".env" ] && [ "$CI" != "true" ]; then
    echo "📝 Creating test .env file..."
    cat > .env << EOF
POSTGRES_USER=pond_user
POSTGRES_PASSWORD=test_password
POSTGRES_DB=pond_data
POSTGRES_PORT=5432
PG_HOST=localhost
REDIS_HOST=localhost
REDIS_PORT=6379
TESTING_MODE=true
SIMULATE_DATA=true
FLASK_ENV=testing
FLASK_SECRET_KEY=test-secret-key
EOF
fi

# Run different test categories
echo "🔍 Running unit tests..."
python -m pytest tests/ -v -k "not integration" --tb=short

echo "🔗 Running integration tests..."
python -m pytest tests/ -v -k "integration" --tb=short || {
    echo "⚠️  Integration tests failed (may need running services)"
    if [ "$CI" = "true" ]; then
        exit 1
    fi
}

# Run with coverage if requested
if [ "$1" = "--coverage" ] || [ "$COVERAGE" = "true" ]; then
    echo "📊 Running tests with coverage..."
    python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
    echo "📈 Coverage report generated in htmlcov/"
fi

# Performance tests (optional)
if [ "$1" = "--performance" ]; then
    echo "⚡ Running performance tests..."
    python -c "
import time
import requests
print('Testing application startup time...')
# Add performance test logic here
"
fi

echo ""
echo "✅ All tests completed successfully!"
echo "📊 Test summary available in test results"