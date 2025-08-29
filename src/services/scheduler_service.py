"""
PondMonitor Background Job Scheduler

Background job scheduling service using APScheduler for:
- Periodic alert rule evaluation
- Data cleanup and maintenance tasks
- Notification retry logic
- Health monitoring and diagnostics
- Automated report generation

Features:
- Persistent job storage with database backing
- Error handling and job retry mechanisms
- Job monitoring and statistics
- Graceful shutdown and recovery
- Integration with Flask application lifecycle
"""

import logging
import atexit
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

# Handle optional APScheduler dependencies
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"APScheduler import failed: {e}")
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    IntervalTrigger = None
    CronTrigger = None
    EVENT_JOB_EXECUTED = None
    EVENT_JOB_ERROR = None
    EVENT_JOB_MISSED = None
    SQLAlchemyJobStore = None
    ThreadPoolExecutor = None

from ..config import get_config
from ..database import get_database
from .alert_engine import get_alert_engine
from .notification_service import get_notification_service

logger = logging.getLogger(__name__)


# Standalone job functions that can be pickled
def evaluate_alert_rules_job():
    """Standalone job function for alert rule evaluation"""
    try:
        logger.debug("Starting periodic alert rule evaluation")
        
        # Get alert engine and evaluate rules
        alert_engine = get_alert_engine()
        triggered_events = alert_engine.evaluate_all_rules()
        
        logger.info(f"Alert rule evaluation completed: {len(triggered_events)} alerts triggered")
        
    except Exception as e:
        logger.error(f"Alert rule evaluation failed: {e}")
        raise


def cleanup_old_data_job():
    """Standalone job function for data cleanup"""
    try:
        logger.debug("Starting data cleanup job")
        
        db = get_database()
        
        # Get retention settings
        result = db.execute_query("""
            SELECT history_retention_days, evaluation_log_retention_days
            FROM alert_system_settings WHERE id = 1
        """)
        
        if not result.rows:
            logger.warning("No system settings found, using defaults")
            history_retention_days = 90
            eval_retention_days = 30
        else:
            settings = result.first_dict()
            history_retention_days = settings['history_retention_days']
            eval_retention_days = settings['evaluation_log_retention_days']
        
        cleanup_count = 0
        
        # Clean up old resolved alerts
        history_cutoff = datetime.now(timezone.utc) - timedelta(days=history_retention_days)
        result = db.execute_query("""
            DELETE FROM alert_history 
            WHERE triggered_at < %s 
            AND status IN ('resolved', 'acknowledged')
        """, (history_cutoff,), fetch=False)
        cleanup_count += result.row_count
        
        # Clean up old evaluation logs
        eval_cutoff = datetime.now(timezone.utc) - timedelta(days=eval_retention_days)
        result = db.execute_query("""
            DELETE FROM alert_rule_evaluations 
            WHERE evaluated_at < %s
        """, (eval_cutoff,), fetch=False)
        cleanup_count += result.row_count
        
        logger.info(f"Data cleanup completed: {cleanup_count} records cleaned")
        
    except Exception as e:
        logger.error(f"Data cleanup job failed: {e}")
        raise


def health_monitoring_job():
    """Standalone job function for system health monitoring"""
    try:
        logger.debug("Starting health monitoring job")
        
        db = get_database()
        config = get_config()
        
        # Check database health
        db_health = db.health_check()
        
        # Check notification service health
        notification_service = get_notification_service()
        channel_status = notification_service.test_channels()
        
        # Check for any critical system issues
        issues = []
        
        if not db_health.get('healthy', False):
            issues.append("Database health check failed")
        
        failed_channels = [ch for ch, status in channel_status.items() if not status]
        if failed_channels:
            issues.append(f"Notification channels failed: {', '.join(failed_channels)}")
        
        # Check for stuck/old data
        latest_metrics = db.get_latest_metrics()
        if latest_metrics:
            data_age_hours = 2
            if 'pond_timestamp' in latest_metrics:
                pond_age = (datetime.now(timezone.utc) - latest_metrics['pond_timestamp']).total_seconds() / 3600
                if pond_age > data_age_hours:
                    issues.append(f"Pond data is {pond_age:.1f} hours old")
            
            if 'station_timestamp' in latest_metrics:
                station_age = (datetime.now(timezone.utc) - latest_metrics['station_timestamp']).total_seconds() / 3600
                if station_age > data_age_hours:
                    issues.append(f"Station data is {station_age:.1f} hours old")
        
        # Generate system health alert if issues found
        if issues and config.alerting.enabled:
            _generate_health_alert(issues)
        
        status = "healthy" if not issues else f"{len(issues)} issues found"
        logger.info(f"Health monitoring completed: {status}")
        
    except Exception as e:
        logger.error(f"Health monitoring job failed: {e}")
        raise


