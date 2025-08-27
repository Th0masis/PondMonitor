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
      chart: {
        ...chartOptions.chart,
        id: 'chartLevel'
      },
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
      chart: {
        ...chartOptions.chart,
        id: 'chartOutflow'
      },
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
  console.log('=== Print Charts Debug ===');
  console.log('Highcharts version:', Highcharts.version);
  console.log('Exporting module loaded:', !!Highcharts.Chart.prototype.getSVG);
  console.log('chartLevel variable:', chartLevel);
  console.log('chartOutflow variable:', chartOutflow);
  console.log('currentData:', currentData);
  
  // Check if chart elements exist and have been initialized
  const levelChartEl = document.getElementById('chartLevel');
  const outflowChartEl = document.getElementById('chartOutflow');
  
  console.log('Level chart element:', levelChartEl);
  console.log('Outflow chart element:', outflowChartEl);
  
  if (!levelChartEl && !outflowChartEl) {
    PondUtils.showError('Žádné grafy k tisku. Stránka se ještě nenačetla.');
    return;
  }
  
  // Try to get Highcharts instances directly if variables are not set
  let levelChart = chartLevel;
  let outflowChart = chartOutflow;
  
  // Also try to get from Highcharts global registry by element ID
  if (!levelChart && window.Highcharts) {
    levelChart = Highcharts.get('chartLevel') || 
                 Highcharts.charts.find(chart => chart && chart.container === levelChartEl);
  }
  
  if (!outflowChart && window.Highcharts) {
    outflowChart = Highcharts.get('chartOutflow') || 
                   Highcharts.charts.find(chart => chart && chart.container === outflowChartEl);
  }
  
  console.log('Final level chart:', levelChart);
  console.log('Final outflow chart:', outflowChart);
  
  if (!levelChart && !outflowChart) {
    PondUtils.showError('Grafy se ještě nenačetly. Počkejte chvilku a zkuste to znovu.');
    return;
  }
  
  // Try enhanced print first, fallback to simple print
  try {
    printChartsEnhanced(levelChart, outflowChart);
  } catch (error) {
    console.warn('Enhanced print failed, falling back to simple print:', error);
    printChartsSimple();
  }
}

