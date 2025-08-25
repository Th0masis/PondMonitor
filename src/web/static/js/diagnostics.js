/* PondMonitor - Diagnostics Module */

let tempChart = null;
let batteryChart = null;
let signalChart = null;
let solarChart = null;
let currentHours = 24;

function batteryPercent(v) {
  const minVoltage = 3.0;  // 0% battery
  const maxVoltage = 4.2;  // 100% battery (adjust based on your battery type)
  
  // Calculate percentage with proper bounds
  const percentage = ((v - minVoltage) / (maxVoltage - minVoltage)) * 100;
  
  // Clamp between 0% and 100%
  return Math.round(Math.max(0, Math.min(100, percentage)));
}

function getSignalQuality(dbm) {
  if (dbm >= -70) return { quality: 'Výborný', color: 'var(--color-green)', icon: '📶' };
  if (dbm >= -85) return { quality: 'Dobrý', color: 'var(--color-blue)', icon: '📶' };
  if (dbm >= -100) return { quality: 'Slabý', color: 'var(--color-yellow)', icon: '📶' };
  return { quality: 'Velmi slabý', color: 'var(--color-red)', icon: '📵' };
}

// Updated diagnostic chart options with dynamic intervals
function createDiagnosticChartOptions(hours = 24) {
  return window.ChartUtils.createBaseChartOptions(hours, 'spline');
}

async function loadDiagnostics(hours = 24) {
  try {
    const data = await PondUtils.apiRequest(`/api/lora?hours=${hours}`);
    
    // Update data point counts
    const tempDataPointsEl = document.getElementById('tempDataPoints');
    const batteryDataPointsEl = document.getElementById('batteryDataPoints');
    const signalDataPointsEl = document.getElementById('signalDataPoints');
    const solarDataPointsEl = document.getElementById('solarDataPoints');
    
    if (tempDataPointsEl) tempDataPointsEl.textContent = `${data.temperature?.length || 0} bodů`;
    if (batteryDataPointsEl) batteryDataPointsEl.textContent = `${data.battery_voltage?.length || 0} bodů`;
    if (signalDataPointsEl) signalDataPointsEl.textContent = `${data.signal_strength?.length || 0} bodů`;
    if (solarDataPointsEl) solarDataPointsEl.textContent = `${data.solar_voltage?.length || 0} bodů`;

    // Create chart options with appropriate intervals for the time range
    const chartOptions = createDiagnosticChartOptions(hours);

    // Update charts
    updateTemperatureChart(data.temperature || [], chartOptions, hours);
    updateBatteryChart(data.battery_voltage || [], data, chartOptions, hours);
    updateSignalChart(data.signal_strength || [], chartOptions, hours);
    updateSolarChart(data.solar_voltage || [], chartOptions, hours);

    PondUtils.updateLastUpdateTime();
  } catch (error) {
    console.error('Diagnostics loading error:', error);
  }
}

function updateTemperatureChart(data, chartOptions, hours) {
  if (!tempChart) {
    const chartEl = document.getElementById('temperatureChart');
    if (!chartEl) return;
    
    tempChart = Highcharts.chart('temperatureChart', {
      ...chartOptions,
      yAxis: { 
        ...chartOptions.yAxis,
        labels: { 
          ...chartOptions.yAxis.labels,
          format: '{value}°C' 
        }
      },
      tooltip: { 
        ...chartOptions.tooltip,
        valueSuffix: ' °C'
      },
      series: [{
        name: 'Teplota',
        data: data,
        color: '#f59e0b'
      }]
    });
  } else {
    tempChart.update({
      xAxis: chartOptions.xAxis
    }, false);
    tempChart.series[0].setData(data, true);
  }
}