def generate_daily_summary_job():
    """Standalone job function for daily summary generation"""
    try:
        logger.debug("Starting daily summary generation")
        
        config = get_config()
        if not config.alerting.enabled or not config.alerting.email_enabled:
            logger.info("Daily summary skipped - alerting not configured")
            return
        
        # Generate summary data (simplified version)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        db = get_database()
        
        # Get alert statistics
        alert_stats = db.execute_query("""
            SELECT 
                COUNT(*) as total_alerts,
                COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
                COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
                COUNT(*) FILTER (WHERE status = 'active') as active_alerts,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts
            FROM alert_history
            WHERE triggered_at BETWEEN %s AND %s
        """, (start_time, end_time)).first_dict()
        
        # Create notification message
        from .notification_service import NotificationMessage
        
        message = NotificationMessage(
            title="PondMonitor Daily Summary",
            message=f"Daily summary: {alert_stats['total_alerts']} alerts, {alert_stats['active_alerts']} active",
            severity="info",
            timestamp=datetime.now(timezone.utc),
            include_chart=True
        )
        
        # Send to email channel only
        notification_service = get_notification_service()
        import asyncio
        asyncio.run(notification_service.send_alert(message, channels=['email']))
        
        logger.info("Daily summary generated and sent")
        
    except Exception as e:
        logger.error(f"Daily summary generation failed: {e}")
        raise


def retry_failed_notifications_job():
    """Standalone job function for notification retry"""
    try:
        logger.debug("Starting notification retry job")
        
        db = get_database()
        
        # Find alerts with failed notifications from last hour
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        result = db.execute_query("""
            SELECT id, rule_id, severity, metric_type, station_id, triggered_at,
                   trigger_value, threshold_value, message, notifications_sent
            FROM alert_history
            WHERE triggered_at > %s
            AND status = 'active'
            AND notifications_sent IS NOT NULL
        """, (cutoff_time,))
        
        retry_count = 0
        
        for row_dict in result.to_dict_list():
            notifications = row_dict['notifications_sent']
            if isinstance(notifications, str):
                import json
                notifications = json.loads(notifications)
            
            # Check for failed notifications
            failed_channels = []
            for notification in notifications:
                if not notification.get('success', True):
                    failed_channels.append(notification['channel'])
            
            if failed_channels:
                # Retry failed notifications (simplified)
                retry_count += 1
                logger.info(f"Would retry notifications for alert {row_dict['id']}")
        
        logger.info(f"Notification retry completed: {retry_count} alerts processed")
        
    except Exception as e:
        logger.error(f"Notification retry job failed: {e}")
        raise


def _generate_health_alert(issues: List[str]):
    """Generate system health alert"""
    try:
        from .notification_service import NotificationMessage
        
        message = NotificationMessage(
            title="System Health Alert",
            message=f"System health issues detected:\n• " + "\n• ".join(issues),
            severity="warning",
            timestamp=datetime.now(timezone.utc),
            include_chart=False
        )
        
        notification_service = get_notification_service()
        import asyncio
        asyncio.run(notification_service.send_alert(message))
        
    except Exception as e:
        logger.error(f"Failed to send health alert: {e}")


@dataclass
class JobStatistics:
    """Statistics for scheduled jobs"""
    job_id: str
    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    average_duration_seconds: float = 0.0
    next_run: Optional[datetime] = None


