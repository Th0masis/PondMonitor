"""
PondMonitor Alert Engine

Rule-based alerting engine with configurable conditions and thresholds.
Supports multiple alert types:
- Threshold alerts (>, <, >=, <=)  
- Range alerts (within/outside range)
- Rate of change alerts (rapid changes)
- Missing data alerts (communication loss)

Features:
- Configurable alert rules with JSON conditions
- Rule composition with AND/OR logic
- Historical rule evaluation tracking
- Cooldown periods to prevent spam
- Alert state management (active, acknowledged, resolved)
- Integration with notification service
"""

import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod

from ..config import get_config
from ..database import get_database, QueryResult
from .notification_service import get_notification_service, NotificationMessage

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status states"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class RuleType(Enum):
    """Types of alert rules"""
    THRESHOLD = "threshold"
    RANGE = "range"
    RATE_OF_CHANGE = "rate_of_change"
    MISSING_DATA = "missing_data"


class MetricType(Enum):
    """Types of metrics that can trigger alerts"""
    WATER_LEVEL = "water_level"
    TEMPERATURE = "temperature"
    BATTERY_VOLTAGE = "battery_voltage"
    SIGNAL_STRENGTH = "signal_strength"
    OUTFLOW = "outflow"


@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    description: str
    rule_type: RuleType
    metric_type: MetricType
    conditions: Dict[str, Any]
    severity: AlertSeverity
    enabled: bool = True
    station_id: Optional[str] = None
    channels: List[str] = None
    cooldown_minutes: int = 60
    max_alerts_per_hour: int = 5
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = "system"
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = ["email"]
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass  
class AlertEvent:
    """Alert event/trigger record"""
    id: str
    rule_id: str
    severity: AlertSeverity
    metric_type: MetricType
    station_id: Optional[str]
    triggered_at: datetime
    trigger_value: Optional[float]
    threshold_value: Optional[float]
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    notifications_sent: List[Dict[str, Any]] = None
    related_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.notifications_sent is None:
            self.notifications_sent = []
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class EvaluationContext:
    """Context for rule evaluation"""
    metric_value: Optional[float]
    metric_timestamp: datetime
    station_id: Optional[str]
    historical_data: List[Dict[str, Any]]
    rule: AlertRule


