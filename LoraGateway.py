# lora_gateway/LoraGateway.py
import os
import json
import time
import psycopg2
import redis
import serial
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Setup from environment
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = 9600
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
PG_HOST = os.getenv("PG_HOST", "timescaledb")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("POSTGRES_USER", "pond_user")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secretpassword")
PG_DB = os.getenv("POSTGRES_DB", "pond_data")

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Connect to TimescaleDB
pg_conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD
)
pg_cursor = pg_conn.cursor()

# Setup serial
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

# Ensure table exists
pg_cursor.execute("""
CREATE TABLE IF NOT EXISTS station_metrics (
    timestamp TIMESTAMPTZ DEFAULT now(),
    temperature_c REAL,
    battery_v REAL,
    solar_v REAL
);
SELECT create_hypertable('station_metrics', 'timestamp', if_not_exists => TRUE);
""")
pg_conn.commit()

print("[LoRa Gateway] Listening on", SERIAL_PORT)

# Main loop
while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue

        data = json.loads(line)

        now = datetime.now(timezone.utc).isoformat()
        latest_status = {
            "battery_v": data.get("battery_v"),
            "solar_v": data.get("solar_v"),
            "signal_dbm": data.get("signal_dbm"),
            "temperature_c": data.get("temperature_c"),
            "last_heartbeat": now
        }

        # Save to Redis (live status)
        redis_client.set("latest_status", json.dumps(latest_status))

        # Save to TimescaleDB (historical)
        pg_cursor.execute(
            "INSERT INTO station_metrics (temperature_c, battery_v, solar_v) VALUES (%s, %s, %s)",
            (latest_status["temperature_c"], latest_status["battery_v"], latest_status["solar_v"])
        )
        pg_conn.commit()

        print("[✓] Packet saved", latest_status)
    except Exception as e:
        print("[!] Error:", e)
        time.sleep(1)
