# PondMonitor Production Deployment

## 🏭 Production Setup Guide

Comprehensive guide for deploying PondMonitor in production with real LoRa hardware. This guide is designed for users who don't have `make` installed or prefer manual setup.

## 📋 Prerequisites

### **System Requirements**
- **Docker:** Version 20.10+ with Docker Compose
- **Operating System:** Linux/macOS/Windows with WSL2
- **Hardware Requirements:** 
  - 4GB RAM minimum, 8GB recommended
  - USB LoRa device connected (typically `/dev/ttyUSB0`)
- **Network:** Internet connection for weather data
- **Permissions:** User access to Docker and serial devices

### **Hardware Requirements**
- **LoRa Module:** USB-connected LoRa transceiver
- **Sensor Station:** Remote sensors with LoRa communication
- **Serial Interface:** USB-to-serial converter (if not integrated)

## 🔧 Hardware Setup

### **1. Connect USB LoRa Device**

```bash
# Check if your USB device is detected
ls -la /dev/ttyUSB*

# Should show something like:
# crw-rw---- 1 root dialout 188, 0 Jan  8 10:30 /dev/ttyUSB0

# If no device appears, check system logs
dmesg | grep tty
```

### **2. Set Device Permissions**

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

**Method C: Create udev rule (system-wide)**
```bash
# Create udev rule for automatic permissions
sudo tee /etc/udev/rules.d/99-pondmonitor-usb.rules << 'EOF'
# PondMonitor LoRa device permissions
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
# Adjust idVendor and idProduct based on your device
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## 🚀 Production Deployment

### **Step 1: Clone and Setup**

```bash
# Clone the repository
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Verify Docker Compose availability
docker compose version || docker-compose version
```

### **Step 2: Configure Environment**

```bash
# Create production environment file
cp .env.testing .env.prod

# Edit the production configuration
nano .env.prod  # or use your preferred editor
```

**Key changes for production in `.env.prod`:**
```bash
# =============================================================================
# PondMonitor Production Configuration
# =============================================================================

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

# Network Configuration
FLASK_PORT=5000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Database Configuration
POSTGRES_USER=pond_user
POSTGRES_DB=pond_data
PG_HOST=timescaledb

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# LoRa Gateway Configuration
MAX_RETRIES=3
RETRY_DELAY=5
```

### **Step 3: Activate Production Configuration**

```bash
# Copy production config to active environment
cp .env.prod .env

# Verify configuration
grep -E "TESTING_MODE|SIMULATE_DATA|SERIAL_PORT" .env
# Should show:
# TESTING_MODE=false
# SIMULATE_DATA=false
# SERIAL_PORT=/dev/ttyUSB0
```

### **Step 4: Build Docker Images**

```bash
# Auto-detect Docker Compose command and build
if command -v docker compose >/dev/null 2>&1; then
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="docker-compose"
fi

echo "Using Docker Compose command: $DOCKER_CMD"
$DOCKER_CMD build
```

### **Step 5: Create Production Override**

Create `docker-compose.prod.yml` if it doesn't exist:

```yaml
# docker-compose.prod.yml - Production overrides
version: '3.8'

services:
  # LoRa Gateway with USB device mounting
  lora_gateway:
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    environment:
      - TESTING_MODE=false
      - SIMULATE_DATA=false
    restart: always
    
  # Flask UI with production settings
  flask_ui:
    environment:
      - FLASK_ENV=production
    restart: always
    
  # Database with production optimizations
  timescaledb:
    environment:
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=timescaledb
    restart: always
    
  # Redis with production settings
  redis:
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    restart: always
```

### **Step 6: Deploy Production Services**

```bash
# Deploy with production configuration (includes USB device mounting)
$DOCKER_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Step 7: Verify Deployment**

```bash
# Check service status
$DOCKER_CMD ps

# Expected output should show all services as "Up"
# NAME                    SERVICE       STATUS       PORTS
# pondmonitor-flask_ui-1      flask_ui      Up          0.0.0.0:5000->5000/tcp
# pondmonitor-lora_gateway-1  lora_gateway  Up
# pondmonitor-redis-1         redis         Up          0.0.0.0:6379->6379/tcp
# pondmonitor-timescaledb-1   timescaledb   Up          0.0.0.0:5432->5432/tcp
```

### **Step 8: Test Production System**

```bash
# Test API health
curl -s http://localhost:5000/health | python3 -m json.tool

# Check LoRa gateway logs for hardware connection
$DOCKER_CMD logs -f lora_gateway
# Look for messages like: "✅ Connected to serial port /dev/ttyUSB0"

# Test sensor data reception
curl -s http://localhost:5000/api/status | python3 -m json.tool
```

## 🔍 Monitoring and Maintenance

### **View Real-time Logs**

```bash
# All services
$DOCKER_CMD logs -f

# Specific service
$DOCKER_CMD logs -f lora_gateway
$DOCKER_CMD logs -f flask_ui
$DOCKER_CMD logs -f timescaledb
```

### **Check System Status**

```bash
# Service health
curl http://localhost:5000/health

# Current sensor status  
curl http://localhost:5000/api/status

# Container resource usage
docker stats

# Database connection test
$DOCKER_CMD exec timescaledb pg_isready -U pond_user -d pond_data
```

### **Database Operations**

```bash
# Connect to database
$DOCKER_CMD exec -it timescaledb psql -U pond_user -d pond_data

# View recent data (in psql):
SELECT timestamp, temperature_c, battery_v, signal_dbm 
FROM station_metrics 
ORDER BY timestamp DESC 
LIMIT 10;

# Check data volume
SELECT COUNT(*) as total_records, 
       MAX(timestamp) as latest_data,
       MIN(timestamp) as earliest_data
FROM station_metrics;
```

