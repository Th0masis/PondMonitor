/* PondMonitor - Weather Module */

let meteogramChart = null;
let currentWeatherData = null;

// Weather icon mapping for better display
const weatherIconMap = {
  'clearsky': '☀️',
  'fair': '🌤️',
  'partlycloudy': '⛅',
  'cloudy': '☁️',
  'rainshowers': '🌦️',
  'rain': '🌧️',
  'lightrain': '🌦️',
  'heavyrain': '🌧️',
  'sleet': '🌨️',
  'snow': '❄️',
  'snowshowers': '🌨️',
  'fog': '🌫️',
  'thunderstorm': '⛈️'
};

function getWeatherIcon(symbolCode) {
  const baseIcon = symbolCode.split('_')[0];
  return weatherIconMap[baseIcon] || '🌤️';
}

function getWindDirection(degrees) {
  const directions = ['S', 'SSZ', 'SZ', 'ZSZ', 'Z', 'ZSV', 'SV', 'SSV', 'S', 'SSZ', 'SZ', 'ZSZ', 'Z', 'ZSV', 'SV', 'SSV'];
  const index = Math.round(degrees / 22.5) % 16;
  return directions[index];
}

async function loadCurrentWeather() {
  try {
    let currentData;
    
    // Try to get current weather from API
    try {
      const currentRes = await fetch('/api/weather/current');
      currentData = await currentRes.json();
    } catch {
      // Fallback: use latest data from meteogram
      const res = await fetch('/api/weather/meteogram');
      const data = await res.json();
      if (data.length === 0) return;
      
      const now = Date.now();
      currentData = data.find(d => d.time >= now) || data[0];
    }
    
    updateCurrentWeatherCards(currentData);
  } catch (error) {
    console.error('Error loading current weather:', error);
    PondUtils.showError('Chyba při načítání aktuálního počasí');
  }
}

function updateCurrentWeatherCards(data) {
  const container = document.getElementById('currentWeather');
  if (!container) return;
  
  const icon = getWeatherIcon(data.symbol_code || 'clearsky');
  const windDir = getWindDirection(data.wind_direction || 0);
  
  container.innerHTML = `
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 197, 253, 0.1));">
      <div class="weather-icon">${icon}</div>
      <div class="weather-value">${data.temperature?.toFixed(1) || 'N/A'}°C</div>
      <div class="weather-label">Teplota</div>
    </div>
    
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(103, 232, 249, 0.1));">
      <div class="weather-icon">💧</div>
      <div class="weather-value">${data.rain?.toFixed(1) || '0.0'} mm</div>
      <div class="weather-label">Srážky (1h)</div>
    </div>
    
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(110, 231, 183, 0.1));">
      <div class="weather-icon">💨</div>
      <div class="weather-value">${data.wind?.toFixed(1) || 'N/A'} m/s</div>
      <div class="weather-label">Vítr ${windDir}</div>
    </div>
    
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(196, 181, 253, 0.1));">
      <div class="weather-icon">🌡️</div>
      <div class="weather-value">${data.pressure?.toFixed(0) || 'N/A'} hPa</div>
      <div class="weather-label">Tlak vzduchu</div>
    </div>
  `;
}

async function loadWeatherStats() {
  try {
    const res = await fetch('/api/weather/meteogram');
    const data = await res.json();
    
    if (data.length === 0) return;
    
    // Calculate 24h statistics
    const last24h = data.filter(d => d.time >= Date.now() - 24 * 3600 * 1000);
    
    const temps = last24h.map(d => d.temperature);
    const rains = last24h.map(d => d.rain);
    const winds = last24h.map(d => d.wind);
    const pressures = last24h.map(d => d.pressure);
    
    const stats = {
      tempMax: Math.max(...temps),
      tempMin: Math.min(...temps),
      totalRain: rains.reduce((sum, r) => sum + r, 0),
      maxWind: Math.max(...winds),
      avgPressure: pressures.reduce((sum, p) => sum + p, 0) / pressures.length
    };
    
    updateWeatherStats(stats);
  } catch (error) {
    console.error('Error loading weather stats:', error);
  }
}

function updateWeatherStats(stats) {
  const container = document.getElementById('weatherStats');
  if (!container) return;
  
  container.innerHTML = `
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(252, 165, 165, 0.1));">
      <div class="weather-value" style="color: var(--color-red);">${stats.tempMax.toFixed(1)}°C</div>
      <div class="weather-label">Max teplota</div>
    </div>
    
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 197, 253, 0.1));">
      <div class="weather-value" style="color: var(--color-blue);">${stats.tempMin.toFixed(1)}°C</div>
      <div class="weather-label">Min teplota</div>
    </div>
    
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(103, 232, 249, 0.1));">
      <div class="weather-value" style="color: var(--color-blue);">${stats.totalRain.toFixed(1)} mm</div>
      <div class="weather-label">Celkové srážky</div>
    </div>
    
    <div class="weather-card" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(110, 231, 183, 0.1));">
      <div class="weather-value" style="color: var(--color-green);">${stats.maxWind.toFixed(1)} m/s</div>
      <div class="weather-label">Max vítr</div>
    </div>
  `;
}

