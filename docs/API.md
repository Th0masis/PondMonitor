# PondMonitor API Documentation

## 📊 REST API Reference

PondMonitor provides a comprehensive REST API for accessing sensor data, system status, and weather information. All endpoints return JSON responses with consistent error handling.

## 🔗 Base URL

```
http://localhost:5000
```

For production deployments, replace with your domain:
```
https://your-domain.com
```

## 📋 API Endpoints Overview

| Category | Endpoint | Method | Description |
|----------|----------|---------|-------------|
| **System** | `/health` | GET | System health check |
| **Status** | `/api/status` | GET | Current sensor status |
| **Data** | `/api/dashboard` | GET | Time-series data for charts |
| **Diagnostics** | `/api/lora` | GET | LoRa diagnostics data |
| **Weather** | `/api/weather/current` | GET | Current weather conditions |
| **Weather** | `/api/weather/meteogram` | GET | 48-hour detailed forecast |
| **Weather** | `/api/weather/daily` | GET | 7-day daily forecast |
| **Weather** | `/api/weather/stats` | GET | Weather statistics |
| **Export** | `/api/export/formats` | GET | Available export formats |
| **Export** | `/api/export/{format}` | GET | Export data in specified format |

## 🏥 System Health

### **GET /health**

Returns overall system health and service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "weather_api": "healthy"
  }
}
```

**Status Values:**
- `healthy` - All services operational
- `degraded` - Some services have issues
- `unhealthy` - Critical services down

**Example:**
```bash
curl -s http://localhost:5000/health | jq
```

## 📡 Sensor Status

### **GET /api/status**

Returns latest sensor readings and connectivity status.

**Response:**
```json
{
  "temperature_c": 23.4,
  "battery_v": 12.1,
  "solar_v": 16.8,
  "signal_dbm": -75,
  "connected": true,
  "on_solar": true,
  "last_heartbeat": "2025-01-08T10:29:45Z",
  "last_seen_minutes": 0,
  "device_id": "POND-001",
  "firmware_version": "1.0.0"
}
```

**Field Descriptions:**
- `temperature_c` - Ambient temperature in Celsius
- `battery_v` - Battery voltage
- `solar_v` - Solar panel voltage
- `signal_dbm` - LoRa signal strength in dBm
- `connected` - Connection status (true if seen within 2 minutes)
- `on_solar` - Solar charging status (true if solar_v > 1.0V)
- `last_heartbeat` - ISO timestamp of last data received
- `last_seen_minutes` - Minutes since last contact

**Example:**
```bash
curl -s http://localhost:5000/api/status | jq
```

## 📊 Dashboard Data

### **GET /api/dashboard**

Returns time-series data for dashboard charts.

**Parameters:**
- `start` (required) - ISO 8601 start timestamp
- `end` (required) - ISO 8601 end timestamp

**Example Request:**
```bash
curl -s "http://localhost:5000/api/dashboard?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z" | jq
```

**Response:**
```json
{
  "level": [
    [1704672000000, 145.2],
    [1704675600000, 144.8],
    [1704679200000, 144.5]
  ],
  "outflow": [
    [1704672000000, 2.1],
    [1704675600000, 2.0], 
    [1704679200000, 1.9]
  ],
  "data_points": 144
}
```

**Data Format:**
- Arrays contain `[timestamp_ms, value]` pairs
- `timestamp_ms` - Unix timestamp in milliseconds
- `level` - Water level in centimeters
- `outflow` - Outflow rate in liters per second

**Time Range Limits:**
- Maximum range: 30 days
- Maximum past: 1 year

## 🔧 LoRa Diagnostics

### **GET /api/lora**

Returns sensor telemetry data for diagnostics.

**Parameters:**
- `hours` (optional) - Number of hours to retrieve (1-168), default: 24

**Example Request:**
```bash
curl -s "http://localhost:5000/api/lora?hours=24" | jq
```

**Response:**
```json
{
  "temperature": [
    [1704672000000, 23.4],
    [1704675600000, 23.1]
  ],
  "battery_voltage": [
    [1704672000000, 12.1],
    [1704675600000, 12.0]
  ],
  "solar_voltage": [
    [1704672000000, 16.8],
    [1704675600000, 16.5]
  ],
  "signal_strength": [
    [1704672000000, -75],
    [1704675600000, -78]
  ],
  "data_points": 144,
  "time_range_hours": 24
}
```

## 🌦️ Weather APIs

### **GET /api/weather/current**

Returns current weather conditions.

**Response:**
```json
{
  "timestamp": "2025-01-08T10:30:00Z",
  "temperature": 15.2,
  "pressure": 1013.5,
  "humidity": 65,
  "wind": 12.5,
  "wind_direction": 225,
  "wind_gust": 18.0,
  "cloud_coverage": 25,
  "rain": 0.0,
  "symbol_code": "partlycloudy_day"
}
```

### **GET /api/weather/meteogram**

Returns 48-hour detailed forecast for meteogram visualization.

**Response:**
```json
[
  {
    "time": 1704672000000,
    "temperature": 15.2,
    "rain": 0.0,
    "wind": 12.5,
    "wind_direction": 225,
    "wind_gust": 18.0,
    "pressure": 1013.5,
    "humidity": 65,
    "cloud": 25,
    "symbol_code": "partlycloudy_day"
  }
]
```

### **GET /api/weather/daily**

Returns 7-day daily forecast summary.

**Response:**
```json
[
  {
    "date": "2025-01-08",
    "temp": 18.5,
    "temp_min": 12.0,
    "temp_avg": 15.2,
    "wind_avg": 10.5,
    "wind_gust": 25.0,
    "rain": 2.5,
    "humidity_avg": 70,
    "pressure_avg": 1015.0,
    "icon": "rain"
  }
]
```

### **GET /api/weather/stats**

Returns weather statistics for the last 24 hours.

**Response:**
```json
{
  "temperature": {
    "current": 15.2,
    "min": 8.5,
    "max": 22.1,
    "avg": 15.8
  },
  "pressure": {
    "current": 1013.5,
    "min": 1008.2,
    "max": 1018.7,
    "avg": 1013.1
  },
  "wind": {
    "current": 12.5,
    "min": 2.1,
    "max": 28.3,
    "avg": 11.2
  },
  "humidity": {
    "current": 65,
    "min": 45,
    "max": 85,
    "avg": 67
  }
}
```

## 📤 Data Export APIs

### **GET /api/export/formats**

Returns available export formats.

**Response:**
```json
{
  "formats": [
    {
      "name": "csv",
      "description": "Comma-separated values",
      "mime_type": "text/csv",
      "extension": ".csv"
    },
    {
      "name": "json", 
      "description": "JavaScript Object Notation",
      "mime_type": "application/json",
      "extension": ".json"
    },
    {
      "name": "excel",
      "description": "Microsoft Excel format",
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "extension": ".xlsx"
    }
  ]
}
```

### **GET /api/export/estimate**

Estimates export size and processing time.

**Parameters:**
- `start` (required) - ISO 8601 start timestamp
- `end` (required) - ISO 8601 end timestamp  
- `format` (optional) - Export format (csv, json, excel)

**Response:**
```json
{
  "estimated_records": 1440,
  "estimated_size_bytes": 145920,
  "estimated_size_mb": 0.14,
  "estimated_processing_time_seconds": 2.3,
  "recommended": true
}
```

### **GET /api/export/{format}**

Export data in the specified format.

**Supported Formats:** `csv`, `json`, `excel`

**Parameters:**
- `start` (required) - ISO 8601 start timestamp
- `end` (required) - ISO 8601 end timestamp
- `include_pond` (optional) - Include pond data (default: true)
- `include_station` (optional) - Include station data (default: true)
- `station_id` (optional) - Filter by station ID
- `limit` (optional) - Maximum records to export

**Example:**
```bash
# Export as CSV
curl -o data.csv "http://localhost:5000/api/export/csv?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z"

