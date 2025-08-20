#!/bin/bash
# Week 1 Testing Commands

echo "🧪 Running Week 1 Tests"

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/ -v --cov=. --cov-report=html

# Test configuration
echo "Testing configuration..."
python -c "from config import init_config; config = init_config('.env.testing'); print('✅ Configuration OK')"

# Test database connection (requires running containers)
echo "Testing database connection..."
python -c "
from config import init_config
from database import init_database
try:
    config = init_config('.env.testing')
    db = init_database(config.database)
    health = db.health_check()
    print(f'✅ Database health: {health.get("healthy", False)}')
except Exception as e:
    print(f'⚠️ Database test failed: {e}')
"

# Test weather service
echo "Testing weather service..."
python -c "
from config import init_config
from services.weather_service import create_weather_service
try:
    config = init_config('.env.testing')
    weather = create_weather_service(config.weather, config.redis)
    health = weather.health_check()
    print(f'✅ Weather service health: {health.get("healthy", False)}')
except Exception as e:
    print(f'⚠️ Weather test failed: {e}')
"

echo "✅ All tests completed!"
