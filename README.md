<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

<img src="PondMonitor.png" width="30%" style="position: relative; top: 0; right: 0;" alt="Project Logo"/>

# PONDMONITOR

<em>Transforming Water Monitoring with Intelligent Insights</em>

<!-- BADGES -->
<img src="https://img.shields.io/github/last-commit/Th0masis/PondMonitor?style=flat&logo=git&logoColor=white&color=0080ff" alt="last-commit">
<img src="https://img.shields.io/github/languages/top/Th0masis/PondMonitor?style=flat&color=0080ff" alt="repo-top-language">
<img src="https://img.shields.io/github/languages/count/Th0masis/PondMonitor?style=flat&color=0080ff" alt="repo-language-count">

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white" alt="Python">

</div>
<br>

---

## 📄 Table of Contents

- [Overview](#-overview)
- [Getting Started](#-getting-started)
    - [Prerequisites](#-prerequisites)
    - [Installation](#-installation)
    - [Usage](#-usage)
    - [Testing](#-testing)
- [Features](#-features)
- [Project Structure](#-project-structure)
    - [Project Index](#-project-index)

---

## ✨ Overview

PondMonitor is an all-in-one IoT monitoring platform that orchestrates data collection, storage, and visualization for environmental systems. Built with containerized architecture, it ensures scalable and consistent deployment across development and production environments. The core features include:

- 🧪 **Containerized Multi-Service Architecture:** Uses Docker Compose to seamlessly integrate Flask UI, LoRa gateway, TimescaleDB, and Redis, simplifying deployment and management.
- 🚀 **Real-Time Data Collection:** Gathers live sensor data from LoRa devices, updating Redis for instant status and TimescaleDB for historical analysis.
- 📊 **Interactive Web Dashboard:** Provides dynamic visualizations of pond metrics, weather forecasts, and system diagnostics using Tailwind CSS and Highcharts.
- 🔧 **Robust Diagnostics & Monitoring:** Offers real-time hardware health status and troubleshooting tools to maintain system reliability.
- 🌦️ **Comprehensive Weather Insights:** Displays detailed meteorological data with interactive charts for better environmental understanding.

---

## 📌 Features

|      | Component       | Details                                                                                     |
| :--- | :-------------- | :------------------------------------------------------------------------------------------ |
| ⚙️  | **Architecture**  | <ul><li>Microservices-based design with separate components for data collection, processing, and visualization</li><li>Uses Docker Compose for orchestration</li></ul> |
| 🔩 | **Code Quality**  | <ul><li>Python code adheres to PEP 8 standards</li><li>Includes modular functions and classes for maintainability</li></ul> |
| 📄 | **Documentation** | <ul><li>Basic README with project overview and setup instructions</li><li>Inline code comments present but limited</li></ul> |
| 🔌 | **Integrations**  | <ul><li>Docker for containerization</li><li>Python scripts for data processing</li><li>HTML for frontend visualization</li></ul> |
| 🧩 | **Modularity**    | <ul><li>Separate modules for sensor data collection, data storage, and web interface</li><li>Docker images for each component</li></ul> |
| 🧪 | **Testing**       | <ul><li>Minimal testing; no formal test suite detected</li><li>Potential for unit tests in Python modules</li></ul> |
| ⚡️  | **Performance**   | <ul><li>Lightweight Python scripts optimized for low-latency data handling</li><li>Docker containers configured for efficient resource use</li></ul> |
| 🛡️ | **Security**      | <ul><li>Basic security measures; no authentication or encryption implemented</li><li>Potential vulnerabilities in exposed web interface</li></ul> |
| 📦 | **Dependencies**  | <ul><li>Python standard libraries</li><li>HTML and Dockerfile dependencies</li><li>Uses Docker Compose for dependency management</li></ul> |

---

## 📁 Project Structure

```sh
└── PondMonitor/
    ├── LoraGeteway.py
    ├── UI
    │   ├── app.py
    │   ├── static
    │   └── templates
    ├── dockercompose
    ├── dockerfile
    └── dockerfile.gateway
```

---

### 📑 Project Index

<details open>
	<summary><b><code>PONDMONITOR/</code></b></summary>
	<!-- __root__ Submodule -->
	<details>
		<summary><b>__root__</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ __root__</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/dockercompose'>dockercompose</a></b></td>
					<td style='padding: 8px;'>- Defines the Docker Compose configuration orchestrating the applications multi-service environment<br>- It manages containerized components including the Flask UI, LoRa gateway, TimescaleDB, and Redis, ensuring seamless integration and communication among data storage, processing, and user interface layers within the overall architecture<br>- This setup facilitates scalable deployment and efficient data handling for the system.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/dockerfile'>dockerfile</a></b></td>
					<td style='padding: 8px;'>- Defines the Docker environment for deploying the Flask UI, ensuring consistent setup and execution<br>- It encapsulates the application’s dependencies and runtime configuration, facilitating streamlined development, testing, and deployment within containerized infrastructure<br>- This setup integrates the user interface component into the broader architecture, enabling seamless interaction with backend services and supporting scalable, isolated deployment.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/LoraGeteway.py'>LoraGeteway.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates real-time collection and storage of environmental sensor data from LoRa devices<br>- It reads serial data, processes metrics such as temperature, battery, and solar voltage, and updates both a Redis cache for live status and a TimescaleDB database for historical analysis<br>- This component is central to maintaining an up-to-date and historical record of station metrics within the overall system architecture.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/dockerfile.gateway'>dockerfile.gateway</a></b></td>
					<td style='padding: 8px;'>- Defines the Docker configuration for deploying the Lora Gateway application, ensuring a lightweight, consistent environment for running the Python-based gateway service<br>- It manages dependencies and sets the entry point, facilitating seamless containerized deployment within the overall architecture, which integrates data collection, processing, and communication for IoT network management.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- UI Submodule -->
	<details>
		<summary><b>UI</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ UI</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/UI/app.py'>app.py</a></b></td>
					<td style='padding: 8px;'>- Provides a Flask-based web API and frontend for monitoring and visualizing pond and environmental data<br>- Integrates real-time status updates, historical pond metrics, weather forecasts, and sensor diagnostics, enabling comprehensive oversight of pond conditions, weather patterns, and system health within the overall monitoring architecture.</td>
				</tr>
			</table>
			<!-- templates Submodule -->
			<details>
				<summary><b>templates</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ UI.templates</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/UI/templates/diagnostics.html'>diagnostics.html</a></b></td>
							<td style='padding: 8px;'>- Provides a user interface for real-time diagnostics and status monitoring of station hardware<br>- Displays live data on temperature, battery voltage, connection status, and recent activity, enabling quick assessment of system health and operational conditions through dynamic charts and status cards<br>- Facilitates proactive maintenance and troubleshooting within the overall system architecture.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/UI/templates/weather.html'>weather.html</a></b></td>
							<td style='padding: 8px;'>- Provides a weather forecast interface combining a dynamic short-term meteogram visualization with detailed long-term daily forecast cards<br>- It fetches real-time meteorological data, displays temperature, precipitation, wind, and pressure trends, and enhances user experience with interactive charts and weather icons, supporting comprehensive weather insights within the applications architecture.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/UI/templates/dashboard.html'>dashboard.html</a></b></td>
							<td style='padding: 8px;'>- Provides an interactive dashboard interface for visualizing water level and outflow data over customizable time ranges<br>- Facilitates quick data exploration through preset time buttons and manual date selection, dynamically fetching and rendering real-time charts to support monitoring and analysis within the overall system architecture.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/Th0masis/PondMonitor/blob/master/UI/templates/base.html'>base.html</a></b></td>
							<td style='padding: 8px;'>- Defines the foundational HTML structure and layout for the applications user interface, integrating Tailwind CSS for styling and Highcharts for dynamic data visualization<br>- Facilitates consistent navigation and visual branding across pages, serving as the primary template that ensures a cohesive look and feel within the overall architecture.</td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
</details>

---

## 🚀 Getting Started

### 📋 Prerequisites

This project requires the following dependencies:

- **Programming Language:** HTML

### ⚙️ Installation

Build PondMonitor from the source and install dependencies:

1. **Clone the repository:**

    ```sh
    git clone https://github.com/Th0masis/PondMonitor
    ```

2. **Navigate to the project directory:**

    ```sh
    cd PondMonitor
    ```

3. **Install the dependencies:**

echo 'INSERT-INSTALL-COMMAND-HERE'

### 💻 Usage

Run the project with:

```sh
docker compose build --no-cache
docker compose up -d
```

### 🧪 Testing

Pondmonitor uses the {__test_framework__} test framework. Run the test suite with:

echo 'INSERT-TEST-COMMAND-HERE'

---

<div align="left"><a href="#top">⬆ Return</a></div>

---
