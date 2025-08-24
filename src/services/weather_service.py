"""
PondMonitor Weather Service

Handles all weather-related API calls and data processing with intelligent
caching, error handling, and data transformation. Replaces inline weather
logic in the main application.

Features:
- Met.no API integration with proper headers
- Intelligent caching with Redis fallback
- Data aggregation and statistics
- Weather icon mapping
- Error handling with graceful degradation
- Rate limiting and request optimization
"""

import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

import requests
import redis

from ..config import WeatherConfig, RedisConfig
from ..utils import ServiceError, ValidationError, RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Structured weather data"""
    timestamp: str
    temperature: float
    pressure: float
    humidity: float
    wind_speed: float
    wind_direction: int
    wind_gust: float
    cloud_coverage: int
    precipitation: float
    symbol_code: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DailyForecast:
    """Daily weather forecast summary"""
    date: str
    temp_max: float
    temp_min: float
    temp_avg: float
    wind_avg: float
    wind_gust: float
    precipitation: float
    humidity_avg: float
    pressure_avg: float
    symbol_code: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class WeatherStats:
    """Weather statistics for a time period"""
    period_hours: int
    data_points: int
    temperature: Dict[str, float]
    precipitation: Dict[str, float]
    wind: Dict[str, float]
    pressure: Dict[str, float]
    calculated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class WeatherIconMapper:
    """Maps weather symbols to appropriate icons and descriptions"""
    
    ICON_MAP = {
        'clearsky': {'emoji': '☀️', 'description': 'Clear sky'},
        'fair': {'emoji': '🌤️', 'description': 'Fair weather'},
        'partlycloudy': {'emoji': '⛅', 'description': 'Partly cloudy'},
        'cloudy': {'emoji': '☁️', 'description': 'Cloudy'},
        'rainshowers': {'emoji': '🌦️', 'description': 'Rain showers'},
        'rain': {'emoji': '🌧️', 'description': 'Rain'},
        'lightrain': {'emoji': '🌦️', 'description': 'Light rain'},
        'heavyrain': {'emoji': '🌧️', 'description': 'Heavy rain'},
        'sleet': {'emoji': '🌨️', 'description': 'Sleet'},
        'snow': {'emoji': '❄️', 'description': 'Snow'},
        'snowshowers': {'emoji': '🌨️', 'description': 'Snow showers'},
        'fog': {'emoji': '🌫️', 'description': 'Fog'},
        'thunderstorm': {'emoji': '⛈️', 'description': 'Thunderstorm'}
    }
    
    @classmethod
    def get_icon_info(cls, symbol_code: str) -> Dict[str, str]:
        """
        Get icon information for weather symbol.
        
        Args:
            symbol_code: Weather symbol code (may include day/night suffix)
        
        Returns:
            Dictionary with emoji and description
        """
        # Remove day/night suffix
        base_symbol = symbol_code.split('_')[0] if symbol_code else 'clearsky'
        return cls.ICON_MAP.get(base_symbol, cls.ICON_MAP['clearsky'])
    
    @classmethod
    def guess_symbol(cls, precipitation: float, cloud_coverage: float) -> str:
        """
        Guess weather symbol based on precipitation and cloud coverage.
        
        Args:
            precipitation: Precipitation amount in mm
            cloud_coverage: Cloud coverage percentage
        
        Returns:
            Weather symbol code
        """
        if precipitation > 2:
            return 'rain'
        elif precipitation > 0.2:
            return 'lightrain'
        elif cloud_coverage > 80:
            return 'cloudy'
        elif cloud_coverage > 40:
            return 'partlycloudy_day'
        else:
            return 'clearsky_day'


class WeatherCache:
    """Weather data caching with Redis and in-memory fallback"""
    
    def __init__(self, redis_config: Optional[RedisConfig] = None):
        """
        Initialize weather cache.
        
        Args:
            redis_config: Redis configuration (optional)
        """
        self.redis_client = None
        self.memory_cache = {}
        self.cache_timeout = 3600  # 1 hour default
        
        if redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config.get_connection_dict())
                self.redis_client.ping()
                logger.info("Weather cache: Using Redis")
            except Exception as e:
                logger.warning(f"Redis not available for weather cache: {e}")
                logger.info("Weather cache: Using memory fallback")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            # Try Redis first
            if self.redis_client:
                cached = self.redis_client.get(f"weather:{key}")
                if cached:
                    return json.loads(cached)
            
            # Fallback to memory cache
            if key in self.memory_cache:
                data, timestamp = self.memory_cache[key]
                if time.time() - timestamp < self.cache_timeout:
                    return data
                else:
                    del self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")
            return None
    
    def set(self, key: str, data: Any, timeout: Optional[int] = None) -> bool:
        """Set cached data"""
        try:
            timeout = timeout or self.cache_timeout
            
            # Try Redis first
            if self.redis_client:
                self.redis_client.setex(
                    f"weather:{key}",
                    timeout,
                    json.dumps(data, default=str)
                )
                return True
            
            # Fallback to memory cache
            self.memory_cache[key] = (data, time.time())
            
            # Clean old entries periodically
            if len(self.memory_cache) > 100:
                self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")
            return False
    
    def _cleanup_memory_cache(self) -> None:
        """Clean expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.memory_cache.items()
            if current_time - timestamp > self.cache_timeout
        ]
        for key in expired_keys:
            del self.memory_cache[key]


