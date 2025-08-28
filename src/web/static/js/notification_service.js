/**
 * Browser Notification Service for PondMonitor
 * Handles real-time notifications from Redis via polling and desktop push notifications
 */

class BrowserNotificationService {
    constructor() {
        this.isPolling = false;
        this.pollingInterval = null;
        this.pollingIntervalMs = 5000; // 5 seconds
        this.lastNotificationCheck = Date.now();
        this.notificationPermission = null;
        this.notificationQueue = [];
        this.maxNotifications = 50;
        this.seenNotifications = new Set();
        
        // Initialize service
        this.init();
    }
    
    async init() {
        console.log('🔔 Inicializuji Browser Notification Service...');
        
        // Request notification permission
        await this.requestNotificationPermission();
        
        // Start polling for notifications
        this.startPolling();
        
        // Set up page visibility handler to pause/resume polling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pausePolling();
            } else {
                this.resumePolling();
            }
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            this.stopPolling();
        });
    }
    
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.warn('🔕 Prohlížeč nepodporuje desktop notifikace');
            this.notificationPermission = 'not-supported';
            return false;
        }
        
        if (Notification.permission === 'granted') {
            this.notificationPermission = 'granted';
            console.log('✅ Desktop notifikace jsou povoleny');
            return true;
        } else if (Notification.permission === 'denied') {
            this.notificationPermission = 'denied';
            console.warn('❌ Desktop notifikace jsou zakázány');
            return false;
        } else {
            // Ask for permission
            try {
                const permission = await Notification.requestPermission();
                this.notificationPermission = permission;
                if (permission === 'granted') {
                    console.log('✅ Uživatel povolil desktop notifikace');
                    return true;
                } else {
                    console.warn('❌ Uživatel odmítl desktop notifikace');
                    return false;
                }
            } catch (error) {
                console.error('❌ Chyba při vyžádání oprávnění pro notifikace:', error);
                this.notificationPermission = 'denied';
                return false;
            }
        }
    }
    
    startPolling() {
        if (this.isPolling) return;
        
        console.log(`🔄 Spouštím polling notifikací (každých ${this.pollingIntervalMs/1000}s)`);
        this.isPolling = true;
        
        // Poll immediately
        this.pollNotifications();
        
        // Set up interval
        this.pollingInterval = setInterval(() => {
            this.pollNotifications();
        }, this.pollingIntervalMs);
    }
    
    pausePolling() {
        console.log('⏸️ Pozastavuji polling (stránka není viditelná)');
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
    }
    
    resumePolling() {
        if (!this.isPolling) {
            console.log('▶️ Obnovuji polling (stránka je viditelná)');
            this.startPolling();
        }
    }
    
    stopPolling() {
        console.log('⏹️ Zastavuji polling notifikací');
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
    }
    
    async pollNotifications() {
        try {
            const response = await fetch('/api/alerts/notifications/browser');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            const notifications = data.notifications || [];
            
            // Process new notifications
            const newNotifications = notifications.filter(notification => 
                !this.seenNotifications.has(this.getNotificationId(notification))
            );
            
            if (newNotifications.length > 0) {
                console.log(`📬 Obdrženy ${newNotifications.length} nové notifikace`);
                
                for (const notification of newNotifications) {
                    const notificationId = this.getNotificationId(notification);
                    this.seenNotifications.add(notificationId);
                    await this.processNotification(notification);
                }
            }
            
        } catch (error) {
            console.error('❌ Chyba při polling notifikací:', error);
        }
    }
    
    getNotificationId(notification) {
        // Create unique ID from notification content and timestamp
        return `${notification.alert_id || notification.timestamp || Date.now()}_${notification.severity}_${notification.title}`;
    }
    
    async processNotification(notification) {
        console.log('🔔 Zpracovávám notifikaci:', notification);
        
        // Add to queue
        this.notificationQueue.unshift(notification);
        
        // Limit queue size
        if (this.notificationQueue.length > this.maxNotifications) {
            this.notificationQueue = this.notificationQueue.slice(0, this.maxNotifications);
        }
        
        // Show desktop notification if permitted
        if (this.notificationPermission === 'granted') {
            this.showDesktopNotification(notification);
        }
        
        // Show in-page notification
        this.showInPageNotification(notification);
        
        // Update notification badge/indicator
        this.updateNotificationIndicator();
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('pondmonitor:notification', { 
            detail: notification 
        }));
    }
    
    showDesktopNotification(notification) {
        try {
            const severityEmojis = {
                'critical': '🚨',
                'warning': '⚠️', 
                'info': 'ℹ️'
            };
            
            const title = `${severityEmojis[notification.severity] || '🔔'} ${notification.title}`;
            const options = {
                body: notification.message,
                icon: '/static/favicon.ico',
                badge: '/static/favicon.ico',
                tag: notification.alert_id || this.getNotificationId(notification),
                requireInteraction: notification.severity === 'critical',
                silent: false,
                data: notification
            };
            
            const desktopNotification = new Notification(title, options);
            
            desktopNotification.onclick = () => {
                window.focus();
                // Navigate to alerts page if not already there
                if (!window.location.pathname.includes('alerts')) {
                    window.location.href = '/alerts';
                }
                desktopNotification.close();
            };
            
            // Auto close after 10 seconds (except critical)
            if (notification.severity !== 'critical') {
                setTimeout(() => {
                    desktopNotification.close();
                }, 10000);
            }
            
        } catch (error) {
            console.error('❌ Chyba při zobrazování desktop notifikace:', error);
        }
    }
    
    showInPageNotification(notification) {
        // Create in-page notification element
        const notificationElement = document.createElement('div');
        notificationElement.className = `in-page-notification severity-${notification.severity}`;
        
        const severityColors = {
            'critical': '#dc2626',
            'warning': '#d97706',
            'info': '#2563eb'
        };
        
        const severityIcons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        notificationElement.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                background: white;
                border: 1px solid ${severityColors[notification.severity] || '#6b7280'};
                border-left: 4px solid ${severityColors[notification.severity] || '#6b7280'};
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                max-width: 400px;
                animation: slideInRight 0.3s ease-out;
                cursor: pointer;
            ">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <div style="font-size: 1.25rem;">${severityIcons[notification.severity] || '🔔'}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 4px;">
                            ${notification.title}
                        </div>
                        <div style="color: #6b7280; font-size: 14px; line-height: 1.4;">
                            ${notification.message}
                        </div>
                        ${notification.station_id ? `
                            <div style="color: #9ca3af; font-size: 12px; margin-top: 8px;">
                                Stanice: ${notification.station_id}
                            </div>
                        ` : ''}
                    </div>
                    <button style="
                        background: none;
                        border: none;
                        font-size: 18px;
                        color: #9ca3af;
                        cursor: pointer;
                        padding: 0;
                        line-height: 1;
                    ">×</button>
                </div>
            </div>
        `;
        
        // Add click handlers
        const closeButton = notificationElement.querySelector('button');
        const notificationBody = notificationElement.querySelector('div');
        
        closeButton.onclick = (e) => {
            e.stopPropagation();
            this.removeInPageNotification(notificationElement);
        };
        
        notificationBody.onclick = () => {
            if (!window.location.pathname.includes('alerts')) {
                window.location.href = '/alerts';
            }
            this.removeInPageNotification(notificationElement);
        };
        
        document.body.appendChild(notificationElement);
        
        // Auto remove after 8 seconds (except critical)
        if (notification.severity !== 'critical') {
            setTimeout(() => {
                this.removeInPageNotification(notificationElement);
            }, 8000);
        }
    }
    
    removeInPageNotification(element) {
        element.style.animation = 'slideOutRight 0.3s ease-in forwards';
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 300);
    }
    
    updateNotificationIndicator() {
        // Update notification count in navigation or header
        const unreadCount = this.getUnreadCount();
        
        // Find notification indicators
        const indicators = document.querySelectorAll('.notification-indicator, #notificationIndicator');
        indicators.forEach(indicator => {
            if (unreadCount > 0) {
                indicator.textContent = unreadCount > 99 ? '99+' : unreadCount.toString();
                indicator.style.display = 'inline-block';
            } else {
                indicator.style.display = 'none';
            }
        });
        
        // Update page title
        if (unreadCount > 0) {
            if (!document.title.startsWith('(')) {
                document.title = `(${unreadCount}) ${document.title}`;
            }
        } else {
            document.title = document.title.replace(/^\(\d+\)\s/, '');
        }
    }
    
    getUnreadCount() {
        // For now, count all notifications in queue as unread
        // In a more sophisticated system, we'd track read status
        return this.notificationQueue.length;
    }
    
    getNotifications() {
        return [...this.notificationQueue];
    }
    
    async markAsRead(notificationIds) {
        try {
            const response = await fetch('/api/alerts/notifications/browser/mark-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    notification_ids: notificationIds
                })
            });
            
            if (response.ok) {
                // Remove from local queue
                notificationIds.forEach(id => {
                    const index = this.notificationQueue.findIndex(n => 
                        this.getNotificationId(n) === id
                    );
                    if (index !== -1) {
                        this.notificationQueue.splice(index, 1);
                    }
                });
                
                this.updateNotificationIndicator();
                return true;
            }
            
        } catch (error) {
            console.error('❌ Chyba při označování notifikací jako přečtených:', error);
        }
        return false;
    }
}

// Global instance
let browserNotificationService = null;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    browserNotificationService = new BrowserNotificationService();
    
    // Make available globally
    window.BrowserNotificationService = browserNotificationService;
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-indicator {
        background: #dc2626;
        color: white;
        border-radius: 10px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: bold;
        min-width: 18px;
        text-align: center;
        display: none;
        position: absolute;
        top: -8px;
        right: -8px;
    }
`;
document.head.appendChild(style);