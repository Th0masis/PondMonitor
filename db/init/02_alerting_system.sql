-- =====================================================
-- PondMonitor Alerting System Database Schema
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Alert Rules Table
-- Stores configurable alert conditions and thresholds
-- =====================================================
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Rule configuration
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('threshold', 'range', 'rate_of_change', 'missing_data')),
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('water_level', 'temperature', 'battery_voltage', 'signal_strength', 'outflow')),
    station_id VARCHAR(50), -- NULL means applies to all stations
    
    -- Condition parameters (JSON for flexibility)
    conditions JSONB NOT NULL,
    -- Examples:
    -- Threshold: {"operator": "gt", "value": 40.0}
    -- Range: {"min": -10.0, "max": 50.0}
    -- Rate: {"change_threshold": 5.0, "time_window_minutes": 30}
    -- Missing: {"max_age_minutes": 60}
    
    -- Alert configuration
    severity VARCHAR(20) NOT NULL DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
    enabled BOOLEAN NOT NULL DEFAULT true,
    
    -- Notification settings
    channels JSONB NOT NULL DEFAULT '["email"]',
    -- Examples: ["email"], ["sms"], ["email", "sms"]
    
    -- Timing and repetition
    cooldown_minutes INTEGER NOT NULL DEFAULT 60, -- Minimum time between repeat alerts
    max_alerts_per_hour INTEGER DEFAULT 5,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    
    -- Indexes for performance
    CONSTRAINT alert_rules_name_unique UNIQUE (name)
);

-- Create index for efficient rule evaluation
CREATE INDEX IF NOT EXISTS idx_alert_rules_active 
ON alert_rules (enabled, metric_type, station_id) 
WHERE enabled = true;

-- =====================================================
-- Alert History Table
-- Records all alert events and their outcomes
-- =====================================================
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    
    -- Alert details
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    metric_type VARCHAR(50) NOT NULL,
    station_id VARCHAR(50),
    
    -- Trigger information
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    trigger_value NUMERIC,
    threshold_value NUMERIC,
    message TEXT NOT NULL,
    
    -- Alert state management
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved', 'suppressed')),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),
    
    -- Notification tracking
    notifications_sent JSONB DEFAULT '[]',
    -- Example: [{"channel": "email", "sent_at": "2025-08-27T10:00:00Z", "success": true, "recipient": "admin@pond.com"}]
    
    -- Related data snapshot
    related_data JSONB,
    -- Store snapshot of metrics that triggered the alert
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('alert_history', 'triggered_at', if_not_exists => TRUE);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_alert_history_rule_id ON alert_history (rule_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_history_status ON alert_history (status, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_history_severity ON alert_history (severity, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_history_station ON alert_history (station_id, triggered_at DESC);

-- =====================================================
-- User Notification Preferences
-- Manages how users want to receive alerts
-- =====================================================
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL, -- For future user system integration
    
    -- Contact information
    email VARCHAR(255),
    phone_number VARCHAR(20),
    
    -- Notification preferences
    email_enabled BOOLEAN NOT NULL DEFAULT true,
    sms_enabled BOOLEAN NOT NULL DEFAULT false,
    
    -- Alert filtering
    min_severity VARCHAR(20) NOT NULL DEFAULT 'warning' CHECK (min_severity IN ('info', 'warning', 'critical')),
    station_filter JSONB, -- ["station1", "station2"] or null for all
    metric_filter JSONB, -- ["water_level", "temperature"] or null for all
    
    -- Timing preferences
    quiet_hours_start TIME, -- e.g., '22:00'
    quiet_hours_end TIME, -- e.g., '08:00'
    weekend_notifications BOOLEAN NOT NULL DEFAULT true,
    
    -- Rate limiting
    max_emails_per_hour INTEGER DEFAULT 10,
    max_sms_per_hour INTEGER DEFAULT 5,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT user_notification_preferences_user_id_unique UNIQUE (user_id)
);

-- =====================================================
-- Notification Channels Configuration
-- Manages different notification delivery methods
-- =====================================================
CREATE TABLE IF NOT EXISTS notification_channels (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Channel identification
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'sms', 'webhook', 'slack')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Configuration (JSON for flexibility)
    config JSONB NOT NULL,
    -- Email: {"smtp_server": "smtp.gmail.com", "smtp_port": 587, "username": "alerts@pond.com"}
    -- SMS: {"provider": "twilio", "account_sid": "...", "auth_token": "..."}
    -- Webhook: {"url": "https://hooks.slack.com/...", "method": "POST", "headers": {...}}
    
    -- Channel status
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_test_at TIMESTAMP WITH TIME ZONE,
    last_test_success BOOLEAN,
    last_error TEXT,
    
    -- Rate limiting
    rate_limit_per_hour INTEGER DEFAULT 100,
    current_hour_count INTEGER DEFAULT 0,
    current_hour_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT notification_channels_type_name_unique UNIQUE (channel_type, name)
);

-- =====================================================
-- Alert Rule Evaluation Log
-- Tracks rule evaluation performance and debugging
-- =====================================================
CREATE TABLE IF NOT EXISTS alert_rule_evaluations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    
    -- Evaluation details
    evaluated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    evaluation_time_ms INTEGER NOT NULL,
    
    -- Input data
    metric_value NUMERIC,
    station_id VARCHAR(50),
    data_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Result
    rule_triggered BOOLEAN NOT NULL DEFAULT false,
    trigger_reason TEXT,
    
    -- Error handling
    evaluation_error TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('alert_rule_evaluations', 'evaluated_at', if_not_exists => TRUE);

-- Index for performance monitoring
CREATE INDEX IF NOT EXISTS idx_alert_rule_evaluations_rule_id 
ON alert_rule_evaluations (rule_id, evaluated_at DESC);

-- =====================================================
-- System Alert Settings
-- Global alerting system configuration
-- =====================================================
CREATE TABLE IF NOT EXISTS alert_system_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    
    -- System-wide toggles
    alerting_enabled BOOLEAN NOT NULL DEFAULT true,
    email_notifications_enabled BOOLEAN NOT NULL DEFAULT true,
    sms_notifications_enabled BOOLEAN NOT NULL DEFAULT false,
    
    -- Default settings
    default_cooldown_minutes INTEGER NOT NULL DEFAULT 60,
    default_max_alerts_per_hour INTEGER NOT NULL DEFAULT 10,
    
    -- Evaluation settings
    evaluation_interval_seconds INTEGER NOT NULL DEFAULT 60,
    max_evaluation_time_ms INTEGER NOT NULL DEFAULT 5000,
    
    -- Cleanup settings
    history_retention_days INTEGER NOT NULL DEFAULT 90,
    evaluation_log_retention_days INTEGER NOT NULL DEFAULT 30,
    
    -- Emergency settings
    emergency_disable_threshold INTEGER NOT NULL DEFAULT 100, -- Disable if more than N alerts in hour
    
    -- Metadata
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system',
    
    CONSTRAINT alert_system_settings_singleton CHECK (id = 1)
);

