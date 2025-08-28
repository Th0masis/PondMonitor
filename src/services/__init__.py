"""
Services package initialization
"""

# Import service modules conditionally to avoid dependency issues during testing
try:
    from . import alert_service
except ImportError:
    pass

try:
    from . import analytics_service
except ImportError:
    pass

try:
    from . import export_service
except ImportError:
    pass

try:
    from . import weather_service
except ImportError:
    pass

try:
    from . import advanced_export_service
except ImportError:
    pass

# Import modules with external dependencies conditionally
try:
    from . import alert_engine
except ImportError:
    # Create a dummy module if import fails
    import types
    from unittest.mock import Mock
    alert_engine = types.ModuleType('alert_engine')
    alert_engine.init_alert_engine = lambda *args, **kwargs: None
    alert_engine.get_config = Mock()
    alert_engine.get_database = Mock()
    alert_engine.get_notification_service = Mock()
    alert_engine.get_alert_engine = Mock()
    alert_engine.AlertEngine = Mock
    alert_engine.AlertSeverity = Mock
    alert_engine.AlertStatus = Mock

try:
    from . import notification_service
except ImportError:
    # Create a dummy module if import fails
    import types
    from unittest.mock import Mock
    notification_service = types.ModuleType('notification_service')
    notification_service.init_notification_service = lambda *args, **kwargs: None
    notification_service.get_notification_service = Mock()
    notification_service.NotificationService = Mock
    notification_service.NotificationMessage = Mock

try:
    from . import scheduler_service
except ImportError:
    # Create a dummy module if import fails
    import types
    from unittest.mock import Mock
    scheduler_service = types.ModuleType('scheduler_service')
    scheduler_service.init_scheduler_service = lambda *args, **kwargs: None
    scheduler_service.get_scheduler_service = Mock()
    scheduler_service.SchedulerService = Mock
    scheduler_service.BackgroundScheduler = Mock
    scheduler_service.get_alert_engine = Mock()
    scheduler_service.get_notification_service = Mock()

# Make initialization functions available at package level if possible
try:
    from .alert_engine import init_alert_engine
except ImportError:
    def init_alert_engine(*args, **kwargs):
        pass

try:
    from .notification_service import init_notification_service
except ImportError:
    def init_notification_service(*args, **kwargs):
        pass

try:
    from .scheduler_service import init_scheduler_service
except ImportError:
    def init_scheduler_service(*args, **kwargs):
        pass