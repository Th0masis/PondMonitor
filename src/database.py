"""
PondMonitor Database Service Layer

Provides a clean abstraction over database operations with:
- Connection pooling for better performance
- Automatic transaction management
- Proper error handling and logging
- Type-safe query methods
- Connection health monitoring

This replaces direct psycopg2 calls throughout the application.
"""

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union, Generator
from dataclasses import dataclass

import psycopg2
import psycopg2.pool
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations"""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails"""
    pass


class QueryError(DatabaseError):
    """Exception raised when query execution fails"""
    pass


class ValidationError(DatabaseError):
    """Exception raised when data validation fails"""
    pass


@dataclass
class QueryResult:
    """Container for query results with metadata"""
    rows: List[Tuple]
    row_count: int
    column_names: List[str]
    execution_time: float
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert rows to list of dictionaries"""
        return [
            dict(zip(self.column_names, row))
            for row in self.rows
        ]
    
    def first(self) -> Optional[Tuple]:
        """Get first row or None"""
        return self.rows[0] if self.rows else None
    
    def first_dict(self) -> Optional[Dict[str, Any]]:
        """Get first row as dictionary or None"""
        if not self.rows:
            return None
        return dict(zip(self.column_names, self.rows[0]))


class DatabaseService:
    """
    Database service providing connection pooling and query abstraction.
    
    Features:
    - Connection pooling with automatic retry
    - Transaction management
    - Query execution with proper error handling
    - Health monitoring and diagnostics
    - Time-series optimized queries for TimescaleDB
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database service with configuration.
        
        Args:
            config: Database configuration object
        """
        self.config = config
        self._pool: Optional[psycopg2.pool.SimpleConnectionPool] = None
        self._pool_lock = threading.Lock()
        self._health_check_interval = 30  # seconds
        self._last_health_check = 0
        
        # Statistics tracking
        self._query_count = 0
        self._error_count = 0
        self._total_execution_time = 0.0
        
        logger.info("Database service initialized")
    
    def initialize(self) -> None:
        """Initialize connection pool"""
        try:
            with self._pool_lock:
                if self._pool is None:
                    logger.info("Creating database connection pool")
                    self._pool = psycopg2.pool.SimpleConnectionPool(
                        minconn=1,
                        maxconn=self.config.pool_size,
                        **self.config.get_connection_dict()
                    )
                    logger.info(f"Connection pool created with {self.config.pool_size} connections")
                    
                    # Verify connection and check database schema
                    self._verify_connection()
                    self._check_schema()
                    
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise ConnectionError(f"Database initialization failed: {e}")
    
    def _verify_connection(self) -> None:
        """Verify database connection and TimescaleDB extension"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check PostgreSQL version
                cur.execute("SELECT version()")
                pg_version = cur.fetchone()[0]
                logger.info(f"Connected to: {pg_version}")
                
                # Check TimescaleDB extension
                cur.execute("""
                    SELECT extname, extversion 
                    FROM pg_extension 
                    WHERE extname = 'timescaledb'
                """)
                result = cur.fetchone()
                if result:
                    logger.info(f"TimescaleDB version: {result[1]}")
                else:
                    logger.warning("TimescaleDB extension not found")
    
    def _check_schema(self) -> None:
        """Verify required database tables exist"""
        required_tables = ['pond_metrics', 'station_metrics']
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = ANY(%s)
                """, (required_tables,))
                
                existing_tables = [row[0] for row in cur.fetchall()]
                missing_tables = set(required_tables) - set(existing_tables)
                
                if missing_tables:
                    raise ValidationError(f"Missing required tables: {missing_tables}")
                
                logger.info(f"Schema validation passed: {existing_tables}")
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Get database connection from pool with automatic cleanup.
        
        Yields:
            Database connection
        
        Raises:
            ConnectionError: If unable to get connection
        """
        if self._pool is None:
            self.initialize()
        
        conn = None
        try:
            conn = self._pool.getconn()
            if conn is None:
                raise ConnectionError("Unable to get connection from pool")
            
            # Ensure connection is in a good state
            if conn.closed:
                logger.warning("Connection was closed, getting new one")
                self._pool.putconn(conn, close=True)
                conn = self._pool.getconn()
            
            yield conn
            
        except Exception as e:
            if conn:
                # Connection might be in bad state, close it
                try:
                    conn.rollback()
                except:
                    pass
                self._pool.putconn(conn, close=True)
                conn = None
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> QueryResult:
        """
        Execute a query with parameters and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
        
        Returns:
            QueryResult with execution metadata
        
        Raises:
            QueryError: If query execution fails
        """
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Execute query
                    cur.execute(query, params)
                    
                    # Fetch results if requested
                    rows = []
                    column_names = []
                    row_count = 0
                    
                    if fetch and cur.description:
                        rows = cur.fetchall()
                        column_names = [desc[0] for desc in cur.description]
                        row_count = len(rows)
                    elif not fetch:
                        row_count = cur.rowcount
                    
                    # Commit transaction
                    conn.commit()
                    
                    execution_time = time.time() - start_time
                    
                    # Update statistics
                    self._query_count += 1
                    self._total_execution_time += execution_time
                    
                    logger.debug(f"Query executed in {execution_time:.3f}s, {row_count} rows")
                    
                    return QueryResult(
                        rows=rows,
                        row_count=row_count,
                        column_names=column_names,
                        execution_time=execution_time
                    )
                    
        except Exception as e:
            self._error_count += 1
            execution_time = time.time() - start_time
            logger.error(f"Query failed after {execution_time:.3f}s: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Query params: {params}")
            raise QueryError(f"Query execution failed: {e}")
    
    def get_pond_metrics(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pond metrics (water level and outflow) for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of records to return
        
        Returns:
            List of pond metric records
        """
        query = """
            SELECT 
                timestamp,
                level_cm,
                outflow_lps
            FROM pond_metrics 
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """
        
        params = (start_time, end_time)
        
        if limit:
            query += " LIMIT %s"
            params += (limit,)
        
        result = self.execute_query(query, params)
        return result.to_dict_list()
    
    def get_station_metrics(
        self, 
        start_time: datetime, 
        end_time: datetime,
        station_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get station telemetry data for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            station_id: Optional station ID filter
            limit: Maximum number of records to return
        
        Returns:
            List of station metric records
        """
        query = """
            SELECT 
                timestamp,
                temperature_c,
                battery_v,
                solar_v,
                signal_dbm,
                station_id
            FROM station_metrics 
            WHERE timestamp BETWEEN %s AND %s
        """
        
        params = [start_time, end_time]
        
        if station_id:
            query += " AND station_id = %s"
            params.append(station_id)
        
        query += " ORDER BY timestamp ASC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        result = self.execute_query(query, tuple(params))
        return result.to_dict_list()
    
    def insert_pond_metrics(
        self, 
        level_cm: Optional[float], 
        outflow_lps: Optional[float],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Insert pond metrics record.
        
        Args:
            level_cm: Water level in centimeters
            outflow_lps: Outflow in liters per second
            timestamp: Timestamp (defaults to now)
        
        Returns:
            True if insert was successful
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        try:
            self.execute_query(
                """
                INSERT INTO pond_metrics (timestamp, level_cm, outflow_lps) 
                VALUES (%s, %s, %s)
                """,
                (timestamp, level_cm, outflow_lps),
                fetch=False
            )
            logger.debug(f"Inserted pond metrics: level={level_cm}, outflow={outflow_lps}")
            return True
            
        except QueryError as e:
            logger.error(f"Failed to insert pond metrics: {e}")
            return False
    
    def insert_station_metrics(
        self,
        temperature_c: Optional[float],
        battery_v: Optional[float],
        solar_v: Optional[float],
        signal_dbm: Optional[int],
        station_id: str = "default",
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Insert station telemetry record.
        
        Args:
            temperature_c: Temperature in Celsius
            battery_v: Battery voltage
            solar_v: Solar voltage
            signal_dbm: Signal strength in dBm
            station_id: Station identifier
            timestamp: Timestamp (defaults to now)
        
        Returns:
            True if insert was successful
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        try:
            self.execute_query(
                """
                INSERT INTO station_metrics 
                (timestamp, temperature_c, battery_v, solar_v, signal_dbm, station_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (timestamp, temperature_c, battery_v, solar_v, signal_dbm, station_id),
                fetch=False
            )
            logger.debug(f"Inserted station metrics for {station_id}")
            return True
            
        except QueryError as e:
            logger.error(f"Failed to insert station metrics: {e}")
            return False
    
    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent metrics from both tables.
        
        Returns:
            Dictionary with latest metrics or None
        """
        try:
            # Get latest pond metrics
            pond_result = self.execute_query("""
                SELECT timestamp, level_cm, outflow_lps
                FROM pond_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            # Get latest station metrics
            station_result = self.execute_query("""
                SELECT timestamp, temperature_c, battery_v, solar_v, signal_dbm, station_id
                FROM station_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            latest = {}
            
            if pond_result.rows:
                pond_data = pond_result.first_dict()
                latest.update({
                    'level_cm': pond_data['level_cm'],
                    'outflow_lps': pond_data['outflow_lps'],
                    'pond_timestamp': pond_data['timestamp']
                })
            
            if station_result.rows:
                station_data = station_result.first_dict()
                latest.update({
                    'temperature_c': station_data['temperature_c'],
                    'battery_v': station_data['battery_v'],
                    'solar_v': station_data['solar_v'],
                    'signal_dbm': station_data['signal_dbm'],
                    'station_id': station_data['station_id'],
                    'station_timestamp': station_data['timestamp']
                })
            
            return latest if latest else None
            
        except QueryError as e:
            logger.error(f"Failed to get latest metrics: {e}")
            return None
    
    def get_data_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary statistics for the specified time period.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Dictionary with summary statistics
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        try:
            # Pond metrics summary
            pond_summary = self.execute_query("""
                SELECT 
                    COUNT(*) as record_count,
                    AVG(level_cm) as avg_level,
                    MIN(level_cm) as min_level,
                    MAX(level_cm) as max_level,
                    AVG(outflow_lps) as avg_outflow,
                    MIN(outflow_lps) as min_outflow,
                    MAX(outflow_lps) as max_outflow
                FROM pond_metrics 
                WHERE timestamp >= %s AND level_cm IS NOT NULL
            """, (start_time,))
            
            # Station metrics summary
            station_summary = self.execute_query("""
                SELECT 
                    COUNT(*) as record_count,
                    AVG(temperature_c) as avg_temperature,
                    MIN(temperature_c) as min_temperature,
                    MAX(temperature_c) as max_temperature,
                    AVG(battery_v) as avg_battery,
                    MIN(battery_v) as min_battery,
                    MIN(signal_dbm) as min_signal,
                    MAX(signal_dbm) as max_signal
                FROM station_metrics 
                WHERE timestamp >= %s AND temperature_c IS NOT NULL
            """, (start_time,))
            
            summary = {
                'time_period_hours': hours,
                'start_time': start_time.isoformat(),
                'pond_metrics': pond_summary.first_dict() if pond_summary.rows else {},
                'station_metrics': station_summary.first_dict() if station_summary.rows else {}
            }
            
            return summary
            
        except QueryError as e:
            logger.error(f"Failed to get data summary: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            Dictionary with health status and metrics
        """
        current_time = time.time()
        
        # Only perform full health check periodically
        if current_time - self._last_health_check < self._health_check_interval:
            return {'status': 'cached', 'healthy': True}
        
        health_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healthy': False,
            'connection_pool': {},
            'query_stats': {},
            'errors': []
        }
        
        try:
            # Check connection pool status
            if self._pool:
                health_info['connection_pool'] = {
                    'total_connections': self.config.pool_size,
                    'available': len(self._pool._pool),
                    'in_use': self.config.pool_size - len(self._pool._pool)
                }
            
            # Test database connectivity
            start_time = time.time()
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            
            connection_time = time.time() - start_time
            
            # Get query statistics
            avg_execution_time = (
                self._total_execution_time / self._query_count 
                if self._query_count > 0 else 0
            )
            
            health_info.update({
                'healthy': True,
                'connection_time': round(connection_time, 3),
                'query_stats': {
                    'total_queries': self._query_count,
                    'total_errors': self._error_count,
                    'avg_execution_time': round(avg_execution_time, 3),
                    'error_rate': round(self._error_count / max(self._query_count, 1), 3)
                }
            })
            
            self._last_health_check = current_time
            
        except Exception as e:
            health_info['errors'].append(str(e))
            logger.error(f"Database health check failed: {e}")
        
        return health_info
    
    def close(self) -> None:
        """Close all database connections"""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("Database connection pool closed")


# Global database service instance
_db_service: Optional[DatabaseService] = None


def init_database(config: DatabaseConfig) -> DatabaseService:
    """
    Initialize global database service.
    
    Args:
        config: Database configuration
    
    Returns:
        Initialized database service
    """
    global _db_service
    _db_service = DatabaseService(config)
    _db_service.initialize()
    return _db_service


def get_database() -> DatabaseService:
    """
    Get the global database service instance.
    
    Returns:
        Database service instance
    
    Raises:
        RuntimeError: If database service hasn't been initialized
    """
    if _db_service is None:
        raise RuntimeError("Database service not initialized. Call init_database() first.")
    return _db_service


# Context manager for database transactions
@contextmanager
def database_transaction():
    """
    Context manager for database transactions with automatic rollback on error.
    
    Usage:
        with database_transaction():
            db.insert_pond_metrics(150.0, 2.5)
            db.insert_station_metrics(25.0, 12.5, 18.0, -75)
            # Automatic commit on success, rollback on exception
    """
    db = get_database()
    with db.get_connection() as conn:
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise


if __name__ == "__main__":
    # Example usage and testing
    from .config import DatabaseConfig
    
    # Create test configuration
    config = DatabaseConfig(
        host="localhost",
        database="test_pond",
        user="test_user",
        password="test_pass"
    )
    
    try:
        # Initialize database service
        db = init_database(config)
        
        # Test health check
        health = db.health_check()
        print("Health check:", health)
        
        # Test queries
        latest = db.get_latest_metrics()
        print("Latest metrics:", latest)
        
        # Test data summary
        summary = db.get_data_summary(24)
        print("24h summary:", summary)
        
    except Exception as e:
        print(f"Database test failed: {e}")