-- Insert default settings
INSERT INTO alert_system_settings DEFAULT VALUES 
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- Initial Alert Rules
-- Pre-configured alert rules for common scenarios
-- =====================================================

-- Critical water level alert
INSERT INTO alert_rules (
    name, description, rule_type, metric_type, conditions, severity, channels, cooldown_minutes
) VALUES (
    'Critical High Water Level',
    'Alert when water level exceeds critical threshold',
    'threshold',
    'water_level',
    '{"operator": "gt", "value": 180.0}',
    'critical',
    '["email", "sms"]',
    30
) ON CONFLICT (name) DO NOTHING;

-- Low water level warning
INSERT INTO alert_rules (
    name, description, rule_type, metric_type, conditions, severity, channels
) VALUES (
    'Low Water Level Warning',
    'Alert when water level drops below normal range',
    'threshold',
    'water_level',
    '{"operator": "lt", "value": 50.0}',
    'warning',
    '["email"]'
) ON CONFLICT (name) DO NOTHING;

-- High temperature alert
INSERT INTO alert_rules (
    name, description, rule_type, metric_type, conditions, severity, channels
) VALUES (
    'High Temperature Alert',
    'Alert when station temperature exceeds safe operating range',
    'threshold',
    'temperature',
    '{"operator": "gt", "value": 45.0}',
    'warning',
    '["email"]'
) ON CONFLICT (name) DO NOTHING;

-- Low battery alert
INSERT INTO alert_rules (
    name, description, rule_type, metric_type, conditions, severity, channels
) VALUES (
    'Low Battery Voltage',
    'Alert when station battery voltage drops below operational threshold',
    'threshold',
    'battery_voltage',
    '{"operator": "lt", "value": 11.5}',
    'warning',
    '["email"]'
) ON CONFLICT (name) DO NOTHING;

-- Missing data alert
INSERT INTO alert_rules (
    name, description, rule_type, metric_type, conditions, severity, channels, cooldown_minutes
) VALUES (
    'Station Communication Lost',
    'Alert when no data received from station for extended period',
    'missing_data',
    'temperature',
    '{"max_age_minutes": 120}',
    'critical',
    '["email", "sms"]',
    120
) ON CONFLICT (name) DO NOTHING;

-- Default notification preferences for system admin
INSERT INTO user_notification_preferences (
    user_id, email, email_enabled, sms_enabled, min_severity
) VALUES (
    'admin',
    'admin@pondmonitor.local',
    true,
    false,
    'warning'
) ON CONFLICT (user_id) DO NOTHING;

-- =====================================================
-- Functions and Triggers
-- =====================================================

-- Function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_alert_rules_updated_at 
    BEFORE UPDATE ON alert_rules 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_notification_preferences_updated_at 
    BEFORE UPDATE ON user_notification_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_channels_updated_at 
    BEFORE UPDATE ON notification_channels 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to get active alerts for a station