function updateBatteryChart(voltageData, rawData, chartOptions, hours) {
  const batterySeries = voltageData.map(([ts, v]) => ({
    x: ts,
    y: batteryPercent(v),
    voltage: v
  }));
  
  // Create charging zones
  const zones = [];
  if (rawData?.solar_voltage?.length) {
    let inCharge = false;
    let chargeStart = null;

    rawData.solar_voltage.forEach(([ts, solar]) => {
      const isCharging = solar > 1.0;
      if (isCharging && !inCharge) {
        inCharge = true;
        chargeStart = ts;
      } else if (!isCharging && inCharge) {
        inCharge = false;
        zones.push({ color: 'rgba(34, 197, 94, 0.1)', from: chargeStart, to: ts });
      }
    });
    if (inCharge && chargeStart) {
      zones.push({ color: 'rgba(34, 197, 94, 0.1)', from: chargeStart, to: Date.now() });
    }
  }

  if (!batteryChart) {
    const chartEl = document.getElementById('batteryChart');
    if (!chartEl) return;
    
    batteryChart = Highcharts.chart('batteryChart', {
      ...chartOptions,
      chart: { ...chartOptions.chart, type: 'column' },
      xAxis: {
        ...chartOptions.xAxis,
        plotBands: zones
      },
      yAxis: { 
        ...chartOptions.yAxis,
        max: 100,
        min: 0,
        labels: { 
          ...chartOptions.yAxis.labels,
          format: '{value}%' 
        }
      },
      tooltip: { 
        ...chartOptions.tooltip,
        formatter: function () {
          const voltage = this.point.voltage;
          const percentage = this.y;
          
          return `<b>${percentage}%</b><br/>` +
                 `${voltage ? voltage.toFixed(2) + ' V' : 'N/A'}<br/>` +
                 `${Highcharts.dateFormat('%e. %b %H:%M', this.x)}`;
        }
      },
      plotOptions: {
        column: {
          pointPadding: 0.1,
          borderWidth: 0,
          zones: [
            { value: 20, color: '#ef4444' },
            { value: 40, color: '#f59e0b' },
            { color: '#22c55e' }
          ]
        }
      },
      series: [{
        name: 'Baterie',
        data: batterySeries
      }]
    });
  } else {
    batteryChart.update({
      xAxis: {
        ...chartOptions.xAxis,
        plotBands: zones
      }
    }, false);
    batteryChart.series[0].setData(batterySeries, true);
  }
}

function updateSignalChart(data, chartOptions, hours) {
  if (!signalChart) {
    const chartEl = document.getElementById('signalChart');
    if (!chartEl) return;
    
    signalChart = Highcharts.chart('signalChart', {
      ...chartOptions,
      yAxis: { 
        ...chartOptions.yAxis,
        labels: { 
          ...chartOptions.yAxis.labels,
          format: '{value} dBm' 
        },
        plotBands: [
          { from: -70, to: 0, color: 'rgba(16, 185, 129, 0.1)' },
          { from: -85, to: -70, color: 'rgba(59, 130, 246, 0.1)' },
          { from: -100, to: -85, color: 'rgba(245, 158, 11, 0.1)' },
          { from: -150, to: -100, color: 'rgba(239, 68, 68, 0.1)' }
        ]
      },
      tooltip: { 
        ...chartOptions.tooltip,
        valueSuffix: ' dBm'
      },
      series: [{
        name: 'Síla signálu',
        data: data,
        color: '#8b5cf6'
      }]
    });
  } else {
    signalChart.update({
      xAxis: chartOptions.xAxis
    }, false);
    signalChart.series[0].setData(data, true);
  }
}

function updateSolarChart(data, chartOptions, hours) {
  if (!solarChart) {
    const chartEl = document.getElementById('solarChart');
    if (!chartEl) return;
    
    solarChart = Highcharts.chart('solarChart', {
      ...chartOptions,
      chart: { ...chartOptions.chart, type: 'area' },
      yAxis: { 
        ...chartOptions.yAxis,
        min: 0,
        labels: { 
          ...chartOptions.yAxis.labels,
          format: '{value} V' 
        }
      },
      tooltip: { 
        ...chartOptions.tooltip,
        valueSuffix: ' V'
      },
      plotOptions: {
        area: {
          fillColor: {
            linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
            stops: [
              [0, 'rgba(255, 193, 7, 0.4)'],
              [1, 'rgba(255, 193, 7, 0)']
            ]
          },
          marker: { enabled: false },
          lineWidth: 2,
          color: '#ffc107'
        }
      },
      series: [{
        name: 'Solární napětí',
        data: data
      }]
    });
  } else {
    solarChart.update({
      xAxis: chartOptions.xAxis
    }, false);
    solarChart.series[0].setData(data, true);
  }
}