# Export as JSON with limit
curl -o data.json "http://localhost:5000/api/export/json?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z&limit=1000"

# Export only pond data as Excel
curl -o pond_data.xlsx "http://localhost:5000/api/export/excel?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z&include_station=false"
```

## 🔧 Error Responses

All API endpoints return consistent error responses:

**Error Response Format:**
```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE", 
  "timestamp": "2025-01-08T10:30:00Z",
  "details": {
    "field": "Additional error context"
  },
  "trace_id": "abc123def456"
}
```

**Common HTTP Status Codes:**
- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters or request format
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

**Example Error Responses:**

**400 Bad Request:**
```json
{
  "error": "Missing required parameter",
  "code": "ValidationError",
  "timestamp": "2025-01-08T10:30:00Z",
  "details": {
    "missing_fields": ["start", "end"]
  }
}
```

**503 Service Unavailable:**
```json
{
  "error": "Weather service unavailable",
  "code": "ServiceError", 
  "timestamp": "2025-01-08T10:30:00Z",
  "details": {
    "service": "weather_api",
    "retry_after": 60
  }
}
```

## 📝 Request Examples

### **Using curl**

```bash
# Get system health
curl -s http://localhost:5000/health

# Get current status with pretty printing
curl -s http://localhost:5000/api/status | python3 -m json.tool

