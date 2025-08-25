/* PondMonitor - Charts Module */

// Global chart configuration and utilities
window.ChartUtils = {
  // Function to calculate appropriate tick intervals based on time range
  getTickInterval(hours) {
    if (hours <= 1) {
      return {
        tickInterval: 15 * 60 * 1000,     // 15 minutes
        minorTickInterval: 5 * 60 * 1000,  // 5 minutes
        format: '{value:%H:%M}'
      };
    } else if (hours <= 6) {
      return {
        tickInterval: 60 * 60 * 1000,      // 1 hour
        minorTickInterval: 15 * 60 * 1000, // 15 minutes
        format: '{value:%H:%M}'
      };
    } else if (hours <= 24) {
      return {
        tickInterval: 4 * 60 * 60 * 1000,  // 4 hours
        minorTickInterval: 60 * 60 * 1000, // 1 hour
        format: '{value:%H:%M}'
      };
    } else if (hours <= 72) {
      return {
        tickInterval: 12 * 60 * 60 * 1000, // 12 hours
        minorTickInterval: 3 * 60 * 60 * 1000, // 3 hours
        format: '{value:%e. %b %H:%M}'
      };
    } else {
      return {
        tickInterval: 24 * 60 * 60 * 1000, // 1 day
        minorTickInterval: 6 * 60 * 60 * 1000, // 6 hours
        format: '{value:%e. %b}'
      };
    }
  },

  // Create base chart options with dynamic intervals
  createBaseChartOptions(hours = 24, chartType = 'spline') {
    const tickConfig = this.getTickInterval(hours);
    
    return {
      chart: { 
        type: chartType,
        backgroundColor: 'transparent',
        style: {
          fontFamily: 'inherit'
        }
      },
      title: { text: null },
      legend: { enabled: false },
      exporting: { enabled: false },
      xAxis: {
        type: 'datetime',
        tickInterval: tickConfig.tickInterval,
        minorTickInterval: tickConfig.minorTickInterval,
        labels: { 
          format: tickConfig.format,
          style: { color: 'var(--chart-text)' },
          rotation: hours > 72 ? -45 : 0 // Rotate labels for longer periods
        },
        gridLineColor: 'var(--chart-grid)',
        lineColor: 'var(--chart-grid)',
        tickColor: 'var(--chart-grid)',
        minorGridLineColor: 'var(--chart-grid)',
        minorGridLineWidth: 0.5
      },
      yAxis: { 
        title: { text: null },
        labels: { style: { color: 'var(--chart-text)' } },
        gridLineColor: 'var(--chart-grid)'
      },
      tooltip: {
        backgroundColor: 'var(--chart-tooltip-bg)',
        borderColor: 'var(--chart-tooltip-border)',
        style: { color: 'var(--chart-text)' },
        xDateFormat: '%A, %e. %B %Y %H:%M',
        valueDecimals: 2,
        shared: true
      },
      plotOptions: {
        spline: {
          marker: { enabled: false },
          lineWidth: 2
        },
        area: {
          fillColor: 'url(#gradient-primary)',
          marker: { enabled: false },
          lineWidth: 2
        }
      }
    };
  },

  // Update chart theme when dark mode changes
  updateChartTheme(chart) {
    if (chart) {
      chart.redraw();
    }
  }
};

// Initialize Highcharts global configuration
document.addEventListener('DOMContentLoaded', function () {
  if (typeof Highcharts === 'undefined') {
    console.warn('Highcharts not loaded - charts will not work');
    return;
  }

  Highcharts.setOptions({
    lang: {
      months: ['leden', 'únor', 'březen', 'duben', 'květen', 'červen',
               'červenec', 'srpen', 'září', 'říjen', 'listopad', 'prosinec'],
      weekdays: ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota'],
      shortMonths: ['Led', 'Úno', 'Bře', 'Dub', 'Kvě', 'Čer', 'Čvc', 'Srp', 'Zář', 'Říj', 'Lis', 'Pro'],
      decimalPoint: ',',
      thousandsSep: ' ',
      loading: 'Načítání...',
      noData: 'Žádná data k zobrazení'
    },
    accessibility: {
      enabled: false
    },
    credits: {
      enabled: false
    },
    time: {
      timezone: 'Europe/Prague'
    }
  });

  // Global gradient definitions
  Highcharts.addEvent(Highcharts.Chart, 'render', function () {
    const chart = this;
    if (!chart.renderer.defs.element.querySelector('#gradient-primary')) {
      chart.renderer
        .createElement('linearGradient')
        .attr({ id: 'gradient-primary', x1: 0, y1: 0, x2: 0, y2: 1 })
        .add(chart.renderer.defs)
        .element.innerHTML = `
          <stop offset="0" style="stop-color: rgba(0, 200, 150, 0.4)"></stop>
          <stop offset="1" style="stop-color: rgba(0, 200, 150, 0)"></stop>
        `;
    }
  });
});