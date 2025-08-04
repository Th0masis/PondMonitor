-- PondMonitor Database Initialization Script
-- TimescaleDB Compatible Schema
-- File: ./db/init/init_pondmonitor.sql

-- Ensure TimescaleDB extension is available
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        RAISE EXCEPTION 'TimescaleDB extension is not available';
    END IF;
    RAISE NOTICE 'TimescaleDB extension confirmed available';
END $$;

-- Create table for pond data (water level and outflow)
-- NOTE: For TimescaleDB hypertables, the partitioning column (timestamp) 
-- must be included in any unique constraints/primary keys
CREATE TABLE IF NOT EXISTS pond_metrics (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level_cm REAL,
    outflow_lps REAL,
    -- Create a composite primary key that includes the partitioning column
    PRIMARY KEY (timestamp)
);

-- Create table for station telemetry
-- Using TEXT instead of VARCHAR for better practices in TimescaleDB
CREATE TABLE IF NOT EXISTS station_metrics (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature_c REAL,
    battery_v REAL,
    solar_v REAL,
    signal_dbm INTEGER,
    station_id TEXT DEFAULT 'default',
    -- Create a composite primary key that includes the partitioning column
    -- If you need uniqueness per station, include station_id in the key
    PRIMARY KEY (timestamp, station_id)
);

-- Convert to hypertables with proper error handling
DO $$
BEGIN
    -- Check if pond_metrics is already a hypertable
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE table_name = 'pond_metrics' AND schema_name = 'public'
    ) THEN
        PERFORM create_hypertable('pond_metrics', 'timestamp', if_not_exists => TRUE);
        RAISE NOTICE 'Created hypertable for pond_metrics';
    ELSE
        RAISE NOTICE 'Hypertable pond_metrics already exists';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Failed to create hypertable for pond_metrics: %', SQLERRM;
END $$;

DO $$
BEGIN
    -- Check if station_metrics is already a hypertable
    IF NOT EXISTS (
        SELECT 1 FROM _timescaledb_catalog.hypertable 
        WHERE table_name = 'station_metrics' AND schema_name = 'public'
    ) THEN
        PERFORM create_hypertable('station_metrics', 'timestamp', if_not_exists => TRUE);
        RAISE NOTICE 'Created hypertable for station_metrics';
    ELSE
        RAISE NOTICE 'Hypertable station_metrics already exists';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Failed to create hypertable for station_metrics: %', SQLERRM;
END $$;

-- Create indexes for query performance
-- Note: TimescaleDB automatically creates indexes on the time column
CREATE INDEX IF NOT EXISTS idx_pond_level ON pond_metrics (level_cm, timestamp DESC) WHERE level_cm IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pond_outflow ON pond_metrics (outflow_lps, timestamp DESC) WHERE outflow_lps IS NOT NULL;

-- Indexes for station metrics
CREATE INDEX IF NOT EXISTS idx_station_temp ON station_metrics (temperature_c, timestamp DESC) WHERE temperature_c IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_station_battery ON station_metrics (battery_v, timestamp DESC) WHERE battery_v IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_station_solar ON station_metrics (solar_v, timestamp DESC) WHERE solar_v IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_station_signal ON station_metrics (signal_dbm, timestamp DESC) WHERE signal_dbm IS NOT NULL;

-- Station-specific index
CREATE INDEX IF NOT EXISTS idx_station_id_time ON station_metrics (station_id, timestamp DESC);

-- Insert some test data for testing mode
-- Use explicit timestamps to avoid conflicts
INSERT INTO station_metrics (timestamp, temperature_c, battery_v, solar_v, signal_dbm, station_id) 
VALUES 
    (NOW() - INTERVAL '2 minutes', 22.5, 12.3, 16.8, -75, 'testing_station'),
    (NOW() - INTERVAL '1 minute', 23.1, 12.2, 17.1, -73, 'testing_station'),
    (NOW(), 22.8, 12.4, 16.9, -76, 'testing_station')
ON CONFLICT (timestamp, station_id) DO NOTHING;

INSERT INTO pond_metrics (timestamp, level_cm, outflow_lps) 
VALUES 
    (NOW() - INTERVAL '2 minutes', 145.2, 2.1),
    (NOW() - INTERVAL '1 minute', 144.8, 2.0),
    (NOW(), 145.5, 2.2)
ON CONFLICT (timestamp) DO NOTHING;

-- Create a view for easier querying with row numbers (if needed)
CREATE OR REPLACE VIEW pond_metrics_with_id AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY timestamp) as id,
    timestamp,
    level_cm,
    outflow_lps
FROM pond_metrics
ORDER BY timestamp;

CREATE OR REPLACE VIEW station_metrics_with_id AS
SELECT 
    ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY timestamp) as id,
    timestamp,
    temperature_c,
    battery_v,
    solar_v,
    signal_dbm,
    station_id
FROM station_metrics
ORDER BY station_id, timestamp;

-- Log successful initialization
DO $$
DECLARE
    pond_count INTEGER;
    station_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO pond_count FROM pond_metrics;
    SELECT COUNT(*) INTO station_count FROM station_metrics;
    
    RAISE NOTICE 'PondMonitor database initialization completed successfully';
    RAISE NOTICE 'Tables created: pond_metrics (% rows), station_metrics (% rows)', pond_count, station_count;
    RAISE NOTICE 'Hypertables configured for time-series data';
    RAISE NOTICE 'Indexes created for optimal query performance';
    RAISE NOTICE 'Views created: pond_metrics_with_id, station_metrics_with_id';
END $$;