class WeatherService:
    """
    Service for weather data retrieval and processing.
    
    Handles all interactions with the Met.no weather API,
    including caching, error handling, and data transformation.
    """
    
    def __init__(self, config: WeatherConfig, redis_config: Optional[RedisConfig] = None):
        """
        Initialize weather service.
        
        Args:
            config: Weather configuration
            redis_config: Optional Redis configuration for caching
        """
        self.config = config
        self.cache = WeatherCache(redis_config)
        self.rate_limiter = RateLimiter()
        
        # API rate limiting (met.no allows reasonable rates)
        self.api_rate_limit = 60  # requests per hour
        self.api_window = 3600    # 1 hour
        
        logger.info("Weather service initialized")
    
    def get_current_weather(self) -> Optional[WeatherData]:
        """
        Get current weather conditions.
        
        Returns:
            Current weather data or None if unavailable
        """
        cache_key = "current_weather"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Returning cached current weather")
            return WeatherData(**cached)
        
        try:
            # Get fresh data from API
            raw_data = self._fetch_weather_data()
            if not raw_data:
                return None
            
            # Extract current conditions (first entry)
            timeseries = raw_data.get("properties", {}).get("timeseries", [])
            if not timeseries:
                return None
            
            current_entry = timeseries[0]
            current_weather = self._parse_weather_entry(current_entry)
            
            # Cache with shorter TTL for current weather
            self.cache.set(cache_key, current_weather.to_dict(), timeout=1800)  # 30 minutes
            
            return current_weather
            
        except Exception as e:
            logger.error(f"Failed to get current weather: {e}")
            return None
    
    def get_meteogram_data(self, hours: int = 48) -> List[WeatherData]:
        """
        Get detailed weather forecast for meteogram display.
        
        Args:
            hours: Number of hours to retrieve (default 48)
        
        Returns:
            List of weather data points
        """
        cache_key = f"meteogram_{hours}h"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Returning cached meteogram data ({hours}h)")
            return [WeatherData(**item) for item in cached]
        
        try:
            # Get fresh data from API
            raw_data = self._fetch_weather_data()
            if not raw_data:
                return []
            
            # Parse all entries
            meteogram_data = []
            timeseries = raw_data.get("properties", {}).get("timeseries", [])
            
            # Filter to requested time range
            now = datetime.now(timezone.utc)
            end_time = now + timedelta(hours=hours)
            
            for entry in timeseries:
                entry_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
                if now <= entry_time <= end_time:
                    weather_data = self._parse_weather_entry(entry)
                    meteogram_data.append(weather_data)
            
            # Cache the result
            cached_data = [item.to_dict() for item in meteogram_data]
            self.cache.set(cache_key, cached_data)
            
            logger.info(f"Retrieved {len(meteogram_data)} meteogram data points")
            return meteogram_data
            
        except Exception as e:
            logger.error(f"Failed to get meteogram data: {e}")
            return []
    
    def get_daily_forecast(self, days: int = 7) -> List[DailyForecast]:
        """
        Get daily weather forecast summary.
        
        Args:
            days: Number of days to retrieve (default 7)
        
        Returns:
            List of daily forecast summaries
        """
        cache_key = f"daily_forecast_{days}d"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Returning cached daily forecast ({days}d)")
            return [DailyForecast(**item) for item in cached]
        
        try:
            # Get meteogram data (need detailed data for aggregation)
            meteogram_data = self.get_meteogram_data(hours=days * 24 + 24)
            if not meteogram_data:
                return []
            
            # Aggregate by day
            daily_data = defaultdict(lambda: {
                'temps': [], 'wind_speeds': [], 'wind_gusts': [], 
                'precipitation': 0.0, 'humidity': [], 'pressure': [],
                'symbols': []
            })
            
            for weather in meteogram_data:
                # Parse date from timestamp
                dt = datetime.fromisoformat(weather.timestamp)
                date_key = dt.date().isoformat()
                
                daily_data[date_key]['temps'].append(weather.temperature)
                daily_data[date_key]['wind_speeds'].append(weather.wind_speed)
                daily_data[date_key]['wind_gusts'].append(weather.wind_gust)
                daily_data[date_key]['precipitation'] += weather.precipitation
                daily_data[date_key]['humidity'].append(weather.humidity)
                daily_data[date_key]['pressure'].append(weather.pressure)
                daily_data[date_key]['symbols'].append(weather.symbol_code)
            
            # Create daily forecasts
            daily_forecasts = []
            for date_str in sorted(daily_data.keys())[:days]:
                day_data = daily_data[date_str]
                
                if not day_data['temps']:
                    continue
                
                # Find most common symbol
                symbol_counts = defaultdict(int)
                for symbol in day_data['symbols']:
                    symbol_counts[symbol] += 1
                most_common_symbol = max(symbol_counts.keys(), key=symbol_counts.get)
                
                forecast = DailyForecast(
                    date=date_str,
                    temp_max=round(max(day_data['temps']), 1),
                    temp_min=round(min(day_data['temps']), 1),
                    temp_avg=round(sum(day_data['temps']) / len(day_data['temps']), 1),
                    wind_avg=round(sum(day_data['wind_speeds']) / len(day_data['wind_speeds']), 1),
                    wind_gust=round(max(day_data['wind_gusts']), 1),
                    precipitation=round(day_data['precipitation'], 1),
                    humidity_avg=round(sum(day_data['humidity']) / len(day_data['humidity']), 1),
                    pressure_avg=round(sum(day_data['pressure']) / len(day_data['pressure']), 1),
                    symbol_code=most_common_symbol
                )
                
                daily_forecasts.append(forecast)
            
            # Cache the result
            cached_data = [item.to_dict() for item in daily_forecasts]
            self.cache.set(cache_key, cached_data)
            
            logger.info(f"Generated {len(daily_forecasts)} daily forecasts")
            return daily_forecasts
            
        except Exception as e:
            logger.error(f"Failed to get daily forecast: {e}")
            return []
    
    def get_weather_statistics(self, hours: int = 24) -> Optional[WeatherStats]:
        """
        Get weather statistics for the specified time period.
        
        Args:
            hours: Number of hours to analyze
        
        Returns:
            Weather statistics or None if unavailable
        """
        cache_key = f"weather_stats_{hours}h"
        
        # Try cache first (shorter cache time for stats)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Returning cached weather stats ({hours}h)")
            return WeatherStats(**cached)
        
        try:
            # Get meteogram data for analysis
            meteogram_data = self.get_meteogram_data(hours=hours)
            if not meteogram_data:
                return None
            
            # Calculate statistics
            temps = [w.temperature for w in meteogram_data]
            precip = [w.precipitation for w in meteogram_data]
            winds = [w.wind_speed for w in meteogram_data]
            pressures = [w.pressure for w in meteogram_data]
            
            stats = WeatherStats(
                period_hours=hours,
                data_points=len(meteogram_data),
                temperature={
                    'max': round(max(temps), 1) if temps else None,
                    'min': round(min(temps), 1) if temps else None,
                    'avg': round(sum(temps) / len(temps), 1) if temps else None
                },
                precipitation={
                    'total': round(sum(precip), 1) if precip else 0,
                    'max_hourly': round(max(precip), 1) if precip else 0
                },
                wind={
                    'max': round(max(winds), 1) if winds else None,
                    'avg': round(sum(winds) / len(winds), 1) if winds else None
                },
                pressure={
                    'max': round(max(pressures), 1) if pressures else None,
                    'min': round(min(pressures), 1) if pressures else None,
                    'avg': round(sum(pressures) / len(pressures), 1) if pressures else None
                },
                calculated_at=datetime.now(timezone.utc).isoformat()
            )
            
            # Cache for shorter time (15 minutes)
            self.cache.set(cache_key, stats.to_dict(), timeout=900)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate weather statistics: {e}")
            return None
    
    def _fetch_weather_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch raw weather data from Met.no API.
        
        Returns:
            Raw API response data or None if failed
        """
        # Check rate limiting
        client_id = "weather_api"
        if not self.rate_limiter.is_allowed(client_id, self.api_rate_limit, self.api_window):
            raise ServiceError("Weather API rate limit exceeded")
        
        try:
            url = (
                f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
                f"?lat={self.config.latitude}&lon={self.config.longitude}"
                f"&altitude={self.config.altitude}"
            )
            
            headers = {
                "User-Agent": self.config.user_agent
            }
            
            logger.debug(f"Fetching weather data from Met.no API")
            
            response = requests.get(url, headers=headers, timeout=self.config.api_timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Successfully fetched weather data from Met.no")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Weather API request failed: {e}")
            raise ServiceError(f"Weather API unavailable: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Weather API response parsing failed: {e}")
            raise ServiceError(f"Weather API response invalid: {e}")
    
    def _parse_weather_entry(self, entry: Dict[str, Any]) -> WeatherData:
        """
        Parse a single weather entry from API response.
        
        Args:
            entry: Raw weather entry from API
        
        Returns:
            Parsed weather data
        """
        try:
            # Extract timestamp
            timestamp = entry["time"]
            
            # Extract instant details
            instant = entry.get("data", {}).get("instant", {}).get("details", {})
            
            # Extract next 1 hour details
            next_1h = entry.get("data", {}).get("next_1_hours", {})
            next_1h_details = next_1h.get("details", {})
            
            # Get symbol code
            symbol_code = next_1h.get("summary", {}).get("symbol_code")
            if not symbol_code:
                # Guess symbol based on available data
                precip = next_1h_details.get("precipitation_amount", 0)
                clouds = instant.get("cloud_area_fraction", 0)
                symbol_code = WeatherIconMapper.guess_symbol(precip, clouds)
            
            return WeatherData(
                timestamp=timestamp,
                temperature=round(instant.get("air_temperature", 0), 1),
                pressure=round(instant.get("air_pressure_at_sea_level", 1013), 1),
                humidity=round(instant.get("relative_humidity", 50), 1),
                wind_speed=round(instant.get("wind_speed", 0), 1),
                wind_direction=int(instant.get("wind_from_direction", 0)),
                wind_gust=round(instant.get("wind_speed_of_gust", 0), 1),
                cloud_coverage=int(instant.get("cloud_area_fraction", 0)),
                precipitation=round(next_1h_details.get("precipitation_amount", 0), 1),
                symbol_code=symbol_code
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse weather entry: {e}")
            # Return minimal valid data
            return WeatherData(
                timestamp=entry.get("time", datetime.now(timezone.utc).isoformat()),
                temperature=0.0,
                pressure=1013.0,
                humidity=50.0,
                wind_speed=0.0,
                wind_direction=0,
                wind_gust=0.0,
                cloud_coverage=50,
                precipitation=0.0,
                symbol_code="clearsky_day"
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform weather service health check.
        
        Returns:
            Health status information
        """
        health_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healthy': False,
            'api_available': False,
            'cache_working': False,
            'location': {
                'latitude': self.config.latitude,
                'longitude': self.config.longitude,
                'altitude': self.config.altitude
            },
            'errors': []
        }
        
        try:
            # Test API connectivity
            url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={self.config.latitude}&lon={self.config.longitude}"
            headers = {"User-Agent": self.config.user_agent}
            
            response = requests.get(url, headers=headers, timeout=5)
            health_info['api_available'] = response.status_code == 200
            
            # Test cache
            test_key = "health_check_test"
            test_data = {"test": "data", "timestamp": time.time()}
            
            cache_set = self.cache.set(test_key, test_data)
            cache_get = self.cache.get(test_key)
            health_info['cache_working'] = cache_set and cache_get is not None
            
            # Overall health
            health_info['healthy'] = health_info['api_available'] and health_info['cache_working']
            
        except Exception as e:
            health_info['errors'].append(str(e))
            logger.error(f"Weather service health check failed: {e}")
        
        return health_info


