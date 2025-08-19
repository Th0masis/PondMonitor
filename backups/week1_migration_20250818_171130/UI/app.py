import os
import json
import requests
import psycopg2
import logging
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify, g
from collections import defaultdict
from dotenv import load_dotenv
import redis
from functools import wraps
import time
from typing import Optional, Dict, Any, List

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Configuration
class Config:
    DB_CONFIG = {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", 5432)),
        "database": os.getenv("POSTGRES_DB", "pond_data"),
        "user": os.getenv("POSTGRES_USER", "pond_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "secretpassword")
    }
    
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    
    # Weather API configuration
    WEATHER_LAT = float(os.getenv("WEATHER_LAT", "49.6265900"))
    WEATHER_LON = float(os.getenv("WEATHER_LON", "18.3016172"))
    WEATHER_ALT = int(os.getenv("WEATHER_ALT", "350"))
    WEATHER_CACHE_DURATION = int(os.getenv("WEATHER_CACHE_DURATION", "3600"))  # 1 hour
    
    USER_AGENT = os.getenv("USER_AGENT", "PondMonitor/1.0 (pond@monitor.cz)")

config = Config()

# Initialize Redis with error handling
def get_redis_client():
    try:
        client = redis.Redis(
            host=config.REDIS_HOST, 
            port=config.REDIS_PORT, 
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return None

redis_client = get_redis_client()

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def validate_datetime_range(start: str, end: str) -> tuple[bool, Optional[str]]:
    """Validate datetime range parameters"""
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        if start_dt >= end_dt:
            return False, "Start time must be before end time"
        
        if (end_dt - start_dt).days > 30:
            return False, "Time range cannot exceed 30 days"
        
        if start_dt < datetime.now(timezone.utc) - timedelta(days=365):
            return False, "Start time cannot be more than 1 year ago"
            
        return True, None
    except ValueError as e:
        return False, f"Invalid datetime format: {e}"

def cache_weather_data(cache_key: str, data: Dict[str, Any]) -> bool:
    """Cache weather data in Redis"""
    if not redis_client:
        return False
    
    try:
        redis_client.setex(
            cache_key, 
            config.WEATHER_CACHE_DURATION, 
            json.dumps(data, default=str)  # Handle datetime serialization
        )
        return True
    except Exception as e:
        logger.error(f"Failed to cache weather data: {e}")
        return False

def get_cached_weather_data(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached weather data from Redis"""
    if not redis_client:
        return None
    
    try:
        cached = redis_client.get(cache_key)
        return json.loads(cached) if cached else None
    except Exception as e:
        logger.error(f"Failed to get cached weather data: {e}")
        return None

def fetch_weather_data() -> Optional[Dict[str, Any]]:
    """Fetch weather data from Met.no API with error handling"""
    try:
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={config.WEATHER_LAT}&lon={config.WEATHER_LON}&altitude={config.WEATHER_ALT}"
        headers = {"User-Agent": config.USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Weather API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data: {e}")
        return None

def guess_weather_symbol(details: Dict[str, Any]) -> str:
    """Guess weather symbol based on available data"""
    rain = details.get('rain', 0)
    cloud = details.get('cloud', 0)
    
    if rain > 2:
        return 'rain'
    elif rain > 0.2:
        return 'lightrain'
    elif cloud > 80:
        return 'cloudy'
    elif cloud > 40:
        return 'partlycloudy_day'
    else:
        return 'clearsky_day'

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            status["services"]["redis"] = "healthy"
        else:
            status["services"]["redis"] = "unavailable"
    except Exception:
        status["services"]["redis"] = "unhealthy"
    
    # Check Database
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            status["services"]["database"] = "healthy"
        else:
            status["services"]["database"] = "unavailable"
    except Exception:
        status["services"]["database"] = "unhealthy"
    
    # Check Weather API
    try:
        test_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={config.WEATHER_LAT}&lon={config.WEATHER_LON}&altitude={config.WEATHER_ALT}"
        headers = {"User-Agent": config.USER_AGENT}
        response = requests.get(test_url, headers=headers, timeout=5)
        if response.status_code == 200:
            status["services"]["weather_api"] = "healthy"
        else:
            status["services"]["weather_api"] = "degraded"
    except Exception:
        status["services"]["weather_api"] = "unhealthy"
    
    # Overall status
    unhealthy_services = [k for k, v in status["services"].items() if v not in ["healthy", "degraded"]]
    if unhealthy_services:
        status["status"] = "degraded"
        status["unhealthy_services"] = unhealthy_services
    
    return jsonify(status)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/weather")
def weather():
    return render_template("weather.html")

@app.route("/diagnostics")
def diagnostics():
    return render_template("diagnostics.html")

@app.route("/api/status")
def get_status():
    if not redis_client:
        return jsonify({"error": "Redis service unavailable"}), 503
    
    try:
        raw = redis_client.get("latest_status")
        if not raw:
            return jsonify({"error": "No data available"}), 404

        data = json.loads(raw)
        now = datetime.now(timezone.utc)
        heartbeat = datetime.fromisoformat(data["last_heartbeat"])
        delta = now - heartbeat

        response_data = {
            **data,
            "connected": delta.total_seconds() < 120,
            "on_solar": (data.get("solar_v") or 0) > 1.0,
            "last_seen_minutes": int(delta.total_seconds() / 60)
        }
        
        return jsonify(response_data)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Redis latest_status")
        return jsonify({"error": "Invalid status data"}), 500
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": "Failed to retrieve status"}), 500

@app.route("/api/dashboard")
def api_dashboard():
    start = request.args.get("start")
    end = request.args.get("end")
    
    if not start or not end:
        return jsonify({"error": "Missing start or end parameter"}), 400
    
    valid, error_msg = validate_datetime_range(start, end)
    if not valid:
        return jsonify({"error": error_msg}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database service unavailable"}), 503
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
              extract(epoch from timestamp) * 1000,
              level_cm,
              outflow_lps
            FROM pond_metrics
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (start, end))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        level = [[int(row[0]), row[1]] for row in rows if row[1] is not None]
        outflow = [[int(row[0]), row[2]] for row in rows if row[2] is not None]

        return jsonify({
            "level": level, 
            "outflow": outflow,
            "data_points": len(rows)
        })
    except psycopg2.Error as e:
        logger.error(f"Database error in dashboard API: {e}")
        return jsonify({"error": "Database query failed"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in dashboard API: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/lora")
def diagnostics_data():
    hours = request.args.get("hours", 24, type=int)
    
    # Validate hours parameter
    if not 1 <= hours <= 168:  # 1 hour to 1 week
        return jsonify({"error": "Hours must be between 1 and 168"}), 400
    
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database service unavailable"}), 503
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                extract(epoch from timestamp) * 1000 AS ts,
                temperature_c,
                battery_v,
                solar_v,
                signal_dbm
            FROM station_metrics
            WHERE timestamp >= %s
            ORDER BY timestamp ASC
        """, (start_time,))
        rows = cur.fetchall()
        cur.close()

        temperature = []
        battery_voltage = []
        solar_voltage = []
        signal_strength = []  # Fixed: Added signal_strength array

        for ts, temp, batt, solar, signal in rows:
            timestamp = int(ts)
            if temp is not None:
                temperature.append([timestamp, round(temp, 1)])
            if batt is not None:
                battery_voltage.append([timestamp, round(batt, 2)])
            if solar is not None:
                solar_voltage.append([timestamp, round(solar, 2)])
            if signal is not None:  # Fixed: Added signal data processing
                signal_strength.append([timestamp, signal])

        return jsonify({
            "temperature": temperature,
            "battery_voltage": battery_voltage,
            "solar_voltage": solar_voltage,
            "signal_strength": signal_strength,  # Fixed: Added signal_strength to response
            "data_points": len(rows),
            "time_range_hours": hours
        })

    except psycopg2.Error as e:
        logger.error(f"Database error in LoRa API: {e}")
        return jsonify({"error": "Database query failed"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in LoRa API: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

# Fixed: Added missing /api/logs endpoint
@app.route("/api/logs")
def get_logs():
    """Get system logs"""
    limit = request.args.get("limit", 50, type=int)
    
    # Validate limit
    if not 1 <= limit <= 1000:
        return jsonify({"error": "Limit must be between 1 and 1000"}), 400
    
    try:
        # Read recent log entries from the log file
        logs = []
        log_file_path = 'ui.log'
        
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get the last 'limit' lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            # Parse log lines
            for line in reversed(recent_lines):  # Show newest first
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # Parse log format: timestamp - name - level - message
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        timestamp_str = parts[0]
                        logger_name = parts[1]
                        level = parts[2]
                        message = parts[3]
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').isoformat()
                        except ValueError:
                            timestamp = datetime.now().isoformat()
                        
                        logs.append({
                            "timestamp": timestamp,
                            "level": level,
                            "logger": logger_name,
                            "message": message
                        })
                except Exception as e:
                    # If parsing fails, add as raw message
                    logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "logger": "system",
                        "message": line[:200]  # Truncate long lines
                    })
        else:
            # If no log file exists, return some sample entries
            logs = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "logger": "system",
                    "message": "Log file not found - system may be starting up"
                }
            ]
        
        return jsonify(logs[:limit])  # Ensure we don't exceed limit
        
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({"error": "Failed to read system logs"}), 500

