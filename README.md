<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

<img src="PondMonitor.png" width="30%" style="position: relative; top: 0; right: 0;" alt="Project Logo"/>

# PONDMONITOR

**Advanced IoT Monitoring System for Environmental Data Collection**

<!-- BADGES -->
<img src="https://img.shields.io/github/last-commit/Th0masis/PondMonitor?style=flat&logo=git&logoColor=white&color=0080ff" alt="last-commit">
<img src="https://img.shields.io/github/languages/top/Th0masis/PondMonitor?style=flat&color=0080ff" alt="repo-top-language">
<img src="https://img.shields.io/github/languages/count/Th0masis/PondMonitor?style=flat&color=0080ff" alt="repo-language-count">
<br>

<em>Built with the tools and technologies:</em>

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success)](https://github.com/Th0masis/PondMonitor)
<br>

</div>
<br>

---

## 📋 Table of Contents

- [🌊 Overview](#-overview)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [🏭 Production Setup (Without Make)](#-production-setup-without-make)
- [📖 User Manual](#-user-manual)
- [🔧 Development](#-development)
- [📊 API Documentation](#-api-documentation)
- [🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

---

## 🌊 Overview

PondMonitor is a comprehensive IoT monitoring platform designed for environmental data collection and analysis. It combines real-time sensor data acquisition via LoRa communication with advanced web-based visualization, weather integration, and historical data analysis.

### **What Does It Do?**

- **🔬 Monitors Environmental Parameters:** Water levels, temperature, flow rates, and system health
- **📡 LoRa Communication:** Long-range, low-power wireless data transmission from remote sensors
- **🌦️ Weather Integration:** Live meteorological data and forecasts from met.no API
- **📊 Real-time Visualization:** Interactive charts and dashboards with historical analysis
- **🏥 System Health Monitoring:** Hardware diagnostics, battery status, and connectivity monitoring
- **💾 Time-series Database:** Efficient storage and querying using TimescaleDB

### **Use Cases**

- Environmental research and monitoring
- Water management systems
- Agricultural irrigation monitoring
- Remote location surveillance
- IoT prototyping and development

---

## ✨ Features

### **🎯 Core Functionality**

| Feature | Description | Status |
|---------|-------------|---------|
| **Real-time Dashboard** | Live water level, outflow, and environmental data | ✅ Active |
| **Weather Integration** | Current conditions, 48h meteogram, 7-day forecast | ✅ Active |
| **System Diagnostics** | Hardware health, battery monitoring, signal strength | ✅ Active |
| **Data Export** | CSV/JSON export with customizable time ranges | ✅ Active |
| **Mobile Responsive** | Optimized for desktop, tablet, and mobile devices | ✅ Active |
| **Dark/Light Theme** | Automatic and manual theme switching | ✅ Active |

### **🛠️ Technical Features**

- **Containerized Architecture:** Docker Compose orchestration
- **Time-series Database:** TimescaleDB for efficient data storage
- **Caching Layer:** Redis for real-time status and performance
- **RESTful API:** JSON API for data access and integration
- **Testing Mode:** Simulated data for development without hardware
- **Health Monitoring:** Built-in service health checks and monitoring

### **📡 Hardware Support**

- **LoRa Communication:** Long-range wireless sensor networks
- **Serial Interface:** USB/UART communication with sensor stations
- **Multi-sensor Support:** Temperature, battery, solar, water level sensors
- **Fault Tolerance:** Automatic reconnection and error handling

---

## 🏗️ Architecture

### **System Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    PondMonitor System                        │
├─────────────────────────────────────────────────────────────┤
│  🌐 Web Interface (Flask + Tailwind CSS + Highcharts)      │
├─────────────────────────────────────────────────────────────┤
│  📊 API Layer (Flask REST API)                             │
├─────────────────────────────────────────────────────────────┤
│  ⚡ Caching (Redis)          │  📡 Data Gateway (Python)    │
├─────────────────────────────────────────────────────────────┤
│  🗄️ Time-series Database (TimescaleDB/PostgreSQL)          │
├─────────────────────────────────────────────────────────────┤
│  🔌 Hardware Interface (LoRa/Serial)                       │
└─────────────────────────────────────────────────────────────┘
```

### **Component Details**

#### **🌐 Web Interface (`UI/`)**
- **Flask Application:** Python web framework with Jinja2 templates
- **Frontend:** Modern responsive design with Tailwind CSS
- **Charts:** Interactive visualizations using Highcharts
- **Pages:** Dashboard, Weather, Diagnostics with real-time updates

#### **📡 Data Gateway (`LoraGateway.py`)**
- **Serial Communication:** Handles USB/UART connections to LoRa modules
- **Data Processing:** Validates, processes, and routes sensor data
- **Dual Storage:** Real-time Redis updates + historical PostgreSQL storage
- **Testing Mode:** Simulated data generation for development

#### **🗄️ Database Layer**
- **TimescaleDB:** Time-series optimized PostgreSQL extension
- **Hypertables:** Automatic partitioning for efficient time-series queries
- **Schema:** Separate tables for pond metrics and station telemetry

#### **⚡ Caching & Performance**
- **Redis:** In-memory cache for latest sensor status
- **Health Checks:** Automatic service monitoring and status reporting
- **Error Handling:** Graceful degradation and automatic reconnection

---

## 🚀 Quick Start

### **Prerequisites**

- **Docker:** Version 20.10+ with Docker Compose
  - **Modern installations:** Use `docker compose` (plugin)
  - **Legacy installations:** Use `docker-compose` (standalone)
  - **System automatically detects** which version you have
- **Operating System:** Linux/macOS/Windows with WSL2
- **Hardware:** 4GB RAM minimum, 8GB recommended
- **Network:** Internet connection for weather data
- **Optional:** `make` utility for convenient commands

> **🏭 Production Deployment:** For production setup with real hardware and without `make`, see the [Production Setup Guide](#-production-setup-without-make) below.

> **🔧 Docker Compose Installation:**
> ```bash
> # Ubuntu/Debian (modern plugin)
> sudo apt update && sudo apt install docker-compose-plugin
> 
> # Ubuntu/Debian (legacy standalone)  
> sudo apt update && sudo apt install docker-compose
> 
> # Check your installation
> docker compose version || docker-compose version
> ```

### **Option 1: Automated Setup (Recommended)**

```bash
# Clone the repository
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Make startup script executable
chmod +x start-testing.sh

# Start in testing mode (no hardware required)
./start-testing.sh
```

### **Option 2: Manual Setup**

```bash
# Clone and navigate
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Copy testing configuration
cp .env.testing .env

# Build and start services (will auto-detect docker compose vs docker-compose)
docker compose build || docker-compose build
docker compose up -d || docker-compose up -d

# Check status
docker compose ps || docker-compose ps
```

### **Option 3: Using Make (if installed)**

```bash
# Quick start with testing mode
make quick-start

# Or step by step
make build
make test-mode

# View logs
make logs

# Check health
make health
```

> **💡 Docker Compose Compatibility:** The system automatically detects whether you have `docker compose` (modern) or `docker-compose` (legacy) and uses the appropriate command.

### **🌐 Access the Application**

Once started, access the web interface at:
- **Main Dashboard:** http://localhost:5000
- **Weather Page:** http://localhost:5000/weather  
- **Diagnostics:** http://localhost:5000/diagnostics
- **API Health:** http://localhost:5000/health

---

## 🏭 Production Setup (Without Make)

For users who don't have `make` installed or prefer manual setup, this section provides comprehensive step-by-step instructions for production deployment with real hardware.

## 📋 Prerequisites

- **Docker:** Version 20.10+ with Docker Compose
- **Operating System:** Linux/macOS/Windows with WSL2
- **Hardware Requirements:** 
  - 4GB RAM minimum, 8GB recommended
  - USB LoRa device connected (typically `/dev/ttyUSB0`)
- **Network:** Internet connection for weather data
- **Permissions:** User access to Docker and serial devices

## 🔧 Hardware Setup

### 1. Connect USB LoRa Device

```bash
# Check if your USB device is detected
ls -la /dev/ttyUSB*

# Should show something like:
# crw-rw---- 1 root dialout 188, 0 Jan  8 10:30 /dev/ttyUSB0

# If no device appears, check system logs
dmesg | grep tty
```

### 2. Set Device Permissions

Choose one of these methods:

**Method A: Direct permissions (temporary)**
```bash
sudo chmod 666 /dev/ttyUSB0
```

**Method B: Add user to dialout group (permanent)**
```bash
# Add your user to the dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in for changes to take effect
# Verify group membership
groups | grep dialout
```

## 🚀 Production Deployment

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Verify Docker Compose availability
docker compose version || docker-compose version
```

### Step 2: Configure Environment

```bash
# Create production environment file
cp .env.testing .env.prod

# Edit the production configuration
nano .env.prod  # or use your preferred editor
```

**Key changes for production in `.env.prod`:**
```bash
# Serial/LoRa Configuration - PRODUCTION MODE
SERIAL_PORT=/dev/ttyUSB0
BAUD_RATE=9600
TESTING_MODE=false
SIMULATE_DATA=false

# Application Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=your_strong_production_secret_key_here

# Security: Change default passwords
POSTGRES_PASSWORD=your_secure_database_password_here
GRAFANA_PASSWORD=your_secure_grafana_password_here

# Weather API Configuration (customize for your location)
WEATHER_LAT=49.6265900
WEATHER_LON=18.3016172
WEATHER_ALT=350
USER_AGENT=YourPondMonitor/1.0 (your.email@domain.com)
```

### Step 3: Activate Production Configuration

```bash
# Copy production config to active environment
cp .env.prod .env

# Verify configuration
grep -E "TESTING_MODE|SIMULATE_DATA" .env
# Should show:
# TESTING_MODE=false
# SIMULATE_DATA=false
```

### Step 4: Build Docker Images

```bash
# Auto-detect Docker Compose command and build
if command -v docker compose >/dev/null 2>&1; then
    docker compose build
else
    docker-compose build
fi
```

### Step 5: Deploy Production Services

```bash
# Deploy with production configuration (includes USB device mounting)
if command -v docker compose >/dev/null 2>&1; then
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
fi
```

### Step 6: Verify Deployment

```bash
# Check service status
if command -v docker compose >/dev/null 2>&1; then
    docker compose ps
else
    docker-compose ps
fi

# Expected output should show all services as "Up"
# NAME                    SERVICE       STATUS       PORTS
# pondmonitor-flask_ui-1      flask_ui      Up          0.0.0.0:5000->5000/tcp
# pondmonitor-lora_gateway-1  lora_gateway  Up
# pondmonitor-redis-1         redis         Up          0.0.0.0:6379->6379/tcp
# pondmonitor-timescaledb-1   timescaledb   Up          0.0.0.0:5432->5432/tcp
```

### Step 7: Test Production System

```bash
# Test API health
curl -s http://localhost:5000/health | python3 -m json.tool

# Check LoRa gateway logs
if command -v docker compose >/dev/null 2>&1; then
    docker compose logs -f lora_gateway
else
    docker-compose logs -f lora_gateway
fi
# Look for messages like: "✅ Connected to serial port /dev/ttyUSB0"
```

## 🔍 Monitoring and Maintenance

### View Real-time Logs

```bash
# All services
if command -v docker compose >/dev/null 2>&1; then
    docker compose logs -f
else
    docker-compose logs -f
fi

# Specific service
if command -v docker compose >/dev/null 2>&1; then
    docker compose logs -f lora_gateway
    docker compose logs -f flask_ui
else
    docker-compose logs -f lora_gateway
    docker-compose logs -f flask_ui
fi
```

### Check System Status

```bash
# Service health
curl http://localhost:5000/health

# Current sensor status
curl http://localhost:5000/api/status

# Container resource usage
docker stats
```

### Database Operations

```bash
# Connect to database
if command -v docker compose >/dev/null 2>&1; then
    docker compose exec timescaledb psql -U pond_user -d pond_data
else
    docker-compose exec timescaledb psql -U pond_user -d pond_data
fi

# View recent data
# In psql:
SELECT timestamp, temperature_c, battery_v, signal_dbm 
FROM station_metrics 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Backup Database

```bash
# Create backup directory
mkdir -p backups

# Backup database
if command -v docker compose >/dev/null 2>&1; then
    docker compose exec timescaledb pg_dump -U pond_user pond_data > backups/pond_data_$(date +%Y%m%d_%H%M%S).sql
else
    docker-compose exec timescaledb pg_dump -U pond_user pond_data > backups/pond_data_$(date +%Y%m%d_%H%M%S).sql
fi
```

## 🛠️ Troubleshooting Production Issues

### Serial Device Problems

```bash
# Check device is still connected
ls -la /dev/ttyUSB*

# Check device permissions
ls -la /dev/ttyUSB0
# Should show: crw-rw---- 1 root dialout

# Test device manually
cat /dev/ttyUSB0
# Should show data if device is working

# Check container device mounting
if command -v docker compose >/dev/null 2>&1; then
    docker compose exec lora_gateway ls -la /dev/ttyUSB0
else
    docker-compose exec lora_gateway ls -la /dev/ttyUSB0
fi
```

### Service Issues

```bash
# Restart specific service
if command -v docker compose >/dev/null 2>&1; then
    docker compose restart lora_gateway
    docker compose restart flask_ui
else
    docker-compose restart lora_gateway
    docker-compose restart flask_ui
fi

# Full system restart
if command -v docker compose >/dev/null 2>&1; then
    docker compose down
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose down
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
fi
```

### Data Issues

```bash
# Check data is being written
if command -v docker compose >/dev/null 2>&1; then
    docker compose exec timescaledb psql -U pond_user -d pond_data -c "SELECT COUNT(*) FROM station_metrics WHERE timestamp > NOW() - INTERVAL '1 hour';"
else
    docker-compose exec timescaledb psql -U pond_user -d pond_data -c "SELECT COUNT(*) FROM station_metrics WHERE timestamp > NOW() - INTERVAL '1 hour';"
fi

# Check Redis cache
if command -v docker compose >/dev/null 2>&1; then
    docker compose exec redis redis-cli get latest_status
else
    docker-compose exec redis redis-cli get latest_status
fi
```

## 🔄 Updates and Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild images
if command -v docker compose >/dev/null 2>&1; then
    docker compose build
else
    docker-compose build
fi

# Restart services with new images
if command -v docker compose >/dev/null 2>&1; then
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
fi
```

### Clean Up Resources

```bash
# Remove unused images and containers
docker system prune -f

# Remove unused volumes (⚠️ This will delete data!)
docker volume prune -f
```

## 📊 Monitoring Stack (Optional)

To enable Grafana and Prometheus monitoring:

```bash
# Start with monitoring profile
if command -v docker compose >/dev/null 2>&1; then
    docker compose --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml up -d
fi

# Access Grafana at http://localhost:3000
# Default login: admin / secure_admin_password (from .env)
```

## 🚨 Emergency Recovery

### Complete System Reset

```bash
# ⚠️ WARNING: This will delete all data!
# Stop all services
if command -v docker compose >/dev/null 2>&1; then
    docker compose down -v
else
    docker-compose down -v
fi

# Remove volumes
docker volume rm pondmonitor_timescale_data pondmonitor_redis_data

# Restart system
if command -v docker compose >/dev/null 2>&1; then
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
fi
```

### Switch Back to Testing Mode

```bash
# Copy testing configuration
cp .env.testing .env

# Restart in testing mode
if command -v docker compose >/dev/null 2>&1; then
    docker compose down
    docker compose up -d
else
    docker-compose down
    docker-compose up -d
fi
```

## 📱 Access Points

Once deployed, access your PondMonitor at:

- **Main Dashboard:** http://localhost:5000
- **Weather Page:** http://localhost:5000/weather  
- **Diagnostics:** http://localhost:5000/diagnostics
- **API Health:** http://localhost:5000/health
- **Grafana (if enabled):** http://localhost:3000

## 🔐 Security Considerations

1. **Change default passwords** in `.env` file
2. **Use firewall** to restrict access to ports 5000, 5432, 6379
3. **Enable HTTPS** in production with reverse proxy (nginx/Apache)
4. **Regular backups** of database
5. **Monitor logs** for suspicious activity
6. **Keep Docker images updated**

## 📞 Getting Help

If you encounter issues:

1. **Check logs first:**
   ```bash
   docker compose logs lora_gateway | tail -50
   ```

2. **Verify configuration:**
   ```bash
   grep -E "TESTING_MODE|SIMULATE_DATA|SERIAL_PORT" .env
   ```

3. **Test individual components:**
   ```bash
   curl http://localhost:5000/health
   ```

4. **Create GitHub issue** with:
   - System information (OS, Docker version)
   - Complete error logs
   - Configuration (without passwords)
   - Steps to reproduce

---

## 📖 User Manual

### **🎮 Dashboard Usage**

#### **Main Dashboard**
- **Real-time Charts:** Water level and outflow data with customizable time ranges
- **Statistics Cards:** Current values, maximums, and trends
- **Time Controls:** Quick buttons (1h, 6h, 24h) or custom date ranges
- **Data Export:** Download data as CSV or JSON formats

#### **Navigation**
- **Sidebar Menu:** Easy navigation between Dashboard, Weather, and Diagnostics
- **Theme Toggle:** Switch between light and dark modes
- **Connection Status:** Real-time indicator of system connectivity
- **Mobile Support:** Responsive design works on all devices

### **📊 Charts and Visualizations**

#### **Interactive Features**
- **Zoom:** Click and drag to zoom into specific time periods
- **Hover Data:** Detailed information on hover/touch
- **Pan:** Navigate through historical data
- **Export:** Built-in chart export to PNG/SVG

#### **Time Range Selection**
```
Quick Buttons:  [1h] [6h] [12h] [24h] [3d] [7d]
Custom Range:   [Start Date/Time] to [End Date/Time] [Load]
```

### **🌦️ Weather Features**

#### **Current Weather Card**
- Temperature, precipitation, wind speed, and atmospheric pressure
- Weather icons and conditions
- Real-time updates every 30 minutes

#### **48-Hour Meteogram**
- Detailed hourly forecast with multiple parameters
- Temperature curves, precipitation bars, wind data
- Interactive zoom and hover information

#### **7-Day Forecast**
- Daily weather cards with high/low temperatures  
- Precipitation probability and wind information
- Weather symbols and trend indicators

### **🔧 Diagnostics Panel**

#### **System Health Overview**
- Overall system health score and status
- Active issues and warnings
- Service availability monitoring

#### **Hardware Monitoring**
- **Battery Status:** Voltage, percentage, charging indicators
- **Temperature:** Sensor readings and trends
- **Signal Strength:** LoRa communication quality
- **Solar Power:** Generation and usage patterns

#### **Troubleshooting Tools**
- Connection testing
- Data export for analysis
- Device restart capabilities
- System logs and events

---

## 🔧 Development

### **🏃‍♂️ Development Setup**

#### **Testing Mode (No Hardware)**
```bash
# Start development environment
make dev

# View logs in real-time
make test-logs

# Check database contents
make show-data

# Monitor Redis cache
make show-redis
```

#### **Production Mode (With Hardware)**
```bash
# Switch to production mode (requires USB device)
make prod-mode

# Manual production setup
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check USB device connection
ls -la /dev/ttyUSB*

# View production logs
docker compose logs -f lora_gateway
```

> **⚠️ Production Mode Requirements:**
> - USB LoRa device connected (typically `/dev/ttyUSB0`)
> - Device permissions: `sudo chmod 666 /dev/ttyUSB0` or add user to `dialout` group
> - Verify device: `dmesg | grep tty` after plugging in device

### **🧪 Testing and Quality Assurance**

#### **Running Tests**
```bash
# Run Python tests
make test

# Code formatting
make format

# Linting
make lint

# Test database connection
make shell-db

# Test Redis connection
make shell-redis
```

#### **Simulated Data in Testing Mode**
The system generates realistic simulated data when `TESTING_MODE=true`:

- **Temperature:** Daily cycles (15-35°C) with random variations
- **Battery:** 11-13V with charging/discharging patterns
- **Solar:** Daily solar generation curves (0-20V)
- **Water Level:** 140-160cm with realistic fluctuations
- **Outflow:** 2-3 L/s with minor variations
- **Signal:** -60 to -100 dBm random signal strength

### **🔧 Configuration**

#### **Environment Variables**

| Variable | Description | Default | Testing | Production |
|----------|-------------|---------|---------|------------|
| `TESTING_MODE` | Enable testing without hardware | `false` | `true` | `false` |
| `SIMULATE_DATA` | Generate synthetic sensor data | `false` | `true` | `false` |
| `SERIAL_PORT` | USB serial port path | `/dev/ttyUSB0` | `/dev/ttyUSB0` | `/dev/ttyUSB0` |
| `POSTGRES_USER` | Database username | `pond_user` | `pond_user` | `pond_user` |
| `REDIS_HOST` | Redis server hostname | `redis` | `redis` | `redis` |
| `WEATHER_LAT` | Weather location latitude | `49.6265900` | `49.6265900` | `49.6265900` |
| `WEATHER_LON` | Weather location longitude | `18.3016172` | `18.3016172` | `18.3016172` |
| `FLASK_ENV` | Flask environment | `production` | `development` | `production` |

#### **Docker Compose Configuration**

The system uses a **multi-file Docker Compose setup** for better separation of concerns:

```bash
# Testing mode (default)
docker compose up -d
# Uses: docker-compose.yml only
# Features: No USB devices, simulated data

# Production mode  
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
# Uses: docker-compose.yml + docker-compose.prod.yml (override)
# Features: USB device mounting, real hardware
```

**Key Configuration Files:**
- `docker-compose.yml` - Base configuration (testing mode)
- `docker-compose.prod.yml` - Production overrides (USB devices)
- `.env.testing` - Testing environment variables
- `.env` - Active environment (copied from .env.testing)

#### **Database Schema**
```sql
-- Pond metrics (water monitoring)
pond_metrics:
  - timestamp (TIMESTAMPTZ)
  - level_cm (REAL)
  - outflow_lps (REAL)

-- Station metrics (sensor telemetry)  
station_metrics:
  - timestamp (TIMESTAMPTZ)
  - temperature_c (REAL)
  - battery_v (REAL)
  - solar_v (REAL)
  - signal_dbm (INTEGER)
  - station_id (VARCHAR)
```

### **📁 Project Structure**

```
PondMonitor/
├── 📄 docker-compose.yml          # Base service configuration (testing mode)
├── 📄 docker-compose.prod.yml     # Production overrides (USB devices)
├── 📄 LoraGateway.py              # Data acquisition service  
├── 📄 init_pondmonitor.sql        # Database schema initialization
├── 📄 requirements.txt            # Python dependencies
├── 📄 Makefile                    # Development commands (auto-detects docker compose)
├── 📄 start-testing.sh            # Quick start script
├── 📄 .env.testing                # Testing configuration template
├── 📁 UI/                         # Web interface
│   ├── 📄 app.py                  # Flask application
│   ├── 📁 templates/              # HTML templates
│   │   ├── 📄 base.html           # Base template with theme support
│   │   ├── 📄 dashboard.html      # Main dashboard with real-time charts
│   │   ├── 📄 weather.html        # Weather page with meteogram
│   │   └── 📄 diagnostics.html    # System diagnostics and health
│   └── 📁 static/                 # CSS, JS, images
│       └── 📄 style.css           # Custom styles with dark/light theme
├── 📁 logs/                       # Application logs (auto-created)
├── 📁 db/                         # Database files (auto-created)
│   └── 📁 backups/                # Database backups
└── 📁 monitoring/                 # Optional monitoring stack
    ├── 📄 prometheus.yml          # Metrics collection
    └── 📁 grafana/                # Visualization dashboards
```

---

## 📊 API Documentation

### **🔗 REST API Endpoints**

#### **System Status**
```http
GET /health
```
Returns overall system health and service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:30:00Z",
  "services": {
    "redis": "healthy",
    "database": "healthy", 
    "weather_api": "healthy"
  }
}
```

#### **Current Status**
```http
GET /api/status
```
Returns latest sensor readings and system status.

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
  "last_seen_minutes": 0
}
```

#### **Dashboard Data**
```http
GET /api/dashboard?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z
```
Returns time-series data for dashboard charts.

**Parameters:**
- `start` (required): ISO 8601 start timestamp
- `end` (required): ISO 8601 end timestamp

**Response:**
```json
{
  "level": [[1704672000000, 145.2], [1704675600000, 144.8]],
  "outflow": [[1704672000000, 2.1], [1704675600000, 2.0]],
  "data_points": 144
}
```

#### **LoRa Diagnostics**
```http
GET /api/lora?hours=24
```
Returns sensor telemetry data for diagnostics.

**Parameters:**
- `hours` (optional): Number of hours to retrieve (1-168), default: 24

**Response:**
```json
{
  "temperature": [[1704672000000, 23.4], [1704675600000, 23.1]],
  "battery_voltage": [[1704672000000, 12.1], [1704675600000, 12.0]],
  "solar_voltage": [[1704672000000, 16.8], [1704675600000, 16.5]],
  "data_points": 144,
  "time_range_hours": 24
}
```

#### **Weather APIs**

**Current Weather:**
```http
GET /api/weather/current
```

**48-Hour Meteogram:**
```http
GET /api/weather/meteogram
```

**7-Day Forecast:**
```http
GET /api/weather/daily
```

**Weather Statistics:**
```http
GET /api/weather/stats
```

### **🔧 Error Responses**

All API endpoints return consistent error responses:

```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Common HTTP Status Codes:**
- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

---

## 🐛 Troubleshooting

### **🚨 Common Issues**

#### **Services Won't Start**
```bash
# Check Docker is running
docker info

# Check Docker Compose version
docker compose version || docker-compose version

# Check port availability
netstat -tulpn | grep :5000

# View detailed logs
docker compose logs flask_ui || docker-compose logs flask_ui
docker compose logs lora_gateway || docker-compose logs lora_gateway
```

#### **Docker Compose Command Issues**
```bash
# If you get "docker-compose: command not found"
sudo apt install docker-compose-plugin

# If you get "docker compose: command not found"  
sudo apt install docker-compose

# The system auto-detects which command to use
make help  # Shows which command is being used
```

#### **Database Connection Issues**
```bash
# Test database connection
make shell-db

# Check database logs
docker compose logs timescaledb || docker-compose logs timescaledb

# Reset database (⚠️ deletes all data)
make reset-db
```

#### **USB Device Issues (Production Mode)**
```bash
# Check if device is detected
ls -la /dev/ttyUSB*
dmesg | grep tty

# Fix permissions
sudo chmod 666 /dev/ttyUSB0
# OR add user to dialout group
sudo usermod -a -G dialout $USER
# (requires logout/login)

# Test device connection
cat /dev/ttyUSB0  # Should show incoming data

# Check Docker device mounting
docker compose ps
docker compose logs lora_gateway
```

#### **No Data Appearing**
```bash
# Check if data is being generated (testing mode)
make show-data

# Verify Redis cache
make show-redis

# Check gateway logs for errors
docker compose logs -f lora_gateway || docker-compose logs -f lora_gateway

# Verify environment variables
grep -E "TESTING_MODE|SIMULATE_DATA" .env

# Force restart gateway service
docker compose restart lora_gateway || docker-compose restart lora_gateway
```

#### **Weather Not Loading**
```bash
# Test weather API directly
curl "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=49.6265900&lon=18.3016172" \
  -H "User-Agent: PondMonitor/1.0 (pond@monitor.cz)"

# Check Flask logs for weather errors
docker compose logs flask_ui | grep -i weather || docker-compose logs flask_ui | grep -i weather

# Clear Redis cache
docker compose exec redis redis-cli flushall || docker-compose exec redis redis-cli flushall
```

### **🔍 Debugging Commands**

```bash
# Full system debug information
make debug

# Check service health
make health

# Monitor real-time logs (auto-detects docker compose command)
docker compose logs -f || docker-compose logs -f

# Connect to database directly
make shell-db

# Connect to Redis directly  
make shell-redis

# Check disk usage
docker system df

# Clean up unused resources
make clean

# Test specific components
curl http://localhost:5000/health  # API health
curl http://localhost:5000/api/status  # Sensor status
```

### **📝 Log Files**

Logs are stored in the `logs/` directory:
- `lora_gateway.log` - Data acquisition logs
- `ui.log` - Web interface logs
- Docker logs accessible via `docker-compose logs`

### **🔄 Recovery Procedures**

#### **Restart Individual Services**
```bash
# Restart just the gateway
docker compose restart lora_gateway || docker-compose restart lora_gateway

# Restart just the web interface
docker compose restart flask_ui || docker-compose restart flask_ui

# Restart database
docker compose restart timescaledb || docker-compose restart timescaledb
```

#### **Complete System Reset**
```bash
# Stop all services
docker compose down || docker-compose down

# Remove volumes (⚠️ deletes all data)
docker compose down -v || docker-compose down -v

# Rebuild and restart
make quick-start
# OR manually:
docker compose build && docker compose up -d
```

#### **Switch Between Modes**
```bash
# Switch to testing mode
make test-mode

# Switch to production mode  
make prod-mode

# Manual mode switching
cp .env.testing .env  # Testing
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d  # Production
```

### **🆘 Getting Help**

If you encounter issues not covered here:

1. **Check the logs** first using `make debug`
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - System information (OS, Docker version)
   - Complete error logs
   - Steps to reproduce
   - Configuration files (without sensitive data)

---

## 🤝 Contributing

### **Development Workflow**

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Make** your changes
4. **Test** thoroughly: `make test`
5. **Format** code: `make format`
6. **Commit** with clear messages
7. **Push** and create a **Pull Request**

### **Code Standards**

- **Python:** Follow PEP 8, use Black formatter
- **JavaScript:** ES6+, consistent indentation
- **HTML/CSS:** Semantic markup, responsive design
- **Documentation:** Update README for new features

### **Testing Requirements**

- All new features must include tests
- Maintain or improve code coverage
- Test in both development and production modes
- Verify mobile responsiveness

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **TimescaleDB** - Time-series database optimization
- **met.no** - Weather data API
- **Highcharts** - Interactive data visualization
- **Tailwind CSS** - Utility-first CSS framework
- **Flask** - Lightweight web framework
- **Redis** - In-memory data caching

---

## 📋 Makefile Commands Reference

For users who have `make` installed, here's a comprehensive reference of all available commands:

### **🚀 Quick Start Commands**
```bash
make help          # Show all available commands with descriptions
make quick-start    # Build and start in testing mode (fastest way to get started)
make dev            # Alias for test-mode (development environment)
```

### **🏗️ Build and Deployment**
```bash
make build          # Build all Docker images
make up             # Start all services in background
make down           # Stop all services
make restart        # Restart all services
```

### **🧪 Testing Mode Commands**
```bash
make test-mode      # Start in testing mode (no USB device required)
make test-logs      # Show logs for testing services (lora_gateway + flask_ui)
make test-status    # Check status of testing services with health check
```

### **🏭 Production Mode Commands**
```bash
make prod-mode      # Switch to production mode (USB device required)
# Note: Automatically creates .env.prod, switches config, and deploys with USB mounting
```

### **📊 Monitoring and Logs**
```bash
make logs           # Show logs for all services (follow mode)
make health         # Check health of all services with API test
make status         # Show container status (docker compose ps)
make debug          # Show comprehensive debugging information
```

### **🗄️ Database Operations**
```bash
make shell-db       # Connect to PostgreSQL database shell
make show-data      # Display recent sensor data from database
make backup         # Create timestamped database backup
make reset-db       # ⚠️ DANGEROUS: Delete all data and reset database
```

### **🔄 Redis Operations**
```bash
make shell-redis    # Connect to Redis shell
make show-redis     # Show current Redis data (latest_status)
```

### **🧹 Maintenance and Cleanup**
```bash
make clean          # Clean up Docker resources (containers, images, networks)
make reset          # Complete system reset (stops services, removes volumes)
```

### **🔍 Development and Testing**
```bash
make test           # Run Python tests with coverage
make lint           # Run code linting (flake8, mypy)
make format         # Format code with Black
```

### **📈 Monitoring Stack**
```bash
make monitoring     # Start with Grafana and Prometheus monitoring
# Access: Grafana at http://localhost:3000, Prometheus at http://localhost:9090
```

### **🔧 Troubleshooting Commands**
```bash
make debug          # Comprehensive system debugging information
make health         # Test all service endpoints and connections
make test-status    # Check if services are responding correctly
```

### **📦 Data Management**
```bash
make show-data      # View recent pond and station metrics
make show-redis     # View current cached status
make backup         # Create database backup with timestamp
```

### **🎯 Most Common Workflows**

#### **First Time Setup (Testing)**
```bash
make quick-start    # One command to build and start everything
```

#### **Development Workflow**
```bash
make dev            # Start development environment
make test-logs      # Monitor logs during development
make show-data      # Check if data is being generated
```

#### **Production Deployment**
```bash
make build          # Build latest images
make prod-mode      # Deploy to production with hardware
make health         # Verify everything is working
```

#### **Troubleshooting Workflow**
```bash
make debug          # Get system overview
make logs           # Check service logs
make health         # Test all connections
make restart        # Restart if needed
```

#### **Maintenance Workflow**
```bash
make backup         # Backup data before maintenance
make clean          # Clean up old resources
make build          # Rebuild with latest changes
make up             # Restart services
```

### **⚠️ Important Notes**

- **Docker Compose Auto-Detection**: All `make` commands automatically detect whether you have `docker compose` (modern) or `docker-compose` (legacy)
- **Environment Management**: `make test-mode` and `make prod-mode` automatically handle `.env` file switching
- **USB Device Requirements**: `make prod-mode` requires USB device at `/dev/ttyUSB0` with proper permissions
- **Data Safety**: Commands like `make reset-db` and `make clean` will delete data - use with caution
- **Testing Mode**: Most commands work in testing mode without any hardware requirements

### **🎓 Usage Examples**

```bash
# Complete setup from scratch
make quick-start

# Switch to production mode
make prod-mode

# Monitor system in real-time
make logs

# Troubleshoot issues
make debug
make health

# Backup before updates
make backup
git pull
make build
make up

# Clean development environment
make clean
make quick-start
```

> **💡 Tip**: Run `make help` anytime to see all available commands with descriptions. The Makefile is designed to make PondMonitor management as simple as possible!

---

<div align="center">

**Made with ❤️ for environmental monitoring**

[⬆ Back to Top](#-pondmonitor)

</div>