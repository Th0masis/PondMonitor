// meteogram-custom.js

// Meteogram Class Definition
function Meteogram(json, container) {
  this.symbols = [];
  this.precipitations = [];
  this.precipitationsError = [];
  this.winds = [];
  this.temperatures = [];
  this.pressures = [];
  this.json = json;
  this.container = container;
  this.parseYrData();
}

Meteogram.dictionary = {
  clearsky: { symbol: '01', text: 'Jasno' },
  fair: { symbol: '02', text: 'Polojasno' },
  partlycloudy: { symbol: '03', text: 'Oblačno' },
  cloudy: { symbol: '04', text: 'Zataženo' },
  lightrain: { symbol: '46', text: 'Slabý déšť' },
  rain: { symbol: '09', text: 'Déšť' },
  heavyrain: { symbol: '10', text: 'Silný déšť' },
  snow: { symbol: '13', text: 'Sněžení' },
  fog: { symbol: '15', text: 'Mlha' }
};

Meteogram.prototype.parseYrData = function () {
  if (!this.json) return;
  const series = this.json.properties.timeseries;
  let pointStart;
  series.forEach((node, i) => {
    const x = Date.parse(node.time);
    const next = node.data.next_1_hours || node.data.next_6_hours;
    const symbolCode = next && next.summary.symbol_code;
    const to = node.data.next_1_hours ? x + 3600000 : x + 21600000;
    if (i === 0) pointStart = (x + to) / 2;

    this.symbols.push(symbolCode);
    this.temperatures.push({ x, y: node.data.instant.details.air_temperature, to, symbolName: Meteogram.dictionary[symbolCode.replace(/_(day|night)/, '')]?.text || '' });
    this.precipitations.push({ x, y: next.details.precipitation_amount });
    this.pressures.push({ x, y: node.data.instant.details.air_pressure_at_sea_level });
    if (i % 2 === 0) {
      this.winds.push({ x, value: node.data.instant.details.wind_speed, direction: node.data.instant.details.wind_from_direction });
    }
  });
  this.createChart();
};

Meteogram.prototype.drawWeatherSymbols = function (chart) {
  chart.series[0].data.forEach((point, i) => {
    if (i % 2 === 0) {
      const [symbol, variant] = this.symbols[i].split('_');
      const icon = Meteogram.dictionary[symbol]?.symbol + (variant === 'day' ? 'd' : 'n');
      chart.renderer.image(
        `https://cdn.jsdelivr.net/gh/nrkno/yr-weather-symbols@8.0.1/dist/svg/${icon}.svg`,
        point.plotX + chart.plotLeft - 8,
        point.plotY + chart.plotTop - 30,
        30,
        30
      ).attr({ zIndex: 5 }).add();
    }
  });
};

Meteogram.prototype.createChart = function () {
  this.chart = Highcharts.chart(this.container, {
    chart: {
      type: 'spline',
      marginBottom: 70,
      height: 350
    },
    title: { text: 'Meteogram: Krátkodobá předpověď' },
    xAxis: [{
      type: 'datetime',
      tickInterval: 2 * 3600 * 1000,
      labels: { format: '{value:%H:%M}' }
    }],
    yAxis: [{
      title: { text: 'Teplota (°C)' },
      labels: { format: '{value}°' },
      tickInterval: 1
    }, {
      title: { text: 'Srážky (mm)' },
      opposite: true,
      min: 0
    }, {
      title: { text: 'Tlak (hPa)' },
      opposite: true,
      gridLineWidth: 0
    }],
    tooltip: {
      shared: true,
      xDateFormat: '%A, %e. %B %H:%M'
    },
    series: [
      {
        name: 'Teplota',
        data: this.temperatures,
        tooltip: { valueSuffix: ' °C' },
        color: '#FF3333',
        yAxis: 0
      },
      {
        name: 'Srážky',
        data: this.precipitations,
        type: 'column',
        color: '#68CFE8',
        yAxis: 1
      },
      {
        name: 'Tlak',
        data: this.pressures,
        dashStyle: 'shortdot',
        color: '#888888',
        yAxis: 2,
        tooltip: { valueSuffix: ' hPa' }
      },
      {
        name: 'Vítr',
        type: 'windbarb',
        data: this.winds,
        color: '#90ed7d',
        yOffset: -15,
        tooltip: { valueSuffix: ' m/s' }
      }
    ]
  }, chart => this.drawWeatherSymbols(chart));
};