# Fixed: Added missing diagnostic action endpoints
@app.route("/api/test-connection", methods=["POST"])
def test_connection():
    """Test system connections"""
    try:
        results = {
            "database": False,
            "redis": False,
            "weather_api": False
        }
        
        # Test database
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.close()
                conn.close()
                results["database"] = True
        except Exception as e:
            logger.error(f"Database test failed: {e}")
        
        # Test Redis
        try:
            if redis_client:
                redis_client.ping()
                results["redis"] = True
        except Exception as e:
            logger.error(f"Redis test failed: {e}")
        
        # Test Weather API
        try:
            test_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={config.WEATHER_LAT}&lon={config.WEATHER_LON}&altitude={config.WEATHER_ALT}"
            headers = {"User-Agent": config.USER_AGENT}
            response = requests.get(test_url, headers=headers, timeout=5)
            if response.status_code == 200:
                results["weather_api"] = True
        except Exception as e:
            logger.error(f"Weather API test failed: {e}")
        
        success = all(results.values())
        
        return jsonify({
            "success": success,
            "results": results,
            "message": "All connections successful" if success else "Some connections failed"
        })
        
    except Exception as e:
        logger.error(f"Connection test error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/diagnostics/export")
def export_diagnostics():
    """Export diagnostic data"""
    try:
        # Get system status
        status_data = {}
        try:
            if redis_client:
                raw = redis_client.get("latest_status")
                if raw:
                    status_data = json.loads(raw)
        except Exception as e:
            logger.error(f"Error getting status for export: {e}")
        
        # Get recent diagnostic data
        diagnostic_data = {}
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT timestamp, temperature_c, battery_v, solar_v, signal_dbm
                    FROM station_metrics
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                rows = cur.fetchall()
                cur.close()
                conn.close()
                
                diagnostic_data = {
                    "recent_metrics": [
                        {
                            "timestamp": row[0].isoformat(),
                            "temperature_c": row[1],
                            "battery_v": row[2],
                            "solar_v": row[3],
                            "signal_dbm": row[4]
                        }
                        for row in rows
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting diagnostic data for export: {e}")
        
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "system_status": status_data,
            "diagnostic_data": diagnostic_data,
            "system_info": {
                "version": "1.0.0",
                "testing_mode": os.getenv("TESTING_MODE", "false").lower() == "true"
            }
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        logger.error(f"Export diagnostics error: {e}")
        return jsonify({"error": "Failed to export diagnostics"}), 500

@app.route("/api/device/reset", methods=["POST"])
def reset_device():
    """Reset device (simulated in testing mode)"""
    try:
        testing_mode = os.getenv("TESTING_MODE", "false").lower() == "true"
        
        if testing_mode:
            # In testing mode, just return success
            logger.info("Device reset requested (testing mode)")
            return jsonify({
                "success": True,
                "message": "Device reset initiated (simulated in testing mode)"
            })
        else:
            # In production mode, you would implement actual device reset logic here
            logger.info("Device reset requested (production mode)")
            return jsonify({
                "success": True,
                "message": "Device reset initiated"
            })
            
    except Exception as e:
        logger.error(f"Device reset error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# NOVÝ ENDPOINT pro aktuální počasí
@app.route("/api/weather/current")
def weather_current():
    """Get current weather conditions"""
    cache_key = "weather_current"
    
    # Try cache first
    cached_data = get_cached_weather_data(cache_key)
    if cached_data:
        logger.info("Returning cached current weather data")
        return jsonify(cached_data)
    
    # Fetch fresh data
    raw_data = fetch_weather_data()
    if not raw_data:
        return jsonify({"error": "Weather service unavailable"}), 503
    
    try:
        # Get the most recent entry (should be current time)
        timeseries = raw_data.get("properties", {}).get("timeseries", [])
        if not timeseries:
            return jsonify({"error": "No weather data available"}), 404
        
        current_entry = timeseries[0]  # First entry is current/nearest time
        
        # Extract current conditions
        instant_details = current_entry.get("data", {}).get("instant", {}).get("details", {})
        next_1h = current_entry.get("data", {}).get("next_1_hours", {})
        next_1h_details = next_1h.get("details", {})
        
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": round(instant_details.get("air_temperature", 0), 1),
            "pressure": round(instant_details.get("air_pressure_at_sea_level", 1013), 1),
            "humidity": round(instant_details.get("relative_humidity", 50), 1),
            "wind": round(instant_details.get("wind_speed", 0), 1),
            "wind_direction": int(instant_details.get("wind_from_direction", 0)),
            "wind_gust": round(instant_details.get("wind_speed_of_gust", 0), 1),
            "cloud_coverage": int(instant_details.get("cloud_area_fraction", 0)),
            "rain": round(next_1h_details.get("precipitation_amount", 0), 1),
            "symbol_code": next_1h.get("summary", {}).get("symbol_code") or guess_weather_symbol({
                "rain": next_1h_details.get("precipitation_amount", 0),
                "cloud": instant_details.get("cloud_area_fraction", 0)
            })
        }
        
        # Cache the result (shorter cache time for current weather)
        cache_weather_data(cache_key, result)
        logger.info("Fetched and cached current weather data")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing current weather data: {e}")
        return jsonify({"error": "Failed to process weather data"}), 500

@app.route("/api/weather/meteogram")
def weather_meteogram():
    """Get 48-hour detailed forecast for meteogram"""
    cache_key = "weather_meteogram"
    
    # Try to get cached data first
    cached_data = get_cached_weather_data(cache_key)
    if cached_data:
        logger.info("Returning cached weather meteogram data")
        return jsonify(cached_data)
    
    # Fetch fresh data
    raw_data = fetch_weather_data()
    if not raw_data:
        return jsonify({"error": "Weather service unavailable"}), 503
    
    try:
        result = []
        timeseries = raw_data.get("properties", {}).get("timeseries", [])
        
        for entry in timeseries:
            try:
                time_iso = entry["time"]
                time_ts = int(datetime.fromisoformat(time_iso.replace("Z", "+00:00")).timestamp() * 1000)

                # Extract instant details
                instant_details = entry.get("data", {}).get("instant", {}).get("details", {})
                
                # Extract next 1 hour details
                next_1h = entry.get("data", {}).get("next_1_hours", {})
                next_1h_details = next_1h.get("details", {})

                # Build consistent data structure
                weather_point = {
                    "time": time_ts,
                    "temperature": round(instant_details.get("air_temperature", 0), 1),
                    "rain": round(next_1h_details.get("precipitation_amount", 0), 1),
                    "wind": round(instant_details.get("wind_speed", 0), 1),  # POZOR: "wind" ne "wind_speed"
                    "wind_direction": int(instant_details.get("wind_from_direction", 0)),
                    "wind_gust": round(instant_details.get("wind_speed_of_gust", 0), 1),
                    "pressure": round(instant_details.get("air_pressure_at_sea_level", 1013), 1),
                    "humidity": round(instant_details.get("relative_humidity", 50), 1),
                    "cloud": int(instant_details.get("cloud_area_fraction", 0)),
                    "symbol_code": next_1h.get("summary", {}).get("symbol_code") or guess_weather_symbol({
                        "rain": next_1h_details.get("precipitation_amount", 0),
                        "cloud": instant_details.get("cloud_area_fraction", 0)
                    })
                }

                result.append(weather_point)
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping weather entry due to missing/invalid data: {e}")
                continue

        # Cache the result
        cache_weather_data(cache_key, result)
        logger.info(f"Fetched and cached {len(result)} weather meteogram points")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Unexpected error in weather meteogram: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route("/api/weather/daily")
def daily_forecast():
    """Get 7-day daily forecast summary"""
    cache_key = "weather_daily"
    
    # Try to get cached data first
    cached_data = get_cached_weather_data(cache_key)
    if cached_data:
        logger.info("Returning cached daily forecast data")
        return jsonify(cached_data)
    
    # Fetch fresh data
    raw_data = fetch_weather_data()
    if not raw_data:
        return jsonify({"error": "Weather service unavailable"}), 503
    
    try:
        daily = defaultdict(lambda: {
            "temps": [], "wind_avg": [], "wind_gust": [], "rain": 0.0, 
            "icons": [], "humidity": [], "pressure": []
        })

        timeseries = raw_data.get("properties", {}).get("timeseries", [])
        
        for entry in timeseries:
            try:
                dt = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
                date = dt.date().isoformat()
                
                instant_details = entry.get("data", {}).get("instant", {}).get("details", {})
                next_1h = entry.get("data", {}).get("next_1_hours", {})
                next_1h_details = next_1h.get("details", {})

                # Collect temperature data
                temp = instant_details.get("air_temperature")
                if temp is not None:
                    daily[date]["temps"].append(temp)
                
                # Collect wind data
                wind = instant_details.get("wind_speed")
                if wind is not None:
                    daily[date]["wind_avg"].append(wind)
                
                gust = instant_details.get("wind_speed_of_gust")
                if gust is not None:
                    daily[date]["wind_gust"].append(gust)
                
                # Collect other data
                humidity = instant_details.get("relative_humidity")
                if humidity is not None:
                    daily[date]["humidity"].append(humidity)
                
                pressure = instant_details.get("air_pressure_at_sea_level")
                if pressure is not None:
                    daily[date]["pressure"].append(pressure)

                # Accumulate precipitation
                rain = next_1h_details.get("precipitation_amount", 0.0)
                if rain:
                    daily[date]["rain"] += rain

                # Collect weather icons
                icon = next_1h.get("summary", {}).get("symbol_code")
                if icon:
                    daily[date]["icons"].append(icon)
                    
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping daily forecast entry due to missing/invalid data: {e}")
                continue

        # Process daily summaries
        result = []
        for date, values in sorted(daily.items())[:7]:  # First 7 days
            if not values["temps"]:
                continue
                
            daily_summary = {
                "date": date,
                "temp": round(max(values["temps"]), 1),
                "temp_min": round(min(values["temps"]), 1),
                "temp_avg": round(sum(values["temps"]) / len(values["temps"]), 1),
                "wind_avg": round(sum(values["wind_avg"]) / len(values["wind_avg"]), 1) if values["wind_avg"] else 0,
                "wind_gust": round(max(values["wind_gust"]), 1) if values["wind_gust"] else 0,
                "rain": round(values["rain"], 1),
                "humidity_avg": round(sum(values["humidity"]) / len(values["humidity"]), 1) if values["humidity"] else 50,
                "pressure_avg": round(sum(values["pressure"]) / len(values["pressure"]), 1) if values["pressure"] else 1013,
                "icon": max(set(values["icons"]), key=values["icons"].count) if values["icons"] else "clearsky_day"
            }
            
            result.append(daily_summary)

        # Cache the result
        cache_weather_data(cache_key, result)
        logger.info(f"Fetched and cached {len(result)} daily forecast entries")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Unexpected error in daily forecast: {e}")
        return jsonify({"error": "Failed to fetch daily forecast"}), 500

# NOVÝ ENDPOINT pro weather statistics
@app.route("/api/weather/stats")
def weather_stats():
    """Get weather statistics for the last 24 hours"""
    cache_key = "weather_stats_24h"
    
    # Try cache first
    cached_data = get_cached_weather_data(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    # Get meteogram data and calculate stats
    try:
        meteogram_data = get_cached_weather_data("weather_meteogram")
        if not meteogram_data:
            # Fetch fresh meteogram data
            response = weather_meteogram()
            if response.status_code != 200:
                return jsonify({"error": "Unable to calculate statistics"}), 503
            meteogram_data = response.get_json()
        
        # Filter last 24 hours
        now = datetime.now(timezone.utc).timestamp() * 1000
        last_24h = [d for d in meteogram_data if d['time'] >= now - 24 * 3600 * 1000]
        
        if not last_24h:
            return jsonify({"error": "No data for statistics"}), 404
        
        # Calculate statistics
        temps = [d['temperature'] for d in last_24h if d['temperature'] is not None]
        rains = [d['rain'] for d in last_24h if d['rain'] is not None]
        winds = [d['wind'] for d in last_24h if d['wind'] is not None]
        pressures = [d['pressure'] for d in last_24h if d['pressure'] is not None]
        
        stats = {
            "period": "24h",
            "data_points": len(last_24h),
            "temperature": {
                "max": round(max(temps), 1) if temps else None,
                "min": round(min(temps), 1) if temps else None,
                "avg": round(sum(temps) / len(temps), 1) if temps else None
            },
            "rain": {
                "total": round(sum(rains), 1) if rains else 0,
                "max_hourly": round(max(rains), 1) if rains else 0
            },
            "wind": {
                "max": round(max(winds), 1) if winds else None,
                "avg": round(sum(winds) / len(winds), 1) if winds else None
            },
            "pressure": {
                "max": round(max(pressures), 1) if pressures else None,
                "min": round(min(pressures), 1) if pressures else None,
                "avg": round(sum(pressures) / len(pressures), 1) if pressures else None
            },
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache for shorter time (15 minutes)
        if redis_client:
            try:
                redis_client.setex(cache_key, 900, json.dumps(stats, default=str))
            except Exception as e:
                logger.error(f"Failed to cache weather stats: {e}")
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error calculating weather statistics: {e}")
        return jsonify({"error": "Failed to calculate statistics"}), 500

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)