async function loadMeteogram() {
  const container = document.getElementById('meteogram');
  if (!container) return;
  
  try {
    const res = await fetch('/api/weather/meteogram');
    const data = await res.json();
    currentWeatherData = data;

    const now = Date.now();
    const shortData = data.filter(d => d.time >= now && d.time <= now + 48 * 3600 * 1000);

    if (shortData.length === 0) {
      container.innerHTML = '<div style="text-align: center; padding: 2rem;" class="text-muted">Žádná data k zobrazení</div>';
      return;
    }

    const temperature = shortData.map(d => [d.time, d.temperature]);
    const rain = shortData.map(d => [d.time, d.rain]);
    const pressure = shortData.map(d => [d.time, d.pressure]);
    const windSpeed = shortData.map(d => [d.time, d.wind]);

    // Weather icons for significant changes
    const weatherIcons = [];
    let lastIcon = null;
    for (let i = 0; i < shortData.length; i += 6) { // Every 6 hours
      const d = shortData[i];
      if (d.symbol_code !== lastIcon) {
        weatherIcons.push({
          x: d.time,
          y: d.temperature + 2,
          dataLabels: {
            enabled: true,
            format: getWeatherIcon(d.symbol_code),
            style: { fontSize: '20px', textOutline: 'none' },
            y: -10
          }
        });
        lastIcon = d.symbol_code;
      }
    }

    // Calculate smart Y-axis max for rain to prevent tiny values from looking huge
    const maxRain = Math.max(...rain.map(r => r[1]));
    const rainYMax = Math.max(5, Math.ceil(maxRain * 1.2)); // Minimum 5mm scale, or 20% above max value

    // Check if we're in dark mode for rain column styling
    const isDarkMode = document.documentElement.classList.contains('dark');

    const chartOptions = {
      chart: {
        height: 400,
        backgroundColor: 'transparent',
        style: { fontFamily: 'inherit' },
        zoomType: 'x'
      },
      title: { text: null },
      legend: { 
        enabled: true,
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: { color: 'var(--chart-text)' }
      },
      exporting: { enabled: false },
      plotOptions: {
        series: { marker: { enabled: false } },
        column: {
          pointPadding: 0.1,
          groupPadding: 0,
          borderWidth: 0,
          borderColor: 'transparent',
          dataLabels: {
            enabled: true,
            formatter: function() {
              return this.y > 0 ? this.y.toFixed(1) + 'mm' : null;
            },
            style: {
              color: 'var(--chart-text)',
              fontSize: '10px',
              fontWeight: 'bold',
              textOutline: isDarkMode ? '1px contrast' : '1px #ffffff'
            },
            y: -5
          }
        }
      },
      xAxis: [
        {
          type: 'datetime',
          tickInterval: 6 * 3600 * 1000,
          minorTickInterval: 3600 * 1000,
          labels: { 
            format: '{value:%H:%M}',
            style: { color: 'var(--chart-text)' }
          },
          gridLineWidth: 1,
          gridLineColor: 'var(--chart-grid)',
          lineColor: 'var(--chart-grid)',
          tickColor: 'var(--chart-grid)'
        },
        {
          type: 'datetime',
          tickInterval: 24 * 3600 * 1000,
          labels: {
            format: '{value:%a %e.%m}',
            style: { fontWeight: 'bold', color: 'var(--chart-text)' }
          },
          opposite: true,
          linkedTo: 0,
          gridLineWidth: 1,
          gridLineColor: 'var(--chart-grid)'
        }
      ],
      yAxis: [
        { // Temperature - Left axis
          title: { 
            text: 'Teplota (°C) / Srážky (mm)',
            style: { color: 'var(--chart-text)' }
          },
          labels: {
            format: '{value}°',
            style: { color: 'var(--chart-text)' }
          },
          plotLines: [{
            value: 0,
            color: '#666',
            width: 1,
            zIndex: 2
          }],
          gridLineColor: 'var(--chart-grid)',
          // Set max to accommodate both temperature and rain scale
          max: Math.max(40, Math.max(...temperature.map(t => t[1])) + 5, rainYMax)
        },
        { // Pressure - Right axis
          title: {
            text: 'Tlak (hPa)',
            style: { color: '#4CAF50' }
          },
          labels: {
            style: { color: '#4CAF50' }
          },
          opposite: true,
          gridLineWidth: 0
        }
      ],
      tooltip: {
        shared: true,
        useHTML: true,
        backgroundColor: 'var(--chart-tooltip-bg)',
        borderColor: 'var(--chart-tooltip-border)',
        style: { color: 'var(--chart-text)' },
        formatter: function () {
          const x = this.x;
          const dateStr = Highcharts.dateFormat('%A, %e. %B %Y', x);
          const timeStr = Highcharts.dateFormat('%H:%M', x);
          
          let html = `<div style="font-size: 12px;"><b>${dateStr}</b><br>${timeStr}</div><hr style="margin: 4px 0;">`;
          
          this.points.forEach(point => {
            const color = point.color;
            const name = point.series.name;
            const value = point.y;
            const suffix = point.series.tooltipOptions.valueSuffix || '';
            
            html += `<div><span style="color: ${color};">●</span> ${name}: <b>${value.toFixed(1)}${suffix}</b></div>`;
          });
          
          return html;
        }
      },
      series: [
        {
          name: 'Teplota',
          type: 'spline',
          data: temperature,
          yAxis: 0,
          color: '#f59e0b',
          tooltip: { valueSuffix: '°C' },
          lineWidth: 2
        },
        {
          name: 'Srážky',
          type: 'column',
          data: rain,
          yAxis: 0, // Use same axis as temperature
          color: '#7cb5ec',
          tooltip: { valueSuffix: ' mm' },
          pointPadding: 0.1,
          groupPadding: 0
        },
        {
          name: 'Tlak vzduchu',
          type: 'spline',
          data: pressure,
          yAxis: 1,
          color: '#4CAF50',
          tooltip: { valueSuffix: ' hPa' },
          dashStyle: 'Dash',
          lineWidth: 1
        },
        {
          name: 'Rychlost větru',
          type: 'spline',
          data: windSpeed,
          yAxis: 0,
          color: '#8b5cf6',
          tooltip: { valueSuffix: ' m/s' },
          lineWidth: 1
        },
        {
          name: 'Ikony počasí',
          type: 'scatter',
          data: weatherIcons,
          yAxis: 0,
          marker: { enabled: false },
          enableMouseTracking: false,
          showInLegend: false
        }
      ]
    };

    meteogramChart = Highcharts.chart('meteogram', chartOptions);
    
  } catch (err) {
    console.error('Chyba při načítání meteogramu:', err);
    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--color-red);">Chyba načítání meteogramu</div>';
  }
}