### **Backup Database**

```bash
# Create backup directory
mkdir -p backups

# Create timestamped backup
BACKUP_FILE="backups/pond_data_$(date +%Y%m%d_%H%M%S).sql"
$DOCKER_CMD exec timescaledb pg_dump -U pond_user pond_data > $BACKUP_FILE

echo "Database backed up to: $BACKUP_FILE"

# Compress backup
gzip $BACKUP_FILE
```

### **Restore from Backup**

```bash
# Stop the application
$DOCKER_CMD down

# Start only the database
$DOCKER_CMD up -d timescaledb

# Wait for database to be ready
sleep 10

# Restore from backup (adjust filename)
BACKUP_FILE="backups/pond_data_20250108_120000.sql"
if [ -f "$BACKUP_FILE.gz" ]; then
    gunzip -c $BACKUP_FILE.gz | $DOCKER_CMD exec -i timescaledb psql -U pond_user -d pond_data
else
    $DOCKER_CMD exec -i timescaledb psql -U pond_user -d pond_data < $BACKUP_FILE
fi

# Start all services
$DOCKER_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🛠️ Troubleshooting Production Issues

### **Serial Device Problems**

```bash
# Check device is still connected
ls -la /dev/ttyUSB*

# Check device permissions
ls -la /dev/ttyUSB0
# Should show: crw-rw---- 1 root dialout

# Test device manually (Ctrl+C to exit)
cat /dev/ttyUSB0

# Check container device mounting
$DOCKER_CMD exec lora_gateway ls -la /dev/ttyUSB0

# Check gateway logs for connection errors
$DOCKER_CMD logs lora_gateway | grep -i "serial\|usb\|connection"
```

### **Service Issues**

```bash
# Restart specific service
$DOCKER_CMD restart lora_gateway
$DOCKER_CMD restart flask_ui

# Check service health
$DOCKER_CMD exec flask_ui curl -f http://localhost:5000/health

# Full system restart
$DOCKER_CMD down
$DOCKER_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Data Issues**

```bash
# Check data is being written to database
$DOCKER_CMD exec timescaledb psql -U pond_user -d pond_data -c \
  "SELECT COUNT(*) FROM station_metrics WHERE timestamp > NOW() - INTERVAL '1 hour';"

# Check Redis cache
$DOCKER_CMD exec redis redis-cli get latest_status

# Verify LoRa communication
$DOCKER_CMD logs lora_gateway | tail -20
```

### **Performance Issues**

```bash
# Monitor resource usage
docker stats

# Check disk space
df -h
docker system df

# Monitor database performance
$DOCKER_CMD exec timescaledb psql -U pond_user -d pond_data -c \
  "SELECT schemaname, tablename, n_tup_ins as inserts, n_tup_upd as updates, n_tup_del as deletes 
   FROM pg_stat_user_tables;"

# Check slow queries (if enabled)
$DOCKER_CMD exec timescaledb psql -U pond_user -d pond_data -c \
  "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"
```

## 🔄 Updates and Maintenance

### **Update Application**

```bash
# Create backup before update
BACKUP_FILE="backups/pre_update_$(date +%Y%m%d_%H%M%S).sql"
$DOCKER_CMD exec timescaledb pg_dump -U pond_user pond_data > $BACKUP_FILE

# Pull latest changes
git pull origin main

# Rebuild images
$DOCKER_CMD build

# Restart services with new images
$DOCKER_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify update
curl http://localhost:5000/health
```

### **Clean Up Resources**

```bash
# Remove unused images and containers
docker system prune -f

# Remove unused volumes (⚠️ This will delete data!)
# docker volume prune -f

# Clean up old log files
find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
```

### **Log Rotation Setup**

Create log rotation configuration:

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/pondmonitor << 'EOF'
/home/*/PondMonitor/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

## 📊 Monitoring Stack (Optional)

### **Enable Grafana and Prometheus**

```bash
# Start with monitoring profile
$DOCKER_CMD --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml up -d

# Access monitoring
echo "Grafana: http://localhost:3000 (admin / your_grafana_password)"
echo "Prometheus: http://localhost:9090"
```

### **Configure Alerting**

```bash
# Create alert configuration
mkdir -p monitoring/alertmanager
cat > monitoring/alertmanager/config.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@yourdomain.com'
    subject: 'PondMonitor Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
EOF
```

## 🔐 Security Considerations

### **Firewall Configuration**

```bash
# Configure UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # PondMonitor web interface
sudo ufw deny 5432/tcp   # PostgreSQL (deny external access)
sudo ufw deny 6379/tcp   # Redis (deny external access)
sudo ufw enable
```

### **SSL/HTTPS Setup with Nginx**

```bash
# Install and configure Nginx reverse proxy
sudo apt install nginx certbot python3-certbot-nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/pondmonitor << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/pondmonitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### **Production Security Checklist**

- [ ] Changed default passwords in `.env`
- [ ] Configured firewall rules
- [ ] Set up SSL/HTTPS
- [ ] Regular database backups
- [ ] Log monitoring
- [ ] Updated all dependencies
- [ ] Restricted Docker socket access
- [ ] Configured log rotation

## 📱 Access Points

Once deployed, access your PondMonitor at:

- **Main Dashboard:** http://localhost:5000 (or https://your-domain.com)
- **Weather Page:** http://localhost:5000/weather  
- **Diagnostics:** http://localhost:5000/diagnostics
- **API Health:** http://localhost:5000/health
- **Grafana (if enabled):** http://localhost:3000

## 📞 Getting Help

If you encounter issues:

1. **Check logs first:**
   ```bash
   $DOCKER_CMD logs lora_gateway | tail -50
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

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).