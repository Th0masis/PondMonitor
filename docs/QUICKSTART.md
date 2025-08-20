# PondMonitor Quick Start

## 🚀 Quick Start Guide

Get PondMonitor running in under 5 minutes with testing mode (no hardware required).

### **Prerequisites**

- **Docker:** Version 20.10+ with Docker Compose
  - **Modern installations:** Use `docker compose` (plugin)
  - **Legacy installations:** Use `docker-compose` (standalone)
  - **System automatically detects** which version you have
- **Operating System:** Linux/macOS/Windows with WSL2
- **Hardware:** 4GB RAM minimum, 8GB recommended
- **Network:** Internet connection for weather data
- **Optional:** `make` utility for convenient commands

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

## 🎯 **Option 1: Automated Setup (Recommended)**

```bash
# Clone the repository
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Make startup script executable
chmod +x start-testing.sh

# Start in testing mode (no hardware required)
./start-testing.sh
```

## 🛠️ **Option 2: Manual Setup**

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

## ⚡ **Option 3: Using Make (if installed)**

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

## 🌐 **Access the Application**

Once started, access the web interface at:
- **Main Dashboard:** http://localhost:5000
- **Weather Page:** http://localhost:5000/weather  
- **Diagnostics:** http://localhost:5000/diagnostics
- **API Health:** http://localhost:5000/health

## ✅ **Verify Installation**

### **Check Services Status**
```bash
# View running containers
docker compose ps || docker-compose ps

# Expected output should show all services as "Up"
# NAME                    SERVICE       STATUS       PORTS
# pondmonitor-flask_ui-1      flask_ui      Up          0.0.0.0:5000->5000/tcp
# pondmonitor-lora_gateway-1  lora_gateway  Up
# pondmonitor-redis-1         redis         Up          0.0.0.0:6379->6379/tcp
# pondmonitor-timescaledb-1   timescaledb   Up          0.0.0.0:5432->5432/tcp
```

### **Test API Health**
```bash
# Test system health
curl -s http://localhost:5000/health | python3 -m json.tool

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-08T10:30:00Z",
#   "services": {
#     "redis": "healthy",
#     "database": "healthy",
#     "weather_api": "healthy"
#   }
# }
```

### **Check Data Generation (Testing Mode)**
```bash
# Check if simulated data is being generated
curl -s http://localhost:5000/api/status | python3 -m json.tool

# Should show current sensor readings:
# {
#   "temperature_c": 23.4,
#   "battery_v": 12.1,
#   "connected": true,
#   "last_heartbeat": "2025-01-08T10:29:45Z"
# }
```

## 📊 **View Real-time Data**

### **Dashboard Features**
- **Real-time Charts:** Water level and outflow with time controls
- **Statistics Cards:** Current values and trends
- **Time Range Selection:** 1h, 6h, 24h, or custom ranges
- **Export Options:** Download data as CSV/JSON

### **Testing Mode Data**
In testing mode, the system generates realistic simulated data:
- **Temperature:** 15-35°C with daily cycles
- **Battery:** 11-13V with charging patterns
- **Solar:** 0-20V daily generation curves
- **Water Level:** 140-160cm with fluctuations
- **Outflow:** 2-3 L/s with variations
- **Signal:** -60 to -100 dBm random strength

## 🛠️ **Next Steps**

### **Development Workflow**
```bash
# Monitor logs during development
make test-logs
# or manually:
docker compose logs -f || docker-compose logs -f

# Check database contents
make show-data
# or manually:
docker compose exec timescaledb psql -U pond_user -d pond_data
```

### **Production Deployment**
For production with real hardware, see [DEPLOYMENT.md](DEPLOYMENT.md):
```bash
# Switch to production mode (requires USB LoRa device)
make prod-mode
```

### **Customization**
- **Weather Location:** Edit `WEATHER_LAT` and `WEATHER_LON` in `.env`
- **Database Settings:** Modify PostgreSQL configuration
- **Sensor Parameters:** Adjust validation ranges in `utils.py`

## 🔍 **Common Commands**

```bash
# View all service logs
docker compose logs -f || docker-compose logs -f

# Check specific service
docker compose logs -f flask_ui || docker-compose logs -f flask_ui
docker compose logs -f lora_gateway || docker-compose logs -f lora_gateway

# Stop services
docker compose down || docker-compose down

# Restart services
docker compose restart || docker-compose restart

# Clean up (removes containers, keeps data)
docker compose down || docker-compose down
```

## 🆘 **Quick Troubleshooting**

### **Services Won't Start**
```bash
# Check Docker is running
docker info

# Check port availability
netstat -tulpn | grep :5000

# View error logs
docker compose logs flask_ui || docker-compose logs flask_ui
```

### **No Data Appearing**
```bash
# Verify testing mode is enabled
grep -E "TESTING_MODE|SIMULATE_DATA" .env
# Should show: TESTING_MODE=true, SIMULATE_DATA=true

# Check gateway logs
docker compose logs lora_gateway || docker-compose logs lora_gateway

# Restart gateway service
docker compose restart lora_gateway || docker-compose restart lora_gateway
```

### **Web Interface Not Loading**
```bash
# Test direct API access
curl http://localhost:5000/health

# Check Flask logs
docker compose logs flask_ui || docker-compose logs flask_ui

# Verify port is open
curl -I http://localhost:5000
```

## 📚 **Further Reading**

- **Complete Feature Tour:** [USER_GUIDE.md](USER_GUIDE.md)
- **Production Setup:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Development Setup:** [DEVELOPMENT.md](DEVELOPMENT.md)
- **API Reference:** [API.md](API.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)