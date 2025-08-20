# PondMonitor Troubleshooting Guide

## 🔍 Troubleshooting Guide

This comprehensive guide covers common issues, diagnostic procedures, and solutions for PondMonitor deployment and operation.

## 🚨 Common Issues

### **🐳 Docker and Deployment Issues**

#### **Services Won't Start**

**Symptoms:**
- Containers exit immediately
- "Port already in use" errors
- Services show as "unhealthy"

**Diagnosis:**
```bash
# Check Docker is running
docker info

# Check Docker Compose version
docker compose version || docker-compose version

# Check port availability
netstat -tulpn | grep :5000
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379

# View detailed logs
docker compose logs flask_ui || docker-compose logs flask_ui
docker compose logs lora_gateway || docker-compose logs lora_gateway
docker compose logs timescaledb || docker-compose logs timescaledb
```

**Solutions:**

1. **Port Conflicts:**
   ```bash
   # Kill processes using required ports
   sudo lsof -ti:5000 | xargs kill -9
   sudo lsof -ti:5432 | xargs kill -9
   sudo lsof -ti:6379 | xargs kill -9
   
   # Or change ports in .env file
   FLASK_PORT=5001
   POSTGRES_PORT=5433
   REDIS_PORT=6380
   ```

2. **Permission Issues:**
   ```bash
   # Fix Docker permissions
   sudo usermod -aG docker $USER
   # Log out and back in
   
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod +x start-testing.sh
   ```

3. **Memory Issues:**
   ```bash
   # Check available memory
   free -h
   
   # Increase Docker memory limit (Docker Desktop)
   # Go to Docker Desktop → Settings → Resources → Memory
   # Set to at least 4GB
   ```

#### **Docker Compose Command Issues**

**Symptoms:**
- "docker-compose: command not found"
- "docker compose: command not found"
- Version conflicts

**Solutions:**

```bash
# Install Docker Compose Plugin (modern)
sudo apt update
sudo apt install docker-compose-plugin

# Or install standalone version (legacy)
sudo apt install docker-compose

# Check which version you have
docker compose version || docker-compose version

# Use the appropriate command
DOCKER_CMD="docker compose"
if ! command -v docker compose >/dev/null 2>&1; then
    DOCKER_CMD="docker-compose"
fi
echo "Using: $DOCKER_CMD"
```

### **💾 Database Connection Issues**

#### **Database Won't Start**

**Symptoms:**
- TimescaleDB container keeps restarting
- Connection refused errors
- Database initialization failures

**Diagnosis:**
```bash
# Check database logs
docker compose logs timescaledb || docker-compose logs timescaledb

# Test database connection
docker compose exec timescaledb pg_isready -U pond_user -d pond_data

# Check database status
docker compose ps timescaledb || docker-compose ps timescaledb
```

**Solutions:**

1. **Database Corruption:**
   ```bash
   # Stop all services
   docker compose down || docker-compose down
   
   # Remove database volume (⚠️ DELETES ALL DATA)
   docker volume rm pondmonitor_timescale_data
   
   # Restart services
   docker compose up -d || docker-compose up -d
   ```

2. **Password Issues:**
   ```bash
   # Check environment variables
   grep POSTGRES .env
   
   # Reset database with new password
   docker compose down -v || docker-compose down -v
   # Edit .env with new password
   docker compose up -d || docker-compose up -d
   ```

3. **Disk Space:**
   ```bash
   # Check disk space
   df -h
   
   # Clean Docker resources
   docker system prune -f
   docker volume prune -f  # ⚠️ Removes unused volumes
   ```

#### **Connection Timeouts**

**Symptoms:**
- Slow database queries
- Timeout errors in logs
- Web interface loading slowly

**Solutions:**

```bash
# Increase database connection timeout
# Add to docker-compose.yml under timescaledb environment:
- POSTGRES_CONNECT_TIMEOUT=60
- POSTGRES_COMMAND_TIMEOUT=300

# Optimize database
docker compose exec timescaledb psql -U pond_user -d pond_data << 'EOF'
VACUUM ANALYZE;
REINDEX DATABASE pond_data;
EOF

# Check database size and performance
docker compose exec timescaledb psql -U pond_user -d pond_data -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### **📡 Hardware and Serial Issues (Production Mode)**

#### **USB Device Not Detected**

**Symptoms:**
- `/dev/ttyUSB0` doesn't exist
- "Permission denied" errors
- LoRa gateway can't connect

**Diagnosis:**
```bash
# Check if device is detected
ls -la /dev/ttyUSB*
ls -la /dev/ttyACM*

