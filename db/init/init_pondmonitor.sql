-- Create extension for TimescaleDB (if not enabled)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create table for pond data (water level and outflow)
CREATE TABLE IF NOT EXISTS pond_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    level_cm REAL,
    outflow_lps REAL,
    PRIMARY KEY (id, timestamp)
);

-- Create table for station telemetry
CREATE TABLE IF NOT EXISTS station_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    temperature_c REAL,
    battery_v REAL,
    solar_v REAL,
    PRIMARY KEY (id, timestamp)
);

-- Convert to hypertables
SELECT create_hypertable('pond_metrics', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('station_metrics', 'timestamp', if_not_exists => TRUE);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_pond_ts ON pond_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_station_ts ON station_metrics (timestamp DESC);
