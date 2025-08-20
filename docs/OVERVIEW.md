# PondMonitor Overview

## 🌊 Project Overview

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

## 📁 Project Structure

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
├── 📁 services/                   # Modular services
│   ├── 📄 weather_service.py      # Weather API integration
│   ├── 📄 export_service.py       # Data export functionality
│   └── 📄 alert_service.py        # Alert and notification system
├── 📁 logs/                       # Application logs (auto-created)
├── 📁 db/                         # Database files (auto-created)
│   └── 📁 backups/                # Database backups
├── 📁 tests/                      # Unit tests
├── 📁 docs/                       # Documentation
└── 📁 monitoring/                 # Optional monitoring stack
    ├── 📄 prometheus.yml          # Metrics collection
    └── 📁 grafana/                # Visualization dashboards
```

## 🔧 Configuration

### **Environment Variables**

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

### **Database Schema**
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

## 📊 Data Flow

1. **Sensors** → **LoRa Gateway** → **Serial/USB**
2. **LoraGateway.py** → **Data Processing** → **Validation**
3. **Redis Cache** (real-time) + **TimescaleDB** (historical)
4. **Flask API** → **JSON responses** → **Web Interface**
5. **Highcharts** → **Interactive visualizations**

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, Flask, TimescaleDB, Redis
- **Frontend**: HTML5, CSS3, JavaScript, Highcharts
- **Deployment**: Docker Compose, multi-stage builds
- **Testing**: pytest, simulated data generation
- **Monitoring**: Health checks, structured logging
- **Hardware**: LoRa wireless communication, USB/Serial interfaces

## 🔗 Next Steps

- **Quick Setup:** See [QUICKSTART.md](QUICKSTART.md)
- **Production Deployment:** Follow [DEPLOYMENT.md](DEPLOYMENT.md)
- **Development:** Check [DEVELOPMENT.md](DEVELOPMENT.md)
- **API Usage:** Reference [API.md](API.md)