CREATE OR REPLACE FUNCTION get_active_alerts_for_station(station_name VARCHAR)
RETURNS TABLE(
    alert_id UUID,
    rule_name VARCHAR,
    severity VARCHAR,
    message TEXT,
    triggered_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ah.id,
        ar.name,
        ah.severity,
        ah.message,
        ah.triggered_at
    FROM alert_history ah
    JOIN alert_rules ar ON ah.rule_id = ar.id
    WHERE ah.station_id = station_name
      AND ah.status = 'active'
    ORDER BY ah.triggered_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get alert statistics
CREATE OR REPLACE FUNCTION get_alert_statistics(days INTEGER DEFAULT 7)
RETURNS TABLE(
    total_alerts BIGINT,
    critical_alerts BIGINT,
    warning_alerts BIGINT,
    info_alerts BIGINT,
    resolved_alerts BIGINT,
    active_alerts BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
        COUNT(*) FILTER (WHERE severity = 'info') as info_alerts,
        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts,
        COUNT(*) FILTER (WHERE status = 'active') as active_alerts
    FROM alert_history
    WHERE triggered_at >= NOW() - INTERVAL '%s days' % days;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Indexes for Performance Optimization
-- =====================================================

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_alert_history_composite_status_time 
ON alert_history (status, severity, triggered_at DESC);

CREATE INDEX IF NOT EXISTS idx_alert_history_rule_status_time 
ON alert_history (rule_id, status, triggered_at DESC);

-- Partial indexes for active alerts (most common queries)
CREATE INDEX IF NOT EXISTS idx_alert_history_active_alerts 
ON alert_history (triggered_at DESC) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled_by_type 
ON alert_rules (metric_type, station_id) 
WHERE enabled = true;

-- =====================================================
-- Data Retention and Cleanup
-- =====================================================

-- Function to clean up old alert data
CREATE OR REPLACE FUNCTION cleanup_alert_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    retention_days INTEGER;
    eval_retention_days INTEGER;
BEGIN
    -- Get retention settings
    SELECT history_retention_days, evaluation_log_retention_days 
    INTO retention_days, eval_retention_days
    FROM alert_system_settings 
    WHERE id = 1;
    
    -- Clean up old alert history (keep resolved alerts longer)
    DELETE FROM alert_history 
    WHERE triggered_at < NOW() - INTERVAL '%s days' % retention_days
      AND status IN ('resolved', 'acknowledged');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old evaluation logs
    DELETE FROM alert_rule_evaluations 
    WHERE evaluated_at < NOW() - INTERVAL '%s days' % eval_retention_days;
    
    -- Reset hourly counters for notification channels if needed
    UPDATE notification_channels 
    SET 
        current_hour_count = 0,
        current_hour_start = NOW()
    WHERE current_hour_start < NOW() - INTERVAL '1 hour';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- View for alert dashboard
CREATE OR REPLACE VIEW alert_dashboard AS
SELECT 
    ar.name as rule_name,
    ar.severity as rule_severity,
    ar.enabled,
    ah.id as alert_id,
    ah.status as alert_status,
    ah.triggered_at,
    ah.message,
    ah.station_id,
    ah.trigger_value,
    ah.threshold_value
FROM alert_rules ar
LEFT JOIN alert_history ah ON ar.id = ah.rule_id 
    AND ah.status = 'active'
WHERE ar.enabled = true
ORDER BY ar.severity DESC, ah.triggered_at DESC NULLS LAST;

-- View for alert summary by station
CREATE OR REPLACE VIEW alert_summary_by_station AS
SELECT 
    COALESCE(ah.station_id, 'system') as station_id,
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE ah.severity = 'critical') as critical_count,
    COUNT(*) FILTER (WHERE ah.severity = 'warning') as warning_count,
    COUNT(*) FILTER (WHERE ah.status = 'active') as active_count,
    MAX(ah.triggered_at) as last_alert_time
FROM alert_history ah
WHERE ah.triggered_at >= NOW() - INTERVAL '7 days'
GROUP BY ah.station_id
ORDER BY critical_count DESC, warning_count DESC;

-- =====================================================
-- Grant Permissions
-- =====================================================

-- Grant permissions to pond_user (application user)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pond_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO pond_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pond_user;

-- =====================================================
-- Schema Complete
-- =====================================================

-- Log schema creation
DO $$
BEGIN
    RAISE NOTICE 'PondMonitor Alerting System schema created successfully';
    RAISE NOTICE 'Created tables: alert_rules, alert_history, user_notification_preferences, notification_channels, alert_rule_evaluations, alert_system_settings';
    RAISE NOTICE 'Created functions: get_active_alerts_for_station, get_alert_statistics, cleanup_alert_data';
    RAISE NOTICE 'Created views: alert_dashboard, alert_summary_by_station';
    RAISE NOTICE 'Inserted default alert rules and system settings';
END $$;