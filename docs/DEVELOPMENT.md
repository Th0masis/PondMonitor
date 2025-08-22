# PondMonitor Development Guide

## 👨‍💻 Development Environment Setup

Complete guide for setting up PondMonitor for development, testing, and contribution.

## 🚀 Quick Development Setup

```bash
# Clone the repository
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Start development environment
make quick-start
# or
chmod +x scripts/start-testing.sh
./scripts/start-testing.sh
```

## 🧪 Testing

PondMonitor includes comprehensive testing infrastructure with unit tests, integration tests, and automated testing scripts.

### **Unit Tests with pytest**

```bash
# Basic test run
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_service.py -v

# Run specific test class
python -m pytest tests/test_service.py::TestPondMonitorConfig -v

# Run specific test method
python -m pytest tests/test_service.py::TestPondMonitorConfig::test_config_initialization -v
```

### **Using Make Commands**

```bash
# Run all tests
make test

# Start testing environment
make test-mode

# View testing logs
make test-logs

# Check test status
make test-status
```

### **Testing Scripts**

#### **Automated Testing Environment Setup**
```bash
# Complete testing environment setup
chmod +x scripts/start-testing.sh
./scripts/start-testing.sh

# Features:
# - Checks Docker availability
# - Creates proper .env file for testing
# - Builds and starts all services
# - Verifies service health
# - Shows access URLs and useful commands
```

#### **Comprehensive Test Suite**
```bash
# Run full test suite with integration tests
chmod +x scripts/test_week1.sh
./scripts/test_week1.sh

# Includes:
# - Unit tests with coverage
# - Configuration validation
# - Database connection tests
# - Weather service integration tests
```

### **Test Coverage**

View coverage report after running tests with coverage:
```bash
# Generate HTML coverage report
python -m pytest tests/ -v --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### **Testing Configuration**

Testing uses the `.env.testing` file which provides:
- **Testing Mode**: `TESTING_MODE=true`
- **Simulated Data**: `SIMULATE_DATA=true`
- **Localhost Services**: Uses localhost instead of Docker service names
- **Test Secret Key**: Safe for testing environment
- **Disabled Hardware**: No USB device required

```bash
# Use testing configuration
cp .env.testing .env

# Verify testing mode
grep -E "TESTING_MODE|SIMULATE_DATA" .env
# Should show: TESTING_MODE=true, SIMULATE_DATA=true
```

## 🔧 Development Workflow

### **1. Environment Setup**

```bash
# Set up development environment
make dev
# or
make test-mode

# Verify services are running
make health
```

### **2. Development Commands**

```bash
# View logs during development
make test-logs

# Check database contents
make show-data

# Connect to database shell
make shell-db

# Connect to Redis shell
make shell-redis

# Show recent data
make show-redis
```

### **3. Code Quality**

```bash
# Run linting
make lint
# or
flake8 *.py UI/ services/ tests/

# Format code
make format
# or
black *.py UI/ services/ tests/

# Type checking
mypy *.py services/
```

### **4. Testing Cycle**

```bash
# 1. Make changes to code
# 2. Run tests
make test

# 3. Check specific functionality
python -m pytest tests/test_service.py::TestExportService -v

# 4. Verify integration
./scripts/test_week1.sh

# 5. Check coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 🐳 Docker Development

### **Development with Docker**

```bash
# Build images
make build

# Start services
make up

# View logs
make logs

# Stop services
make down
```

### **Testing Mode vs Production Mode**

```bash
# Switch to testing mode (no hardware required)
make test-mode

# Switch to production mode (USB device required)
make prod-mode

# Check current mode
grep -E "TESTING_MODE|SIMULATE_DATA" .env
```

### **Docker Troubleshooting**

```bash
# Debug information
make debug

# Clean up Docker resources
make clean

# Reset database (WARNING: deletes all data)
make reset-db
```

## 🗄️ Database Development

### **Database Commands**

```bash
# Connect to database
make shell-db

# View recent sensor data
make show-data

# Backup database
make backup

# Reset database (development only)
make reset-db
```

### **Useful SQL Queries**

```sql
-- Connect to database first: make shell-db

-- View all tables
\dt

-- Recent sensor data
SELECT timestamp, temperature_c, battery_v, signal_dbm 
FROM station_metrics 
ORDER BY timestamp DESC 
LIMIT 10;

-- Data volume by day
SELECT DATE(timestamp) as date, COUNT(*) as records
FROM station_metrics 
GROUP BY DATE(timestamp) 
ORDER BY date DESC;

-- System health
SELECT 
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_data,
    MAX(timestamp) as latest_data
FROM station_metrics;
```