class ScheduledJobs:
    """Container for all scheduled job implementations"""
    
    def __init__(self):
        self.config = get_config()
        self.db = get_database()
        self._job_stats: Dict[str, JobStatistics] = {}
        self._job_durations: Dict[str, List[float]] = {}
        
    def evaluate_alert_rules(self):
        """Periodic job to evaluate all alert rules"""
        job_id = "evaluate_alert_rules"
        start_time = datetime.now()
        
        try:
            logger.debug("Starting periodic alert rule evaluation")
            
            # Get alert engine and evaluate rules
            alert_engine = get_alert_engine()
            triggered_events = alert_engine.evaluate_all_rules()
            
            # Update statistics
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, True, duration)
            
            logger.info(f"Alert rule evaluation completed: {len(triggered_events)} alerts triggered in {duration:.2f}s")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, False, duration, str(e))
            logger.error(f"Alert rule evaluation failed: {e}")
            raise
    
    def cleanup_old_data(self):
        """Cleanup old alert data and logs"""
        job_id = "cleanup_old_data"
        start_time = datetime.now()
        
        try:
            logger.debug("Starting data cleanup job")
            
            # Get retention settings
            result = self.db.execute_query("""
                SELECT history_retention_days, evaluation_log_retention_days
                FROM alert_system_settings WHERE id = 1
            """)
            
            if not result.rows:
                logger.warning("No system settings found, using defaults")
                history_retention_days = 90
                eval_retention_days = 30
            else:
                settings = result.first_dict()
                history_retention_days = settings['history_retention_days']
                eval_retention_days = settings['evaluation_log_retention_days']
            
            cleanup_count = 0
            
            # Clean up old resolved alerts
            history_cutoff = datetime.now(timezone.utc) - timedelta(days=history_retention_days)
            result = self.db.execute_query("""
                DELETE FROM alert_history 
                WHERE triggered_at < %s 
                AND status IN ('resolved', 'acknowledged')
            """, (history_cutoff,), fetch=False)
            cleanup_count += result.row_count
            
            # Clean up old evaluation logs
            eval_cutoff = datetime.now(timezone.utc) - timedelta(days=eval_retention_days)
            result = self.db.execute_query("""
                DELETE FROM alert_rule_evaluations 
                WHERE evaluated_at < %s
            """, (eval_cutoff,), fetch=False)
            cleanup_count += result.row_count
            
            # Reset notification channel hourly counters if needed
            self.db.execute_query("""
                UPDATE notification_channels 
                SET current_hour_count = 0,
                    current_hour_start = NOW()
                WHERE current_hour_start < NOW() - INTERVAL '1 hour'
            """, fetch=False)
            
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, True, duration)
            
            logger.info(f"Data cleanup completed: {cleanup_count} records cleaned in {duration:.2f}s")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, False, duration, str(e))
            logger.error(f"Data cleanup job failed: {e}")
            raise
    
    def health_monitoring(self):
        """Monitor system health and generate alerts if needed"""
        job_id = "health_monitoring"
        start_time = datetime.now()
        
        try:
            logger.debug("Starting health monitoring job")
            
            # Check database health
            db_health = self.db.health_check()
            
            # Check notification service health
            notification_service = get_notification_service()
            channel_status = notification_service.test_channels()
            
            # Check for any critical system issues
            issues = []
            
            if not db_health.get('healthy', False):
                issues.append("Database health check failed")
            
            failed_channels = [ch for ch, status in channel_status.items() if not status]
            if failed_channels:
                issues.append(f"Notification channels failed: {', '.join(failed_channels)}")
            
            # Check for stuck/old data
            latest_metrics = self.db.get_latest_metrics()
            if latest_metrics:
                data_age_hours = 2
                if 'pond_timestamp' in latest_metrics:
                    pond_age = (datetime.now(timezone.utc) - latest_metrics['pond_timestamp']).total_seconds() / 3600
                    if pond_age > data_age_hours:
                        issues.append(f"Pond data is {pond_age:.1f} hours old")
                
                if 'station_timestamp' in latest_metrics:
                    station_age = (datetime.now(timezone.utc) - latest_metrics['station_timestamp']).total_seconds() / 3600
                    if station_age > data_age_hours:
                        issues.append(f"Station data is {station_age:.1f} hours old")
            
            # Generate system health alert if issues found
            if issues and self.config.alerting.enabled:
                self._generate_health_alert(issues)
            
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, True, duration)
            
            status = "healthy" if not issues else f"{len(issues)} issues found"
            logger.info(f"Health monitoring completed: {status} in {duration:.2f}s")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, False, duration, str(e))
            logger.error(f"Health monitoring job failed: {e}")
            raise
    
    def generate_daily_summary(self):
        """Generate and send daily system summary"""
        job_id = "daily_summary"
        start_time = datetime.now()
        
        try:
            logger.debug("Starting daily summary generation")
            
            if not self.config.alerting.enabled or not self.config.alerting.email_enabled:
                logger.info("Daily summary skipped - alerting not configured")
                return
            
            # Get summary data
            summary_data = self._generate_summary_data()
            
            # Send summary notification
            from .notification_service import NotificationMessage
            
            message = NotificationMessage(
                title="PondMonitor Daily Summary",
                message=self._format_summary_message(summary_data),
                severity="info",
                timestamp=datetime.now(timezone.utc),
                include_chart=True
            )
            
            # Send to email channel only
            notification_service = get_notification_service()
            import asyncio
            asyncio.run(notification_service.send_alert(message, channels=['email']))
            
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, True, duration)
            
            logger.info(f"Daily summary generated and sent in {duration:.2f}s")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, False, duration, str(e))
            logger.error(f"Daily summary generation failed: {e}")
            raise
    
    def retry_failed_notifications(self):
        """Retry failed notification deliveries"""
        job_id = "retry_notifications"
        start_time = datetime.now()
        
        try:
            logger.debug("Starting notification retry job")
            
            # Find alerts with failed notifications from last hour
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            result = self.db.execute_query("""
                SELECT id, rule_id, severity, metric_type, station_id, triggered_at,
                       trigger_value, threshold_value, message, notifications_sent
                FROM alert_history
                WHERE triggered_at > %s
                AND status = 'active'
                AND notifications_sent IS NOT NULL
            """, (cutoff_time,))
            
            retry_count = 0
            
            for row_dict in result.to_dict_list():
                notifications = row_dict['notifications_sent']
                if isinstance(notifications, str):
                    import json
                    notifications = json.loads(notifications)
                
                # Check for failed notifications
                failed_channels = []
                for notification in notifications:
                    if not notification.get('success', True):
                        failed_channels.append(notification['channel'])
                
                if failed_channels:
                    # Retry failed notifications
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._retry_alert_notifications(row_dict, failed_channels))
                        loop.close()
                        retry_count += 1
                    except Exception as e:
                        logger.error(f"Failed to retry notifications: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, True, duration)
            
            logger.info(f"Notification retry completed: {retry_count} alerts retried in {duration:.2f}s")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._update_job_stats(job_id, False, duration, str(e))
            logger.error(f"Notification retry job failed: {e}")
            raise
    
    def _generate_health_alert(self, issues: List[str]):
        """Generate system health alert"""
        try:
            from .notification_service import NotificationMessage
            
            message = NotificationMessage(
                title="System Health Alert",
                message=f"System health issues detected:\n• " + "\n• ".join(issues),
                severity="warning",
                timestamp=datetime.now(timezone.utc),
                include_chart=False
            )
            
            notification_service = get_notification_service()
            import asyncio
            asyncio.run(notification_service.send_alert(message))
            
        except Exception as e:
            logger.error(f"Failed to send health alert: {e}")
    
    def _generate_summary_data(self) -> Dict[str, Any]:
        """Generate daily summary data"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        # Get alert statistics
        alert_stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_alerts,
                COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
                COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
                COUNT(*) FILTER (WHERE status = 'active') as active_alerts,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts
            FROM alert_history
            WHERE triggered_at BETWEEN %s AND %s
        """, (start_time, end_time)).first_dict()
        
        # Get data summary
        data_summary = self.db.get_data_summary(24)
        
        return {
            'period': '24 hours',
            'start_time': start_time.strftime('%Y-%m-%d %H:%M UTC'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M UTC'),
            'alerts': alert_stats,
            'data': data_summary
        }
    
    def _format_summary_message(self, data: Dict[str, Any]) -> str:
        """Format summary data into readable message"""
        lines = [
            f"Daily system summary for {data['period']}:",
            f"Period: {data['start_time']} to {data['end_time']}",
            "",
            "📊 Alert Summary:",
            f"  • Total Alerts: {data['alerts']['total_alerts']}",
            f"  • Critical: {data['alerts']['critical_alerts']}",
            f"  • Warning: {data['alerts']['warning_alerts']}",
            f"  • Currently Active: {data['alerts']['active_alerts']}",
            f"  • Resolved: {data['alerts']['resolved_alerts']}",
            "",
            "📈 Data Summary:",
        ]
        
        pond_data = data['data'].get('pond_metrics', {})
        if pond_data.get('record_count', 0) > 0:
            lines.extend([
                f"  • Pond Records: {pond_data['record_count']}",
                f"  • Avg Water Level: {pond_data.get('avg_level', 0):.1f} cm",
                f"  • Water Level Range: {pond_data.get('min_level', 0):.1f} - {pond_data.get('max_level', 0):.1f} cm",
            ])
        
        station_data = data['data'].get('station_metrics', {})
        if station_data.get('record_count', 0) > 0:
            lines.extend([
                f"  • Station Records: {station_data['record_count']}",
                f"  • Avg Temperature: {station_data.get('avg_temperature', 0):.1f}°C",
                f"  • Battery Voltage: {station_data.get('avg_battery', 0):.2f}V",
            ])
        
        return "\n".join(lines)
    
    async def _retry_alert_notifications(self, alert_data: Dict[str, Any], failed_channels: List[str]):
        """Retry failed notifications for an alert"""
        try:
            from .notification_service import NotificationMessage
            
            message = NotificationMessage(
                title="Alert Notification Retry",
                message=alert_data['message'],
                severity=alert_data['severity'],
                station_id=alert_data['station_id'],
                metric_type=alert_data['metric_type'],
                trigger_value=alert_data['trigger_value'],
                threshold_value=alert_data['threshold_value'],
                timestamp=alert_data['triggered_at'],
                alert_id=alert_data['id']
            )
            
            notification_service = get_notification_service()
            results = await notification_service.send_alert(message, failed_channels)
            
            # Update notification status in database
            notifications_sent = alert_data['notifications_sent']
            if isinstance(notifications_sent, str):
                import json
                notifications_sent = json.loads(notifications_sent)
            
            # Add retry results
            for result in results:
                notifications_sent.append({
                    'channel': result.channel,
                    'recipient': result.recipient,
                    'success': result.success,
                    'sent_at': result.sent_at.isoformat() if result.sent_at else None,
                    'error': result.error,
                    'retry': True
                })
            
            # Update database
            self.db.execute_query("""
                UPDATE alert_history 
                SET notifications_sent = %s
                WHERE id = %s
            """, (json.dumps(notifications_sent), alert_data['id']), fetch=False)
            
        except Exception as e:
            logger.error(f"Failed to retry notifications for alert {alert_data['id']}: {e}")
    
    def _update_job_stats(self, job_id: str, success: bool, duration: float, error: Optional[str] = None):
        """Update job execution statistics"""
        if job_id not in self._job_stats:
            self._job_stats[job_id] = JobStatistics(job_id=job_id, job_name=job_id)
        
        stats = self._job_stats[job_id]
        stats.total_runs += 1
        stats.last_run = datetime.now()
        
        if success:
            stats.successful_runs += 1
            stats.last_success = stats.last_run
        else:
            stats.failed_runs += 1
            stats.last_error = error
        
        # Track duration for average calculation
        if job_id not in self._job_durations:
            self._job_durations[job_id] = []
        
        self._job_durations[job_id].append(duration)
        
        # Keep only last 100 durations for average
        if len(self._job_durations[job_id]) > 100:
            self._job_durations[job_id] = self._job_durations[job_id][-100:]
        
        stats.average_duration_seconds = sum(self._job_durations[job_id]) / len(self._job_durations[job_id])
    
    def get_job_statistics(self) -> Dict[str, JobStatistics]:
        """Get job execution statistics"""
        return self._job_stats.copy()


class SchedulerService:
    """
    Main scheduler service that manages background jobs
    
    Features:
    - APScheduler integration with database job store
    - Job monitoring and error handling
    - Graceful shutdown and recovery
    - Integration with Flask app lifecycle
    """
    
    def __init__(self):
        self.config = get_config()
        self.db = get_database()
        self.scheduler: Optional[BackgroundScheduler] = None
        self.jobs = ScheduledJobs()
        self._running = False
        self._shutdown_event = threading.Event()
        
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available, scheduler service will run in limited mode")
        
        logger.info("Scheduler service initialized")
    
    def initialize(self):
        """Initialize and configure the scheduler"""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available, scheduler initialization skipped")
            return
            
        try:
            # Configure job store - try SQLAlchemy first, fallback to memory
            jobstore = None
            try:
                db_url = self.config.database.get_connection_string()
                jobstore = SQLAlchemyJobStore(url=db_url, tablename='scheduler_jobs')
                logger.info("Using SQLAlchemy job store for persistence")
            except Exception as e:
                logger.warning(f"Failed to create SQLAlchemy job store: {e}")
                logger.info("Using memory job store (jobs will not persist across restarts)")
                # Memory jobstore is the default, so we don't need to specify it
            
            # Configure executor
            executor = ThreadPoolExecutor(max_workers=4)
            
            # Configure scheduler
            job_defaults = {
                'coalesce': True,  # Combine multiple pending executions
                'max_instances': 1,  # Only one instance of each job at a time
                'misfire_grace_time': 30  # Grace period for missed jobs
            }
            
            # Create scheduler with or without persistent jobstore
            if jobstore:
                self.scheduler = BackgroundScheduler(
                    jobstores={'default': jobstore},
                    executors={'default': executor},
                    job_defaults=job_defaults,
                    timezone='UTC'
                )
            else:
                self.scheduler = BackgroundScheduler(
                    executors={'default': executor},
                    job_defaults=job_defaults,
                    timezone='UTC'
                )
            
            # Add event listeners
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
            
            logger.info("Scheduler configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise
    
    def start(self):
        """Start the scheduler and add jobs"""
        try:
            if not APSCHEDULER_AVAILABLE:
                logger.warning("APScheduler not available, scheduler will not run")
                return
                
            if not self.scheduler:
                self.initialize()
            
            if self.scheduler:
                self.scheduler.start()
                self._running = True
                
                # Add scheduled jobs
                self._add_scheduled_jobs()
                
                # Register shutdown handler
                atexit.register(self.shutdown)
                
                logger.info("Scheduler started successfully")
            else:
                logger.warning("Scheduler not initialized, skipping start")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def _add_scheduled_jobs(self):
        """Add all scheduled jobs to the scheduler"""
        
        # Clear any existing jobs to avoid duplicates
        try:
            for job in self.scheduler.get_jobs():
                self.scheduler.remove_job(job.id)
            logger.info("Cleared existing scheduled jobs")
        except Exception as e:
            logger.warning(f"Failed to clear existing jobs: {e}")
        
        # Alert rule evaluation - every minute
        self.scheduler.add_job(
            func=evaluate_alert_rules_job,
            trigger=IntervalTrigger(seconds=60),
            id='evaluate_alert_rules',
            name='Evaluate Alert Rules',
            replace_existing=True
        )
        
        # Data cleanup - daily at 2:00 AM
        self.scheduler.add_job(
            func=cleanup_old_data_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_old_data',
            name='Clean Up Old Data',
            replace_existing=True
        )
        
        # Health monitoring - every 5 minutes
        self.scheduler.add_job(
            func=health_monitoring_job,
            trigger=IntervalTrigger(minutes=5),
            id='health_monitoring',
            name='System Health Monitoring',
            replace_existing=True
        )
        
        # Daily summary - daily at 8:00 AM
        self.scheduler.add_job(
            func=generate_daily_summary_job,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_summary',
            name='Generate Daily Summary',
            replace_existing=True
        )
        
        # Retry failed notifications - every 10 minutes
        self.scheduler.add_job(
            func=retry_failed_notifications_job,
            trigger=IntervalTrigger(minutes=10),
            id='retry_notifications',
            name='Retry Failed Notifications',
            replace_existing=True
        )
        
        logger.info(f"Added {len(self.scheduler.get_jobs())} scheduled jobs")
    
    def _job_executed(self, event):
        """Handle successful job execution"""
        logger.debug(f"Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Handle job execution errors"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
        
        # Send error notification for critical job failures
        critical_jobs = ['evaluate_alert_rules', 'health_monitoring']
        if event.job_id in critical_jobs and self.config.alerting.enabled:
            self._send_job_error_alert(event)
    
    def _job_missed(self, event):
        """Handle missed job executions"""
        logger.warning(f"Job {event.job_id} missed execution")
    
    def _send_job_error_alert(self, event):
        """Send alert for job execution errors"""
        try:
            from .notification_service import NotificationMessage, get_notification_service
            
            message = NotificationMessage(
                title="Scheduler Job Failed",
                message=f"Critical background job '{event.job_id}' failed with error: {event.exception}",
                severity="warning",
                timestamp=datetime.now(timezone.utc),
                include_chart=False
            )
            
            notification_service = get_notification_service()
            import asyncio
            asyncio.run(notification_service.send_alert(message, channels=['email']))
            
        except Exception as e:
            logger.error(f"Failed to send job error alert: {e}")
    
    def shutdown(self):
        """Gracefully shutdown the scheduler"""
        if self.scheduler and self._running:
            logger.info("Shutting down scheduler...")
            
            # Signal shutdown to prevent new jobs
            self._shutdown_event.set()
            self._running = False
            
            # Shutdown scheduler
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shutdown complete")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get scheduler and job status information"""
        try:
            status = {
                'scheduler_running': self._running,
                'scheduler_state': self.scheduler.state if self.scheduler else None,
                'job_count': len(self.scheduler.get_jobs()) if self.scheduler else 0,
                'jobs': {},
                'statistics': self.jobs.get_job_statistics()
            }
            
            if self.scheduler:
                for job in self.scheduler.get_jobs():
                    status['jobs'][job.id] = {
                        'name': job.name,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger),
                        'pending': job.pending
                    }
                    
                    # Update next run time in statistics
                    if job.id in status['statistics']:
                        status['statistics'][job.id].next_run = job.next_run_time
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return {'error': str(e)}
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            if self.scheduler:
                self.scheduler.pause_job(job_id)
                logger.info(f"Job {job_id} paused")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            if self.scheduler:
                self.scheduler.resume_job(job_id)
                logger.info(f"Job {job_id} resumed")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False
    
    def run_job_now(self, job_id: str) -> bool:
        """Run a job immediately"""
        try:
            if self.scheduler:
                job = self.scheduler.get_job(job_id)
                if job:
                    job.func()
                    logger.info(f"Job {job_id} executed manually")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False


# Global scheduler service instance
_scheduler_service: Optional[SchedulerService] = None


def init_scheduler_service() -> SchedulerService:
    """Initialize global scheduler service"""
    global _scheduler_service
    _scheduler_service = SchedulerService()
    return _scheduler_service


def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance"""
    if _scheduler_service is None:
        raise RuntimeError("Scheduler service not initialized. Call init_scheduler_service() first.")
    return _scheduler_service


def start_scheduler():
    """Start the global scheduler service"""
    scheduler_service = get_scheduler_service()
    scheduler_service.start()


def stop_scheduler():
    """Stop the global scheduler service"""
    if _scheduler_service:
        _scheduler_service.shutdown()


if __name__ == "__main__":
    # Example usage and testing
    from ..config import init_config
    from ..database import init_database
    from .notification_service import init_notification_service
    from .alert_engine import init_alert_engine
    
    # Initialize services
    config = init_config()
    db = init_database(config.database)
    notification_service = init_notification_service(config.alerting)
    alert_engine = init_alert_engine()
    scheduler_service = init_scheduler_service()
    
    # Start scheduler
    scheduler_service.start()
    
    print("Scheduler started. Press Ctrl+C to stop...")
    
    try:
        # Keep running until interrupted
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        scheduler_service.shutdown()
        print("Scheduler stopped.")