# Check system logs
dmesg | grep -i tty
dmesg | grep -i usb

# Check USB devices
lsusb

# Check device info
udevadm info -a -n /dev/ttyUSB0
```

**Solutions:**

1. **Device Permissions:**
   ```bash
   # Method 1: Direct permissions (temporary)
   sudo chmod 666 /dev/ttyUSB0
   
   # Method 2: Add user to dialout group (permanent)
   sudo usermod -a -G dialout $USER
   # Log out and back in
   
   # Method 3: Create udev rule (system-wide)
   sudo tee /etc/udev/rules.d/99-pondmonitor.rules << 'EOF'
   SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
   EOF
   sudo udevadm control --reload-rules
   ```

2. **Driver Issues:**
   ```bash
   # Install common USB-serial drivers
   sudo apt update
   sudo apt install linux-modules-extra-$(uname -r)
   
   # For specific chip types:
   # CP210x chips:
   sudo modprobe cp210x
   
   # FTDI chips:
   sudo modprobe ftdi_sio
   
   # Check loaded modules
   lsmod | grep -E "cp210x|ftdi_sio|pl2303"
   ```

3. **Device Mounting in Docker:**
   ```bash
   # Check if device is mounted in container
   docker compose exec lora_gateway ls -la /dev/ttyUSB0
   
   # If not, check docker-compose.prod.yml:
   services:
     lora_gateway:
       devices:
         - /dev/ttyUSB0:/dev/ttyUSB0
   ```

#### **LoRa Communication Problems**

**Symptoms:**
- No data received from sensors
- Connection timeouts
- "Failed to read from serial port" errors

**Diagnosis:**
```bash
# Test serial port manually
cat /dev/ttyUSB0  # Should show incoming data

# Check baud rate and settings
stty -F /dev/ttyUSB0

# Test with different baud rates
stty -F /dev/ttyUSB0 9600
stty -F /dev/ttyUSB0 115200

# Monitor LoRa gateway logs
docker compose logs -f lora_gateway || docker-compose logs -f lora_gateway
```

**Solutions:**

1. **Serial Configuration:**
   ```bash
   # Check .env configuration
   grep -E "SERIAL_PORT|BAUD_RATE" .env
   
   # Common baud rates to try:
   BAUD_RATE=9600
   BAUD_RATE=115200
   BAUD_RATE=57600
   
   # Restart gateway with new settings
   docker compose restart lora_gateway
   ```

2. **Hardware Issues:**
   ```bash
   # Check physical connections
   # - USB cable securely connected
   # - LoRa module powered on
   # - Antenna connected properly
   
   # Test with different USB port
   # Update SERIAL_PORT in .env if device path changes
   ```

### **🌐 Web Interface Issues**

#### **Charts Not Loading**

**Symptoms:**
- Blank charts or "No data" messages
- JavaScript errors in browser console
- Slow chart rendering

**Diagnosis:**
```bash
# Check Flask logs for errors
docker compose logs flask_ui | grep -i error

# Test API endpoints directly
curl http://localhost:5000/health
curl http://localhost:5000/api/status
curl "http://localhost:5000/api/dashboard?start=2025-01-08T00:00:00Z&end=2025-01-08T23:59:59Z"

# Check browser console (F12)
# Look for JavaScript errors
```

**Solutions:**

1. **API Issues:**
   ```bash
   # Restart Flask service
   docker compose restart flask_ui
   
   # Check database has data
   docker compose exec timescaledb psql -U pond_user -d pond_data -c "
   SELECT COUNT(*) FROM pond_metrics WHERE timestamp > NOW() - INTERVAL '24 hours';
   SELECT COUNT(*) FROM station_metrics WHERE timestamp > NOW() - INTERVAL '24 hours';
   "
   ```

2. **Browser Issues:**
   ```bash
   # Clear browser cache and cookies
   # Try incognito/private mode
   # Test in different browser
   # Disable browser extensions
   # Check JavaScript is enabled
   ```

3. **Time Range Issues:**
   ```bash
   # Use shorter time ranges
   # Check system timezone settings
   # Verify date format in API calls
   ```

#### **Data Not Updating**

**Symptoms:**
- Stale data in interface
- "Last updated" timestamp not changing
- Real-time updates stopped

**Diagnosis:**
```bash
# Check if data is being generated
curl http://localhost:5000/api/status

