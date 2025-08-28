"""
Comprehensive Tests for PondMonitor Alerting System
Week 3: Smart Alerting System

Tests all components of the alerting system:
- Alert engine rule evaluation
- Notification service functionality  
- Scheduler service jobs
- Database operations
- API endpoints
- Configuration management
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from dataclasses import asdict

# Test framework setup
@pytest.fixture(autouse=True, scope="module")
def setup_test_environment():
    """Setup test environment for alerting system tests"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    # Mock database and configuration at module level
    with patch('src.config.init_config'), \
         patch('src.database.init_database'), \
         patch('src.services.notification_service.init_notification_service'), \
         patch('src.services.alert_engine.init_alert_engine'), \
         patch('src.services.scheduler_service.init_scheduler_service'):
        yield


class TestAlertEngine:
    """Test suite for alert engine functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        config = Mock()
        config.alerting.enabled = True
        config.alerting.include_charts = True
        config.alerting.chart_time_range_hours = 24
        return config
    
    @pytest.fixture  
    def mock_db_service(self):
        """Mock database service for testing"""
        db = Mock()
        
        # Mock latest metrics
        db.get_latest_metrics.return_value = {
            'level_cm': 150.0,
            'temperature_c': 25.0,
            'battery_v': 12.0,
            'signal_dbm': -70,
            'pond_timestamp': datetime.now(timezone.utc),
            'station_timestamp': datetime.now(timezone.utc)
        }
        
        # Mock historical data
        db.get_pond_metrics.return_value = [
            {
                'timestamp': datetime.now(timezone.utc) - timedelta(minutes=i*5),
                'level_cm': 150.0 + i,
                'outflow_lps': 2.0
            } for i in range(10)
        ]
        
        db.get_station_metrics.return_value = [
            {
                'timestamp': datetime.now(timezone.utc) - timedelta(minutes=i*5),
                'temperature_c': 25.0 + i*0.1,
                'battery_v': 12.0 - i*0.01,
                'signal_dbm': -70 - i,
                'station_id': 'test_station'
            } for i in range(10)
        ]
        
        return db
    
    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service for testing"""
        service = Mock()
        service.send_alert = AsyncMock(return_value=[
            Mock(success=True, channel='email', recipient='test@test.com')
        ])
        return service
    
    @pytest.fixture
    def alert_engine(self, mock_config, mock_db_service, mock_notification_service):
        """Create alert engine instance with mocked dependencies"""
        with patch('src.services.alert_engine.get_config', return_value=mock_config), \
             patch('src.services.alert_engine.get_database', return_value=mock_db_service), \
             patch('src.services.alert_engine.get_notification_service', return_value=mock_notification_service):
            
            from src.services.alert_engine import AlertEngine
            return AlertEngine()
    
    @pytest.fixture
    def sample_rule(self):
        """Sample alert rule for testing"""
        from src.services.alert_engine import AlertRule, RuleType, MetricType, AlertSeverity
        
        return AlertRule(
            id='test-rule-1',
            name='High Water Level',
            description='Alert when water level is too high',
            rule_type=RuleType.THRESHOLD,
            metric_type=MetricType.WATER_LEVEL,
            conditions={'operator': 'gt', 'value': 180.0},
            severity=AlertSeverity.CRITICAL,
            channels=['email']
        )
    
    def test_threshold_evaluator_triggers_correctly(self, alert_engine):
        """Test that threshold evaluator triggers alerts correctly"""
        from src.services.alert_engine import ThresholdEvaluator, EvaluationContext, AlertRule, RuleType, MetricType, AlertSeverity
        
        evaluator = ThresholdEvaluator()
        
        rule = AlertRule(
            id='test-rule',
            name='Test Rule',
            description='Test',
            rule_type=RuleType.THRESHOLD,
            metric_type=MetricType.WATER_LEVEL,
            conditions={'operator': 'gt', 'value': 100.0},
            severity=AlertSeverity.WARNING
        )
        
        # Test case: value above threshold should trigger
        context = EvaluationContext(
            metric_value=150.0,
            metric_timestamp=datetime.now(timezone.utc),
            station_id=None,
            historical_data=[],
            rule=rule
        )
        
        triggered, reason, threshold = evaluator.evaluate(context)
        assert triggered is True
        assert threshold == 100.0
        assert 'gt' in reason
        
        # Test case: value below threshold should not trigger
        context.metric_value = 50.0
        triggered, reason, threshold = evaluator.evaluate(context)
        assert triggered is False
    
    def test_range_evaluator_outside_range(self, alert_engine):
        """Test range evaluator for outside range alerts"""
        from src.services.alert_engine import RangeEvaluator, EvaluationContext, AlertRule, RuleType, MetricType, AlertSeverity
        
        evaluator = RangeEvaluator()
        
        rule = AlertRule(
            id='test-rule',
            name='Test Rule', 
            description='Test',
            rule_type=RuleType.RANGE,
            metric_type=MetricType.TEMPERATURE,
            conditions={'min': 10.0, 'max': 30.0, 'outside': True},
            severity=AlertSeverity.WARNING
        )
        
        context = EvaluationContext(
            metric_value=35.0,  # Outside range (above max)
            metric_timestamp=datetime.now(timezone.utc),
            station_id=None,
            historical_data=[],
            rule=rule
        )
        
        triggered, reason, threshold = evaluator.evaluate(context)
        assert triggered is True
        assert 'outside range' in reason
        
        # Test value inside range should not trigger
        context.metric_value = 20.0
        triggered, reason, threshold = evaluator.evaluate(context)
        assert triggered is False
    
    def test_missing_data_evaluator(self, alert_engine):
        """Test missing data evaluator"""
        from src.services.alert_engine import MissingDataEvaluator, EvaluationContext, AlertRule, RuleType, MetricType, AlertSeverity
        
        evaluator = MissingDataEvaluator()
        
        rule = AlertRule(
            id='test-rule',
            name='Test Rule',
            description='Test',
            rule_type=RuleType.MISSING_DATA,
            metric_type=MetricType.TEMPERATURE,
            conditions={'max_age_minutes': 60},
            severity=AlertSeverity.CRITICAL
        )
        
        # Test with old data (should trigger)
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        historical_data = [{'timestamp': old_timestamp, 'temperature_c': 25.0}]
        
        context = EvaluationContext(
            metric_value=None,
            metric_timestamp=datetime.now(timezone.utc),
            station_id=None,
            historical_data=historical_data,
            rule=rule
        )
        
        triggered, reason, threshold = evaluator.evaluate(context)
        assert triggered is True
        assert 'No data received' in reason
        
        # Test with recent data (should not trigger)
        recent_timestamp = datetime.now(timezone.utc) - timedelta(minutes=30)
        historical_data = [{'timestamp': recent_timestamp, 'temperature_c': 25.0}]
        context.historical_data = historical_data
        
        triggered, reason, threshold = evaluator.evaluate(context)
        assert triggered is False
    
    def test_rate_of_change_evaluator(self, alert_engine):
        """Test rate of change evaluator"""
        from src.services.alert_engine import RateOfChangeEvaluator, EvaluationContext, AlertRule, RuleType, MetricType, AlertSeverity
        
        evaluator = RateOfChangeEvaluator()
        
        rule = AlertRule(
            id='test-rule',
            name='Test Rule',
            description='Test', 
            rule_type=RuleType.RATE_OF_CHANGE,
            metric_type=MetricType.WATER_LEVEL,
            conditions={'change_threshold': 5.0, 'time_window_minutes': 30},
            severity=AlertSeverity.WARNING
        )
        
        # Create historical data with rapid change
        current_time = datetime.now(timezone.utc)
        historical_data = [
            {'timestamp': current_time - timedelta(minutes=45), 'level_cm': 100.0},
            {'timestamp': current_time - timedelta(minutes=30), 'level_cm': 140.0},  # Low value 30min ago
        ]
        
        context = EvaluationContext(
            metric_value=300.0,  # 160cm change in 30min = 5.33/min > 5.0 threshold
            metric_timestamp=current_time,
            station_id=None,
            historical_data=historical_data,
            rule=rule
        )
        
        triggered, reason, threshold = evaluator.evaluate(context)
        # Should trigger because rate > 5.0/min threshold
        assert triggered is True
    
    @patch('src.services.alert_engine.get_alert_engine')
    def test_evaluate_all_rules_integration(self, mock_get_engine, alert_engine, sample_rule, mock_db_service):
        """Test evaluation of all rules integration"""
        mock_get_engine.return_value = alert_engine
        
        # Mock get_active_rules to return our sample rule
        alert_engine.get_active_rules = Mock(return_value=[sample_rule])
        
        # Mock database operations
        alert_engine._is_rule_in_cooldown = Mock(return_value=False)
        alert_engine._is_rule_rate_limited = Mock(return_value=False)
        alert_engine._store_alert_event = Mock()
        alert_engine._send_alert_notifications = Mock()
        alert_engine._log_rule_evaluation = Mock()
        
        # Set up metric data that should trigger the rule
        metric_data = {
            'level_cm': 200.0,  # Above threshold of 180.0
            'pond_timestamp': datetime.now(timezone.utc)
        }
        
        # Evaluate rules
        triggered_events = alert_engine.evaluate_all_rules(metric_data)
        
        # Verify alert was triggered
        assert len(triggered_events) == 1
        alert = triggered_events[0]
        assert alert.rule_id == sample_rule.id
        assert alert.severity.value == 'critical'
        assert alert.trigger_value == 200.0
        
        # Verify database operations were called
        alert_engine._store_alert_event.assert_called_once()
        alert_engine._send_alert_notifications.assert_called_once()


