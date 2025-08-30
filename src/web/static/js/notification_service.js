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
        this.lastAlertCount = -1; // Cache last alert count to avoid unnecessary updates
        
        // Initialize service
        this.init();
    }
    
    async init() {
        console.log('🔔 Inicializuji Browser Notification Service...');
        
        // Request notification permission (only on first load, not if denied)
        await this.requestNotificationPermission(false);
        
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
    
    async requestNotificationPermission(forceRequest = false) {
        if (!('Notification' in window)) {
            console.warn('🔕 Prohlížeč nepodporuje desktop notifikace');
            this.notificationPermission = 'not-supported';
            this.showPermissionInfo('not-supported');
            return false;
        }
        
        if (Notification.permission === 'granted') {
            this.notificationPermission = 'granted';
            console.log('✅ Desktop notifikace jsou povoleny');
            this.showPermissionInfo('granted');
            return true;
        } else if (Notification.permission === 'denied') {
            this.notificationPermission = 'denied';
            if (!forceRequest) {
                console.warn('❌ Desktop notifikace jsou trvale zakázány v prohlížeči');
                this.showPermissionInfo('permanently_denied');
                return false;
            } else {
                // Still try to request even if denied (won't show dialog but gives proper feedback)
                console.log('🔔 Pokus o vyžádání oprávnění i přes předchozí odmítnutí...');
                this.showPermissionInfo('requesting');
            }
        } else {
            // Permission is 'default' - ask for permission
            console.log('🔔 Vyžádání oprávnění pro desktop notifikace...');
            this.showPermissionInfo('requesting');
            
            try {
                const permission = await Notification.requestPermission();
                this.notificationPermission = permission;
                if (permission === 'granted') {
                    console.log('✅ Uživatel povolil desktop notifikace');
                    this.showPermissionInfo('granted');
                    this.showWelcomeNotification();
                    return true;
                } else {
                    console.warn('❌ Uživatel odmítl desktop notifikace');
                    this.showPermissionInfo('denied');
                    return false;
                }
            } catch (error) {
                console.error('❌ Chyba při vyžádání oprávnění pro notifikace:', error);
                this.notificationPermission = 'denied';
                this.showPermissionInfo('error');
                return false;
            }
        }
    }
    
    showPermissionInfo(status) {
        // Show permission status in the notifications tab if we're there
        const notificationChannelsContainer = document.getElementById('notificationChannelsContainer');
        if (!notificationChannelsContainer) return;
        
        const permissionStatusHtml = this.getPermissionStatusHtml(status);
        
        // Create or update permission status element
        let permissionElement = document.getElementById('browserPermissionStatus');
        if (!permissionElement) {
            permissionElement = document.createElement('div');
            permissionElement.id = 'browserPermissionStatus';
            permissionElement.style.cssText = `
                margin: 15px 0;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
            `;
            notificationChannelsContainer.appendChild(permissionElement);
        }
        
        permissionElement.innerHTML = permissionStatusHtml;
    }
    
    getPermissionStatusHtml(status) {
        const statusConfigs = {
            'granted': {
                color: 'var(--color-green)',
                bgColor: 'var(--color-green-light)',
                icon: '✅',
                title: 'Desktop notifikace povoleny',
                description: 'Budete dostávat desktop notifikace při novych upozorněních.'
            },
            'denied': {
                color: 'var(--color-red)',
                bgColor: 'var(--color-red-light)',
                icon: '❌',
                title: 'Desktop notifikace zakázány',
                description: 'Pro povolení klikněte na ikonu zámku v adresním řádku a povolte notifikace.',
                action: '<button onclick="browserNotificationService.requestNotificationPermission(true)" class="btn btn-secondary" style="margin-top: 8px;">Zkusit znovu</button>'
            },
            'permanently_denied': {
                color: 'var(--color-red)',
                bgColor: 'var(--color-red-light)',
                icon: '🔒',
                title: 'Desktop notifikace jsou trvale zakázány',
                description: 'Notifikace byly zakázány v prohlížeči. Pro povolení klikněte na ikonu zámku/štítu v adresním řádku (vlevo od URL) a nastavte "Notifikace" na "Povolit".',
                action: `
                    <div style="margin-top: 12px; padding: 8px; background: var(--bg-tertiary); border-radius: 4px; font-size: 12px;">
                        <strong>Krok za krokem:</strong><br>
                        1. Klikněte na 🔒 nebo 🛡️ ikonu vlevo od adresy<br>
                        2. Najděte "Notifikace" nebo "Notifications"<br>
                        3. Změňte z "Blokovat" na "Povolit"<br>
                        4. Obnovte stránku (F5)
                    </div>
                    <button onclick="window.location.reload()" class="btn btn-secondary" style="margin-top: 8px;">
                        <span style="margin-right: 4px;">🔄</span> Obnovit stránku
                    </button>
                `
            },
            'requesting': {
                color: 'var(--color-blue)',
                bgColor: 'var(--color-blue-light)',
                icon: '🔔',
                title: 'Vyžádání oprávnění...',
                description: 'Prosím povolte desktop notifikace v dialogu prohlížeče.'
            },
            'not-supported': {
                color: 'var(--color-yellow)',
                bgColor: 'var(--color-yellow-light)',
                icon: '⚠️',
                title: 'Desktop notifikace nejsou podporovány',
                description: 'Váš prohlížeč nepodporuje desktop notifikace.'
            },
            'error': {
                color: 'var(--color-red)',
                bgColor: 'var(--color-red-light)',
                icon: '❌',
                title: 'Chyba při vyžádání oprávnění',
                description: 'Došlo k chybě při pokusu o povolení desktop notifikací.'
            }
        };
        
        const config = statusConfigs[status] || statusConfigs['error'];
        
        return `
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="
                    width: 32px; height: 32px;
                    background: ${config.color};
                    border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    color: white; font-size: 16px;
                ">
                    ${config.icon}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">
                        ${config.title}
                    </div>
                    <div style="color: var(--text-secondary); font-size: 14px;">
                        ${config.description}
                    </div>
                    ${config.action || ''}
                </div>
            </div>
        `;
    }
    
    showWelcomeNotification() {
        // Show a welcome notification to confirm everything works
        setTimeout(() => {
            const welcomeNotification = new Notification('🎉 PondMonitor Notifikace', {
                body: 'Desktop notifikace jsou nyní aktivní! Budete informováni o všech upozorněních.',
                icon: '/static/favicon.ico',
                tag: 'welcome_notification',
                requireInteraction: false,
                silent: false
            });
            
            welcomeNotification.onclick = () => {
                window.focus();
                welcomeNotification.close();
            };
            
            // Auto close after 5 seconds
            setTimeout(() => {
                welcomeNotification.close();
            }, 5000);
        }, 1000);
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
        this.updateNotificationIndicator().catch(console.warn);
        
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
    
    async updateNotificationIndicator() {
        // Update notification count in navigation or header
        const unreadCount = await this.getUnreadCount();
        
        // Only update if count has changed
        if (unreadCount === this.lastAlertCount) {
            return;
        }
        
        this.lastAlertCount = unreadCount;
        
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
    
    async getUnreadCount() {
        try {
            // Get active alerts count instead of browser notifications
            const response = await fetch('/api/alerts/active');
            if (response.ok) {
                const alerts = await response.json();
                return alerts.length;
            }
        } catch (error) {
            console.warn('Failed to get active alerts count:', error);
        }
        
        // Fallback to notification queue length
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
                
                this.updateNotificationIndicator().catch(console.warn);
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
    
    // Initialize the notification indicator
    browserNotificationService.updateNotificationIndicator().catch(console.warn);
    
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