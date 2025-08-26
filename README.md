# PondMonitor

**Advanced IoT Monitoring System for Environmental Data Collection**

[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status Active](https://img.shields.io/badge/Status-Active-success)](https://github.com/Th0masis/PondMonitor)

> **PondMonitor** is a comprehensive IoT platform for environmental monitoring using LoRa wireless sensors, real-time web dashboards, weather integration, and time-series data analysis.

## 📚 **Project Disclaimer**

> **🎓 Educational Project**: This project serves as a learning platform to explore modern development practices, IoT technologies, and software engineering processes. It was developed in collaboration with Claude AI to demonstrate best practices in:
> 
> - **Modern Python Architecture** - Modular design patterns and service abstractions
> - **CI/CD Pipeline Development** - GitHub Actions workflows and automation
> - **Docker Containerization** - Multi-service orchestration and deployment
> - **IoT Integration** - LoRa wireless communication and sensor data processing
> - **Testing Infrastructure** - Comprehensive test suites and quality assurance
> 
> The project combines practical IoT monitoring capabilities with educational value for developers learning these technologies and methodologies.

## 🚀 Quick Start

Choose your installation method:

### **👥 For End Users (Ready-to-Use Package)**

**📦 Option 1: Download Pre-Built Package** *(Recommended)*
```bash
# Download the latest stable release
wget https://github.com/Th0masis/PondMonitor/releases/latest/download/pondmonitor-latest.zip

# Extract and run (Windows/Linux/Mac)
unzip pondmonitor-latest.zip
cd pondmonitor-*/
./start.sh    # Linux/Mac
# or
start.bat     # Windows

# Open your browser to: http://localhost:5005
```

**🐳 Option 2: Docker (If you have Docker installed)**
```bash
# Download and run with Docker
curl -L https://github.com/Th0masis/PondMonitor/releases/latest/download/pondmonitor-latest.tar.gz | tar -xz
cd pondmonitor-*/
docker compose up -d

# Access at http://localhost:5005
```

**🌐 Option 3: Try Demo Online**
Visit **[demo.pondmonitor.example](http://demo.pondmonitor.example)** to try the system without installation.

---

### **📱 How to Use PondMonitor (End User Guide)**

Once running, access **http://localhost:5005** in your browser:

#### **🏠 Dashboard Page**
- **View real-time data**: Water level and outflow measurements
- **Time ranges**: Switch between 24h, 3 days, 1 week, 1 month views
- **Print reports**: Click "Tisknout grafy" for professional PDF reports
- **Quick actions**: Access advanced export features

#### **🌤️ Weather Page**
- **Current conditions**: Temperature, humidity, pressure from weather station
- **48-hour forecast**: Detailed hourly weather predictions
- **7-day outlook**: Weekly weather summary
- **Weather statistics**: Historical weather data analysis

#### **🔧 Diagnostics Page**
- **System health**: Overall system status and performance
- **Station status**: Battery level, signal strength, connectivity
- **System logs**: View recent system events and errors
- **Diagnostic tools**: Test connection, export diagnostics, restart device

#### **📊 Export Page**
- **Date range selection**: Choose specific time periods for data export
- **Data types**: Select pond data, station diagnostics, or weather data
- **Export formats**: Excel (with charts), CSV, or JSON formats
- **Advanced filters**: Filter by temperature, battery, or signal ranges
- **Real-time preview**: See export size and estimated processing time

#### **⚙️ Quick Tips**
- **🔄 Auto-refresh**: Data updates every 30 seconds automatically
- **📱 Mobile friendly**: Works perfectly on phones and tablets  
- **🖨️ Print ready**: Professional reports optimized for A4 printing
- **🌓 Dark/Light themes**: Toggle theme in the navigation menu
- **⏰ Czech localization**: Dates, times, and messages in Czech language

### **🧑‍💻 For Developers (Full Repository)**
Clone the complete repository for development and contributions:

```bash
# Clone full repository (includes tests, CI/CD, dev tools)
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor

# Start with Docker (recommended)
docker compose -f docker/docker-compose.yml --env-file .env up

# Or use testing script
chmod +x scripts/start-testing.sh
./scripts/start-testing.sh

# Access at http://localhost:5005
```

## ✨ Key Features

- **📊 Real-time Dashboard** - Live water monitoring with interactive charts
- **🌦️ Weather Integration** - Meteorological data and forecasts
- **📡 LoRa Communication** - Long-range wireless sensor networks
- **🏥 System Diagnostics** - Hardware health and battery monitoring
- **📱 Mobile Responsive** - Works on all devices with dark/light themes
- **🐳 Docker Ready** - Complete containerized deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  🌐 Web Interface (Flask + Highcharts + Responsive CSS)    │
│  📊 API Layer (REST JSON endpoints)                        │
│  ⚡ Redis Cache    │  📡 LoRa Gateway    │  🌦️ Weather API │
│  🗄️ TimescaleDB (Time-series PostgreSQL)                  │
│  🔌 Hardware Interface (LoRa/Serial communication)         │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

PondMonitor includes comprehensive testing infrastructure for development and CI/CD.

### **Quick Test Commands**

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=html

# Use Make commands
make test          # Run pytest tests
make test-mode     # Start testing environment
make quick-start   # Build and start in testing mode
```

### **Testing Scripts**

```bash
# Automated testing environment setup
./scripts/start-testing.sh

# Comprehensive test suite with integration tests
./scripts/test_week1.sh
```

### **Testing Features**
- **Unit Tests**: pytest with comprehensive coverage
- **Integration Tests**: Database, weather API, export services
- **Simulated Data**: Realistic sensor data without hardware
- **Docker Testing**: Complete containerized test environment
- **CI/CD Ready**: Automated testing workflows

See [Development Guide](docs/DEVELOPMENT.md) for complete testing documentation.

## 🆕 **Recent Updates** 
*Latest: August 26, 2025*

### **✅ Application Stability Fixes**
- **Fixed Flask startup issues** - Resolved route registration conflicts preventing application launch
- **Restored system messages** - Diagnostics page now displays system events and logs properly  
- **Implemented diagnostic actions** - All diagnostic buttons (connection test, export, device reset) now functional

### **🚀 Enhanced User Experience**
- **Professional print functionality** - Dashboard charts now print in A4 landscape with statistics and metadata
- **Optimized export strategy** - Streamlined button placement across pages for better user flow
- **Complete API coverage** - Added 7 new endpoints for comprehensive diagnostic functionality

### **🔧 Technical Improvements**
- **Enhanced error handling** - Comprehensive coverage across all endpoints with proper HTTP status codes
- **Improved logging** - System events tracking with multiple severity levels (INFO, WARNING, ERROR)
- **Production readiness** - All new features include proper error handling and monitoring integration

*See [**CHANGELOG.md**](CHANGELOG.md) for complete development history and detailed technical changes.*

## 📖 Documentation

**Complete documentation is available in the [`docs/`](docs/) directory:**

| Document | Description |
|----------|-------------|
| [📖 Overview](docs/OVERVIEW.md) | Architecture, features, and system design |
| [🚀 Quick Start](docs/QUICKSTART.md) | 5-minute setup guide |
| [🏭 Deployment](docs/DEPLOYMENT.md) | Production setup with real hardware |
| [👨‍💻 Development](docs/DEVELOPMENT.md) | Development environment and workflows |
| [📊 API Reference](docs/API.md) | Complete REST API documentation |
| [📱 User Guide](docs/USER_GUIDE.md) | Web interface usage guide |
| [🛠️ Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |
| [⚒️ Makefile Commands](docs/MAKEFILE.md) | Build automation reference |
| [🔄 CI/CD Pipeline](docs/CI_CD.md) | GitHub Actions workflows and automation |
| [📝 **Changelog**](CHANGELOG.md) | **Development roadmap and major changes** |

## 🎯 Use Cases

- **Environmental Research** - Water quality and ecosystem monitoring
- **Agriculture** - Irrigation and soil monitoring systems  
- **Infrastructure** - Remote facility monitoring
- **IoT Development** - Sensor network prototyping

## 💡 Technologies

- **Backend**: Python 3.11+, Flask, TimescaleDB, Redis
- **Frontend**: HTML5, CSS3, JavaScript, Highcharts
- **Hardware**: LoRa wireless, USB/Serial communication
- **Deployment**: Docker Compose, automated builds
- **Testing**: pytest, simulated data generation

## 📊 Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)

### Weather Integration  
![Weather](docs/images/weather.png)

### System Diagnostics
![Diagnostics](docs/images/diagnostics.png)

## 🔧 Quick Commands

### Docker Commands
```bash
# Start services (recommended method)
docker compose -f docker/docker-compose.yml --env-file .env up

# Start in background
docker compose -f docker/docker-compose.yml --env-file .env up -d

# Stop services
docker compose -f docker/docker-compose.yml down

# View logs
docker compose -f docker/docker-compose.yml logs -f
```

### Make Commands  
```bash
# Development mode (testing with simulated data)
make quick-start

# Production mode (with real LoRa hardware)  
make prod-mode

# View logs
make logs

# Health check
make health

# Clean up
make clean
```

### Important Notes
- **Port Configuration**: The application runs on http://localhost:5005 (configured in `.env` file)
- **Environment File**: Always include `--env-file .env` when using `-f docker/docker-compose.yml`
- **Why `--env-file`?**: When using `-f` with a path, Docker Compose doesn't automatically find the `.env` file

## 🏃‍♂️ Getting Started

### **📥 What Should I Download?**

| User Type | Method | What You Get | Best For |
|-----------|--------|--------------|----------|
| **End Users** | [📦 Release Download](https://github.com/Th0masis/PondMonitor/releases/latest) | Core app + Docker files only | Production deployment |
| **Developers** | `git clone` | Everything (tests, CI/CD, dev tools) | Contributing, customizing |

### **📋 Setup Guides**

1. **🎯 Testing** (no hardware): [Quick Start Guide](docs/QUICKSTART.md)
2. **🏭 Production** (with sensors): [Deployment Guide](docs/DEPLOYMENT.md) 
3. **🧑‍💻 Development**: [Development Setup](docs/DEVELOPMENT.md)

## 🐛 Issues & Support

- **Documentation**: Check the [docs/](docs/) directory first
- **Common Issues**: See [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- **Bug Reports**: [GitHub Issues](https://github.com/Th0masis/PondMonitor/issues)
- **Questions**: [GitHub Discussions](https://github.com/Th0masis/PondMonitor/discussions)

## 🤝 Contributing

We welcome contributions! See our [Development Guide](docs/DEVELOPMENT.md) for:
- Development setup and workflows
- Code standards and testing
- Pull request process

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [TimescaleDB](https://timescale.com) - Time-series database
- [met.no](https://met.no) - Weather data API
- [Highcharts](https://highcharts.com) - Data visualization
- [Flask](https://flask.palletsprojects.com) - Web framework

---

<div align="center">

**Made with ❤️ for environmental monitoring**

[⭐ Star this repository](https://github.com/Th0masis/PondMonitor) if you find it useful!

</div>