# Check database for recent data
docker compose exec timescaledb psql -U pond_user -d pond_data -c "
SELECT timestamp, temperature_c, battery_v 
FROM station_metrics 
ORDER BY timestamp DESC 
LIMIT 5;
"

# Check Redis cache
docker compose exec redis redis-cli get latest_status
```

**Solutions:**

1. **LoRa Gateway Issues:**
   ```bash
   # Check gateway is running and collecting data
   docker compose logs lora_gateway | tail -20
   
   # Restart gateway
   docker compose restart lora_gateway
   
   # Verify testing mode settings
   grep -E "TESTING_MODE|SIMULATE_DATA" .env
   ```

2. **Cache Issues:**
   ```bash
   # Clear Redis cache
   docker compose exec redis redis-cli flushall
   
   # Restart Redis
   docker compose restart redis
   ```

### **🌦️ Weather Service Issues**

#### **Weather Data Not Loading**

**Symptoms:**
- Weather page shows errors
- "Weather service unavailable" messages
- API timeouts

**Diagnosis:**
```bash
# Test weather API directly
curl -s "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=49.6265900&lon=18.3016172" \
  -H "User-Agent: PondMonitor/1.0 (test@example.com)"

# Check Flask logs for weather errors
docker compose logs flask_ui | grep -i weather

# Test weather endpoint
curl http://localhost:5000/api/weather/current
```

**Solutions:**

1. **API Configuration:**
   ```bash
   # Check weather settings in .env
   grep WEATHER .env
   
   # Update User-Agent string
   USER_AGENT="YourPondMonitor/1.0 (your.email@domain.com)"
   
   # Update coordinates for your location
   WEATHER_LAT=your_latitude
   WEATHER_LON=your_longitude
   ```

2. **Network Issues:**
   ```bash
   # Check internet connectivity
   ping -c 3 api.met.no
   
   # Check DNS resolution
   nslookup api.met.no
   
   # Test from container
   docker compose exec flask_ui curl -s "https://api.met.no"
   ```

3. **Rate Limiting:**
   ```bash
   # Weather API has rate limits
   # Check for 429 errors in logs
   # Wait before retrying
   # Ensure reasonable request frequency
   ```

## 🔄 Data Flow Issues

### **No Data Being Collected**

**Symptoms:**
- Empty database tables
- No recent records
- Zero data points in API responses

**Diagnosis:**
```bash
# Check testing mode is enabled (for testing)
grep -E "TESTING_MODE|SIMULATE_DATA" .env

# Check LoRa gateway is running
docker compose ps lora_gateway

# Check database tables
docker compose exec timescaledb psql -U pond_user -d pond_data -c "
SELECT 
    'pond_metrics' as table_name, COUNT(*) as records, MAX(timestamp) as latest
FROM pond_metrics
UNION ALL
SELECT 
    'station_metrics' as table_name, COUNT(*) as records, MAX(timestamp) as latest  
FROM station_metrics;
"

# Check gateway logs for data processing
docker compose logs lora_gateway | grep -E "processed|inserted|error"
```

**Solutions:**

1. **Testing Mode Issues:**
   ```bash
   # Ensure testing mode is properly configured
   TESTING_MODE=true
   SIMULATE_DATA=true
   
   # Restart gateway to apply changes
   docker compose restart lora_gateway
   ```

2. **Database Connection Issues:**
   ```bash
   # Test database connection from gateway
   docker compose exec lora_gateway python3 -c "
   import psycopg2
   conn = psycopg2.connect(
       host='timescaledb',
       database='pond_data', 
       user='pond_user',
       password='secretpassword'  # Use your actual password
   )
   print('Database connection successful')
   conn.close()
   "
   ```

### **Partial Data Loss**

**Symptoms:**
- Gaps in time-series data
- Some sensors working, others not
- Intermittent data collection

**Diagnosis:**
```bash
# Check for data gaps
docker compose exec timescaledb psql -U pond_user -d pond_data -c "
SELECT 
    date_trunc('hour', timestamp) as hour,
    COUNT(*) as records,
    MIN(timestamp) as first_record,
    MAX(timestamp) as last_record