# Get dashboard data for last 24 hours
START=$(date -d '24 hours ago' -Iseconds)
END=$(date -Iseconds)
curl -s "http://localhost:5000/api/dashboard?start=${START}&end=${END}"

# Export data as CSV
curl -o export.csv "http://localhost:5000/api/export/csv?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z"
```

### **Using Python**

```python
import requests
import json
from datetime import datetime, timedelta

# Base URL
BASE_URL = "http://localhost:5000"

# Get system health
response = requests.get(f"{BASE_URL}/health")
health = response.json()
print(f"System status: {health['status']}")

# Get current sensor status
response = requests.get(f"{BASE_URL}/api/status")
status = response.json()
print(f"Temperature: {status['temperature_c']}°C")
print(f"Battery: {status['battery_v']}V")

# Get dashboard data for last hour
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

params = {
    'start': start_time.isoformat() + 'Z',
    'end': end_time.isoformat() + 'Z'
}

response = requests.get(f"{BASE_URL}/api/dashboard", params=params)
data = response.json()
print(f"Data points: {data['data_points']}")
```

### **Using JavaScript**

```javascript
// Get system health
fetch('/health')
  .then(response => response.json())
  .then(data => {
    console.log('System status:', data.status);
  });

// Get current sensor status
fetch('/api/status')
  .then(response => response.json())
  .then(data => {
    document.getElementById('temperature').textContent = `${data.temperature_c}°C`;
    document.getElementById('battery').textContent = `${data.battery_v}V`;
  });

// Get dashboard data
const endTime = new Date();
const startTime = new Date(endTime - 24 * 60 * 60 * 1000); // 24 hours ago

const params = new URLSearchParams({
  start: startTime.toISOString(),
  end: endTime.toISOString()
});

fetch(`/api/dashboard?${params}`)
  .then(response => response.json())
  .then(data => {
    console.log('Level data points:', data.level.length);
    console.log('Outflow data points:', data.outflow.length);
  });
```

## 🔒 Authentication & Rate Limiting

### **Authentication**
Currently, the API does not require authentication for read operations. For production deployments, consider implementing:
- API key authentication
- JWT tokens
- OAuth 2.0
- IP-based access control

### **Rate Limiting**
Default rate limits (configurable):
- 100 requests per minute per IP
- 1000 requests per hour per IP
- Export endpoints: 10 requests per hour per IP

## 📚 Integration Examples

### **Grafana Integration**

```json
{
  "dashboard": {
    "title": "PondMonitor Data",
    "panels": [
      {
        "title": "Water Level",
        "type": "graph",
        "targets": [
          {
            "expr": "http_request",
            "url": "http://pondmonitor:5000/api/dashboard"
          }
        ]
      }
    ]
  }
}
```

### **Home Assistant Integration**

```yaml
# configuration.yaml
sensor:
  - platform: rest
    name: pond_temperature
    resource: http://pondmonitor:5000/api/status
    value_template: '{{ value_json.temperature_c }}'
    unit_of_measurement: '°C'
    
  - platform: rest
    name: pond_water_level
    resource: http://pondmonitor:5000/api/status  
    value_template: '{{ value_json.level_cm }}'
    unit_of_measurement: 'cm'
```

## 🔗 Related Documentation

- **System Overview:** [OVERVIEW.md](OVERVIEW.md)
- **Web Interface Guide:** [USER_GUIDE.md](USER_GUIDE.md) 
- **Development Setup:** [DEVELOPMENT.md](DEVELOPMENT.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)