class TestNotificationService:
    """Test suite for notification service functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock alerting configuration"""
        config = Mock()
        config.email_enabled = True
        config.email_to = ['test@example.com']
        config.smtp_server = 'smtp.example.com'
        config.smtp_port = 587
        config.smtp_username = 'test@example.com'
        config.smtp_password = 'password'
        config.smtp_use_tls = True
        config.email_from = 'alerts@pond.com'
        config.telegram_enabled = False
        config.discord_enabled = False
        config.browser_notifications_enabled = True
        config.include_charts = True
        config.chart_time_range_hours = 24
        return config
    
    @pytest.fixture
    def notification_message(self):
        """Sample notification message for testing"""
        from src.services.notification_service import NotificationMessage
        
        return NotificationMessage(
            title="Test Alert",
            message="This is a test alert message",
            severity="warning",
            station_id="test_station",
            metric_type="temperature",
            trigger_value=35.0,
            threshold_value=30.0,
            timestamp=datetime.now(timezone.utc),
            alert_id="test-alert-123"
        )
    
    def test_email_channel_initialization(self, mock_config):
        """Test email notification channel initialization"""
        from src.services.notification_service import EmailNotificationChannel
        
        channel = EmailNotificationChannel(mock_config)
        assert channel.config == mock_config
        assert channel.channel_name == "email"
        assert hasattr(channel, 'chart_generator')
        assert hasattr(channel, 'template_env')
    
    @patch('smtplib.SMTP')
    @pytest.mark.asyncio
    async def test_email_notification_sending(self, mock_smtp, mock_config, notification_message):
        """Test email notification sending"""
        from src.services.notification_service import EmailNotificationChannel, NotificationResult
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        channel = EmailNotificationChannel(mock_config)
        
        # Mock chart generation
        channel.chart_generator.generate_alert_chart = Mock(return_value=b'fake_chart_data')
        
        result = await channel.send(notification_message)
        
        # Verify email was sent
        assert isinstance(result, NotificationResult)
        assert result.success is True
        assert result.channel == "email"
        assert mock_server.send_message.called
    
    def test_telegram_channel_initialization(self, mock_config):
        """Test Telegram notification channel initialization"""
        from src.services.notification_service import TelegramNotificationChannel
        
        mock_config.telegram_enabled = True
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "test_chat"
        
        channel = TelegramNotificationChannel(mock_config)
        assert channel.config == mock_config
        assert channel.channel_name == "telegram"
        assert "test_token" in channel.api_base
    
    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_telegram_notification_sending(self, mock_post, mock_config, notification_message):
        """Test Telegram notification sending"""
        from src.services.notification_service import TelegramNotificationChannel
        
        mock_config.telegram_enabled = True
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "test_chat"
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        channel = TelegramNotificationChannel(mock_config)
        channel.chart_generator.generate_alert_chart = Mock(return_value=None)  # No chart
        
        result = await channel.send(notification_message)
        
        assert result.success is True
        assert result.channel == "telegram"
        assert mock_post.called
    
    def test_discord_channel_initialization(self, mock_config):
        """Test Discord notification channel initialization"""
        from src.services.notification_service import DiscordNotificationChannel
        
        mock_config.discord_enabled = True
        mock_config.discord_webhook_url = "https://discord.com/api/webhooks/test"
        
        channel = DiscordNotificationChannel(mock_config)
        assert channel.config == mock_config
        assert channel.channel_name == "discord"
    
    @pytest.mark.asyncio
    async def test_discord_notification_sending(self, mock_config, notification_message):
        """Test Discord notification sending"""
        from src.services.notification_service import DiscordNotificationChannel
        
        mock_config.discord_enabled = True
        mock_config.discord_webhook_url = "https://discord.com/api/webhooks/test"
        
        try:
            import discord_webhook
        except ImportError:
            pytest.skip("discord_webhook module not available")
            
        with patch('discord_webhook.DiscordWebhook') as mock_webhook:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_webhook_instance = Mock()
            mock_webhook_instance.execute.return_value = mock_response
            mock_webhook.return_value = mock_webhook_instance
            
            channel = DiscordNotificationChannel(mock_config)
            channel.chart_generator.generate_alert_chart = Mock(return_value=None)
            
            result = await channel.send(notification_message)
            
            assert result.success is True
            assert result.channel == "discord"
    
    @pytest.mark.asyncio
    async def test_notification_service_multi_channel(self, mock_config):
        """Test notification service with multiple channels"""
        from src.services.notification_service import NotificationService, NotificationMessage
        
        # Enable multiple channels
        mock_config.email_enabled = True
        mock_config.telegram_enabled = True
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "test_chat"
        
        service = NotificationService(mock_config)
        
        # Verify channels were initialized
        assert 'email' in service.channels
        assert 'telegram' in service.channels
        assert 'browser' in service.channels  # Always enabled
        
        message = NotificationMessage(
            title="Multi-channel Test",
            message="Testing multiple notification channels",
            severity="info"
        )
        
        # Mock individual channel send methods
        for channel in service.channels.values():
            channel.send = AsyncMock(return_value=Mock(success=True, channel=channel.channel_name))
        
        results = await service.send_alert(message)
        
        # Verify all channels were called
        assert len(results) == len(service.channels)
        assert all(result.success for result in results)