class AlertRuleEvaluator(ABC):
    """Abstract base class for rule evaluators"""
    
    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Evaluate if rule conditions are met
        
        Args:
            context: Evaluation context with metric data and rule
            
        Returns:
            Tuple of (triggered, reason, threshold_value)
        """
        pass


class ThresholdEvaluator(AlertRuleEvaluator):
    """Evaluates threshold-based alert rules"""
    
    def evaluate(self, context: EvaluationContext) -> Tuple[bool, Optional[str], Optional[float]]:
        """Evaluate threshold rule"""
        if context.metric_value is None:
            return False, "No metric value", None
            
        conditions = context.rule.conditions
        operator = conditions.get('operator', 'gt')
        threshold = conditions.get('value')
        
        if threshold is None:
            return False, "No threshold value configured", None
        
        # Evaluate condition
        triggered = False
        if operator == 'gt':
            triggered = context.metric_value > threshold
        elif operator == 'gte':
            triggered = context.metric_value >= threshold
        elif operator == 'lt':
            triggered = context.metric_value < threshold  
        elif operator == 'lte':
            triggered = context.metric_value <= threshold
        elif operator == 'eq':
            triggered = abs(context.metric_value - threshold) < 0.001
        elif operator == 'ne':
            triggered = abs(context.metric_value - threshold) >= 0.001
        else:
            return False, f"Unknown operator: {operator}", None
        
        if triggered:
            reason = f"Value {context.metric_value} {operator} {threshold}"
            return True, reason, threshold
        
        return False, None, None


class RangeEvaluator(AlertRuleEvaluator):
    """Evaluates range-based alert rules"""
    
    def evaluate(self, context: EvaluationContext) -> Tuple[bool, Optional[str], Optional[float]]:
        """Evaluate range rule"""
        if context.metric_value is None:
            return False, "No metric value", None
            
        conditions = context.rule.conditions
        min_value = conditions.get('min')
        max_value = conditions.get('max')
        outside = conditions.get('outside', True)  # True = alert when outside range
        
        if min_value is None and max_value is None:
            return False, "No range values configured", None
        
        # Check if value is within range
        within_range = True
        if min_value is not None and context.metric_value < min_value:
            within_range = False
        if max_value is not None and context.metric_value > max_value:
            within_range = False
        
        # Trigger based on outside/inside logic
        triggered = (outside and not within_range) or (not outside and within_range)
        
        if triggered:
            if outside:
                reason = f"Value {context.metric_value} outside range [{min_value}, {max_value}]"
                threshold = min_value if context.metric_value < min_value else max_value
            else:
                reason = f"Value {context.metric_value} within range [{min_value}, {max_value}]"
                threshold = (min_value + max_value) / 2 if min_value and max_value else min_value or max_value
            return True, reason, threshold
        
        return False, None, None


class RateOfChangeEvaluator(AlertRuleEvaluator):
    """Evaluates rate of change alert rules"""
    
    def evaluate(self, context: EvaluationContext) -> Tuple[bool, Optional[str], Optional[float]]:
        """Evaluate rate of change rule"""
        if context.metric_value is None or not context.historical_data:
            return False, "Insufficient data for rate calculation", None
            
        conditions = context.rule.conditions
        change_threshold = conditions.get('change_threshold')
        time_window_minutes = conditions.get('time_window_minutes', 30)
        
        if change_threshold is None:
            return False, "No change threshold configured", None
        
        # Find data point from time window ago
        cutoff_time = context.metric_timestamp - timedelta(minutes=time_window_minutes)
        
        historical_value = None
        for data_point in reversed(context.historical_data):  # Most recent first
            if data_point['timestamp'] <= cutoff_time:
                historical_value = data_point.get(self._get_metric_column(context.rule.metric_type))
                break
        
        if historical_value is None:
            return False, f"No historical data from {time_window_minutes} minutes ago", None
        
        # Calculate rate of change
        change = abs(context.metric_value - historical_value)
        rate_per_minute = change / time_window_minutes
        
        if rate_per_minute > change_threshold:
            reason = f"Rate of change {rate_per_minute:.2f}/min exceeds {change_threshold}/min"
            return True, reason, change_threshold
        
        return False, None, None
    
    def _get_metric_column(self, metric_type: MetricType) -> str:
        """Get database column name for metric type"""
        mapping = {
            MetricType.WATER_LEVEL: 'level_cm',
            MetricType.OUTFLOW: 'outflow_lps',
            MetricType.TEMPERATURE: 'temperature_c',
            MetricType.BATTERY_VOLTAGE: 'battery_v',
            MetricType.SIGNAL_STRENGTH: 'signal_dbm'
        }
        return mapping.get(metric_type, 'value')


class MissingDataEvaluator(AlertRuleEvaluator):
    """Evaluates missing data alert rules"""
    
    def evaluate(self, context: EvaluationContext) -> Tuple[bool, Optional[str], Optional[float]]:
        """Evaluate missing data rule"""
        conditions = context.rule.conditions
        max_age_minutes = conditions.get('max_age_minutes', 60)
        
        if not context.historical_data:
            reason = "No historical data available"
            return True, reason, max_age_minutes
        
        # Find most recent data point
        most_recent = max(context.historical_data, key=lambda x: x['timestamp'])
        most_recent_time = most_recent['timestamp']
        
        # Check if data is too old
        age_minutes = (context.metric_timestamp - most_recent_time).total_seconds() / 60
        
        if age_minutes > max_age_minutes:
            reason = f"No data received for {age_minutes:.1f} minutes (threshold: {max_age_minutes})"
            return True, reason, max_age_minutes
        
        return False, None, None


class AlertEngine:
    """
    Main alert engine that evaluates rules and triggers notifications
    
    Features:
    - Rule evaluation with multiple evaluator types
    - Cooldown management to prevent alert spam
    - Alert state tracking and management
    - Integration with notification service
    - Performance monitoring and logging
    """
    
    def __init__(self):
        self.config = get_config()
        self.db = get_database()
        self.notification_service = get_notification_service()
        
        # Rule evaluators
        self.evaluators = {
            RuleType.THRESHOLD: ThresholdEvaluator(),
            RuleType.RANGE: RangeEvaluator(),
            RuleType.RATE_OF_CHANGE: RateOfChangeEvaluator(),
            RuleType.MISSING_DATA: MissingDataEvaluator()
        }
        
        # Statistics
        self._evaluation_count = 0
        self._alert_count = 0
        self._error_count = 0
        
        logger.info("Alert engine initialized")
    
    def evaluate_all_rules(self, metric_data: Dict[str, Any] = None) -> List[AlertEvent]:
        """
        Evaluate all enabled alert rules against current or provided metric data
        
        Args:
            metric_data: Optional metric data to evaluate against
            
        Returns:
            List of triggered alert events
        """
        try:
            # Get current metric data if not provided
            if metric_data is None:
                metric_data = self.db.get_latest_metrics()
                if not metric_data:
                    logger.warning("No metric data available for rule evaluation")
                    return []
            
            # Get all enabled rules
            rules = self.get_active_rules()
            logger.debug(f"Evaluating {len(rules)} alert rules")
            
            triggered_events = []
            
            for rule in rules:
                try:
                    events = self.evaluate_rule(rule, metric_data)
                    triggered_events.extend(events)
                    self._evaluation_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to evaluate rule {rule.name}: {e}")
                    self._error_count += 1
            
            logger.info(f"Rule evaluation complete: {len(triggered_events)} alerts triggered")
            return triggered_events
            
        except Exception as e:
            logger.error(f"Rule evaluation failed: {e}")
            self._error_count += 1
            return []
    
    def evaluate_rule(self, rule: AlertRule, metric_data: Dict[str, Any]) -> List[AlertEvent]:
        """
        Evaluate a single alert rule
        
        Args:
            rule: Alert rule to evaluate
            metric_data: Current metric data
            
        Returns:
            List of alert events (empty if rule not triggered)
        """
        try:
            # Check if rule is in cooldown
            if self._is_rule_in_cooldown(rule):
                logger.debug(f"Rule {rule.name} is in cooldown period")
                return []
            
            # Check rate limiting
            if self._is_rule_rate_limited(rule):
                logger.debug(f"Rule {rule.name} is rate limited")
                return []
            
            # Get metric value and historical data
            context = self._build_evaluation_context(rule, metric_data)
            if context is None:
                return []
            
            # Evaluate rule
            evaluator = self.evaluators.get(rule.rule_type)
            if not evaluator:
                logger.error(f"No evaluator for rule type: {rule.rule_type}")
                return []
            
            start_time = datetime.now()
            triggered, reason, threshold_value = evaluator.evaluate(context)
            evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log evaluation
            self._log_rule_evaluation(rule, context, triggered, reason, evaluation_time)
            
            if not triggered:
                return []
            
            # Create alert event
            alert_event = self._create_alert_event(rule, context, reason, threshold_value)
            
            # Store in database
            self._store_alert_event(alert_event)
            
            # Send notifications
            self._send_alert_notifications(alert_event)
            
            self._alert_count += 1
            logger.info(f"Alert triggered: {rule.name} - {reason}")
            
            return [alert_event]
            
        except Exception as e:
            logger.error(f"Failed to evaluate rule {rule.name}: {e}")
            return []
    
    def get_active_rules(self) -> List[AlertRule]:
        """Get all enabled alert rules from database"""
        try:
            result = self.db.execute_query("""
                SELECT id, name, description, rule_type, metric_type, station_id,
                       conditions, severity, enabled, channels, cooldown_minutes,
                       max_alerts_per_hour, created_at, updated_at, created_by
                FROM alert_rules 
                WHERE enabled = true
                ORDER BY severity DESC, name ASC
            """)
            
            rules = []
            for row_dict in result.to_dict_list():
                # Parse JSON fields
                conditions = json.loads(row_dict['conditions']) if isinstance(row_dict['conditions'], str) else row_dict['conditions']
                channels = json.loads(row_dict['channels']) if isinstance(row_dict['channels'], str) else row_dict['channels']
                
                rule = AlertRule(
                    id=row_dict['id'],
                    name=row_dict['name'],
                    description=row_dict['description'],
                    rule_type=RuleType(row_dict['rule_type']),
                    metric_type=MetricType(row_dict['metric_type']),
                    station_id=row_dict['station_id'],
                    conditions=conditions,
                    severity=AlertSeverity(row_dict['severity']),
                    enabled=row_dict['enabled'],
                    channels=channels,
                    cooldown_minutes=row_dict['cooldown_minutes'],
                    max_alerts_per_hour=row_dict['max_alerts_per_hour'],
                    created_at=row_dict['created_at'],
                    updated_at=row_dict['updated_at'],
                    created_by=row_dict['created_by']
                )
                rules.append(rule)
            
            return rules
            
        except Exception as e:
            logger.error(f"Failed to get active rules: {e}")
            return []
    
    def _build_evaluation_context(self, rule: AlertRule, metric_data: Dict[str, Any]) -> Optional[EvaluationContext]:
        """Build evaluation context for rule"""
        try:
            # Get current metric value
            metric_value = None
            metric_timestamp = datetime.now(timezone.utc)
            
            # Map metric types to data keys
            metric_mapping = {
                MetricType.WATER_LEVEL: 'level_cm',
                MetricType.OUTFLOW: 'outflow_lps', 
                MetricType.TEMPERATURE: 'temperature_c',
                MetricType.BATTERY_VOLTAGE: 'battery_v',
                MetricType.SIGNAL_STRENGTH: 'signal_dbm'
            }
            
            metric_key = metric_mapping.get(rule.metric_type)
            if metric_key and metric_key in metric_data:
                metric_value = metric_data[metric_key]
                
                # Get timestamp from appropriate field
                timestamp_key = 'pond_timestamp' if rule.metric_type in [MetricType.WATER_LEVEL, MetricType.OUTFLOW] else 'station_timestamp'
                if timestamp_key in metric_data:
                    metric_timestamp = metric_data[timestamp_key]
            
            # Get historical data for rate of change and missing data rules
            historical_data = []
            if rule.rule_type in [RuleType.RATE_OF_CHANGE, RuleType.MISSING_DATA]:
                historical_data = self._get_historical_data(rule, metric_timestamp)
            
            return EvaluationContext(
                metric_value=metric_value,
                metric_timestamp=metric_timestamp,
                station_id=rule.station_id,
                historical_data=historical_data,
                rule=rule
            )
            
        except Exception as e:
            logger.error(f"Failed to build evaluation context: {e}")
            return None
    
    def _get_historical_data(self, rule: AlertRule, current_time: datetime) -> List[Dict[str, Any]]:
        """Get historical data for rule evaluation"""
        try:
            # Look back further for rate of change calculations
            hours_back = 2
            if rule.rule_type == RuleType.MISSING_DATA:
                hours_back = rule.conditions.get('max_age_minutes', 60) / 60 * 2
            
            start_time = current_time - timedelta(hours=hours_back)
            
            if rule.metric_type in [MetricType.WATER_LEVEL, MetricType.OUTFLOW]:
                return self.db.get_pond_metrics(start_time, current_time, limit=500)
            else:
                return self.db.get_station_metrics(start_time, current_time, rule.station_id, limit=500)
                
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return []
    
    def _is_rule_in_cooldown(self, rule: AlertRule) -> bool:
        """Check if rule is in cooldown period"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)
            
            result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM alert_history 
                WHERE rule_id = %s 
                AND triggered_at > %s
                AND status = 'active'
            """, (rule.id, cutoff_time))
            
            count = result.first_dict()['count'] if result.rows else 0
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check cooldown for rule {rule.name}: {e}")
            return False
    
    def _is_rule_rate_limited(self, rule: AlertRule) -> bool:
        """Check if rule has exceeded rate limit"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM alert_history 
                WHERE rule_id = %s 
                AND triggered_at > %s
            """, (rule.id, cutoff_time))
            
            count = result.first_dict()['count'] if result.rows else 0
            return count >= rule.max_alerts_per_hour
            
        except Exception as e:
            logger.error(f"Failed to check rate limit for rule {rule.name}: {e}")
            return False
    
    def _create_alert_event(self, rule: AlertRule, context: EvaluationContext, 
                           reason: str, threshold_value: Optional[float]) -> AlertEvent:
        """Create alert event from rule evaluation"""
        
        # Generate alert message
        message = self._generate_alert_message(rule, context, reason, threshold_value)
        
        return AlertEvent(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            severity=rule.severity,
            metric_type=rule.metric_type,
            station_id=context.station_id,
            triggered_at=context.metric_timestamp,
            trigger_value=context.metric_value,
            threshold_value=threshold_value,
            message=message,
            status=AlertStatus.ACTIVE,
            related_data={
                'rule_name': rule.name,
                'conditions': rule.conditions,
                'evaluation_reason': reason
            }
        )
    
    def _generate_alert_message(self, rule: AlertRule, context: EvaluationContext, 
                               reason: str, threshold_value: Optional[float]) -> str:
        """Generate human-readable alert message"""
        
        metric_display_names = {
            MetricType.WATER_LEVEL: "Water Level",
            MetricType.OUTFLOW: "Outflow Rate", 
            MetricType.TEMPERATURE: "Temperature",
            MetricType.BATTERY_VOLTAGE: "Battery Voltage",
            MetricType.SIGNAL_STRENGTH: "Signal Strength"
        }
        
        metric_units = {
            MetricType.WATER_LEVEL: "cm",
            MetricType.OUTFLOW: "L/s",
            MetricType.TEMPERATURE: "°C", 
            MetricType.BATTERY_VOLTAGE: "V",
            MetricType.SIGNAL_STRENGTH: "dBm"
        }
        
        metric_name = metric_display_names.get(rule.metric_type, rule.metric_type.value)
        unit = metric_units.get(rule.metric_type, "")
        
        if context.metric_value is not None:
            value_str = f"{context.metric_value}{unit}"
            if threshold_value is not None:
                threshold_str = f"{threshold_value}{unit}"
                return f"{metric_name} is {value_str} (threshold: {threshold_str}). {reason}"
            else:
                return f"{metric_name} is {value_str}. {reason}"
        else:
            return f"{metric_name} alert: {reason}"
    
    def _store_alert_event(self, event: AlertEvent):
        """Store alert event in database"""
        try:
            self.db.execute_query("""
                INSERT INTO alert_history 
                (id, rule_id, severity, metric_type, station_id, triggered_at, 
                 trigger_value, threshold_value, message, status, related_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event.id,
                event.rule_id,
                event.severity.value,
                event.metric_type.value,
                event.station_id,
                event.triggered_at,
                event.trigger_value,
                event.threshold_value,
                event.message,
                event.status.value,
                json.dumps(event.related_data) if event.related_data else None
            ), fetch=False)
            
        except Exception as e:
            logger.error(f"Failed to store alert event: {e}")
    
    def _send_alert_notifications(self, event: AlertEvent):
        """Send notifications for alert event"""
        try:
            # Get rule to determine channels
            rule = next((r for r in self.get_active_rules() if r.id == event.rule_id), None)
            if not rule:
                logger.error(f"Rule not found for alert event: {event.rule_id}")
                return
            
            # Create notification message
            notification = NotificationMessage(
                title=f"{rule.name}",
                message=event.message,
                severity=event.severity.value,
                station_id=event.station_id,
                metric_type=event.metric_type.value,
                trigger_value=event.trigger_value,
                threshold_value=event.threshold_value,
                timestamp=event.triggered_at,
                alert_id=event.id,
                include_chart=self.config.alerting.include_charts
            )
            
            # Send notifications
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule in running loop
                asyncio.create_task(
                    self.notification_service.send_alert(notification, rule.channels)
                )
            else:
                # Run in new loop
                results = asyncio.run(
                    self.notification_service.send_alert(notification, rule.channels)
                )
                
                # Update notification status in database
                notifications_sent = []
                for result in results:
                    notifications_sent.append({
                        'channel': result.channel,
                        'recipient': result.recipient,
                        'success': result.success,
                        'sent_at': result.sent_at.isoformat() if result.sent_at else None,
                        'error': result.error
                    })
                
                # Update alert event
                self.db.execute_query("""
                    UPDATE alert_history 
                    SET notifications_sent = %s
                    WHERE id = %s
                """, (json.dumps(notifications_sent), event.id), fetch=False)
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    def _log_rule_evaluation(self, rule: AlertRule, context: EvaluationContext, 
                            triggered: bool, reason: Optional[str], evaluation_time_ms: float):
        """Log rule evaluation for debugging and monitoring"""
        try:
            self.db.execute_query("""
                INSERT INTO alert_rule_evaluations
                (rule_id, evaluated_at, evaluation_time_ms, metric_value, 
                 station_id, data_timestamp, rule_triggered, trigger_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                rule.id,
                datetime.now(timezone.utc),
                int(evaluation_time_ms),
                context.metric_value,
                context.station_id,
                context.metric_timestamp,
                triggered,
                reason
            ), fetch=False)
            
        except Exception as e:
            logger.error(f"Failed to log rule evaluation: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        try:
            result = self.db.execute_query("""
                UPDATE alert_history 
                SET status = %s, acknowledged_at = %s, acknowledged_by = %s
                WHERE id = %s AND status = %s
            """, (
                AlertStatus.ACKNOWLEDGED.value,
                datetime.now(timezone.utc),
                acknowledged_by,
                alert_id,
                AlertStatus.ACTIVE.value
            ), fetch=False)
            
            return result.row_count > 0
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""
        try:
            result = self.db.execute_query("""
                UPDATE alert_history 
                SET status = %s, resolved_at = %s, resolved_by = %s
                WHERE id = %s AND status IN (%s, %s)
            """, (
                AlertStatus.RESOLVED.value,
                datetime.now(timezone.utc),
                resolved_by,
                alert_id,
                AlertStatus.ACTIVE.value,
                AlertStatus.ACKNOWLEDGED.value
            ), fetch=False)
            
            return result.row_count > 0
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    def get_active_alerts(self, station_id: Optional[str] = None) -> List[AlertEvent]:
        """Get all active alerts"""
        try:
            query = """
                SELECT id, rule_id, severity, metric_type, station_id, triggered_at,
                       trigger_value, threshold_value, message, status,
                       acknowledged_at, acknowledged_by, resolved_at, resolved_by,
                       notifications_sent, related_data
                FROM alert_history 
                WHERE status = %s
            """
            params = [AlertStatus.ACTIVE.value]
            
            if station_id:
                query += " AND station_id = %s"
                params.append(station_id)
            
            query += " ORDER BY triggered_at DESC"
            
            result = self.db.execute_query(query, tuple(params))
            
            alerts = []
            for row_dict in result.to_dict_list():
                # Parse JSON fields
                notifications_sent = json.loads(row_dict['notifications_sent']) if row_dict['notifications_sent'] else []
                related_data = json.loads(row_dict['related_data']) if row_dict['related_data'] else {}
                
                alert = AlertEvent(
                    id=row_dict['id'],
                    rule_id=row_dict['rule_id'],
                    severity=AlertSeverity(row_dict['severity']),
                    metric_type=MetricType(row_dict['metric_type']),
                    station_id=row_dict['station_id'],
                    triggered_at=row_dict['triggered_at'],
                    trigger_value=row_dict['trigger_value'],
                    threshold_value=row_dict['threshold_value'],
                    message=row_dict['message'],
                    status=AlertStatus(row_dict['status']),
                    acknowledged_at=row_dict['acknowledged_at'],
                    acknowledged_by=row_dict['acknowledged_by'],
                    resolved_at=row_dict['resolved_at'],
                    resolved_by=row_dict['resolved_by'],
                    notifications_sent=notifications_sent,
                    related_data=related_data
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert engine statistics"""
        try:
            # Get recent alert counts
            cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
            
            stats_24h = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
                    COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
                    COUNT(*) FILTER (WHERE status = 'active') as active_alerts
                FROM alert_history
                WHERE triggered_at > %s
            """, (cutoff_24h,)).first_dict()
            
            stats_7d = self.db.execute_query("""
                SELECT COUNT(*) as total_alerts
                FROM alert_history
                WHERE triggered_at > %s
            """, (cutoff_7d,)).first_dict()
            
            # Get rule statistics
            rule_stats = self.db.execute_query("""
                SELECT COUNT(*) as total_rules, 
                       COUNT(*) FILTER (WHERE enabled = true) as enabled_rules
                FROM alert_rules
            """).first_dict()
            
            return {
                'evaluation_count': self._evaluation_count,
                'alert_count': self._alert_count,
                'error_count': self._error_count,
                'rules': rule_stats,
                'alerts_24h': stats_24h,
                'alerts_7d': stats_7d['total_alerts'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}


# Global alert engine instance
_alert_engine: Optional[AlertEngine] = None


def init_alert_engine() -> AlertEngine:
    """Initialize global alert engine"""
    global _alert_engine
    _alert_engine = AlertEngine()
    return _alert_engine


def get_alert_engine() -> AlertEngine:
    """Get the global alert engine instance"""
    if _alert_engine is None:
        raise RuntimeError("Alert engine not initialized. Call init_alert_engine() first.")
    return _alert_engine


if __name__ == "__main__":
    # Example usage and testing
    from ..config import init_config
    from ..database import init_database
    from .notification_service import init_notification_service
    
    # Initialize services
    config = init_config()
    db = init_database(config.database)
    notification_service = init_notification_service(config.alerting)
    alert_engine = init_alert_engine()
    
    # Test rule evaluation
    print("Testing alert engine...")
    
    # Evaluate all rules
    events = alert_engine.evaluate_all_rules()
    print(f"Triggered {len(events)} alerts")
    
    # Get statistics
    stats = alert_engine.get_statistics()
    print(f"Engine statistics: {stats}")
    
    # Get active alerts
    active_alerts = alert_engine.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")