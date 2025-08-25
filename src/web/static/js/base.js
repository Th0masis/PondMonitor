/* PondMonitor - Base JavaScript Module */

// Global configuration
window.pondConfig = {
  apiBase: (function() {
    // Get base URL dynamically from current page
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port;
    const baseUrl = `${protocol}//${hostname}${port ? ':' + port : ''}`;
    return `${baseUrl}/api`;
  })(),
  refreshInterval: 30000,
  timezone: 'Europe/Prague'
};

// Dark mode detection and initialization
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

// Initialize theme immediately
initTheme();

// Global utilities
window.PondUtils = {
  // Show loading indicator
  showLoading() {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
      indicator.style.transform = 'scaleX(1)';
    }
  },
  
  // Hide loading indicator
  hideLoading() {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
      indicator.style.transform = 'scaleX(0)';
    }
  },
  
  // Show error message
  showError(message, type = 'error') {
    const toast = document.getElementById('errorToast');
    const messageEl = document.getElementById('errorMessage');
    
    if (!toast || !messageEl) return;
    
    // Reset classes
    toast.className = `toast ${type}`;
    messageEl.textContent = message;
    toast.style.transform = 'translateX(0)';
    
    setTimeout(() => {
      toast.style.transform = 'translateX(calc(100% + 2rem))';
    }, 5000);
  },
  
  // Show success message
  showSuccess(message) {
    this.showError(message, 'success');
  },
  
  // Show info message
  showInfo(message) {
    this.showError(message, 'info');
  },
  
  // Format date for display
  formatDate(date) {
    return new Intl.DateTimeFormat('cs-CZ', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(date));
  },
  
  // API request wrapper with error handling
  async apiRequest(url, options = {}) {
    this.showLoading();
    try {
      const fullUrl = url.startsWith('http') ? url : 
                     url.startsWith('/api') ? `${window.location.origin}${url}` :
                     `${window.pondConfig.apiBase}/${url.replace(/^\/+/, '')}`;
      
      const response = await fetch(fullUrl, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      this.showError(`Chyba načítání: ${error.message}`);
      throw error;
    } finally {
      this.hideLoading();
    }
  },
  
  // Update last update time
  updateLastUpdateTime() {
    const timeEl = document.getElementById('lastUpdateTime');
    if (timeEl) {
      timeEl.textContent = this.formatDate(new Date());
    }
  }
};

// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
  const themeToggle = document.getElementById('themeToggle');
  const sunIcon = document.getElementById('sunIcon');
  const moonIcon = document.getElementById('moonIcon');
  const themeText = document.getElementById('themeText');
  
  if (!themeToggle) return;
  
  function updateThemeUI() {
    const isDark = document.documentElement.classList.contains('dark');
    
    if (sunIcon) sunIcon.style.display = isDark ? 'none' : 'block';
    if (moonIcon) moonIcon.style.display = isDark ? 'block' : 'none';
    if (themeText) themeText.textContent = isDark ? 'Tmavý režim' : 'Světlý režim';
    
    // Update CSS custom properties for charts
    document.documentElement.style.setProperty('--chart-text', isDark ? '#f3f4f6' : '#374151');
    document.documentElement.style.setProperty('--chart-grid', isDark ? '#4b5563' : '#e5e7eb');
    document.documentElement.style.setProperty('--chart-tooltip-bg', isDark ? '#374151' : '#ffffff');
    document.documentElement.style.setProperty('--chart-tooltip-border', isDark ? '#6b7280' : '#d1d5db');
  }
  
  themeToggle.addEventListener('click', function() {
    if (document.documentElement.classList.contains('dark')) {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    }
    updateThemeUI();
    
    // Trigger theme change event for charts
    window.dispatchEvent(new CustomEvent('themeChange'));
  });
  
  updateThemeUI();
});

// Mobile menu functionality
function toggleMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobileOverlay');
  const body = document.body;
  
  if (!sidebar || !overlay) return;
  
  sidebar.classList.toggle('mobile-open');
  overlay.classList.toggle('active');
  body.classList.toggle('mobile-menu-open');
}

// Connection status monitoring
async function updateConnectionStatus() {
  try {
    const response = await fetch('/health');
    const data = await response.json();
    
    const indicator = document.getElementById('statusIndicator');
    const text = document.getElementById('statusText');
    
    if (!indicator || !text) return;
    
    if (data.status === 'healthy') {
      indicator.className = 'status-indicator online';
      text.textContent = 'Připojeno';
    } else if (data.status === 'degraded') {
      indicator.className = 'status-indicator warning';
      text.textContent = 'Částečně dostupné';
    } else {
      indicator.className = 'status-indicator offline';
      text.textContent = 'Nedostupné';
    }
  } catch (error) {
    const indicator = document.getElementById('statusIndicator');
    const text = document.getElementById('statusText');
    
    if (indicator && text) {
      indicator.className = 'status-indicator offline';
      text.textContent = 'Chyba připojení';
    }
  }
}

// Initialize mobile menu handling and connection monitoring
document.addEventListener('DOMContentLoaded', function() {
  // Close mobile menu when clicking on nav links
  const navLinks = document.querySelectorAll('.sidebar .nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        toggleMobileMenu();
      }
    });
  });

  // Show/hide mobile elements based on screen size
  function updateMobileElements() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileCloseBtn = document.getElementById('mobileCloseBtn');
    
    if (window.innerWidth <= 768) {
      if (mobileMenuBtn) mobileMenuBtn.style.display = 'block';
      if (mobileCloseBtn) mobileCloseBtn.style.display = 'block';
    } else {
      if (mobileMenuBtn) mobileMenuBtn.style.display = 'none';
      if (mobileCloseBtn) mobileCloseBtn.style.display = 'none';
      
      // Close mobile menu if open
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('mobileOverlay');
      const body = document.body;
      
      if (sidebar) sidebar.classList.remove('mobile-open');
      if (overlay) overlay.classList.remove('active');
      body.classList.remove('mobile-menu-open');
    }
  }

  updateMobileElements();
  window.addEventListener('resize', updateMobileElements);
  
  // Update connection status every 30 seconds
  updateConnectionStatus();
  setInterval(updateConnectionStatus, 30000);
});