FROM station_metrics 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', timestamp)
ORDER BY hour;
"

# Check error patterns
docker compose logs lora_gateway | grep -i error | tail -20
```

**Solutions:**

1. **Communication Issues:**
   ```bash
   # Check signal strength logs
   docker compose logs lora_gateway | grep -i signal
   
   # Look for timeout/retry patterns
   docker compose logs lora_gateway | grep -E "timeout|retry|failed"
   ```

2. **Resource Issues:**
   ```bash
   # Check container resource usage
   docker stats
   
   # Check disk space
   df -h
   
   # Check memory usage
   free -h
   ```

## 🧹 Maintenance and Recovery

### **Database Maintenance**

#### **Regular Maintenance Tasks**

```bash
# Create maintenance script
cat > maintenance.sh << 'EOF'
#!/bin/bash
echo "🔧 PondMonitor Maintenance Script"

# Backup database
BACKUP_FILE="backups/maintenance_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p backups
docker compose exec timescaledb pg_dump -U pond_user pond_data > $BACKUP_FILE
echo "✅ Database backed up to $BACKUP_FILE"

# Vacuum and analyze database
docker compose exec timescaledb psql -U pond_user -d pond_data -c "VACUUM ANALYZE;"
echo "✅ Database vacuumed and analyzed"

# Check database size
docker compose exec timescaledb psql -U pond_user -d pond_data -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database 
WHERE datname = 'pond_data';
"

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
echo "✅ Old logs cleaned"

# Docker cleanup
docker system prune -f
echo "✅ Docker resources cleaned"

echo "🎉 Maintenance completed"
EOF

chmod +x maintenance.sh
```

#### **Data Retention Policies**

```sql
-- Connect to database
-- docker compose exec timescaledb psql -U pond_user -d pond_data

-- Create retention policy for old data (example: 1 year)
SELECT add_retention_policy('pond_metrics', INTERVAL '1 year');
SELECT add_retention_policy('station_metrics', INTERVAL '1 year');

-- Check retention policies
SELECT * FROM timescaledb_information.jobs WHERE job_type = 'retention';

-- Manual cleanup of old data
DELETE FROM pond_metrics WHERE timestamp < NOW() - INTERVAL '1 year';
DELETE FROM station_metrics WHERE timestamp < NOW() - INTERVAL '1 year';
```

### **Complete System Reset**

#### **Emergency Recovery Procedure**

```bash
#!/bin/bash
echo "🚨 EMERGENCY RESET - This will delete ALL data!"
read -p "Are you sure? Type 'YES' to continue: " confirm

if [ "$confirm" = "YES" ]; then
    echo "🛑 Stopping all services..."
    docker compose down -v || docker-compose down -v
    
    echo "🗑️ Removing volumes..."
    docker volume rm pondmonitor_timescale_data pondmonitor_redis_data 2>/dev/null || true
    
    echo "🧹 Cleaning Docker resources..."
    docker system prune -af
    
    echo "🔧 Recreating configuration..."
    cp .env.testing .env
    
    echo "🚀 Starting services..."
    docker compose build || docker-compose build
    docker compose up -d || docker-compose up -d
    
    echo "✅ System reset complete!"
    echo "🌐 Access at http://localhost:5000"
else
    echo "❌ Reset cancelled"
fi
```

### **Switch Between Modes**

```bash
# Switch to testing mode
switch_to_testing() {
    echo "🧪 Switching to testing mode..."
    cp .env.testing .env
    docker compose down || docker-compose down
    docker compose up -d || docker-compose up -d
    echo "✅ Now in testing mode"
}