async function loadStatus() {
  try {
    const data = await PondUtils.apiRequest('/api/status');
    updateStatusCards(data);
    updateSystemHealth(data);
    updateHardwareInfo(data);
    updateNetworkInfo(data);
  } catch (error) {
    console.error('Status loading error:', error);
  }
}

function updateStatusCards(data) {
  const container = document.getElementById('statusCards');
  if (!container) return;
  
  container.innerHTML = '';

  const batteryPct = batteryPercent(data.battery_v);
  const signal = getSignalQuality(data.signal_dbm);
  
  // Energy Status Card
  const energyCard = createStatusCard({
    title: 'Napájení',
    icon: '🔋',
    value: `${batteryPct}%`,
    details: [
      `Napětí baterie: ${data.battery_v.toFixed(2)} V`,
      `Solární vstup: ${data.solar_v.toFixed(2)} V`,
      `Zdroj: ${data.on_solar ? 'Solární ☀️' : 'Baterie 🔋'}`
    ],
    status: batteryPct > 40 ? 'good' : batteryPct > 20 ? 'warning' : 'error',
    warning: data.battery_v < 3.5
  });

  // Connection Status Card
  const connectionCard = createStatusCard({
    title: 'Připojení',
    icon: data.connected ? '🟢' : '🔴',
    value: data.connected ? 'Online' : 'Offline',
    details: [
      `Síla signálu: ${data.signal_dbm} dBm`,
      `Kvalita: ${signal.quality} ${signal.icon}`,
      `Poslední heartbeat: ${new Date(data.last_heartbeat).toLocaleTimeString('cs-CZ')}`
    ],
    status: data.connected ? 'good' : 'error'
  });

  // Temperature Card
  const tempCard = createStatusCard({
    title: 'Teplota',
    icon: '🌡️',
    value: `${data.temperature_c?.toFixed(1) || 'N/A'}°C`,
    details: [
      `Interní čidlo`,
      `Poslední měření: ${data.last_reading ? new Date(data.last_reading).toLocaleTimeString('cs-CZ') : 'N/A'}`
    ],
    status: 'good'
  });

  // Uptime Card
  const uptimeCard = createStatusCard({
    title: 'Provoz',
    icon: '⏱️',
    value: formatUptime(data.uptime_seconds || 0),
    details: [
      `Od: ${data.boot_time ? new Date(data.boot_time).toLocaleString('cs-CZ') : 'N/A'}`,
      `Restart count: ${data.restart_count || 0}`
    ],
    status: 'good'
  });

  container.appendChild(energyCard);
  container.appendChild(connectionCard);
  container.appendChild(tempCard);
  container.appendChild(uptimeCard);
}

