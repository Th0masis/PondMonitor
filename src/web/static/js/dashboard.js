/* PondMonitor - Dashboard Module */

// Dashboard-specific variables and functions
let chartLevel = null;
let chartOutflow = null;
let currentData = null;
let currentHours = 24;

// Create dashboard-specific chart options
function createDashboardChartOptions(hours = 24) {
  const baseOptions = window.ChartUtils.createBaseChartOptions(hours, 'area');
  return baseOptions;
}

async function loadDashboard(start, end) {
  try {
    const data = await PondUtils.apiRequest(`/api/dashboard?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
    currentData = data;

    // Calculate time range in hours for proper axis scaling
    const startTime = new Date(start);
    const endTime = new Date(end);
    const hours = Math.round((endTime - startTime) / (1000 * 60 * 60));
    currentHours = hours;

    // Update statistics
    updateStatistics(data);

    // Update charts with dynamic axis configuration
    updateLevelChart(data.level, hours);
    updateOutflowChart(data.outflow, hours);

    // Update data point counts
    const levelDataPointsEl = document.getElementById('levelDataPoints');
    const outflowDataPointsEl = document.getElementById('outflowDataPoints');
    
    if (levelDataPointsEl) levelDataPointsEl.textContent = `${data.level.length} bodů`;
    if (outflowDataPointsEl) outflowDataPointsEl.textContent = `${data.outflow.length} bodů`;

    PondUtils.updateLastUpdateTime();
  } catch (error) {
    console.error('Dashboard loading error:', error);
  }
}

function updateStatistics(data) {
  if (data.level.length > 0) {
    const latestLevel = data.level[data.level.length - 1][1];
    const maxLevel = Math.max(...data.level.map(p => p[1]));
    
    const currentLevelEl = document.getElementById('currentLevel');
    const maxLevel24hEl = document.getElementById('maxLevel24h');
    
    if (currentLevelEl) currentLevelEl.textContent = `${latestLevel.toFixed(1)} cm`;
    if (maxLevel24hEl) maxLevel24hEl.textContent = `${maxLevel.toFixed(1)} cm`;
    
    // Calculate trend
    if (data.level.length >= 2) {
      const firstLevel = data.level[0][1];
      const trend = latestLevel - firstLevel;
      const trendEl = document.getElementById('levelTrend');
      
      if (trendEl) {
        if (trend > 0.5) {
          trendEl.textContent = '↗ Stoupá';
          trendEl.style.color = 'var(--color-green)';
        } else if (trend < -0.5) {
          trendEl.textContent = '↘ Klesá';
          trendEl.style.color = 'var(--color-red)';
        } else {
          trendEl.textContent = '→ Stabilní';
          trendEl.style.color = 'var(--text-secondary)';
        }
      }
    }
  }

  if (data.outflow.length > 0) {
    const latestOutflow = data.outflow[data.outflow.length - 1][1];
    const currentOutflowEl = document.getElementById('currentOutflow');
    if (currentOutflowEl) {
      currentOutflowEl.textContent = `${latestOutflow.toFixed(2)} l/s`;
    }
  }
}

function updateLevelChart(data, hours) {
  const chartOptions = createDashboardChartOptions(hours);
  
  if (!chartLevel) {
    const chartEl = document.getElementById('chartLevel');
    if (!chartEl) return;
    
    chartLevel = Highcharts.chart('chartLevel', {
      ...chartOptions,
      yAxis: { 
        ...chartOptions.yAxis,
        title: { text: 'cm', style: { color: 'var(--chart-text)' } }
      },
      series: [{
        name: 'Výška hladiny',
        data: data,
        color: '#00c896'
      }]
    });
  } else {
    // Update existing chart with new axis configuration
    chartLevel.update({
      xAxis: chartOptions.xAxis
    }, false);
    chartLevel.series[0].setData(data, true);
  }
}

function updateOutflowChart(data, hours) {
  const chartOptions = createDashboardChartOptions(hours);
  
  if (!chartOutflow) {
    const chartEl = document.getElementById('chartOutflow');
    if (!chartEl) return;
    
    chartOutflow = Highcharts.chart('chartOutflow', {
      ...chartOptions,
      yAxis: { 
        ...chartOptions.yAxis,
        title: { text: 'l/s', style: { color: 'var(--chart-text)' } }
      },
      series: [{
        name: 'Odtok',
        data: data,
        color: '#00c896'
      }]
    });
  } else {
    // Update existing chart with new axis configuration
    chartOutflow.update({
      xAxis: chartOptions.xAxis
    }, false);
    chartOutflow.series[0].setData(data, true);
  }
}

function loadQuick(hours) {
  const now = new Date();
  const start = new Date(now.getTime() - hours * 3600 * 1000);
  
  const startDateEl = document.getElementById('startDate');
  const endDateEl = document.getElementById('endDate');
  
  if (startDateEl) startDateEl.value = start.toISOString().slice(0, 16);
  if (endDateEl) endDateEl.value = now.toISOString().slice(0, 16);
  
  loadDashboard(start.toISOString(), now.toISOString());
}

function loadManual() {
  const startDateEl = document.getElementById('startDate');
  const endDateEl = document.getElementById('endDate');
  
  if (!startDateEl || !endDateEl) return;
  
  const start = startDateEl.value;
  const end = endDateEl.value;

  // Reset all buttons to secondary
  document.querySelectorAll('.range-btn').forEach(b => {
    b.className = 'btn btn-secondary range-btn';
  });

  if (start && end) {
    loadDashboard(new Date(start).toISOString(), new Date(end).toISOString());
  } else {
    PondUtils.showError("Zadejte časový rozsah");
  }
}

function exportData(format) {
  if (!currentData) {
    PondUtils.showError("Nejprve načtěte data");
    return;
  }

  let content, filename, mimeType;

  if (format === 'csv') {
    content = 'Timestamp,Level_cm,Outflow_lps\n';
    // Merge data by timestamp
    const dataMap = new Map();
    currentData.level.forEach(([ts, val]) => {
      if (!dataMap.has(ts)) dataMap.set(ts, {});
      dataMap.get(ts).level = val;
    });
    currentData.outflow.forEach(([ts, val]) => {
      if (!dataMap.has(ts)) dataMap.set(ts, {});
      dataMap.get(ts).outflow = val;
    });
    
    for (const [ts, values] of dataMap) {
      const date = new Date(ts).toISOString();
      content += `${date},${values.level || ''},${values.outflow || ''}\n`;
    }
    
    filename = `pond_data_${new Date().toISOString().slice(0, 10)}.csv`;
    mimeType = 'text/csv';
  } else if (format === 'json') {
    content = JSON.stringify(currentData, null, 2);
    filename = `pond_data_${new Date().toISOString().slice(0, 10)}.json`;
    mimeType = 'application/json';
  }

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function printCharts() {
  window.print();
}

// Update charts when theme changes
function updateChartTheme() {
  if (chartLevel) chartLevel.redraw();
  if (chartOutflow) chartOutflow.redraw();
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  // Only run on dashboard page
  if (!document.getElementById('chartLevel')) return;
  
  loadQuick(24);
  
  // Theme change listener
  window.addEventListener('themeChange', updateChartTheme);
  
  // Range button event listeners
  document.querySelectorAll('.range-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      const hours = parseInt(btn.dataset.hours);
      loadQuick(hours);

      // Update button styles
      document.querySelectorAll('.range-btn').forEach(b => {
        b.className = 'btn btn-secondary range-btn';
      });
      btn.className = 'btn btn-primary range-btn';
    });
  });
  
  // Set initial active button
  const defaultBtn = document.querySelector('[data-hours="24"]');
  if (defaultBtn) {
    defaultBtn.className = 'btn btn-primary range-btn';
  }
  
  // Auto-refresh every 5 minutes
  setInterval(() => {
    const endInput = document.getElementById('endDate');
    if (endInput && endInput.value) {
      const endTime = new Date(endInput.value);
      const now = new Date();
      // Only auto-refresh if we're looking at recent data
      if (now - endTime < 60 * 60 * 1000) { // Within 1 hour of now
        endInput.value = now.toISOString().slice(0, 16);
        loadManual();
      }
    }
  }, 5 * 60 * 1000);
});

// Make functions globally available
window.loadManual = loadManual;
window.exportData = exportData;
window.printCharts = printCharts;