# Switch to production mode  
switch_to_production() {
    echo "🏭 Switching to production mode..."
    
    # Check USB device exists
    if [ ! -e "/dev/ttyUSB0" ]; then
        echo "❌ USB device /dev/ttyUSB0 not found"
        echo "Connect LoRa device and check permissions"
        return 1
    fi
    
    # Update configuration
    sed -i 's/TESTING_MODE=true/TESTING_MODE=false/' .env
    sed -i 's/SIMULATE_DATA=true/SIMULATE_DATA=false/' .env
    
    # Deploy with production overrides
    docker compose down || docker-compose down
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d || \
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    echo "✅ Now in production mode"
}
```

## 📞 Getting Additional Help

### **Collecting Debug Information**

```bash
# Create debug information script
cat > collect_debug_info.sh << 'EOF'
#!/bin/bash
echo "🔍 Collecting PondMonitor Debug Information"

DEBUG_DIR="debug_$(date +%Y%m%d_%H%M%S)"
mkdir -p $DEBUG_DIR

# System information
echo "📋 System Information" > $DEBUG_DIR/system_info.txt
uname -a >> $DEBUG_DIR/system_info.txt
docker --version >> $DEBUG_DIR/system_info.txt
docker compose version >> $DEBUG_DIR/system_info.txt 2>&1 || docker-compose version >> $DEBUG_DIR/system_info.txt 2>&1

# Configuration
echo "⚙️ Configuration" > $DEBUG_DIR/config.txt
grep -v PASSWORD .env >> $DEBUG_DIR/config.txt 2>/dev/null || echo "No .env file" >> $DEBUG_DIR/config.txt

# Service status
echo "📊 Service Status" > $DEBUG_DIR/services.txt
docker compose ps >> $DEBUG_DIR/services.txt 2>&1 || docker-compose ps >> $DEBUG_DIR/services.txt 2>&1

# Logs
echo "📝 Collecting logs..."
docker compose logs --tail=100 flask_ui > $DEBUG_DIR/flask_ui.log 2>&1 || true
docker compose logs --tail=100 lora_gateway > $DEBUG_DIR/lora_gateway.log 2>&1 || true
docker compose logs --tail=100 timescaledb > $DEBUG_DIR/timescaledb.log 2>&1 || true
docker compose logs --tail=100 redis > $DEBUG_DIR/redis.log 2>&1 || true

# API tests
echo "🔗 API Tests" > $DEBUG_DIR/api_tests.txt
curl -s http://localhost:5000/health >> $DEBUG_DIR/api_tests.txt 2>&1 || echo "Health check failed" >> $DEBUG_DIR/api_tests.txt
curl -s http://localhost:5000/api/status >> $DEBUG_DIR/api_tests.txt 2>&1 || echo "Status check failed" >> $DEBUG_DIR/api_tests.txt

# Hardware info (if in production mode)
if [ -e "/dev/ttyUSB0" ]; then
    echo "🔌 Hardware Information" > $DEBUG_DIR/hardware.txt
    ls -la /dev/ttyUSB* >> $DEBUG_DIR/hardware.txt 2>&1 || true
    lsusb >> $DEBUG_DIR/hardware.txt 2>&1 || true
fi

echo "✅ Debug information collected in $DEBUG_DIR/"
echo "📎 Include this directory when reporting issues"
EOF

chmod +x collect_debug_info.sh
```

### **When to Seek Help**

**Create a GitHub Issue if:**
- You've followed troubleshooting steps
- The issue persists across restarts
- You have debug information ready
- The issue affects core functionality

**Include in your issue:**
- System information (OS, Docker version)
- Complete error logs
- Configuration (without passwords)
- Steps to reproduce
- Debug information from script above

### **Community Resources**

- **GitHub Issues:** https://github.com/Th0masis/PondMonitor/issues
- **Documentation:** Check all files in `docs/` directory
- **Stack Overflow:** Tag questions with `pondmonitor`
- **Docker Community:** For Docker-specific issues

### **Professional Support**

For production deployments requiring guaranteed support:
- Consider commercial support options
- Engage IoT consultants familiar with the stack
- Contact TimescaleDB for database optimization
- Seek LoRa specialists for hardware issues

Remember: Most issues are configuration-related and can be resolved by carefully checking logs and following the diagnostic procedures above.