function createStatusCard({ title, icon, value, details, status, warning }) {
  const card = document.createElement('div');
  card.className = `status-card status-${status} card animate-fade-in`;

  card.innerHTML = `
    <div class="card-body">
      <div style="display: flex; align-items: flex-start; justify-content: space-between;">
        <div style="flex: 1;">
          <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">${icon}</span>
            <h4 style="font-size: 0.875rem; font-weight: 500; margin: 0;" class="text-secondary">${title}</h4>
            ${warning ? '<span style="margin-left: 0.5rem; color: var(--color-yellow);">⚠️</span>' : ''}
          </div>
          <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;" class="text-primary">${value}</div>
          <div style="display: flex; flex-direction: column; gap: 0.25rem;">
            ${details.map(detail => `<div style="font-size: 0.875rem;" class="text-secondary">${detail}</div>`).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  return card;
}

function updateSystemHealth(data) {
  const healthEl = document.getElementById('systemHealth');
  const metricsEl = document.getElementById('healthMetrics');
  
  if (!healthEl || !metricsEl) return;
  
  // Calculate overall health score
  let score = 100;
  const issues = [];
  
  if (!data.connected) { score -= 40; issues.push('Bez připojení'); }
  if (data.battery_v < 3.3) { score -= 30; issues.push('Nízká baterie'); }
  if (data.signal_dbm < -100) { score -= 20; issues.push('Slabý signál'); }
  if (data.temperature_c && (data.temperature_c < -10 || data.temperature_c > 50)) { 
    score -= 10; issues.push('Extrémní teplota'); 
  }
  
  let healthStatus, healthColor, healthText;
  if (score >= 80) {
    healthStatus = 'good';
    healthColor = 'background: var(--color-green-light); color: var(--color-green-dark);';
    healthText = 'Systém v pořádku';
  } else if (score >= 60) {
    healthStatus = 'warning';
    healthColor = 'background:  var(--color-yellow-light); color: var(--color-yellow-dark);';
    healthText = 'Drobné problémy';
  } else {
    healthStatus = 'error';
    healthColor = 'background: var(--color-red-light); color: var(--color-red-dark);';
    healthText = 'Problémy vyžadují pozornost';
  }
  
  healthEl.style.cssText = `display: flex; align-items: center; padding: 0.5rem 1rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 500; ${healthColor}`;
  healthEl.innerHTML = `
    <div style="width: 0.5rem; height: 0.5rem; border-radius: 50%; margin-right: 0.5rem; background-color: ${healthStatus === 'good' ? 'var(--color-green)' : 
      healthStatus === 'warning' ? 'var(--color-yellow)' : 'var(--color-red)'};"></div>
    <span>${healthText}</span>
  `;
  
  // Health metrics
  metricsEl.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700;" class="text-primary">${score}</div>
      <div style="font-size: 0.875rem;" class="text-secondary">Health Score</div>
    </div>
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700;" class="text-primary">${issues.length}</div>
      <div style="font-size: 0.875rem;" class="text-secondary">Aktivní problémy</div>
    </div>
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700;" class="text-primary">${Math.round((Date.now() - new Date(data.last_heartbeat)) / 60000)}min</div>
      <div style="font-size: 0.875rem;" class="text-secondary">Poslední kontakt</div>
    </div>
  `;
}

function updateHardwareInfo(data) {
  const container = document.getElementById('hardwareInfo');
  if (!container) return;
  
  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Device ID:</span>
      <span style="font-family: monospace;" class="text-primary">${data.device_id || 'N/A'}</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Firmware:</span>
      <span style="font-family: monospace;" class="text-primary">${data.firmware_version || 'N/A'}</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Hardware:</span>
      <span style="font-family: monospace;" class="text-primary">${data.hardware_version || 'N/A'}</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Volná paměť:</span>
      <span style="font-family: monospace;" class="text-primary">${data.free_memory ? (data.free_memory / 1024).toFixed(1) + ' KB' : 'N/A'}</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0;">
      <span class="text-secondary">CPU Load:</span>
      <span style="font-family: monospace;" class="text-primary">${data.cpu_usage ? data.cpu_usage.toFixed(1) + '%' : 'N/A'}</span>
    </div>
  `;
}

function updateNetworkInfo(data) {
  const container = document.getElementById('networkInfo');
  if (!container) return;
  
  const signal = getSignalQuality(data.signal_dbm);
  
  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Stav připojení:</span>
      <span style="font-weight: 600; color: ${data.connected ? 'var(--color-green)' : 'var(--color-red)'};">
        ${data.connected ? '🟢 Online' : '🔴 Offline'}
      </span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Síla signálu:</span>
      <span style="font-family: monospace; color: ${signal.color};" class="text-primary">${data.signal_dbm} dBm (${signal.quality})</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">Operátor:</span>
      <span style="font-family: monospace;" class="text-primary">${data.network_operator || 'N/A'}</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
      <span class="text-secondary">IP adresa:</span>
      <span style="font-family: monospace;" class="text-primary">${data.ip_address || 'N/A'}</span>
    </div>
    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0;">
      <span class="text-secondary">Datový přenos:</span>
      <span style="font-family: monospace;" class="text-primary">${data.data_usage ? (data.data_usage / 1024 / 1024).toFixed(2) + ' MB' : 'N/A'}</span>
    </div>
  `;
}

function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