async function loadLongForecast() {
  try {
    const response = await fetch('/api/weather/daily');
    const forecastData = await response.json();
    const cards = document.getElementById('forecastCards');
    
    if (!cards) return;
    
    cards.innerHTML = '';
    
    forecastData.forEach(day => {
      const card = document.createElement('div');
      card.className = 'weather-card animate-fade-in';
      card.style.cssText = `
        background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
        border: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.3s ease;
      `;
      
      const icon = getWeatherIcon(day.icon);
      const date = new Date(day.date).toLocaleDateString('cs-CZ', { 
        weekday: 'short', 
        day: 'numeric', 
        month: 'short' 
      });
      
      card.innerHTML = `
        <div class="weather-label" style="margin-bottom: 0.5rem; font-weight: 600;">${date}</div>
        <div class="weather-icon" style="font-size: 2.5rem; margin: 0.75rem 0;">${icon}</div>
        <div class="weather-value" style="font-size: 1.25rem; margin-bottom: 0.25rem;">${day.temp.toFixed(1)}°C</div>
        <div class="weather-label" style="margin-bottom: 0.5rem; font-size: 0.75rem;">${day.temp_min.toFixed(1)}°C min</div>
        <div style="font-size: 0.875rem; color: var(--color-blue); margin-bottom: 0.25rem;">💧 ${day.rain.toFixed(1)} mm</div>
        <div class="weather-label" style="font-size: 0.75rem;">
          💨 ${day.wind_avg.toFixed(1)} | ${day.wind_gust.toFixed(1)} m/s
        </div>
      `;
      
      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-2px)';
        card.style.boxShadow = '0 8px 25px var(--shadow)';
      });
      
      card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = '0 2px 8px var(--shadow-sm)';
      });
      
      cards.appendChild(card);
    });
  } catch (err) {
    console.error('Chyba při načítání dlouhodobé předpovědi:', err);
    const cardsEl = document.getElementById('forecastCards');
    if (cardsEl) {
      cardsEl.innerHTML = 
        '<div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--color-red);">Chyba načítání předpovědi</div>';
    }
  }
}

function updateChartTheme() {
  if (meteogramChart) {
    const isDarkMode = document.documentElement.classList.contains('dark');
    
    // Update rain series border for dark mode
    const rainSeries = meteogramChart.series.find(s => s.name === 'Srážky');
    if (rainSeries) {
      rainSeries.update({
        borderWidth: isDarkMode ? 1 : 0,
        borderColor: isDarkMode ? 'var(--chart-text)' : 'transparent'
      });
    }
    
    meteogramChart.redraw();
  }
}

// Initialize weather page
document.addEventListener('DOMContentLoaded', function () {
  // Only run on weather page
  if (!document.getElementById('meteogram')) return;
  
  // Load all weather data
  loadCurrentWeather();
  loadMeteogram();
  loadLongForecast();
  loadWeatherStats();
  
  // Theme change listener
  window.addEventListener('themeChange', updateChartTheme);
  
  // Auto-refresh every 30 minutes
  setInterval(() => {
    loadCurrentWeather();
    loadMeteogram();
    loadLongForecast();
    loadWeatherStats();
    PondUtils.updateLastUpdateTime();
  }, 30 * 60 * 1000);
});