function printChartsEnhanced(levelChart, outflowChart) {
  
  try {
    // Get current chart SVGs with error handling
    let levelChartSVG = '<div style="text-align: center; padding: 2rem; color: #6b7280;">Graf hladiny není k dispozici</div>';
    let outflowChartSVG = '<div style="text-align: center; padding: 2rem; color: #6b7280;">Graf průtoku není k dispozici</div>';
    
    console.log('Print: Level chart available:', !!levelChart);
    console.log('Print: Outflow chart available:', !!outflowChart);
    
    if (levelChart) {
      try {
        // Try different methods to get SVG depending on Highcharts version
        console.log('Level chart getSVG method:', typeof levelChart.getSVG);
        if (typeof levelChart.getSVG === 'function') {
          levelChartSVG = levelChart.getSVG({
            chart: { 
              backgroundColor: '#ffffff',
              width: 800,  // Optimized for A4 landscape print
              height: 350,  // Good aspect ratio for print
              spacing: [20, 20, 20, 20]  // Reduced padding for print
            },
            title: { 
              text: 'Hladina rybníka', 
              style: { fontSize: '18px', color: '#333' } 
            },
            subtitle: { 
              text: `Období: ${getDateRangeText()}`, 
              style: { fontSize: '14px', color: '#666' } 
            },
            legend: {
              enabled: true,
              itemStyle: { fontSize: '12px', color: '#333' }
            }
          });
        } else {
          // Fallback: Create a data table representation
          const data = levelChart.series && levelChart.series[0] && levelChart.series[0].data;
          let tableContent = '<p>Žádná data k zobrazení</p>';
          
          if (data && data.length > 0) {
            const recentData = data.slice(-10); // Last 10 data points
            tableContent = `
              <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
                <thead>
                  <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Čas</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Hladina (cm)</th>
                  </tr>
                </thead>
                <tbody>
                  ${recentData.map(point => `
                    <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;">${new Date(point.x || point[0]).toLocaleString('cs-CZ', { hour12: false })}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${(point.y || point[1]).toFixed(2)}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `;
          }
          
          levelChartSVG = `
            <div style="text-align: center; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; background: white;">
              <h3 style="margin-bottom: 1rem; font-size: 18px;">Hladina rybníka</h3>
              <p style="margin-bottom: 1rem; font-size: 14px; color: #666;">${getDateRangeText()}</p>
              <p style="margin-bottom: 1rem; color: #888; font-size: 12px;">Posledních 10 měření:</p>
              ${tableContent}
            </div>
          `;
        }
        console.log('Level chart content generated successfully');
      } catch (e) {
        console.warn('Error getting level chart content:', e);
        levelChartSVG = `
          <div style="text-align: center; padding: 2rem; color: #666; border: 1px solid #ddd; border-radius: 8px;">
            <h3>Hladina rybníka</h3>
            <p>Graf je k dispozici pouze v interaktivní verzi</p>
          </div>
        `;
      }
    }
    
    if (outflowChart) {
      try {
        // Try different methods to get SVG depending on Highcharts version
        console.log('Outflow chart getSVG method:', typeof outflowChart.getSVG);
        if (typeof outflowChart.getSVG === 'function') {
          outflowChartSVG = outflowChart.getSVG({
            chart: { 
              backgroundColor: '#ffffff',
              width: 800,  // Optimized for A4 landscape print
              height: 350,  // Good aspect ratio for print
              spacing: [20, 20, 20, 20]  // Reduced padding for print
            },
            title: { 
              text: 'Průtok výpustě', 
              style: { fontSize: '18px', color: '#333' } 
            },
            subtitle: { 
              text: `Období: ${getDateRangeText()}`, 
              style: { fontSize: '14px', color: '#666' } 
            },
            legend: {
              enabled: true,
              itemStyle: { fontSize: '12px', color: '#333' }
            }
          });
        } else {
          // Fallback: Create a data table representation
          const data = outflowChart.series && outflowChart.series[0] && outflowChart.series[0].data;
          let tableContent = '<p>Žádná data k zobrazení</p>';
          
          if (data && data.length > 0) {
            const recentData = data.slice(-10); // Last 10 data points
            tableContent = `
              <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
                <thead>
                  <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Čas</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Průtok (l/s)</th>
                  </tr>
                </thead>
                <tbody>
                  ${recentData.map(point => `
                    <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;">${new Date(point.x || point[0]).toLocaleString('cs-CZ', { hour12: false })}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${(point.y || point[1]).toFixed(2)}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `;
          }
          
          outflowChartSVG = `
            <div style="text-align: center; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; background: white;">
              <h3 style="margin-bottom: 1rem; font-size: 18px;">Průtok výpustě</h3>
              <p style="margin-bottom: 1rem; font-size: 14px; color: #666;">${getDateRangeText()}</p>
              <p style="margin-bottom: 1rem; color: #888; font-size: 12px;">Posledních 10 měření:</p>
              ${tableContent}
            </div>
          `;
        }
        console.log('Outflow chart content generated successfully');
      } catch (e) {
        console.warn('Error getting outflow chart content:', e);
        outflowChartSVG = `
          <div style="text-align: center; padding: 2rem; color: #666; border: 1px solid #ddd; border-radius: 8px;">
            <h3>Průtok výpustě</h3>
            <p>Graf je k dispozici pouze v interaktivní verzi</p>
          </div>
        `;
      }
    }
    
    // Get current statistics
    const stats = getFormattedStats();
  
  const printHTML = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PondMonitor - Dashboard Export</title>
    <style>
        @page {
            size: A4 landscape;
            margin: 1.5cm 1cm;  /* Top/bottom 1.5cm, left/right 1cm for better chart fit */
        }
        
        @media print {
            body { -webkit-print-color-adjust: exact; }
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: white;
            color: #1f2937;
        }
        
        .print-header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 20px;
        }
        
        .print-header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
            color: #1f2937;
        }
        
        .print-header p {
            margin: 5px 0;
            color: #6b7280;
            font-size: 14px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .stat-card {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
        }
        
        .charts-container {
            display: block;
            width: 100%;
        }
        
        .chart-section {
            page-break-inside: avoid;
            margin-bottom: 30px;
            width: 100%;
        }
        
        .chart-section:last-child {
            margin-bottom: 0;
        }
        
        .chart-wrapper {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
            text-align: center;
            width: 100%;
        }
        
        .chart-wrapper svg {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }
        
        .print-footer {
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #9ca3af;
            border-top: 1px solid #e5e7eb;
            padding-top: 15px;
        }
    </style>
</head>
<body>
    <div class="print-header">
        <h1>🐟 PondMonitor Dashboard</h1>
        <p><strong>Datum exportu:</strong> ${new Date().toLocaleString('cs-CZ', { hour12: false })}</p>
        <p><strong>Období dat:</strong> ${getDateRangeText()}</p>
        <p><strong>Celkem datových bodů:</strong> ${getTotalDataPoints()}</p>
    </div>
    
    <div class="stats-grid">
        ${stats.map(stat => `
            <div class="stat-card">
                <div class="stat-value">${stat.value}</div>
                <div class="stat-label">${stat.label}</div>
            </div>
        `).join('')}
    </div>
    
    <div class="charts-container">
        <div class="chart-section">
            <div class="chart-wrapper">
                ${levelChartSVG}
            </div>
        </div>
        
        <div class="chart-section">
            <div class="chart-wrapper">
                ${outflowChartSVG}
            </div>
        </div>
    </div>
    
    <div class="print-footer">
        <p>Vygenerováno systémem PondMonitor • ${window.location.hostname} • ${new Date().toLocaleDateString('cs-CZ')}</p>
    </div>
</body>
</html>`;
    
    // Create and open print window with better error handling
    const printWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
    
    if (!printWindow) {
      PondUtils.showError('Popup blokován. Prosím povolte popup okna pro tisk.');
      return;
    }
    
    // Write content to window
    try {
      printWindow.document.open();
      printWindow.document.write(printHTML);
      printWindow.document.close();
      
      // Wait for content to load, then print
      if (printWindow.document.readyState === 'complete') {
        setTimeout(() => {
          printWindow.focus();
          printWindow.print();
          setTimeout(() => printWindow.close(), 1000);
        }, 500);
      } else {
        printWindow.addEventListener('load', () => {
          setTimeout(() => {
            printWindow.focus();
            printWindow.print();
            setTimeout(() => printWindow.close(), 1000);
          }, 500);
        });
      }
      
    } catch (error) {
      console.error('Print window error:', error);
      PondUtils.showError('Chyba při otevírání tisku. Zkuste to prosím znovu.');
      if (printWindow && !printWindow.closed) {
        printWindow.close();
      }
    }
    
  } catch (error) {
    console.error('Print function error:', error);
    PondUtils.showError('Chyba při přípravě tisku. Zkuste to prosím znovu.');
  }
}

// Helper functions for print optimization
function getDateRangeText() {
  const rangeBtn = document.querySelector('.range-btn.btn-primary');
  if (rangeBtn) {
    const hours = parseInt(rangeBtn.dataset.hours);
    if (hours === 24) return 'Posledních 24 hodin';
    if (hours === 72) return 'Poslední 3 dny';  
    if (hours === 168) return 'Poslední týden';
    if (hours === 720) return 'Poslední měsíc';
  }
  return 'Vybrané období';
}

function getTotalDataPoints() {
  if (!currentData) return '0';
  const levelCount = currentData.level ? currentData.level.length : 0;
  const outflowCount = currentData.outflow ? currentData.outflow.length : 0;
  return `${levelCount + outflowCount}`;
}

function getFormattedStats() {
  const stats = [];
  
  if (currentData && currentData.level.length > 0) {
    const latestLevel = currentData.level[currentData.level.length - 1][1];
    const maxLevel = Math.max(...currentData.level.map(p => p[1]));
    const minLevel = Math.min(...currentData.level.map(p => p[1]));
    const avgLevel = currentData.level.reduce((sum, p) => sum + p[1], 0) / currentData.level.length;
    
    stats.push(
      { value: `${latestLevel.toFixed(2)} cm`, label: 'Aktuální hladina' },
      { value: `${maxLevel.toFixed(2)} cm`, label: 'Maximální hladina' },
      { value: `${minLevel.toFixed(2)} cm`, label: 'Minimální hladina' },
      { value: `${avgLevel.toFixed(2)} cm`, label: 'Průměrná hladina' }
    );
  }
  
  if (currentData && currentData.outflow.length > 0) {
    const latestOutflow = currentData.outflow[currentData.outflow.length - 1][1];
    const maxOutflow = Math.max(...currentData.outflow.map(p => p[1]));
    const avgOutflow = currentData.outflow.reduce((sum, p) => sum + p[1], 0) / currentData.outflow.length;
    
    stats.push(
      { value: `${latestOutflow.toFixed(2)} l/s`, label: 'Aktuální průtok' },
      { value: `${maxOutflow.toFixed(2)} l/s`, label: 'Maximální průtok' },
      { value: `${avgOutflow.toFixed(2)} l/s`, label: 'Průměrný průtok' }
    );
  }
  
  return stats.slice(0, 8); // Limit to fit the grid
}

function printChartsSimple() {
  // Simple fallback print method
  console.log('Using simple print fallback');
  
  // Create a simple print stylesheet
  const printStyles = `
    @media print {
      body * { visibility: hidden; }
      .charts-section, .charts-section * { visibility: visible; }
      .charts-section { 
        position: absolute; 
        left: 0; 
        top: 0; 
        width: 100%;
      }
      .sidebar, .navbar, .quick-actions, .card-header button { display: none !important; }
      .chart-container { 
        page-break-inside: avoid; 
        margin-bottom: 2rem;
      }
    }
  `;
  
  // Add print styles to head
  const styleSheet = document.createElement('style');
  styleSheet.media = 'print';
  styleSheet.innerHTML = printStyles;
  document.head.appendChild(styleSheet);
  
  // Add print header
  const printHeader = document.createElement('div');
  printHeader.id = 'print-header-temp';
  printHeader.innerHTML = `
    <div style="display: none;">
      <h1 style="text-align: center; margin-bottom: 1rem;">🐟 PondMonitor Dashboard</h1>
      <p style="text-align: center; margin-bottom: 2rem;">
        <strong>Datum exportu:</strong> ${new Date().toLocaleString('cs-CZ', { hour12: false })} | 
        <strong>Období:</strong> ${getDateRangeText()}
      </p>
    </div>
  `;
  printHeader.querySelector('div').style.display = 'block';
  document.body.insertBefore(printHeader, document.body.firstChild);
  
  // Print
  try {
    window.print();
  } finally {
    // Cleanup
    setTimeout(() => {
      document.head.removeChild(styleSheet);
      if (document.getElementById('print-header-temp')) {
        document.body.removeChild(printHeader);
      }
    }, 1000);
  }
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