# PondMonitor User Guide

## 📦 Installation for End Users

### **Option 1: Pre-Built Package (Easiest)**

1. **Download the latest release** from GitHub:
   - Go to: https://github.com/Th0masis/PondMonitor/releases/latest
   - Download `pondmonitor-latest.zip` (Windows/Mac/Linux)
   
2. **Extract and run**:
   ```bash
   # Extract the zip file
   unzip pondmonitor-latest.zip
   cd pondmonitor-*
   
   # Run the application
   ./start.sh      # On Linux/Mac
   start.bat       # On Windows
   ```
   
3. **Open your browser** to http://localhost:5005

### **Option 2: Using Docker**

If you have Docker installed:
```bash
# Download and extract
curl -L https://github.com/Th0masis/PondMonitor/releases/latest/download/pondmonitor-latest.tar.gz | tar -xz
cd pondmonitor-*

# Run with Docker
docker compose up -d

# Access at http://localhost:5005
```

### **Option 3: Try Demo Online**

Visit the online demo to try the system without installing anything:
**[demo.pondmonitor.example](http://demo.pondmonitor.example)**

---

## 📱 Web Interface User Guide

This guide covers how to use the PondMonitor web interface effectively. The interface is designed to be intuitive and responsive, working seamlessly on desktop, tablet, and mobile devices.

## 🌐 Accessing PondMonitor

**Default URLs:**
- **Local Development:** http://localhost:5000
- **Production:** https://your-domain.com

## 🏠 Dashboard Overview

### **Main Navigation**

The sidebar contains the main navigation menu:

- **🏠 Dashboard** - Real-time monitoring and charts
- **🌦️ Weather** - Meteorological data and forecasts  
- **🔧 Diagnostics** - System health and hardware status
- **🌙/☀️ Theme Toggle** - Switch between dark and light modes

### **Connection Status**

The sidebar displays real-time connection status:
- **🟢 Connected** - System is receiving data
- **🟡 Degraded** - Partial connectivity issues
- **🔴 Offline** - Connection problems

## 📊 Dashboard Features

### **Real-time Charts**

#### **Water Level Chart**
- **Purpose:** Displays pond water level over time
- **Units:** Centimeters (cm)
- **Features:**
  - Interactive zoom and pan
  - Hover for exact values
  - Gradient fill visualization
  - Real-time updates

#### **Outflow Chart**  
- **Purpose:** Shows water outflow rate
- **Units:** Liters per second (L/s)
- **Features:**
  - Synchronized with water level chart
  - Historical trend analysis
  - Export capabilities

### **Time Range Controls**

**Quick Time Buttons:**
```
[1h] [6h] [12h] [24h] [3d] [7d]
```

**Custom Range Picker:**
- Start Date/Time selector
- End Date/Time selector  
- Load button to apply range
- Maximum range: 30 days

### **Statistics Cards**

#### **Current Water Level**
- Current level in cm
- Change from previous reading
- Visual trend indicator
- Last update timestamp

#### **Current Outflow**
- Flow rate in L/s
- Average flow calculation
- Peak flow indicator
- Stability assessment

#### **System Status**
- Overall health score
- Active alerts count
- Data collection status
- Last heartbeat time

### **Interactive Features**

#### **Chart Interactions**
- **Zoom:** Click and drag to zoom into time periods
- **Pan:** Hold and drag to navigate through time
- **Hover:** View exact values and timestamps
- **Reset:** Double-click to reset zoom
- **Export:** Built-in chart export to PNG/SVG

#### **Data Export**
- **CSV Format:** Spreadsheet-compatible data
- **JSON Format:** Structured data for APIs
- **Time Range:** Export specific periods
- **File Download:** Automatic filename with timestamp

## 🌦️ Weather Page

### **Current Weather Card**

**Displays:**
- Current temperature with trend
- Precipitation amount and probability
- Wind speed and direction
- Atmospheric pressure
- Humidity percentage
- Cloud coverage
- Weather symbol/icon

**Update Frequency:** Every 30 minutes

### **48-Hour Meteogram**

**Interactive Chart Features:**
- **Temperature Curve:** Hourly temperature forecast
- **Precipitation Bars:** Rain/snow amounts
- **Wind Data:** Speed and direction indicators
- **Pressure Line:** Atmospheric pressure trend
- **Symbol Track:** Weather condition icons

**Navigation:**
- Zoom into specific time periods
- Hover for detailed hourly data
- Scroll through 48-hour timeline

### **7-Day Forecast Cards**

**Each Day Shows:**
- Date and day of week
- High/low temperatures
- Weather symbol and description
- Precipitation probability
- Wind speed and direction
- Brief conditions summary

**Interactive Elements:**
- Click cards for detailed view
- Swipe on mobile devices
- Responsive grid layout

### **Weather Statistics**

**24-Hour Overview:**
- Temperature range (min/max/average)
- Pressure trends and changes
- Wind patterns and gusts
- Precipitation totals
- Humidity variations

## 🔧 Diagnostics Page

### **System Health Overview**

#### **Health Score**
- Overall system health percentage
- Color-coded status (green/yellow/red)
- Active issues count
- Performance metrics

#### **Service Status**
- **Database:** Connection and query performance
- **Redis Cache:** Memory usage and hit rates
- **Weather API:** External service availability
- **LoRa Gateway:** Hardware communication status

### **Hardware Monitoring**

#### **Battery Status**
- **Voltage:** Current battery voltage
- **Percentage:** Estimated charge level
- **Charging Status:** Solar charging indicator
- **History:** Voltage trend over time
- **Alerts:** Low battery warnings

#### **Temperature Monitoring**
- **Ambient Temperature:** Sensor readings
- **Operating Range:** Normal/warning/critical
- **Trend Analysis:** Temperature patterns
- **Seasonal Comparison:** Historical data

#### **Signal Strength**
- **LoRa RSSI:** Signal strength in dBm
- **Quality Indicator:** Excellent/Good/Fair/Poor
- **Connection Stability:** Dropout frequency
- **Range Assessment:** Distance estimation

#### **Solar Power System**
- **Solar Voltage:** Panel output voltage
- **Generation Curve:** Daily solar patterns
- **Efficiency Metrics:** Power generation stats
- **Weather Correlation:** Cloud impact analysis

### **Data Quality Metrics**

#### **Data Collection Statistics**
- Records per hour/day
- Missing data percentage
- Data validation errors
- Storage efficiency

#### **Communication Statistics**
- Successful transmissions
- Retry attempts
- Timeout occurrences
- Data packet integrity

## 🎨 Themes and Customization

### **Theme Switching**

**Light Mode:**
- Clean, bright interface
- High contrast for outdoor viewing
- Optimized for daylight use
- Better for printing/screenshots

**Dark Mode:**
- Reduced eye strain
- Better for low-light environments
- Modern appearance
- Battery saving on OLED displays

**Auto Mode:**
- Follows system preference
- Automatic day/night switching
- Seamless transitions

### **Mobile Responsiveness**

#### **Mobile Navigation**
- Hamburger menu for small screens
- Touch-friendly buttons
- Swipe gestures for charts
- Optimized touch targets

#### **Tablet View**
- Adaptive grid layouts
- Larger touch areas
- Landscape optimization
- Split-screen friendly

#### **Desktop Features**
- Sidebar navigation
- Keyboard shortcuts
- Multi-monitor support
- High-resolution charts

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `D` | Go to Dashboard |
| `W` | Go to Weather page |
| `G` | Go to Diagnostics |
| `T` | Toggle theme |
| `R` | Refresh current page |
| `E` | Export current data |
| `?` | Show help (if available) |

## 📱 Mobile App Features

### **Progressive Web App (PWA)**
- Install to home screen
- Offline data viewing
- Push notifications (future)
- Native app experience

### **Touch Gestures**
- **Pinch to Zoom:** Chart navigation
- **Swipe:** Page navigation
- **Pull to Refresh:** Update data
- **Long Press:** Context menus

## 🔔 Alerts and Notifications

### **Visual Indicators**

#### **Status Colors**
- **🟢 Green:** Normal operation
- **🟡 Yellow:** Warning conditions
- **🔴 Red:** Critical issues
- **⚪ Gray:** Unknown/offline

#### **Alert Types**
- **Battery Low:** Battery below threshold
- **Connection Lost:** Communication failure
- **Data Quality:** Invalid sensor readings
- **System Error:** Application issues

### **Alert Management**
- View active alerts
- Alert history log
- Acknowledgment system
- Severity filtering

## 🔧 Settings and Preferences

### **Display Settings**
- **Theme:** Light/Dark/Auto
- **Units:** Metric/Imperial
- **Language:** Interface language (future)
- **Time Zone:** Local time display
- **Refresh Rate:** Data update frequency

### **Chart Preferences**
- **Default Time Range:** Starting view
- **Chart Type:** Line/Area/Bar options
- **Grid Lines:** Show/hide grid
- **Tooltips:** Enable/disable hover info
- **Animation:** Chart transition effects

### **Export Options**
- **Default Format:** CSV/JSON/Excel
- **Date Format:** ISO/Local/Custom
- **Decimal Places:** Precision settings
- **Include Headers:** Column names option

### **🖨️ Professional Print Functionality**
*Enhanced feature for high-quality reports*

#### **Dashboard Print Features**
- **Print Button Location:** Dashboard page → "Quick Actions" → "Tisknout grafy"
- **Professional Layout:** A4 landscape format optimized for charts
- **High-Quality Output:** SVG-based charts for crisp printing
- **Complete Reports:** Includes statistics, charts, and metadata

#### **What's Included in Print**
- **Report Header:** PondMonitor title with export timestamp
- **Time Period:** Shows selected date range (24h, 3 days, week, month)
- **Statistics Grid:** Key metrics (current, min, max, average values)
- **Charts:** Both water level and outflow charts with professional styling
- **Footer:** Generation timestamp and system attribution

#### **Print Quality Features**
- **Optimized Dimensions:** 800px × 350px charts perfect for A4 landscape
- **Print Colors:** Black/gray text optimized for monochrome printing
- **Professional Typography:** 18px titles, 14px subtitles, 12px details
- **Page Layout:** Single-column layout maximizing chart visibility
- **No Page Breaks:** Charts never split across pages

#### **Browser Compatibility**
- ✅ **Works in:** Chrome, Firefox, Edge, Opera, Safari
- ✅ **Mobile Support:** Print functionality available on tablets
- ✅ **Popup Handling:** Clear error messages if popups are blocked
- ✅ **Fallback Options:** Data tables if chart export fails

#### **How to Print**
1. **Navigate to Dashboard** page
2. **Select time range** (24h, 3 days, 1 week, 1 month)
3. **Wait for data to load** (charts must be visible)
4. **Click "Tisknout grafy"** in Quick Actions section
5. **Print window opens** with professional report layout
6. **Use browser print dialog** to save as PDF or print to paper

#### **Print Tips**
- **Best Quality:** Use "Print to PDF" for digital reports
- **Paper Setting:** Choose A4 landscape in printer settings
- **Color Options:** Works well in both color and black & white
- **File Sharing:** PDF exports are perfect for email reports

## 🆘 Troubleshooting UI Issues

### **Common Display Problems**

#### **Charts Not Loading**
1. Check browser console for errors
2. Verify JavaScript is enabled
3. Clear browser cache
4. Try different browser
5. Check network connectivity

#### **Data Not Updating**
1. Check connection status indicator
2. Refresh the page manually
3. Verify system is collecting data
4. Check browser developer tools

#### **Mobile Display Issues**
1. Rotate device (landscape/portrait)
2. Update browser app
3. Clear mobile browser cache
4. Check mobile data/WiFi

#### **Theme Problems**
1. Try manual theme toggle
2. Check system dark mode setting
3. Clear browser localStorage
4. Reset to default theme

### **Performance Optimization**

#### **For Slow Loading**
- Use shorter time ranges
- Close unnecessary browser tabs
- Check network speed
- Reduce chart animation
- Use simplified chart views

#### **For Memory Issues**
- Refresh page periodically
- Close other applications
- Use lighter browser
- Reduce data range

## 📊 Data Interpretation

### **Understanding Charts**

#### **Normal Patterns**
- **Water Level:** Gradual changes, seasonal trends
- **Outflow:** Correlation with level changes
- **Temperature:** Daily cycles, weather patterns
- **Battery:** Charging cycles, seasonal variation

#### **Warning Signs**
- **Sudden Level Drops:** Possible leaks or blockages
- **Erratic Outflow:** Sensor issues or debris
- **Temperature Extremes:** Equipment problems
- **Battery Decline:** Charging system failure

### **Data Quality Indicators**
- **Smooth Curves:** High-quality data
- **Gaps:** Communication interruptions
- **Spikes:** Possible sensor errors
- **Flat Lines:** Sensor malfunction

## 📞 Getting Help

### **Built-in Help**
- Hover tooltips on interface elements
- Status indicators with explanations
- Error messages with suggested actions

### **External Resources**
- **Documentation:** Check [docs/](../docs/) directory
- **API Reference:** [API.md](API.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues:** Report bugs and feature requests

### **Contact Information**
- **GitHub Repository:** Link to project issues
- **Email Support:** Contact information (if provided)
- **Community Forum:** User discussions (if available)

This user guide should help you make the most of PondMonitor's web interface. The system is designed to be intuitive, but don't hesitate to explore and experiment with different features!