async function refreshLogs() {
  try {
    const logs = await PondUtils.apiRequest('/api/logs?limit=50');
    const container = document.getElementById('systemLogs');
    
    if (!container) return;
    
    if (logs.length === 0) {
      container.innerHTML = '<div class="text-muted" style="font-size: 0.875rem;">Žádné události k zobrazení</div>';
      return;
    }
    
    container.innerHTML = logs.map(log => {
      const date = new Date(log.timestamp).toLocaleString('cs-CZ');
      const levelColors = {
        'ERROR': 'var(--color-red)',
        'WARNING': 'var(--color-yellow)',
        'INFO': 'var(--color-blue)',
        'DEBUG': 'var(--text-muted)'
      };
      const levelColor = levelColors[log.level] || 'var(--text-muted)';
      
      return `
        <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border-light); font-size: 0.875rem;">
          <div class="text-muted" style="width: 8rem; flex-shrink: 0; font-size: 0.75rem;">${date}</div>
          <div style="width: 4rem; flex-shrink: 0; font-weight: 600; color: ${levelColor}; font-size: 0.75rem;">${log.level}</div>
          <div class="text-primary" style="flex: 1;">${log.message}</div>
        </div>
      `;
    }).join('');
  } catch (error) {
    const container = document.getElementById('systemLogs');
    if (container) {
      container.innerHTML = 
        '<div style="color: var(--color-red); font-size: 0.875rem;">Chyba při načítání událostí</div>';
    }
  }
}

async function testConnection() {
  try {
    PondUtils.showLoading();
    const result = await PondUtils.apiRequest('/api/test-connection', { method: 'POST' });
    
    if (result.success) {
      PondUtils.showSuccess('✅ Test připojení úspěšný');
    } else {
      PondUtils.showError('❌ Test připojení selhal: ' + result.error);
    }
  } catch (error) {
    PondUtils.showError('❌ Test připojení selhal: ' + error.message);
  } finally {
    PondUtils.hideLoading();
  }
}

async function exportDiagnostics() {
  try {
    PondUtils.showLoading();
    const data = await PondUtils.apiRequest('/api/diagnostics/export');
    
    const content = JSON.stringify(data, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnostics_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    PondUtils.showSuccess('Export úspěšně dokončen');
  } catch (error) {
    PondUtils.showError('Chyba při exportu: ' + error.message);
  } finally {
    PondUtils.hideLoading();
  }
}

async function resetDevice() {
  if (!confirm('Opravdu chcete restartovat zařízení? Tato akce může trvat několik minut.')) {
    return;
  }
  
  try {
    PondUtils.showLoading();
    await PondUtils.apiRequest('/api/device/reset', { method: 'POST' });
    PondUtils.showInfo('🔄 Restart zařízení byl zahájen');
  } catch (error) {
    PondUtils.showError('Chyba při restartu: ' + error.message);
  } finally {
    PondUtils.hideLoading();
  }
}

function updateChartTheme() {
  // Redraw charts if they exist
  [tempChart, batteryChart, signalChart, solarChart].forEach(chart => {
    if (chart) chart.redraw();
  });
}

// Initialize diagnostics page
document.addEventListener('DOMContentLoaded', function () {
  // Only run on diagnostics page
  if (!document.getElementById('temperatureChart')) return;
  
  loadDiagnostics();
  loadStatus();
  refreshLogs();
  
  // Theme change listener
  window.addEventListener('themeChange', updateChartTheme);
  
  // Range button event listeners
  document.querySelectorAll('.diag-range-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      const hours = parseInt(btn.dataset.hours);
      currentHours = hours;
      loadDiagnostics(hours);

      // Update button styles
      document.querySelectorAll('.diag-range-btn').forEach(b => {
        b.className = 'btn btn-secondary diag-range-btn';
      });
      btn.className = 'btn btn-primary diag-range-btn';
    });
  });
  
  // Set initial active button
  const defaultBtn = document.querySelector('[data-hours="24"]');
  if (defaultBtn) {
    defaultBtn.className = 'btn btn-primary diag-range-btn';
  }
  
  // Auto-refresh every 30 seconds
  setInterval(() => {
    loadStatus();
    loadDiagnostics(currentHours);
  }, 30000);
  
  // Auto-refresh logs every 60 seconds
  setInterval(refreshLogs, 60000);
});

// Make functions globally available
window.refreshLogs = refreshLogs;
window.testConnection = testConnection;
window.exportDiagnostics = exportDiagnostics;
window.resetDevice = resetDevice;