def create_weather_service(
    weather_config: WeatherConfig,
    redis_config: Optional[RedisConfig] = None
) -> WeatherService:
    """
    Factory function to create weather service.
    
    Args:
        weather_config: Weather configuration
        redis_config: Optional Redis configuration
    
    Returns:
        Configured weather service
    """
    return WeatherService(weather_config, redis_config)


if __name__ == "__main__":
    # Example usage and testing
    from ..config import WeatherConfig, RedisConfig
    
    # Create test configuration
    weather_config = WeatherConfig(
        latitude=49.6265900,
        longitude=18.3016172,
        altitude=350
    )
    
    redis_config = RedisConfig(
        host="localhost",
        port=6379
    )
    
    try:
        # Initialize weather service
        weather_service = create_weather_service(weather_config, redis_config)
        
        # Test health check
        health = weather_service.health_check()
        print(f"Health check: {health}")
        
        # Test current weather
        current = weather_service.get_current_weather()
        if current:
            print(f"Current weather: {current.temperature}°C, {current.symbol_code}")
        
        # Test daily forecast
        forecast = weather_service.get_daily_forecast(3)
        print(f"3-day forecast: {len(forecast)} days")
        
        # Test statistics
        stats = weather_service.get_weather_statistics(24)
        if stats:
            print(f"24h stats: {stats.temperature}")
        
    except Exception as e:
        print(f"Weather service test failed: {e}")