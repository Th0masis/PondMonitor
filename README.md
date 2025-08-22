# PondMonitor

**Advanced IoT Monitoring System for Environmental Data Collection**

[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status Active](https://img.shields.io/badge/Status-Active-success)](https://github.com/Th0masis/PondMonitor)

> **PondMonitor** is a comprehensive IoT platform for environmental monitoring using LoRa wireless sensors, real-time web dashboards, weather integration, and time-series data analysis.

## 🚀 Quick Start

Get up and running in under 5 minutes:

```bash
# Clone and start in testing mode (no hardware required)
git clone https://github.com/Th0masis/PondMonitor.git
cd PondMonitor
chmod +x start-testing.sh
./start-testing.sh

# Access at http://localhost:5000
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

## 🏃‍♂️ Getting Started

1. **For testing** (no hardware): [Quick Start Guide](docs/QUICKSTART.md)
2. **For production** (with sensors): [Deployment Guide](docs/DEPLOYMENT.md) 
3. **For development**: [Development Setup](docs/DEVELOPMENT.md)

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