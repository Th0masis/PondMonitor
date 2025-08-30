"""
PondMonitor Notification Service

Handles multi-channel notifications with rich content support:
- Email with HTML templates and embedded charts
- Telegram instant messaging
- Discord channel notifications  
- Browser push notifications (WebSocket/SSE)

Features:
- Template-based message formatting
- Chart generation for visual alerts
- Delivery confirmation and retry logic
- Rate limiting and error handling
- Channel-specific message optimization
"""

import logging
import smtplib
import asyncio
import io
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod

import requests
from jinja2 import Environment, FileSystemLoader, Template

# Handle optional dependencies gracefully
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    matplotlib = None
    plt = None
    mdates = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    from discord_webhook import DiscordWebhook, DiscordEmbed
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    DiscordWebhook = None
    DiscordEmbed = None

from ..config import AlertingConfig, get_config
from ..database import get_database

logger = logging.getLogger(__name__)


@dataclass
class NotificationMessage:
    """Container for notification message data"""
    title: str
    message: str
    severity: str  # 'info', 'warning', 'critical'
    station_id: Optional[str] = None
    metric_type: Optional[str] = None
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    timestamp: Optional[datetime] = None
    alert_id: Optional[str] = None
    include_chart: bool = True
    chart_data: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResult:
    """Result of notification delivery attempt"""
    success: bool
    channel: str
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    sent_at: Optional[datetime] = None


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult:
        """Send notification message"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if channel is properly configured and accessible"""
        pass
    
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Get channel name for logging and identification"""
        pass


class ChartGenerator:
    """Generates charts for alert notifications"""
    
    def __init__(self, config: AlertingConfig):
        self.config = config
        try:
            self.db = get_database()
        except RuntimeError:
            # Database not initialized (likely in test environment)
            self.db = None
        
        # Configure matplotlib for better-looking charts if available
        if MATPLOTLIB_AVAILABLE and plt:
            try:
                plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
            except:
                pass
        
    def generate_alert_chart(self, message: NotificationMessage) -> Optional[bytes]:
        """
        Generate chart image for alert notification
        
        Args:
            message: Notification message with alert details
            
        Returns:
            PNG image data as bytes, or None if generation fails
        """
        try:
            if not message.include_chart or not self.config.include_charts or not MATPLOTLIB_AVAILABLE:
                return None
                
            # Determine time range
            end_time = message.timestamp or datetime.now()
            start_time = end_time - timedelta(hours=self.config.chart_time_range_hours)
            
            # Get data based on metric type
            chart_data = self._get_chart_data(message.metric_type, message.station_id, start_time, end_time)
            if not chart_data:
                return None
                
            # Generate chart
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if message.metric_type == 'water_level':
                self._plot_water_level_chart(ax, chart_data, message)
            elif message.metric_type == 'temperature':
                self._plot_temperature_chart(ax, chart_data, message)
            elif message.metric_type == 'battery_voltage':
                self._plot_battery_chart(ax, chart_data, message)
            else:
                self._plot_generic_metric_chart(ax, chart_data, message)
            
            # Add alert indicator
            if message.trigger_value is not None and message.threshold_value is not None:
                self._add_alert_indicators(ax, message)
            
            # Format chart
            self._format_chart(ax, message)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            return None
    
    def _get_chart_data(self, metric_type: str, station_id: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get data for chart generation"""
        if self.db is None:
            logger.warning("Database not available, returning empty chart data")
            return []
            
        try:
            if metric_type in ['water_level', 'outflow']:
                return self.db.get_pond_metrics(start_time, end_time, limit=1000)
            else:
                return self.db.get_station_metrics(start_time, end_time, station_id, limit=1000)
        except Exception as e:
            logger.error(f"Failed to get chart data: {e}")
            return []
    
    def _plot_water_level_chart(self, ax, data: List[Dict], message: NotificationMessage):
        """Plot water level chart"""
        if not data:
            return
            
        timestamps = [row['timestamp'] for row in data]
        levels = [row['level_cm'] for row in data if row['level_cm'] is not None]
        
        if not levels:
            return
            
        ax.plot(timestamps[:len(levels)], levels, 'b-', linewidth=2, label='Water Level')
        ax.set_ylabel('Water Level (cm)', fontsize=12)
        ax.set_title(f'Water Level Trend - {message.title}', fontsize=14, fontweight='bold')
        
        # Add threshold lines
        if message.threshold_value:
            ax.axhline(y=message.threshold_value, color='red', linestyle='--', 
                      label=f'Alert Threshold ({message.threshold_value:.1f} cm)')
    
    def _plot_temperature_chart(self, ax, data: List[Dict], message: NotificationMessage):
        """Plot temperature chart"""
        if not data:
            return
            
        timestamps = [row['timestamp'] for row in data]
        temps = [row['temperature_c'] for row in data if row['temperature_c'] is not None]
        
        if not temps:
            return
            
        ax.plot(timestamps[:len(temps)], temps, 'r-', linewidth=2, label='Temperature')
        ax.set_ylabel('Temperature (°C)', fontsize=12)
        ax.set_title(f'Temperature Trend - {message.title}', fontsize=14, fontweight='bold')
        
        if message.threshold_value:
            ax.axhline(y=message.threshold_value, color='orange', linestyle='--',
                      label=f'Alert Threshold ({message.threshold_value:.1f}°C)')
    
    def _plot_battery_chart(self, ax, data: List[Dict], message: NotificationMessage):
        """Plot battery voltage chart"""
        if not data:
            return
            
        timestamps = [row['timestamp'] for row in data]
        voltages = [row['battery_v'] for row in data if row['battery_v'] is not None]
        
        if not voltages:
            return
            
        ax.plot(timestamps[:len(voltages)], voltages, 'g-', linewidth=2, label='Battery Voltage')
        ax.set_ylabel('Battery Voltage (V)', fontsize=12)
        ax.set_title(f'Battery Voltage Trend - {message.title}', fontsize=14, fontweight='bold')
        
        if message.threshold_value:
            ax.axhline(y=message.threshold_value, color='red', linestyle='--',
                      label=f'Low Battery Threshold ({message.threshold_value:.1f}V)')
    
    def _plot_generic_metric_chart(self, ax, data: List[Dict], message: NotificationMessage):
        """Plot generic metric chart"""
        if not data:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=14)
            return
        
        # Try to find appropriate metric to plot
        metric_key = None
        for key in data[0].keys():
            if key != 'timestamp' and key != 'station_id' and data[0][key] is not None:
                metric_key = key
                break
        
        if not metric_key:
            return
            
        timestamps = [row['timestamp'] for row in data]
        values = [row[metric_key] for row in data if row[metric_key] is not None]
        
        ax.plot(timestamps[:len(values)], values, 'b-', linewidth=2, label=metric_key.replace('_', ' ').title())
        ax.set_ylabel(metric_key.replace('_', ' ').title(), fontsize=12)
        ax.set_title(f'{metric_key.replace("_", " ").title()} - {message.title}', fontsize=14, fontweight='bold')
    
    def _add_alert_indicators(self, ax, message: NotificationMessage):
        """Add alert indicators to chart"""
        if message.timestamp and message.trigger_value is not None:
            ax.scatter([message.timestamp], [message.trigger_value], 
                      color='red', s=100, zorder=5, label='Alert Triggered')
    
    def _format_chart(self, ax, message: NotificationMessage):
        """Format chart appearance"""
        if not MATPLOTLIB_AVAILABLE or not mdates:
            return
            
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%m-%d'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, self.config.chart_time_range_hours // 12)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add alert severity color coding
        severity_colors = {'info': '#2196F3', 'warning': '#FF9800', 'critical': '#F44336'}
        if message.severity in severity_colors:
            ax.spines['top'].set_color(severity_colors[message.severity])
            ax.spines['top'].set_linewidth(3)


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel with HTML templates and charts"""
    
    def __init__(self, config: AlertingConfig):
        self.config = config
        self.chart_generator = ChartGenerator(config)
        self._setup_templates()
    
    def _setup_templates(self):
        """Setup Jinja2 templates for email formatting"""
        # Create templates directory if it doesn't exist
        template_dir = Path(__file__).parent.parent / "templates" / "notifications"
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default email template if it doesn't exist
        email_template_path = template_dir / "email_alert.html"
        if not email_template_path.exists():
            self._create_default_email_template(email_template_path)
        
        self.template_env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def _create_default_email_template(self, path: Path):
        """Create default HTML email template"""
        template_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PondMonitor Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { padding: 20px; background: {% if severity == 'critical' %}#f44336{% elif severity == 'warning' %}#ff9800{% else %}#2196f3{% endif %}; color: white; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 20px; }
        .alert-details { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .alert-details h3 { margin-top: 0; color: #333; }
        .metric-value { font-size: 18px; font-weight: bold; color: {% if severity == 'critical' %}#f44336{% elif severity == 'warning' %}#ff9800{% else %}#2196f3{% endif %}; }
        .chart-container { text-align: center; margin: 20px 0; }
        .footer { background: #f0f0f0; padding: 15px; text-align: center; color: #666; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f0f0f0; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 {{ title }}</h1>
            <p>{{ timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else 'Just now' }}</p>
        </div>
        
        <div class="content">
            <div class="alert-details">
                <h3>Alert Details</h3>
                <p><strong>Severity:</strong> <span class="metric-value">{{ severity.upper() }}</span></p>
                {% if station_id %}<p><strong>Station:</strong> {{ station_id }}</p>{% endif %}
                {% if metric_type %}<p><strong>Metric:</strong> {{ metric_type.replace('_', ' ').title() }}</p>{% endif %}
                {% if trigger_value is not none %}<p><strong>Current Value:</strong> <span class="metric-value">{{ trigger_value }}</span></p>{% endif %}
                {% if threshold_value is not none %}<p><strong>Threshold:</strong> {{ threshold_value }}</p>{% endif %}
            </div>
            
            <p>{{ message }}</p>
            
            {% if chart_attached %}
            <div class="chart-container">
                <h3>📊 Data Visualization</h3>
                <p>See attached chart for detailed trend analysis over the last {{ chart_hours }} hours.</p>
            </div>
            {% endif %}
            
            <div class="alert-details">
                <h3>Recommended Actions</h3>
                <ul>
                    {% if severity == 'critical' %}
                    <li>Immediate attention required - check pond monitoring system</li>
                    <li>Verify sensor readings are accurate</li>
                    <li>Contact maintenance team if issue persists</li>
                    {% elif severity == 'warning' %}
                    <li>Monitor situation closely</li>
                    <li>Check for any environmental factors</li>
                    <li>Review recent trends in the dashboard</li>
                    {% else %}
                    <li>Note the alert for future reference</li>
                    <li>Check dashboard for additional context</li>
                    {% endif %}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>This alert was generated by PondMonitor System</p>
            <p>Alert ID: {{ alert_id or 'N/A' }} | Generated at {{ timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else 'Unknown time' }}</p>
        </div>
    </div>
</body>
</html>'''
        path.write_text(template_content, encoding='utf-8')
    
    async def send(self, message: NotificationMessage) -> NotificationResult:
        """Send email notification"""
        try:
            # Validate configuration
            if not self.config.email_enabled or not self.config.smtp_server:
                return NotificationResult(
                    success=False,
                    channel="email",
                    recipient="N/A",
                    error="Email notifications not configured"
                )
            
            if not self.config.email_to:
                return NotificationResult(
                    success=False,
                    channel="email", 
                    recipient="N/A",
                    error="No email recipients configured"
                )
            
            # Generate chart if requested
            chart_data = None
            if message.include_chart:
                chart_data = self.chart_generator.generate_alert_chart(message)
            
            # Render email template
            template = self.template_env.get_template('email_alert.html')
            html_content = template.render(
                title=message.title,
                message=message.message,
                severity=message.severity,
                station_id=message.station_id,
                metric_type=message.metric_type,
                trigger_value=message.trigger_value,
                threshold_value=message.threshold_value,
                timestamp=message.timestamp,
                alert_id=message.alert_id,
                chart_attached=chart_data is not None,
                chart_hours=self.config.chart_time_range_hours
            )
            
            # Send emails to all recipients
            results = []
            for recipient in self.config.email_to:
                result = await self._send_single_email(recipient, message, html_content, chart_data)
                results.append(result)
            
            # Return overall result
            success_count = sum(1 for r in results if r.success)
            if success_count == 0:
                return NotificationResult(
                    success=False,
                    channel="email",
                    recipient=", ".join(self.config.email_to),
                    error=f"Failed to send to all {len(results)} recipients"
                )
            elif success_count < len(results):
                return NotificationResult(
                    success=True,
                    channel="email",
                    recipient=f"{success_count}/{len(results)} recipients",
                    error=f"Partial delivery: {len(results) - success_count} failed"
                )
            else:
                return NotificationResult(
                    success=True,
                    channel="email",
                    recipient=", ".join(self.config.email_to),
                    sent_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return NotificationResult(
                success=False,
                channel="email",
                recipient="N/A",
                error=str(e)
            )
    
    async def _send_single_email(self, recipient: str, message: NotificationMessage, 
                                html_content: str, chart_data: Optional[bytes]) -> NotificationResult:
        """Send email to a single recipient"""
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = f"[PondMonitor] {message.severity.upper()}: {message.title}"
            msg['From'] = self.config.email_from
            msg['To'] = recipient
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add chart as attachment if available
            if chart_data:
                chart_part = MIMEImage(chart_data, _subtype='png')
                chart_part.add_header('Content-Disposition', 'attachment', filename='alert_chart.png')
                chart_part.add_header('Content-ID', '<chart>')
                msg.attach(chart_part)
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient}")
            return NotificationResult(
                success=True,
                channel="email",
                recipient=recipient,
                sent_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return NotificationResult(
                success=False,
                channel="email",
                recipient=recipient,
                error=str(e)
            )
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=10) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    @property
    def channel_name(self) -> str:
        return "email"


class TelegramNotificationChannel(NotificationChannel):
    """Telegram notification channel for instant mobile alerts"""
    
    def __init__(self, config: AlertingConfig):
        self.config = config
        self.chart_generator = ChartGenerator(config)
        self.api_base = "https://api.telegram.org/bot{}/".format(config.telegram_bot_token)
    
    async def send(self, message: NotificationMessage) -> NotificationResult:
        """Send Telegram notification"""
        try:
            if not self.config.telegram_enabled or not self.config.telegram_bot_token:
                return NotificationResult(
                    success=False,
                    channel="telegram",
                    recipient=self.config.telegram_chat_id,
                    error="Telegram notifications not configured"
                )
            
            # Format message for Telegram
            telegram_message = self._format_telegram_message(message)
            
            # Generate and send chart if requested
            if message.include_chart:
                chart_data = self.chart_generator.generate_alert_chart(message)
                if chart_data:
                    await self._send_chart(chart_data, telegram_message)
                else:
                    await self._send_text(telegram_message)
            else:
                await self._send_text(telegram_message)
            
            return NotificationResult(
                success=True,
                channel="telegram",
                recipient=self.config.telegram_chat_id,
                sent_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return NotificationResult(
                success=False,
                channel="telegram",
                recipient=self.config.telegram_chat_id,
                error=str(e)
            )
    
    def _format_telegram_message(self, message: NotificationMessage) -> str:
        """Format message for Telegram with emoji and markdown"""
        # Severity emoji
        severity_emoji = {
            'critical': '🚨',
            'warning': '⚠️', 
            'info': 'ℹ️'
        }
        
        # Metric emoji
        metric_emoji = {
            'water_level': '💧',
            'temperature': '🌡️',
            'battery_voltage': '🔋',
            'signal_strength': '📶'
        }
        
        emoji = severity_emoji.get(message.severity, '📊')
        metric_emoji_str = metric_emoji.get(message.metric_type, '📊')
        
        # Build message
        lines = [
            f"{emoji} *{message.severity.upper()}: {message.title}*",
            "",
            f"{metric_emoji_str} {message.message}",
        ]
        
        if message.station_id:
            lines.append(f"📍 Station: `{message.station_id}`")
        
        if message.trigger_value is not None:
            lines.append(f"📈 Current Value: *{message.trigger_value}*")
        
        if message.threshold_value is not None:
            lines.append(f"🎯 Threshold: `{message.threshold_value}`")
        
        if message.timestamp:
            lines.append(f"⏰ Time: `{message.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}`")
        
        if message.alert_id:
            lines.append(f"🆔 Alert ID: `{message.alert_id}`")
        
        return "\n".join(lines)
    
    async def _send_text(self, text: str):
        """Send text message to Telegram"""
        url = self.api_base + "sendMessage"
        data = {
            'chat_id': self.config.telegram_chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
    
    async def _send_chart(self, chart_data: bytes, caption: str):
        """Send chart image with caption to Telegram"""
        url = self.api_base + "sendPhoto"
        
        files = {'photo': ('alert_chart.png', chart_data, 'image/png')}
        data = {
            'chat_id': self.config.telegram_chat_id,
            'caption': caption,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            url = self.api_base + "getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            bot_info = response.json()
            if bot_info.get('ok'):
                logger.info(f"Telegram bot connected: {bot_info.get('result', {}).get('username', 'Unknown')}")
                return True
            return False
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
    
    @property
    def channel_name(self) -> str:
        return "telegram"


class DiscordNotificationChannel(NotificationChannel):
    """Discord notification channel via webhooks"""
    
    def __init__(self, config: AlertingConfig):
        self.config = config
        self.chart_generator = ChartGenerator(config)
    
    async def send(self, message: NotificationMessage) -> NotificationResult:
        """Send Discord notification"""
        try:
            if not self.config.discord_enabled or not self.config.discord_webhook_url:
                return NotificationResult(
                    success=False,
                    channel="discord",
                    recipient="webhook",
                    error="Discord notifications not configured"
                )
            
            # Use requests directly with SSL verification disabled for corporate environments
            import requests
            import urllib3
            # Suppress only the single warning from urllib3 needed
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Create Discord embed data
            embed_data = {
                "title": f"{message.severity.upper()}: {message.title}",
                "description": message.message,
                "color": {
                    'critical': 0xFF0000,  # Red
                    'warning': 0xFF8C00,   # Orange
                    'info': 0x0099FF       # Blue
                }.get(message.severity, 0x0099FF),
                "fields": [],
                "footer": {
                    "text": "PondMonitor Alert System",
                    "icon_url": "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"
                }
            }
            
            # Add fields
            if message.station_id:
                embed_data["fields"].append({"name": "Station", "value": message.station_id, "inline": True})
            
            if message.metric_type:
                embed_data["fields"].append({"name": "Metric", "value": message.metric_type.replace('_', ' ').title(), "inline": True})
            
            if message.trigger_value is not None:
                embed_data["fields"].append({"name": "Current Value", "value": str(message.trigger_value), "inline": True})
            
            if message.threshold_value is not None:
                embed_data["fields"].append({"name": "Threshold", "value": str(message.threshold_value), "inline": True})
            
            if message.alert_id:
                embed_data["fields"].append({"name": "Alert ID", "value": message.alert_id, "inline": True})
            
            # Add timestamp
            if message.timestamp:
                embed_data["timestamp"] = message.timestamp.isoformat()
            
            # Prepare payload
            payload = {
                'username': 'PondMonitor',
                'embeds': [embed_data]
            }
            
            # Add chart if requested
            files = None
            if message.include_chart:
                chart_data = self.chart_generator.generate_alert_chart(message)
                if chart_data:
                    files = {'file': ('alert_chart.png', chart_data, 'image/png')}
                    embed_data["image"] = {"url": "attachment://alert_chart.png"}
            
            # Send webhook with SSL verification disabled for Docker/corporate environments
            if files:
                response = requests.post(
                    self.config.discord_webhook_url,
                    data={'payload_json': json.dumps(payload)},
                    files=files,
                    timeout=30,
                    verify=False  # Disable SSL verification for corporate environments
                )
            else:
                response = requests.post(
                    self.config.discord_webhook_url,
                    json=payload,
                    timeout=10,
                    verify=False  # Disable SSL verification for corporate environments
                )
            
            if response.status_code in [200, 204]:
                return NotificationResult(
                    success=True,
                    channel="discord",
                    recipient="webhook",
                    sent_at=datetime.now()
                )
            else:
                return NotificationResult(
                    success=False,
                    channel="discord", 
                    recipient="webhook",
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return NotificationResult(
                success=False,
                channel="discord",
                recipient="webhook", 
                error=str(e)
            )
    
    def _create_discord_embed(self, message: NotificationMessage) -> DiscordEmbed:
        """Create Discord embed for alert message"""
        # Color based on severity
        colors = {
            'critical': 0xFF0000,  # Red
            'warning': 0xFF8C00,   # Orange
            'info': 0x0099FF       # Blue
        }
        
        embed = DiscordEmbed(
            title=f"{message.severity.upper()}: {message.title}",
            description=message.message,
            color=colors.get(message.severity, 0x0099FF)
        )
        
        # Add fields
        if message.station_id:
            embed.add_embed_field(name="Station", value=message.station_id, inline=True)
        
        if message.metric_type:
            embed.add_embed_field(name="Metric", value=message.metric_type.replace('_', ' ').title(), inline=True)
        
        if message.trigger_value is not None:
            embed.add_embed_field(name="Current Value", value=str(message.trigger_value), inline=True)
        
        if message.threshold_value is not None:
            embed.add_embed_field(name="Threshold", value=str(message.threshold_value), inline=True)
        
        if message.alert_id:
            embed.add_embed_field(name="Alert ID", value=message.alert_id, inline=True)
        
        # Add timestamp
        if message.timestamp:
            embed.set_timestamp(message.timestamp)
        
        # Add footer
        embed.set_footer(text="PondMonitor Alert System", icon_url="https://cdn-icons-png.flaticon.com/512/1077/1077114.png")
        
        return embed
    
    def test_connection(self) -> bool:
        """Test Discord webhook connection"""
        try:
            # Use requests directly with SSL verification disabled for Docker environments
            import requests
            import urllib3
            # Suppress only the single warning from urllib3 needed
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            payload = {
                'content': '**PondMonitor Connection Test**\nDiscord integration is working correctly!',
                'username': 'PondMonitor'
            }
            
            response = requests.post(
                self.config.discord_webhook_url, 
                json=payload, 
                timeout=10, 
                verify=False  # Disable SSL verification for Docker environments
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Discord connection test failed: {e}")
            return False
    
    @property
    def channel_name(self) -> str:
        return "discord"


class BrowserNotificationChannel(NotificationChannel):
    """Browser push notification channel via WebSocket/SSE"""
    
    def __init__(self, config: AlertingConfig):
        self.config = config
        self._active_connections = set()  # Will be managed by Flask-SocketIO
    
    async def send(self, message: NotificationMessage) -> NotificationResult:
        """Send browser notification via WebSocket"""
        try:
            if not self.config.browser_notifications_enabled:
                return NotificationResult(
                    success=False,
                    channel="browser",
                    recipient="web_clients",
                    error="Browser notifications disabled"
                )
            
            # Format notification data
            notification_data = {
                'type': 'alert',
                'severity': message.severity,
                'title': message.title,
                'message': message.message,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                'station_id': message.station_id,
                'metric_type': message.metric_type,
                'trigger_value': message.trigger_value,
                'threshold_value': message.threshold_value,
                'alert_id': message.alert_id
            }
            
            # This would integrate with Flask-SocketIO when implemented
            # For now, we'll store the notification in Redis for web clients to poll
            try:
                import redis
                from ..config import get_config
                
                config = get_config()
                r = redis.Redis(**config.redis.get_connection_dict())
                
                # Store notification for web polling
                r.lpush('browser_notifications', 
                       json.dumps(notification_data, default=str))
                r.ltrim('browser_notifications', 0, 99)  # Keep last 100 notifications
                r.expire('browser_notifications', 3600)   # Expire after 1 hour
                
            except Exception as redis_error:
                logger.warning(f"Failed to store browser notification in Redis: {redis_error}")
            
            return NotificationResult(
                success=True,
                channel="browser",
                recipient="web_clients",
                sent_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Browser notification failed: {e}")
            return NotificationResult(
                success=False,
                channel="browser",
                recipient="web_clients",
                error=str(e)
            )
    
    def test_connection(self) -> bool:
        """Test browser notification capability"""
        return self.config.browser_notifications_enabled
    
    @property
    def channel_name(self) -> str:
        return "browser"


class NotificationService:
    """
    Central notification service that manages multiple channels
    
    Features:
    - Multi-channel notification dispatch
    - Delivery confirmation and retry logic
    - Rate limiting and error handling
    - Channel health monitoring
    """
    
    def __init__(self, config: AlertingConfig):
        self.config = config
        self.channels: Dict[str, NotificationChannel] = {}
        self._init_channels()
        
        # Delivery tracking
        self._delivery_history: List[NotificationResult] = []
        self._max_history = 1000
        
        logger.info("Notification service initialized")
    
    def _init_channels(self):
        """Initialize notification channels from database configuration"""
        from src.database import get_database
        
        try:
            # Always add browser notifications (no database config needed)
            if self.config.browser_notifications_enabled:
                self.channels['browser'] = BrowserNotificationChannel(self.config)
            
            # Load channels from database
            db = get_database()
            result = db.execute_query("""
                SELECT channel_type, name, config, enabled
                FROM notification_channels
                WHERE enabled = true
                ORDER BY channel_type, name
            """)
            
            for row_dict in result.to_dict_list():
                channel_type = row_dict['channel_type']
                channel_config = row_dict['config']
                channel_name = row_dict['name'].lower()
                
                # Create appropriate channel instance based on type
                if channel_type == 'discord' and channel_config.get('webhook_url'):
                    # Create a mock config with database values
                    mock_config = type('Config', (), {
                        'discord_enabled': True,
                        'discord_webhook_url': channel_config['webhook_url']
                    })()
                    # Copy other needed attributes from main config
                    for attr in ['include_charts', 'chart_time_range_hours']:
                        if hasattr(self.config, attr):
                            setattr(mock_config, attr, getattr(self.config, attr))
                    
                    self.channels['discord'] = DiscordNotificationChannel(mock_config)
                    
                elif channel_type == 'telegram' and channel_config.get('bot_token'):
                    # Create a mock config with database values
                    mock_config = type('Config', (), {
                        'telegram_enabled': True,
                        'telegram_bot_token': channel_config['bot_token'],
                        'telegram_chat_id': channel_config.get('chat_id')
                    })()
                    # Copy other needed attributes from main config
                    for attr in ['include_charts', 'chart_time_range_hours']:
                        if hasattr(self.config, attr):
                            setattr(mock_config, attr, getattr(self.config, attr))
                    
                    self.channels['telegram'] = TelegramNotificationChannel(mock_config)
                    
                elif channel_type == 'email' and channel_config.get('smtp_server'):
                    # Create a mock config with database values
                    mock_config = type('Config', (), {
                        'email_enabled': True,
                        'smtp_server': channel_config['smtp_server'],
                        'smtp_port': channel_config.get('smtp_port', 587),
                        'smtp_username': channel_config.get('smtp_username'),
                        'smtp_password': channel_config.get('smtp_password'),
                        'smtp_use_tls': channel_config.get('smtp_use_tls', True),
                        'email_from': channel_config.get('email_from'),
                        'email_to': channel_config.get('email_to', [])
                    })()
                    # Copy other needed attributes from main config
                    for attr in ['include_charts', 'chart_time_range_hours']:
                        if hasattr(self.config, attr):
                            setattr(mock_config, attr, getattr(self.config, attr))
                    
                    self.channels['email'] = EmailNotificationChannel(mock_config)
            
            logger.info(f"Initialized {len(self.channels)} notification channels from database: {list(self.channels.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load notification channels from database: {e}")
            # Fallback to .env config if database fails
            self._init_channels_fallback()
    
    def _init_channels_fallback(self):
        """Fallback to .env-based channel initialization"""
        logger.warning("Using fallback .env-based channel initialization")
        
        if self.config.email_enabled:
            self.channels['email'] = EmailNotificationChannel(self.config)
            
        if self.config.telegram_enabled:
            self.channels['telegram'] = TelegramNotificationChannel(self.config)
            
        if self.config.discord_enabled:
            self.channels['discord'] = DiscordNotificationChannel(self.config)
            
        if self.config.browser_notifications_enabled:
            self.channels['browser'] = BrowserNotificationChannel(self.config)
        
        logger.info(f"Initialized {len(self.channels)} notification channels from .env: {list(self.channels.keys())}")
    
    def reload_channels(self):
        """Reload notification channels from database"""
        logger.info("Reloading notification channels from database...")
        self.channels.clear()
        self._init_channels()
        logger.info(f"Reloaded {len(self.channels)} notification channels: {list(self.channels.keys())}")
    
    async def send_alert(self, message: NotificationMessage, 
                        channels: Optional[List[str]] = None) -> List[NotificationResult]:
        """
        Send alert notification to specified channels
        
        Args:
            message: Notification message to send
            channels: List of channel names (defaults to all enabled)
            
        Returns:
            List of delivery results for each channel
        """
        if not self.config.enabled:
            logger.warning("Alerting system is disabled")
            return []
        
        # Use all channels if none specified
        if channels is None:
            channels = list(self.channels.keys())
        
        # Send to each channel
        results = []
        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Unknown notification channel: {channel_name}")
                continue
            
            try:
                channel = self.channels[channel_name]
                result = await channel.send(message)
                results.append(result)
                
                # Log result
                if result.success:
                    logger.info(f"Alert sent via {channel_name} to {result.recipient}")
                else:
                    logger.error(f"Failed to send alert via {channel_name}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Unexpected error sending to {channel_name}: {e}")
                results.append(NotificationResult(
                    success=False,
                    channel=channel_name,
                    recipient="unknown",
                    error=str(e)
                ))
        
        # Store delivery history
        self._delivery_history.extend(results)
        if len(self._delivery_history) > self._max_history:
            self._delivery_history = self._delivery_history[-self._max_history:]
        
        return results
    
    def test_channels(self) -> Dict[str, bool]:
        """Test connectivity for all configured channels"""
        results = {}
        for name, channel in self.channels.items():
            try:
                results[name] = channel.test_connection()
            except Exception as e:
                logger.error(f"Channel test failed for {name}: {e}")
                results[name] = False
        return results
    
    def get_channel_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all channels"""
        status = {}
        
        for name, channel in self.channels.items():
            # Get recent delivery stats
            recent_results = [r for r in self._delivery_history 
                            if r.channel == name and r.sent_at 
                            and r.sent_at > datetime.now() - timedelta(hours=24)]
            
            success_count = sum(1 for r in recent_results if r.success)
            
            status[name] = {
                'enabled': True,
                'healthy': channel.test_connection(),
                'deliveries_24h': len(recent_results),
                'success_rate_24h': success_count / len(recent_results) if recent_results else 0,
                'last_delivery': max((r.sent_at for r in recent_results if r.sent_at), default=None)
            }
        
        return status
    
    def get_delivery_history(self, hours: int = 24) -> List[NotificationResult]:
        """Get delivery history for the specified time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [r for r in self._delivery_history 
                if r.sent_at and r.sent_at > cutoff]


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def init_notification_service(config: AlertingConfig) -> NotificationService:
    """Initialize global notification service"""
    global _notification_service
    _notification_service = NotificationService(config)
    return _notification_service


def get_notification_service() -> NotificationService:
    """Get the global notification service instance"""
    if _notification_service is None:
        raise RuntimeError("Notification service not initialized. Call init_notification_service() first.")
    return _notification_service


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    from ..config import AlertingConfig
    
    # Create test configuration
    test_config = AlertingConfig(
        enabled=True,
        email_enabled=True,
        email_to=["test@example.com"],
        telegram_enabled=True,
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat"
    )
    
    async def test_notifications():
        service = NotificationService(test_config)
        
        # Test message
        message = NotificationMessage(
            title="Test Alert",
            message="This is a test alert from PondMonitor",
            severity="warning",
            station_id="test_station",
            metric_type="temperature",
            trigger_value=42.5,
            threshold_value=40.0,
            timestamp=datetime.now()
        )
        
        # Test channel connectivity
        channel_status = service.test_channels()
        print("Channel status:", channel_status)
        
        # Send test notification
        results = await service.send_alert(message)
        for result in results:
            print(f"Result: {result}")
    
    # Run test
    asyncio.run(test_notifications())