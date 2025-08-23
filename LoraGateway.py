# lora_gateway/LoraGateway.py
import os
import json
import time
import signal
import sys
import logging
import psycopg2
import redis
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Try to import serial, but don't fail if not available in testing mode
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    class MockSerial:
        def __init__(self, *args, **kwargs):
            self.is_open = True
        def readline(self):
            return b""
        def close(self):
            pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lora_gateway.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoRaGateway:
    def __init__(self):
        load_dotenv()
        self.setup_config()
        self.running = True
        self.connections = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_config(self):
        """Load and validate configuration from environment"""
        self.config = {
            'serial_port': os.getenv("SERIAL_PORT", "/dev/ttyUSB0"),
            'baud_rate': int(os.getenv("BAUD_RATE", "9600")),
            'redis_host': os.getenv("REDIS_HOST", "redis"),
            'redis_port': int(os.getenv("REDIS_PORT", "6379")),
            'pg_host': os.getenv("PG_HOST", "timescaledb"),
            'pg_port': int(os.getenv("PG_PORT", "5432")),
            'pg_user': os.getenv("POSTGRES_USER", "pond_user"),
            'pg_password': os.getenv("POSTGRES_PASSWORD", "secretpassword"),
            'pg_db': os.getenv("POSTGRES_DB", "pond_data"),
            'retry_delay': int(os.getenv("RETRY_DELAY", "5")),
            'max_retries': int(os.getenv("MAX_RETRIES", "3")),
            'testing_mode': os.getenv("TESTING_MODE", "false").lower() == "true",
            'simulate_data': os.getenv("SIMULATE_DATA", "false").lower() == "true"
        }
        
        if self.config['testing_mode']:
            logger.info("🧪 TESTING MODE ENABLED - No physical hardware required")
        
        if self.config['simulate_data']:
            logger.info("📊 DATA SIMULATION ENABLED - Generating synthetic sensor data")
    
    def connect_redis(self) -> bool:
        """Establish Redis connection with retry logic"""
        for attempt in range(self.config['max_retries']):
            try:
                self.redis_client = redis.Redis(
                    host=self.config['redis_host'],
                    port=self.config['redis_port'],
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self.redis_client.ping()
                logger.info("✅ Connected to Redis")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(self.config['retry_delay'])
        
        logger.error("❌ Failed to connect to Redis after all retries")
        return False
    
    def connect_postgres(self) -> bool:
        """Establish PostgreSQL connection with retry logic"""
        for attempt in range(self.config['max_retries']):
            try:
                self.pg_conn = psycopg2.connect(
                    host=self.config['pg_host'],
                    port=self.config['pg_port'],
                    database=self.config['pg_db'],
                    user=self.config['pg_user'],
                    password=self.config['pg_password'],
                    connect_timeout=10
                )
                self.pg_cursor = self.pg_conn.cursor()
                self.verify_database_schema()
                logger.info("✅ Connected to PostgreSQL")
                return True
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL connection attempt {attempt + 1} failed: {e}")
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(self.config['retry_delay'])
        
        logger.error("❌ Failed to connect to PostgreSQL after all retries")
        return False
    
    def connect_serial(self) -> bool:
        """Establish serial connection with retry logic (or mock in testing mode)"""
        if self.config['testing_mode']:
            logger.info("🧪 Using mock serial connection for testing")
            if SERIAL_AVAILABLE:
                try:
                    # Try to create a null device connection for testing
                    self.serial_conn = serial.Serial(port=None, timeout=1)
                    self.serial_conn.is_open = True
                except:
                    self.serial_conn = MockSerial()
            else:
                self.serial_conn = MockSerial()
            return True
        
        if not SERIAL_AVAILABLE:
            logger.error("❌ Serial library not available and not in testing mode")
            return False
        
        for attempt in range(self.config['max_retries']):
            try:
                self.serial_conn = serial.Serial(
                    self.config['serial_port'],
                    self.config['baud_rate'],
                    timeout=1
                )
                logger.info(f"✅ Connected to serial port {self.config['serial_port']}")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Serial connection attempt {attempt + 1} failed: {e}")
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(self.config['retry_delay'])
        
        logger.error("❌ Failed to connect to serial port after all retries")
        return False
    
    def verify_database_schema(self):
        """Verify that required database tables exist (created by init script)"""
        try:
            # Check if required tables exist
            self.pg_cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('pond_metrics', 'station_metrics');
            """)
            
            existing_tables = [row[0] for row in self.pg_cursor.fetchall()]
            
            required_tables = ['pond_metrics', 'station_metrics']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.error(f"❌ Missing required database tables: {missing_tables}")
                logger.error("💡 Make sure init_pondmonitor.sql is properly mounted and executed")
                raise Exception(f"Missing database tables: {missing_tables}")
            
            logger.info("✅ Database schema verified - all required tables exist")
            
            # Log table info for debugging
            for table in existing_tables:
                self.pg_cursor.execute(f"""
                    SELECT COUNT(*) FROM {table};
                """)
                count = self.pg_cursor.fetchone()[0]
                logger.info(f"📊 Table '{table}' has {count} records")
                
        except Exception as e:
            logger.error(f"❌ Database schema verification failed: {e}")
            raise
    
    def generate_simulated_data(self) -> Dict[str, Any]:
        """Generate realistic simulated sensor data for testing"""
        # Base values with some realistic variation
        base_temp = 20.0 + 15 * (time.time() % 86400) / 86400  # Daily temperature cycle
        base_battery = 5.0
        base_solar = max(0, 18 * abs((time.time() % 86400 - 43200) / 43200))  # Solar cycle
        
        return {
            "temperature_c": round(base_temp + random.uniform(-2, 2), 1),
            "battery_v": round(base_battery + random.uniform(-5, 0), 2),
            "solar_v": round(base_solar + random.uniform(-2, 2), 2),
            "signal_dbm": random.randint(-100, -60),
            "station_id": "testing_station",
            "level_cm": round(150 + random.uniform(-10, 10), 1),
            "outflow_lps": round(2.5 + random.uniform(-0.5, 0.5), 2)
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate incoming sensor data"""
        required_fields = ['temperature_c', 'battery_v', 'solar_v']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"⚠️ Missing required field: {field}")
                return False
            
            value = data[field]
            if not isinstance(value, (int, float)) or value is None:
                logger.warning(f"⚠️ Invalid value for {field}: {value}")
                return False
        
        # Validate ranges
        if not (-50 <= data['temperature_c'] <= 80):
            logger.warning(f"⚠️ Temperature out of range: {data['temperature_c']}")
            return False
        
        if not (0 <= data['battery_v'] <= 20):
            logger.warning(f"⚠️ Battery voltage out of range: {data['battery_v']}")
            return False
        
        if not (0 <= data['solar_v'] <= 25):
            logger.warning(f"⚠️ Solar voltage out of range: {data['solar_v']}")
            return False
        
        return True
    
    def process_data(self, raw_data: str = None) -> Optional[Dict[str, Any]]:
        """Process and validate incoming data (or generate simulated data)"""
        try:
            if raw_data is None:
                if self.config['simulate_data']:
                    data = self.generate_simulated_data()
                    logger.debug("📊 Generated simulated data")
                else:
                    return None
            else:
                data = json.loads(raw_data)
            
            if not self.validate_data(data):
                return None
            
            now = datetime.now(timezone.utc).isoformat()
            processed_data = {
                "battery_v": round(float(data["battery_v"]), 2),
                "solar_v": round(float(data["solar_v"]), 2),
                "signal_dbm": data.get("signal_dbm", -75),
                "temperature_c": round(float(data["temperature_c"]), 1),
                "last_heartbeat": now,
                "station_id": data.get("station_id", "default"),
                "connected": True,
                "on_solar": data["solar_v"] > 1.0,
                "device_id": "POND-001",
                "firmware_version": "1.0.0-testing" if self.config['testing_mode'] else "1.0.0"
            }
            
            # Add pond data if available
            if "level_cm" in data:
                processed_data["level_cm"] = round(float(data["level_cm"]), 1)
            if "outflow_lps" in data:
                processed_data["outflow_lps"] = round(float(data["outflow_lps"]), 2)
            
            return processed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Data processing error: {e}")
            return None
    
    def save_to_redis(self, data: Dict[str, Any]) -> bool:
        """Save latest status to Redis"""
        try:
            self.redis_client.set("latest_status", json.dumps(data), ex=300)  # 5 min expiry
            return True
        except Exception as e:
            logger.error(f"❌ Redis save error: {e}")
            return False
    
    def save_to_postgres(self, data: Dict[str, Any]) -> bool:
        """Save historical data to PostgreSQL"""
        try:
            # Save station metrics
            self.pg_cursor.execute(
                """INSERT INTO station_metrics 
                   (temperature_c, battery_v, solar_v, signal_dbm, station_id) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (data["temperature_c"], data["battery_v"], data["solar_v"], 
                 data["signal_dbm"], data["station_id"])
            )
            
            # Save pond metrics if available
            if "level_cm" in data or "outflow_lps" in data:
                self.pg_cursor.execute(
                    """INSERT INTO pond_metrics (level_cm, outflow_lps) 
                       VALUES (%s, %s)""",
                    (data.get("level_cm"), data.get("outflow_lps"))
                )
            
            self.pg_conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL save error: {e}")
            # Try to rollback
            try:
                self.pg_conn.rollback()
            except:
                pass
            return False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def cleanup(self):
        """Clean up connections"""
        if hasattr(self, 'serial_conn') and hasattr(self.serial_conn, 'is_open') and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("🔌 Serial connection closed")
        
        if hasattr(self, 'pg_conn') and not self.pg_conn.closed:
            self.pg_conn.close()
            logger.info("🗄️ PostgreSQL connection closed")
        
        logger.info("🧹 Cleanup completed")
    
    def run(self):
        """Main execution loop"""
        logger.info("🚀 Starting LoRa Gateway")
        
        if self.config['testing_mode']:
            logger.info("🧪 Running in TESTING MODE")
        if self.config['simulate_data']:
            logger.info("📊 Data simulation is ENABLED")
        
        # Initialize connections
        if not all([
            self.connect_redis(),
            self.connect_postgres(),
            self.connect_serial()
        ]):
            logger.error("❌ Failed to initialize connections")
            return False
        
        logger.info("✅ All connections established, starting main loop")
        
        try:
            while self.running:
                try:
                    if self.config['simulate_data']:
                        # Generate and process simulated data
                        processed_data = self.process_data()
                        if processed_data:
                            # Save data
                            redis_success = self.save_to_redis(processed_data)
                            postgres_success = self.save_to_postgres(processed_data)
                            
                            if redis_success and postgres_success:
                                logger.info(f"✅ Data saved: T={processed_data['temperature_c']}°C, "
                                          f"B={processed_data['battery_v']}V, S={processed_data['solar_v']}V, "
                                          f"Level={processed_data.get('level_cm', 'N/A')}cm")
                            else:
                                logger.warning("⚠️ Partial save failure")
                        
                        # Wait 30 seconds between simulated readings
                        time.sleep(30)
                    else:
                        # Real serial data processing
                        if not self.serial_conn.is_open:
                            logger.warning("⚠️ Serial connection lost, attempting to reconnect")
                            if not self.connect_serial():
                                time.sleep(self.config['retry_delay'])
                                continue
                        
                        line = self.serial_conn.readline().decode('utf-8').strip()
                        if not line:
                            continue
                        
                        processed_data = self.process_data(line)
                        if not processed_data:
                            continue
                        
                        # Save data
                        redis_success = self.save_to_redis(processed_data)
                        postgres_success = self.save_to_postgres(processed_data)
                        
                        if redis_success and postgres_success:
                            logger.info(f"✅ Data saved successfully: T={processed_data['temperature_c']}°C, "
                                      f"B={processed_data['battery_v']}V, S={processed_data['solar_v']}V")
                        else:
                            logger.warning("⚠️ Partial save failure - data may be incomplete")
                
                except Exception as e:
                    logger.error(f"❌ Unexpected error in main loop: {e}")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        finally:
            self.cleanup()
        
        return True

if __name__ == "__main__":
    gateway = LoRaGateway()
    sys.exit(0 if gateway.run() else 1)