## 📁 Project Structure

```
PondMonitor/
├── 📄 config.py                    # Configuration system
├── 📄 database.py                  # Database service layer
├── 📄 utils.py                     # Utilities and validation
├── 📄 LoraGateway.py               # LoRa communication
├── 🗂️ UI/                          # Flask web application
├── 🗂️ services/                    # Service modules
│   ├── 📄 export_service.py        # Data export functionality
│   ├── 📄 weather_service.py       # Weather API integration
│   └── 📄 alert_service.py         # Alert system (future)
├── 🗂️ tests/                       # Test suite
│   ├── 📄 test_config.py           # Configuration tests
│   ├── 📄 test_service.py          # Service tests
│   └── 📄 test_database.py         # Database tests
├── 🗂️ scripts/                     # Automation scripts
│   ├── 📄 start-testing.sh         # Testing environment setup
│   ├── 📄 test_week1.sh            # Comprehensive test suite
│   └── 📄 makefile                 # Make commands
├── 🗂️ docs/                        # Documentation
└── 📄 .env.testing                 # Testing configuration
```

## 🔀 Git Workflow

### **Development Branch Strategy**

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
make test

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### **Before Submitting PR**

```bash
# Run full test suite
./scripts/test_week1.sh

# Check code quality
make lint
make format

# Verify tests pass
make test

# Test both modes
make test-mode
make health

make prod-mode  # (if you have hardware)
make health
```

## 🐛 Debugging

### **Common Debug Commands**

```bash
# Show debugging information
make debug

# Check service health
make health

# View specific service logs
docker compose logs -f flask_ui
docker compose logs -f lora_gateway
docker compose logs -f timescaledb

# Test API endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/status
```

### **Test Debugging**

```bash
# Run tests with verbose output
python -m pytest tests/ -v -s

# Run single test with debugging
python -m pytest tests/test_service.py::TestPondMonitorConfig::test_config_initialization -v -s

# Debug failing test
python -m pytest tests/test_service.py::TestExportService::test_csv_export -v -s --pdb
```

## 📊 Performance Testing

### **Load Testing**

```bash
# Test API endpoints with curl
for i in {1..10}; do
  curl -s http://localhost:5000/api/status &
done
wait

# Monitor resource usage
docker stats

# Check database performance
make shell-db
# Then run: \timing on
# SELECT COUNT(*) FROM station_metrics;
```

### **Memory and Storage**

```bash
# Check Docker resource usage
docker system df

# Check database size
make shell-db
# SELECT pg_size_pretty(pg_database_size('pond_data'));

# Monitor logs size
du -sh logs/
```

## 🔒 Security Testing

### **Basic Security Checks**

```bash
# Check for secrets in logs
grep -r "password\|secret\|key" logs/ || echo "No secrets found in logs"

# Verify test configuration doesn't expose secrets
grep -E "secret|password|key" .env.testing

# Check container security
docker scout quickview  # if available
```

## 🚀 Deployment Testing

### **Pre-deployment Checklist**

```bash
# 1. All tests pass
make test
./scripts/test_week1.sh

# 2. Code quality checks
make lint
make format

# 3. Security review
# - No hardcoded secrets
# - Proper environment variables
# - Updated dependencies

# 4. Documentation updated
# - API changes documented
# - README updated if needed
# - Changelog updated

# 5. Database migrations tested
# - Schema changes tested
# - Backup/restore procedures verified
```

## 📚 Resources

### **Documentation**
- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Deployment Guide](DEPLOYMENT.md) - Production setup
- [API Reference](API.md) - Complete API documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

### **External Dependencies**
- [pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Docker Compose](https://docs.docker.com/compose/)
- [TimescaleDB](https://docs.timescale.com/)

## 💡 Tips & Best Practices

### **Testing Tips**
- Always run tests before committing
- Use descriptive test names
- Test both success and failure scenarios
- Mock external dependencies
- Use fixtures for common test data

### **Development Tips**
- Use testing mode for development (no hardware required)
- Monitor logs during development: `make test-logs`
- Use `make debug` for troubleshooting
- Keep `.env.testing` as template, customize `.env` for local needs

### **Performance Tips**
- Use `make show-data` to verify data generation
- Monitor Docker stats during development
- Use database indices for query performance
- Cache frequently accessed data in Redis

---

## 🤝 Contributing

We welcome contributions! To get started:

1. **Fork the repository**
2. **Set up development environment**: `make quick-start`
3. **Create feature branch**: `git checkout -b feature/name`
4. **Make changes and test**: `make test`
5. **Submit pull request**

For questions or help, create an issue or start a discussion on GitHub.