# PondMonitor Makefile Commands Reference

## ⚒️ Make Commands Reference

The PondMonitor project includes a comprehensive Makefile with automated commands for development, testing, and deployment workflows.

## 🚀 Getting Started

```bash
# Show all available commands
make help

# Quick start (build and start in testing mode)
make quick-start
```

## 📋 Command Categories

### **🏗️ Build & Setup Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make build` | Build Docker images | `make build` |
| `make up` | Start all services | `make up` |
| `make down` | Stop all services | `make down` |
| `make clean` | Clean up Docker resources | `make clean` |

### **🧪 Testing Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make test` | Run pytest unit tests | `make test` |
| `make test-mode` | Start in testing mode (no USB required) | `make test-mode` |
| `make test-logs` | Show logs for testing services | `make test-logs` |
| `make test-status` | Check status of testing services | `make test-status` |
| `make dev` | Alias for test-mode | `make dev` |
| `make quick-start` | Build and start in testing mode | `make quick-start` |

### **🏭 Production Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make prod-mode` | Switch to production mode (USB required) | `make prod-mode` |

### **📊 Monitoring Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make logs` | Show logs for all services | `make logs` |
| `make health` | Check health of all services | `make health` |
| `make monitoring` | Start with monitoring stack | `make monitoring` |
| `make debug` | Show debugging information | `make debug` |

### **🗄️ Database Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make shell-db` | Connect to database shell | `make shell-db` |
| `make show-data` | Show recent data from database | `make show-data` |
| `make backup` | Backup database | `make backup` |
| `make reset-db` | Reset database (⚠️ deletes all data) | `make reset-db` |

### **🔍 Redis Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make shell-redis` | Connect to Redis shell | `make shell-redis` |
| `make show-redis` | Show current Redis data | `make show-redis` |

### **🔧 Code Quality Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make lint` | Run linting (flake8, mypy) | `make lint` |
| `make format` | Format code (black) | `make format` |

## 🛠️ Detailed Command Usage

### **Development Workflow**

```bash
# 1. Start development environment
make quick-start

# 2. View logs during development
make test-logs

# 3. Run tests
make test

# 4. Check service health
make health

# 5. View recent data
make show-data
```

### **Testing Workflow**

```bash
# Start testing environment
make test-mode

# Check everything is working
make test-status
make health

# Run unit tests
make test

# View test logs
make test-logs

# Check generated data
make show-data
```

### **Production Workflow**

```bash
# Switch to production mode (requires USB device)
make prod-mode

# Monitor services
make logs

# Check health
make health

# Create backup
make backup
```

### **Debugging Workflow**

```bash
# Show comprehensive debugging info
make debug

# Check individual services
make health
make show-data
make show-redis

# View specific logs
docker compose logs flask_ui
docker compose logs lora_gateway
```

## 🔍 Command Details

### **make test-mode**
Starts PondMonitor in testing mode with simulated data:
- Copies `.env.testing` to `.env`
- Starts Docker Compose services
- No USB hardware required
- Generates realistic simulated sensor data
- Displays helpful information and URLs

### **make prod-mode** 
Switches to production mode with real hardware:
- Creates production configuration
- Requires USB LoRa device connected
- Uses Docker Compose with production overrides
- Disables simulation and testing flags

### **make health**
Performs comprehensive health checks:
- Tests Flask API endpoints
- Shows Docker container status
- Verifies service connectivity
- Displays JSON health response

### **make show-data**
Displays recent sensor data from database:
- Shows last 10 station metrics (temperature, battery, signal)
- Shows last 10 pond metrics (water level, outflow)
- Useful for verifying data collection

### **make debug**
Comprehensive debugging information:
- Docker Compose command being used
- Container status and health
- Docker images and volumes
- Environment variables (sanitized)
- Recent service logs

### **make clean**
Cleanup Docker resources:
- Stops all containers
- Removes containers and networks
- Prunes unused Docker system resources
- Keeps data volumes intact

### **make reset-db**
⚠️ **Destructive Operation** - Resets database:
- Confirms before proceeding
- Stops all services
- Removes data volumes
- Deletes ALL collected data
- Use only for development/testing

## 🐳 Docker Compose Detection

The Makefile automatically detects your Docker Compose installation:

```bash
# Modern Docker Compose (plugin)
DOCKER_COMPOSE := docker compose

# Legacy Docker Compose (standalone)
DOCKER_COMPOSE := docker-compose
```

You can see which command is being used:
```bash
make help
# Shows: Using: docker compose
```

## 📊 Database Operations

### **Interactive Database Shell**
```bash
make shell-db
# Opens: psql -U pond_user -d pond_data

# Useful SQL commands:
\dt                          # List tables
\d station_metrics          # Describe table
SELECT COUNT(*) FROM station_metrics;
```

### **Data Inspection**
```bash
# Recent sensor data
make show-data

# Current Redis cache
make show-redis

# Database backup
make backup
# Creates: backups/pond_data_YYYYMMDD_HHMMSS.sql
```

## 🔧 Customization

### **Environment Variables**
The Makefile respects these environment variables:

```bash
# Custom serial port
export SERIAL_PORT=/dev/ttyUSB1
make prod-mode

# Custom Docker Compose command
export DOCKER_COMPOSE="docker compose"
make up
```

### **Adding Custom Commands**
Add to `scripts/makefile`:

```makefile
my-custom-command: ## Description of custom command
	@echo "Running custom command"
	# Your commands here
```

## 🚨 Troubleshooting Make Commands

### **Common Issues**

**Command not found:**
```bash
# Check if make is installed
which make

# Install make (Ubuntu/Debian)
sudo apt install build-essential

# Install make (macOS)
xcode-select --install
```

**Docker Compose issues:**
```bash
# Check Docker Compose
make help
# Shows which command is detected

# Manual override
DOCKER_COMPOSE="docker-compose" make up
```

**Permission errors:**
```bash
# Fix script permissions
chmod +x scripts/start-testing.sh
chmod +x scripts/test_week1.sh

# Fix Docker permissions
sudo usermod -aG docker $USER
# Log out and back in
```

### **Debugging Make Commands**

```bash
# Verbose output
make -n test-mode    # Dry run (show commands without executing)
make -d test-mode    # Debug mode (show make decisions)

# Check Makefile syntax
make -f scripts/makefile --dry-run
```

## 📚 Integration with Other Tools

### **IDE Integration**
Many IDEs support Make integration:

**VS Code:**
- Install "Makefile Tools" extension
- Commands appear in Command Palette

**JetBrains IDEs:**
- Built-in Make support
- Run configurations for Make targets

### **CI/CD Integration**
Use in GitHub Actions, GitLab CI, etc.:

```yaml
# Example GitHub Actions step
- name: Run tests
  run: make test

- name: Build and test
  run: make quick-start && make health
```

## 💡 Tips & Best Practices

### **Development Tips**
- Use `make quick-start` for fastest setup
- Keep `make test-logs` running during development
- Use `make health` to verify everything is working
- Run `make test` before committing changes

### **Production Tips**  
- Always backup before production changes: `make backup`
- Use `make debug` for troubleshooting
- Monitor with `make logs` in production
- Test production mode in staging first

### **Maintenance Tips**
- Regular cleanup: `make clean`
- Monitor disk usage: `docker system df`
- Update dependencies regularly
- Keep database backups: `make backup`

---

For complete development workflows, see [DEVELOPMENT.md](DEVELOPMENT.md).
For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).