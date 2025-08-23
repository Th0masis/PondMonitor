#!/bin/bash
# Health check script for deployment validation

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5000}"
TIMEOUT="${TIMEOUT:-30}"
RETRY_INTERVAL="${RETRY_INTERVAL:-2}"
MAX_RETRIES="${MAX_RETRIES:-15}"

echo "🏥 PondMonitor Health Check"
echo "=========================="
echo "Target: $BASE_URL"
echo "Timeout: ${TIMEOUT}s per request"
echo "Max retries: $MAX_RETRIES"
echo ""

# Function to check HTTP endpoint
check_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    echo -n "🔍 Checking $description... "
    
    if curl -s -f --max-time $TIMEOUT "$url" > /dev/null 2>&1; then
        echo "✅ PASSED"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Function to check JSON endpoint with content validation
check_json_endpoint() {
    local url="$1"
    local jq_filter="$2"
    local description="$3"
    
    echo -n "🔍 Checking $description... "
    
    local response
    response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | jq -e "$jq_filter" > /dev/null 2>&1; then
        echo "✅ PASSED"
        return 0
    else
        echo "❌ FAILED"
        echo "   Response: ${response:0:100}..."
        return 1
    fi
}

# Wait for service to be available
echo "⏳ Waiting for service to be available..."
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    if curl -s --max-time 5 "$BASE_URL/health" > /dev/null 2>&1; then
        echo "✅ Service is responding"
        break
    fi
    
    retry_count=$((retry_count + 1))
    if [ $retry_count -eq $MAX_RETRIES ]; then
        echo "❌ Service not available after $MAX_RETRIES attempts"
        echo "🔍 Debug information:"
        curl -v "$BASE_URL/health" || true
        exit 1
    fi
    
    echo "   Attempt $retry_count/$MAX_RETRIES failed, retrying in ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

echo ""
echo "🧪 Running Health Checks"
echo "========================"

# Exit code tracking
FAILED_CHECKS=0

# Basic connectivity
if ! check_endpoint "$BASE_URL/" "200" "Main page"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Health endpoint
if ! check_json_endpoint "$BASE_URL/health" ".healthy == true" "Health endpoint"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# API endpoints
if ! check_json_endpoint "$BASE_URL/api/data" "type == \"array\"" "Data API"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

if ! check_json_endpoint "$BASE_URL/api/weather" ".temperature" "Weather API"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

if ! check_json_endpoint "$BASE_URL/api/diagnostics" ".services" "Diagnostics API"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Static resources
if ! check_endpoint "$BASE_URL/static/style.css" "200" "CSS assets"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

if ! check_endpoint "$BASE_URL/static/js/charts.js" "200" "JavaScript assets"; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Database connectivity (through API)
echo -n "🔍 Checking database connectivity... "
db_response=$(curl -s --max-time $TIMEOUT "$BASE_URL/api/diagnostics" 2>/dev/null)
if echo "$db_response" | jq -e '.services.database.healthy == true' > /dev/null 2>&1; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
    echo "   Database status: $(echo "$db_response" | jq -r '.services.database.status' 2>/dev/null || echo 'unknown')"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Redis connectivity (through API)
echo -n "🔍 Checking Redis connectivity... "
if echo "$db_response" | jq -e '.services.redis.healthy == true' > /dev/null 2>&1; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
    echo "   Redis status: $(echo "$db_response" | jq -r '.services.redis.status' 2>/dev/null || echo 'unknown')"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Weather service
echo -n "🔍 Checking weather service... "
if echo "$db_response" | jq -e '.services.weather.healthy == true' > /dev/null 2>&1; then
    echo "✅ PASSED"
else
    echo "⚠️  WARNING"
    echo "   Weather status: $(echo "$db_response" | jq -r '.services.weather.status' 2>/dev/null || echo 'unknown')"
    # Don't fail on weather service issues
fi

# Performance check
echo -n "🔍 Checking response time... "
start_time=$(date +%s.%N)
curl -s --max-time $TIMEOUT "$BASE_URL/health" > /dev/null
end_time=$(date +%s.%N)
response_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "unknown")

if [ "$response_time" != "unknown" ]; then
    # Convert to milliseconds
    response_ms=$(echo "$response_time * 1000" | bc)
    echo "✅ PASSED (${response_ms%.*}ms)"
    
    if (( $(echo "$response_time > 2.0" | bc -l 2>/dev/null) )); then
        echo "   ⚠️  Slow response time: ${response_ms%.*}ms"
    fi
else
    echo "⚠️  Could not measure response time"
fi

# Load test (basic)
if [ "$LOAD_TEST" = "true" ]; then
    echo ""
    echo "⚡ Running basic load test..."
    echo -n "🔍 Testing concurrent requests... "
    
    # Run 10 concurrent requests
    for i in {1..10}; do
        curl -s --max-time 5 "$BASE_URL/health" > /dev/null &
    done
    wait
    
    if curl -s --max-time 5 "$BASE_URL/health" > /dev/null; then
        echo "✅ PASSED"
    else
        echo "❌ FAILED - Service degraded under load"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi

# Summary
echo ""
echo "📊 Health Check Summary"
echo "======================"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo "✅ All health checks passed!"
    echo "🚀 Service is healthy and ready"
    
    # Additional info
    echo ""
    echo "📋 Service Information:"
    service_info=$(curl -s "$BASE_URL/api/diagnostics" 2>/dev/null)
    if [ -n "$service_info" ]; then
        echo "   Version: $(echo "$service_info" | jq -r '.version // "unknown"')"
        echo "   Uptime: $(echo "$service_info" | jq -r '.uptime // "unknown"')"
        echo "   Memory: $(echo "$service_info" | jq -r '.memory // "unknown"')"
    fi
    
    exit 0
else
    echo "❌ $FAILED_CHECKS health check(s) failed"
    echo "🔧 Service may not be fully operational"
    
    # Debug information
    echo ""
    echo "🔍 Debug Information:"
    echo "   Service logs: docker-compose logs flask_ui"
    echo "   Database logs: docker-compose logs timescaledb"
    echo "   Full diagnostics: curl $BASE_URL/api/diagnostics"
    
    exit 1
fi