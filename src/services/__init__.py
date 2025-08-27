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
    alert_engine = types.ModuleType('alert_engine')
    alert_engine.init_alert_engine = lambda *args, **kwargs: None

try:
    from . import notification_service
except ImportError:
    # Create a dummy module if import fails
    import types
    notification_service = types.ModuleType('notification_service')
    notification_service.init_notification_service = lambda *args, **kwargs: None

try:
    from . import scheduler_service
except ImportError:
    # Create a dummy module if import fails
    import types
    scheduler_service = types.ModuleType('scheduler_service')
    scheduler_service.init_scheduler_service = lambda *args, **kwargs: None

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