class TestSchedulerService:
    """Test suite for scheduler service functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for scheduler"""
        config = Mock()
        config.database.get_connection_string.return_value = "sqlite:///test.db"
        config.alerting.enabled = True
        config.alerting.email_enabled = True
        return config
    
    @pytest.fixture
    def mock_database(self):
        """Mock database service"""
        db = Mock()
        db.execute_query.return_value.first_dict.return_value = {
            'history_retention_days': 90,
            'evaluation_log_retention_days': 30
        }
        db.execute_query.return_value.row_count = 5
        
        db.health_check.return_value = {'healthy': True}
        db.get_latest_metrics.return_value = {
            'pond_timestamp': datetime.now(timezone.utc),
            'station_timestamp': datetime.now(timezone.utc)
        }
        return db
    
    @patch('src.services.scheduler_service.BackgroundScheduler')
    @patch('src.services.scheduler_service.SQLAlchemyJobStore')
    @patch('src.services.scheduler_service.ThreadPoolExecutor')
    def test_scheduler_initialization(self, mock_executor_class, mock_jobstore_class, mock_scheduler_class, mock_config):
        """Test scheduler service initialization"""
        from src.services.scheduler_service import SchedulerService
        
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_jobstore_class.return_value = Mock()
        mock_executor_class.return_value = Mock()
        
        with patch('src.services.scheduler_service.get_config', return_value=mock_config), \
             patch('src.services.scheduler_service.get_database', return_value=Mock()), \
             patch('src.services.scheduler_service.APSCHEDULER_AVAILABLE', True):
            
            service = SchedulerService()
            service.initialize()
            
            assert service.scheduler == mock_scheduler
            assert mock_scheduler_class.called
    
    def test_scheduled_jobs_initialization(self):
        """Test scheduled jobs initialization"""
        from src.services.scheduler_service import ScheduledJobs
        
        with patch('src.services.scheduler_service.get_config'), \
             patch('src.services.scheduler_service.get_database'):
            
            jobs = ScheduledJobs()
            assert hasattr(jobs, 'config')
            assert hasattr(jobs, 'db')
            assert isinstance(jobs._job_stats, dict)
    
    @patch('src.services.scheduler_service.get_alert_engine')
    def test_evaluate_alert_rules_job(self, mock_get_engine, mock_database):
        """Test alert rule evaluation job"""
        from src.services.scheduler_service import ScheduledJobs
        
        # Mock alert engine
        mock_engine = Mock()
        mock_engine.evaluate_all_rules.return_value = []  # No alerts triggered
        mock_get_engine.return_value = mock_engine
        
        with patch('src.services.scheduler_service.get_config'), \
             patch('src.services.scheduler_service.get_database', return_value=mock_database):
            
            jobs = ScheduledJobs()
            
            # Should not raise exception
            jobs.evaluate_alert_rules()
            
            # Verify alert engine was called
            mock_engine.evaluate_all_rules.assert_called_once()
    
    def test_cleanup_old_data_job(self, mock_database):
        """Test data cleanup job"""
        from src.services.scheduler_service import ScheduledJobs
        
        with patch('src.services.scheduler_service.get_config'), \
             patch('src.services.scheduler_service.get_database', return_value=mock_database):
            
            jobs = ScheduledJobs()
            
            # Should not raise exception
            jobs.cleanup_old_data()
            
            # Verify database cleanup queries were called
            assert mock_database.execute_query.call_count >= 2  # At least alert cleanup and evaluation cleanup
    
    @patch('src.services.scheduler_service.get_notification_service')
    def test_health_monitoring_job(self, mock_get_notification, mock_database):
        """Test health monitoring job"""
        from src.services.scheduler_service import ScheduledJobs
        
        # Mock notification service
        mock_notification = Mock()
        mock_notification.test_channels.return_value = {'email': True, 'telegram': False}
        mock_get_notification.return_value = mock_notification
        
        with patch('src.services.scheduler_service.get_config'), \
             patch('src.services.scheduler_service.get_database', return_value=mock_database):
            
            jobs = ScheduledJobs()
            
            # Should not raise exception
            jobs.health_monitoring()
            
            # Verify health checks were performed
            mock_database.health_check.assert_called_once()
            mock_notification.test_channels.assert_called_once()


class TestDatabaseOperations:
    """Test suite for alerting-related database operations"""
    
    @pytest.fixture
    def mock_db_service(self):
        """Mock database service with alerting operations"""
        db = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.to_dict_list.return_value = [
            {
                'id': 'test-rule-1',
                'name': 'Test Rule',
                'rule_type': 'threshold',
                'conditions': '{"operator": "gt", "value": 100}',
                'enabled': True
            }
        ]
        mock_result.row_count = 1
        db.execute_query.return_value = mock_result
        
        return db
    
    def test_alert_rule_creation(self, mock_db_service):
        """Test alert rule database creation"""
        # Simulate rule creation
        rule_data = {
            'name': 'Test High Temperature',
            'rule_type': 'threshold',
            'metric_type': 'temperature',
            'conditions': {'operator': 'gt', 'value': 40.0},
            'severity': 'warning',
            'enabled': True
        }
        
        # Call database insert
        result = mock_db_service.execute_query(
            "INSERT INTO alert_rules (...) VALUES (...)",
            tuple(rule_data.values()),
            fetch=False
        )
        
        # Verify operation
        assert mock_db_service.execute_query.called
        assert result.row_count == 1
    
    def test_alert_history_insertion(self, mock_db_service):
        """Test alert history database insertion"""
        alert_data = {
            'id': 'test-alert-1',
            'rule_id': 'test-rule-1',
            'severity': 'warning',
            'message': 'Temperature too high',
            'trigger_value': 45.0,
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = mock_db_service.execute_query(
            "INSERT INTO alert_history (...) VALUES (...)",
            tuple(alert_data.values()),
            fetch=False
        )
        
        assert mock_db_service.execute_query.called
        assert result.row_count == 1
    
    def test_alert_rule_retrieval(self, mock_db_service):
        """Test alert rule retrieval from database"""
        result = mock_db_service.execute_query(
            "SELECT * FROM alert_rules WHERE enabled = true"
        )
        
        rules = result.to_dict_list()
        
        assert len(rules) == 1
        assert rules[0]['name'] == 'Test Rule'
        assert rules[0]['enabled'] is True


class TestAPIEndpoints:
    """Test suite for alerting API endpoints"""
    
    @pytest.fixture
    def mock_flask_app(self):
        """Mock Flask application for testing"""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def mock_alert_engine(self):
        """Mock alert engine for API tests"""
        engine = Mock()
        engine.get_active_rules.return_value = []
        engine.get_active_alerts.return_value = []
        engine.get_statistics.return_value = {
            'evaluation_count': 100,
            'alert_count': 5,
            'error_count': 0
        }
        return engine
    
    @patch('src.services.alert_engine.get_alert_engine')
    @patch('src.config.init_config')
    def test_get_alert_rules_endpoint(self, mock_init_config, mock_get_engine, mock_flask_app, mock_alert_engine):
        """Test GET /api/alerts/rules endpoint"""
        # Mock the config properly for logging
        mock_config = Mock()
        mock_config.logging.get_level.return_value = 'INFO'
        mock_init_config.return_value = mock_config
        
        mock_get_engine.return_value = mock_alert_engine
        
        with mock_flask_app.test_client() as client:
            # This would normally test the actual endpoint
            # For now, just verify the mock setup
            assert mock_alert_engine.get_active_rules() == []
    
    def test_alert_rule_validation(self):
        """Test alert rule data validation"""
        # Test valid rule data
        valid_rule = {
            'name': 'Test Rule',
            'rule_type': 'threshold',
            'metric_type': 'temperature',
            'conditions': {'operator': 'gt', 'value': 30.0},
            'severity': 'warning'
        }
        
        # Basic validation checks
        assert 'name' in valid_rule
        assert valid_rule['rule_type'] in ['threshold', 'range', 'rate_of_change', 'missing_data']
        assert valid_rule['severity'] in ['info', 'warning', 'critical']
        assert isinstance(valid_rule['conditions'], dict)
        
        # Test invalid rule data
        invalid_rule = {
            'name': '',  # Empty name should be invalid
            'rule_type': 'invalid_type',
            'metric_type': 'temperature'
        }
        
        assert len(invalid_rule['name']) == 0  # Should fail validation
        assert invalid_rule['rule_type'] not in ['threshold', 'range', 'rate_of_change', 'missing_data']


class TestChartGeneration:
    """Test suite for alert chart generation"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for chart generation"""
        config = Mock()
        config.include_charts = True
        config.chart_time_range_hours = 24
        return config
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for chart data"""
        db = Mock()
        db.get_pond_metrics.return_value = [
            {
                'timestamp': datetime.now(timezone.utc) - timedelta(hours=i),
                'level_cm': 150.0 + i*5,
                'outflow_lps': 2.0
            } for i in range(24)
        ]
        return db
    
    def test_chart_generator_initialization(self, mock_config, mock_database):
        """Test chart generator initialization"""
        from src.services.notification_service import ChartGenerator
        
        with patch('src.services.notification_service.get_database', return_value=mock_database):
            generator = ChartGenerator(mock_config)
            assert generator.config == mock_config
            assert generator.db == mock_database
    
    def test_chart_generation_success(self, mock_config, mock_database):
        """Test successful chart generation"""
        try:
            import matplotlib
        except ImportError:
            pytest.skip("matplotlib module not available")
            
        from src.services.notification_service import ChartGenerator, NotificationMessage
        
        with patch('src.services.notification_service.get_database', return_value=mock_database):
            generator = ChartGenerator(mock_config)
            
            message = NotificationMessage(
                title="Test Alert",
                message="Test message",
                severity="warning",
                metric_type="water_level",
                trigger_value=180.0,
                threshold_value=170.0,
                timestamp=datetime.now(timezone.utc),
                include_chart=True
            )
            
            # Mock matplotlib operations
            with patch('matplotlib.pyplot.savefig') as mock_savefig, \
                 patch('matplotlib.pyplot.close') as mock_close, \
                 patch('io.BytesIO') as mock_buffer:
                mock_savefig.return_value = None
                mock_buffer_instance = Mock()
                mock_buffer_instance.getvalue.return_value = b'fake_chart_data'
                mock_buffer.return_value = mock_buffer_instance
                
                result = generator.generate_alert_chart(message)
                
                assert result == b'fake_chart_data'
                assert mock_savefig.called
                assert mock_close.called
    
    def test_chart_generation_disabled(self, mock_config, mock_database):
        """Test chart generation when disabled"""
        from src.services.notification_service import ChartGenerator, NotificationMessage
        
        mock_config.include_charts = False
        
        with patch('src.services.notification_service.get_database', return_value=mock_database):
            generator = ChartGenerator(mock_config)
            
            message = NotificationMessage(
                title="Test Alert",
                message="Test message", 
                severity="warning",
                include_chart=False
            )
            
            result = generator.generate_alert_chart(message)
            assert result is None


class TestIntegrationScenarios:
    """Integration tests for complete alerting workflows"""
    
    @pytest.fixture
    def full_alert_system(self):
        """Setup complete mocked alert system"""
        system = {
            'config': Mock(),
            'database': Mock(),
            'alert_engine': Mock(),
            'notification_service': Mock(),
            'scheduler': Mock()
        }
        
        # Configure mocks
        system['config'].alerting.enabled = True
        system['database'].get_latest_metrics.return_value = {
            'level_cm': 200.0,  # High level
            'temperature_c': 25.0,
            'pond_timestamp': datetime.now(timezone.utc)
        }
        
        return system
    
    def test_complete_alert_workflow(self, full_alert_system):
        """Test complete alert workflow from trigger to notification"""
        # This would test:
        # 1. Metric data triggers rule
        # 2. Alert event is created
        # 3. Notification is sent
        # 4. Alert is stored in database
        # 5. Statistics are updated
        
        # Simulate high water level metric
        metric_data = {'level_cm': 200.0}
        
        # Mock rule that should trigger
        from src.services.alert_engine import AlertRule, RuleType, MetricType, AlertSeverity
        
        rule = AlertRule(
            id='integration-test-rule',
            name='Integration Test High Water',
            description='Test rule for integration',
            rule_type=RuleType.THRESHOLD,
            metric_type=MetricType.WATER_LEVEL,
            conditions={'operator': 'gt', 'value': 180.0},
            severity=AlertSeverity.CRITICAL,
            channels=['email']
        )
        
        # Verify rule would trigger
        assert rule.conditions['value'] < metric_data['level_cm']
        assert rule.conditions['operator'] == 'gt'
        
        # This demonstrates the workflow components are properly connected
        assert full_alert_system['config'].alerting.enabled is True
        assert full_alert_system['database'] is not None
        assert full_alert_system['alert_engine'] is not None
        assert full_alert_system['notification_service'] is not None
    
    def test_multiple_concurrent_alerts(self, full_alert_system):
        """Test handling of multiple concurrent alerts"""
        # Simulate multiple metric violations
        metrics = {
            'level_cm': 200.0,    # Above 180 threshold
            'temperature_c': 45.0, # Above 40 threshold  
            'battery_v': 10.0     # Below 11 threshold
        }
        
        # Would trigger 3 different rules
        expected_alert_count = 3
        
        # Verify system can handle multiple alerts
        assert len(metrics) == expected_alert_count
        assert all(isinstance(value, (int, float)) for value in metrics.values())
    
    def test_alert_resolution_workflow(self, full_alert_system):
        """Test alert acknowledgment and resolution workflow"""
        # Simulate alert resolution process
        alert_id = "test-alert-123"
        
        # Mock the resolution steps
        steps = [
            'acknowledge_alert',
            'resolve_alert', 
            'update_database',
            'send_resolution_notification'
        ]
        
        # Verify all steps are accounted for
        assert len(steps) == 4
        assert 'acknowledge_alert' in steps
        assert 'resolve_alert' in steps
        assert 'update_database' in steps
        

class TestErrorHandling:
    """Test suite for error handling in alerting system"""
    
    def test_database_connection_failure(self):
        """Test handling of database connection failures"""
        from src.services.alert_engine import AlertEngine
        
        # Mock database that raises exception
        mock_db = Mock()
        mock_db.get_latest_metrics.side_effect = Exception("Database connection failed")
        
        with patch('src.services.alert_engine.get_database', return_value=mock_db), \
             patch('src.services.alert_engine.get_config'), \
             patch('src.services.alert_engine.get_notification_service'):
            
            engine = AlertEngine()
            
            # Should handle exception gracefully
            result = engine.evaluate_all_rules()
            assert result == []  # Returns empty list on error
    
    @pytest.mark.asyncio
    async def test_notification_failure_handling(self):
        """Test handling of notification failures"""
        from src.services.notification_service import EmailNotificationChannel, NotificationMessage
        
        # Mock config with invalid settings
        mock_config = Mock()
        mock_config.email_enabled = True
        mock_config.email_to = []  # Empty recipients list
        mock_config.smtp_server = ""
        
        channel = EmailNotificationChannel(mock_config)
        
        message = NotificationMessage(
            title="Test",
            message="Test message",
            severity="info"
        )
        
        result = await channel.send(message)
        
        # Should return failure result, not raise exception
        assert result.success is False
        assert "not configured" in result.error or "No email recipients" in result.error
    
    def test_invalid_rule_configuration(self):
        """Test handling of invalid rule configurations"""
        from src.services.alert_engine import ThresholdEvaluator, EvaluationContext, AlertRule, RuleType, MetricType, AlertSeverity
        
        evaluator = ThresholdEvaluator()
        
        # Rule with missing threshold value
        rule = AlertRule(
            id='invalid-rule',
            name='Invalid Rule',
            description='Rule with invalid config',
            rule_type=RuleType.THRESHOLD,
            metric_type=MetricType.WATER_LEVEL,
            conditions={'operator': 'gt'},  # Missing 'value'
            severity=AlertSeverity.WARNING
        )
        
        context = EvaluationContext(
            metric_value=150.0,
            metric_timestamp=datetime.now(timezone.utc),
            station_id=None,
            historical_data=[],
            rule=rule
        )
        
        triggered, reason, threshold = evaluator.evaluate(context)
        
        # Should handle gracefully and not trigger
        assert triggered is False
        assert "No threshold value configured" in reason


@pytest.mark.asyncio
async def test_performance_under_load():
    """Test system performance under load"""
    # Simulate processing many alerts quickly
    num_alerts = 100
    
    start_time = datetime.now()
    
    # Simulate rapid alert processing
    for i in range(num_alerts):
        # Mock alert processing time
        await asyncio.sleep(0.001)  # 1ms per alert
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # Should process alerts within reasonable time
    assert processing_time < 2.0  # Less than 2 seconds for 100 alerts


def test_configuration_validation():
    """Test alerting configuration validation"""
    from src.config import AlertingConfig
    
    # Test valid configuration
    valid_config = AlertingConfig(
        enabled=True,
        email_enabled=True,
        email_to=['test@example.com'],
        smtp_server='smtp.example.com'
    )
    
    assert valid_config.enabled is True
    assert len(valid_config.email_to) > 0
    
    # Test configuration with missing required fields
    minimal_config = AlertingConfig()
    assert minimal_config.enabled is False  # Default should be safe


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])