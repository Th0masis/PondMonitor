/**
 * PondMonitor Alert Management JavaScript
 * Week 3: Smart Alerting System
 * 
 * Handles:
 * - Alert rule management (CRUD operations)
 * - Active alert monitoring and actions
 * - Alert history visualization
 * - Notification testing and configuration
 * - Real-time updates and WebSocket integration
 */

class AlertManager {
    constructor() {
        this.currentTab = 'active-alerts';
        this.activeAlerts = [];
        this.alertRules = [];
        this.alertHistory = [];
        this.notificationStatus = {};
        
        // Auto-refresh intervals
        this.refreshIntervals = {
            activeAlerts: null,
            statistics: null
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupTabNavigation();
        this.loadInitialData();
        this.setupAutoRefresh();
        this.setupModalHandlers();
    }
    
    setupEventListeners() {
        // Tab navigation is handled in setupTabNavigation()
        
        // Refresh buttons
        document.getElementById('refreshActiveAlerts')?.addEventListener('click', () => {
            this.loadActiveAlerts();
        });
        
        document.getElementById('refreshAlertRules')?.addEventListener('click', () => {
            this.loadAlertRules();
        });
        
        document.getElementById('refreshHistory')?.addEventListener('click', () => {
            this.loadAlertHistory();
        });
        
        document.getElementById('refreshNotificationStatus')?.addEventListener('click', () => {
            this.loadNotificationStatus();
        });
        
        // Acknowledge all alerts
        document.getElementById('acknowledgeAllAlerts')?.addEventListener('click', () => {
            this.acknowledgeAllAlerts();
        });
        
        // Create new rule
        document.getElementById('createNewRule')?.addEventListener('click', () => {
            this.showRuleModal();
        });
        
        // Test notifications
        document.getElementById('testNotifications')?.addEventListener('click', () => {
            this.sendTestNotification();
        });
        
        document.getElementById('sendTestNotification')?.addEventListener('click', () => {
            this.sendTestNotification();
        });
        
        document.getElementById('testBrowserNotification')?.addEventListener('click', () => {
            this.testBrowserNotification();
        });
        
        document.getElementById('enableDesktopNotifications')?.addEventListener('click', () => {
            this.enableDesktopNotifications();
        });
        
        
        // History filters
        document.getElementById('historyTimeRange')?.addEventListener('change', () => {
            this.loadAlertHistory();
        });
        
        document.getElementById('historySeverityFilter')?.addEventListener('change', () => {
            this.loadAlertHistory();
        });
        
        document.getElementById('historyStatusFilter')?.addEventListener('change', () => {
            this.loadAlertHistory();
        });
        
        document.getElementById('historySearchInput')?.addEventListener('input', 
            this.debounce(() => this.loadAlertHistory(), 500)
        );
        
        // Rule filters
        document.getElementById('ruleTypeFilter')?.addEventListener('change', () => {
            this.filterAlertRules();
        });
        
        document.getElementById('metricTypeFilter')?.addEventListener('change', () => {
            this.filterAlertRules();
        });
        
        document.getElementById('severityFilter')?.addEventListener('change', () => {
            this.filterAlertRules();
        });
        
        document.getElementById('enabledOnlyFilter')?.addEventListener('change', () => {
            this.filterAlertRules();
        });
        
        // Rule form handlers
        document.getElementById('ruleType')?.addEventListener('change', () => {
            this.updateConditionFields();
        });
        
        document.getElementById('ruleMetricType')?.addEventListener('change', () => {
            this.updateConditionFields();
        });
        
        // Channel management event listeners
        document.getElementById('addChannelBtn')?.addEventListener('click', () => {
            this.showChannelModal();
        });
        
        document.getElementById('channelType')?.addEventListener('change', () => {
            this.updateChannelConfigFields();
        });
        
        document.getElementById('channelForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveChannel();
        });
        
        document.getElementById('cancelChannelEdit')?.addEventListener('click', () => {
            this.hideModal(document.getElementById('channelModal'));
        });
        
        document.getElementById('testChannelBtn')?.addEventListener('click', () => {
            this.testCurrentChannel();
        });
    }
    
    setupTabNavigation() {
        const tabs = document.querySelectorAll('.tab-button');
        const panels = document.querySelectorAll('.tab-panel');
        
        console.log(`🔧 AlertManager: Setting up tab navigation - Found ${tabs.length} tabs and ${panels.length} panels`);
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.dataset.tab;
                console.log(`🔄 AlertManager: Switching to tab: ${targetTab}`);
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Show corresponding panel
                panels.forEach(panel => {
                    panel.classList.remove('active');
                    if (panel.id === targetTab) {
                        panel.classList.add('active');
                    }
                });
                
                this.currentTab = targetTab;
                this.loadTabData(targetTab);
            });
        });
    }
    
    setupModalHandlers() {
        // Rule modal
        const ruleModal = document.getElementById('ruleModal');
        const alertModal = document.getElementById('alertModal');
        
        // Close modal handlers
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal);
            });
        });
        
        // Click outside to close
        [ruleModal, alertModal].forEach(modal => {
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        this.hideModal(modal);
                    }
                });
            }
        });
        
        // Rule form submission
        document.getElementById('ruleForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAlertRule();
        });
        
        // Cancel rule edit
        document.getElementById('cancelRuleEdit')?.addEventListener('click', () => {
            this.hideModal(ruleModal);
        });
        
        // Setup browser notification listeners
        this.setupBrowserNotificationListeners();
    }
    
    setupAutoRefresh() {
        // Auto-refresh active alerts every 30 seconds
        this.refreshIntervals.activeAlerts = setInterval(() => {
            if (this.currentTab === 'active-alerts') {
                this.loadActiveAlerts();
            }
        }, 30000);
        
        // Auto-refresh statistics every 60 seconds
        this.refreshIntervals.statistics = setInterval(() => {
            this.loadStatistics();
            this.loadNotificationStatus(); // Also refresh notification status
        }, 60000);
    }
    
    setupBrowserNotificationListeners() {
        // Listen for new browser notifications
        window.addEventListener('pondmonitor:notification', (event) => {
            const notification = event.detail;
            console.log('📬 Přijata browser notifikace:', notification);
            
            // Refresh notification status and statistics when new notification arrives
            this.loadNotificationStatus();
            this.loadStatistics();
            
            // If we're on the active alerts tab, refresh the list
            if (this.currentTab === 'active-alerts' && notification.type === 'alert') {
                setTimeout(() => {
                    this.loadActiveAlerts();
                }, 1000); // Small delay to ensure backend is updated
            }
            
            // Update notification history if we're on notifications tab
            if (this.currentTab === 'notifications') {
                this.addNotificationToHistory(notification);
            }
        });
        
        // Check for existing notifications on page load
        if (window.BrowserNotificationService) {
            const existingNotifications = window.BrowserNotificationService.getNotifications();
            if (existingNotifications.length > 0) {
                console.log(`📬 Nalezeny ${existingNotifications.length} existující notifikace`);
            }
        }
    }
    
    addNotificationToHistory(notification) {
        const container = document.getElementById('notificationHistoryContainer');
        if (!container) return;
        
        // Create notification history item
        const historyItem = document.createElement('div');
        historyItem.className = 'notification-history-item';
        historyItem.style.cssText = `
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            background: var(--bg-secondary);
        `;
        
        const severityColors = {
            'critical': 'var(--color-red)',
            'warning': 'var(--color-yellow)', 
            'info': 'var(--color-blue)'
        };
        
        const severityIcons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        historyItem.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="
                    width: 32px; height: 32px;
                    border-radius: 50%;
                    background: ${severityColors[notification.severity] || 'var(--color-blue)'};
                    display: flex; align-items: center; justify-content: center;
                    color: white; font-size: 14px;
                ">
                    ${severityIcons[notification.severity] || '🔔'}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">
                        ${notification.title}
                    </div>
                    <div style="color: var(--text-secondary); font-size: 14px; margin-bottom: 8px;">
                        ${notification.message}
                    </div>
                    <div style="display: flex; gap: 16px; font-size: 12px; color: var(--text-muted);">
                        <span>🕒 ${new Date(notification.timestamp).toLocaleString('cs-CZ')}</span>
                        ${notification.station_id ? `<span>📍 ${notification.station_id}</span>` : ''}
                        <span>🔔 Browser</span>
                    </div>
                </div>
            </div>
        `;
        
        // Insert at the top of the container
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        container.insertBefore(historyItem, container.firstChild);
        
        // Limit to 20 items
        const items = container.querySelectorAll('.notification-history-item');
        if (items.length > 20) {
            items[items.length - 1].remove();
        }
    }
    
    async loadInitialData() {
        await this.loadStatistics();
        await this.loadNotificationStatus(); // Load notification status on initial page load
        await this.loadTabData(this.currentTab);
    }
    
    async loadTabData(tab) {
        switch (tab) {
            case 'active-alerts':
                await this.loadActiveAlerts();
                break;
            case 'alert-rules':
                await this.loadAlertRules();
                break;
            case 'history':
                await this.loadAlertHistory();
                break;
            case 'notifications':
                await this.loadNotificationStatus();
                await this.loadNotificationChannels();
                await this.loadAlertSettings();
                break;
        }
    }
    
    async loadStatistics() {
        try {
            const response = await fetch('/api/alerts/statistics');
            if (!response.ok) throw new Error('Failed to load statistics');
            
            const stats = await response.json();
            this.updateStatistics(stats);
            
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.showError('Failed to load alert statistics');
        }
    }
    
    updateStatistics(stats) {
        // Update stat cards
        const activeCount = stats.alerts_24h?.active_alerts || 0;
        const rulesCount = stats.rules?.enabled_rules || 0;
        const notificationsCount = stats.alerts_24h?.total_alerts || 0;
        
        document.getElementById('activeAlertsCount').textContent = activeCount;
        document.getElementById('rulesCount').textContent = rulesCount;
        document.getElementById('notificationsCount').textContent = notificationsCount;
        
        // Update notification status (will be updated by loadNotificationStatus)
        document.getElementById('channelsOnlineCount').textContent = '--';
    }
    
    async loadActiveAlerts() {
        const container = document.getElementById('activeAlertsContainer');
        const loading = document.getElementById('activeAlertsLoading');
        const noAlerts = document.getElementById('noActiveAlerts');
        
        this.showLoading(loading);
        
        try {
            const response = await fetch('/api/alerts/active');
            if (!response.ok) throw new Error('Failed to load active alerts');
            
            const alerts = await response.json();
            console.log('DEBUG: Active alerts loaded:', alerts);
            this.activeAlerts = alerts;
            
            this.hideLoading(loading);
            
            if (alerts.length === 0) {
                console.log('DEBUG: No active alerts found, showing empty state');
                container.style.display = 'none';
                noAlerts.style.display = 'block';
            } else {
                console.log('DEBUG: Displaying', alerts.length, 'active alerts');
                container.style.display = 'block';
                noAlerts.style.display = 'none';
                this.renderActiveAlerts(alerts, container);
            }
            
        } catch (error) {
            console.error('Failed to load active alerts:', error);
            this.hideLoading(loading);
            this.showError('Failed to load active alerts');
        }
    }
    
    renderActiveAlerts(alerts, container) {
        container.innerHTML = alerts.map(alert => `
            <div class="alert-card ${alert.severity}" data-alert-id="${alert.id}">
                <div class="alert-header">
                    <div class="alert-title">
                        <h3>${this.escapeHtml(alert.message)}</h3>
                        <div class="alert-meta">
                            <span>📊 ${alert.metric_type.replace('_', ' ')}</span>
                            ${alert.station_id ? `<span>📍 ${alert.station_id}</span>` : ''}
                            <span>⏰ ${this.formatDateTime(alert.triggered_at)}</span>
                        </div>
                    </div>
                    <div class="alert-actions">
                        <button class="btn btn-sm btn-secondary" onclick="alertManager.showAlertDetails('${alert.id}')">
                            <span class="icon">👁️</span> Details
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="alertManager.acknowledgeAlert('${alert.id}')">
                            <span class="icon">✅</span> Acknowledge
                        </button>
                        <button class="btn btn-sm btn-success" onclick="alertManager.resolveAlert('${alert.id}')">
                            <span class="icon">✔️</span> Resolve
                        </button>
                    </div>
                </div>
                
                ${alert.trigger_value !== null ? `
                <div class="alert-details">
                    <div class="alert-detail">
                        <div class="alert-detail-label">Current Value</div>
                        <div class="alert-detail-value">${alert.trigger_value}</div>
                    </div>
                    ${alert.threshold_value !== null ? `
                    <div class="alert-detail">
                        <div class="alert-detail-label">Threshold</div>
                        <div class="alert-detail-value">${alert.threshold_value}</div>
                    </div>` : ''}
                    <div class="alert-detail">
                        <div class="alert-detail-label">Severity</div>
                        <div class="alert-detail-value">
                            <span class="severity-badge ${alert.severity}">${alert.severity.toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="alert-detail">
                        <div class="alert-detail-label">Notifications</div>
                        <div class="alert-detail-value">${alert.notifications_sent?.length || 0} sent</div>
                    </div>
                </div>` : ''}
            </div>
        `).join('');
    }
    
    async loadAlertRules() {
        const container = document.getElementById('alertRulesContainer');
        const loading = document.getElementById('alertRulesLoading');
        
        this.showLoading(loading);
        
        try {
            const response = await fetch('/api/alerts/rules');
            if (!response.ok) throw new Error('Failed to load alert rules');
            
            const rules = await response.json();
            this.alertRules = rules;
            
            this.hideLoading(loading);
            this.renderAlertRules(rules, container);
            
        } catch (error) {
            console.error('Failed to load alert rules:', error);
            this.hideLoading(loading);
            this.showError('Failed to load alert rules');
        }
    }
    
    renderAlertRules(rules, container) {
        if (rules.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📋</div>
                    <h3>No Alert Rules</h3>
                    <p>Create your first alert rule to start monitoring your pond system.</p>
                    <button class="btn btn-primary" onclick="alertManager.showRuleModal()">
                        <span class="icon">➕</span> Create Rule
                    </button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = rules.map(rule => `
            <div class="rule-card ${rule.enabled ? '' : 'disabled'}" data-rule-id="${rule.id}">
                <div class="rule-header">
                    <div class="rule-title">
                        <h3>${this.escapeHtml(rule.name)}</h3>
                        <p class="rule-description">${this.escapeHtml(rule.description || '')}</p>
                        <div class="rule-tags">
                            <span class="rule-tag ${rule.severity}">${rule.severity.toUpperCase()}</span>
                            <span class="rule-tag">${rule.rule_type.replace('_', ' ')}</span>
                            <span class="rule-tag">${rule.metric_type.replace('_', ' ')}</span>
                            ${rule.station_id ? `<span class="rule-tag">Station: ${rule.station_id}</span>` : ''}
                            <span class="rule-tag">${rule.enabled ? 'ENABLED' : 'DISABLED'}</span>
                        </div>
                    </div>
                    <div class="rule-actions">
                        <button class="btn btn-sm btn-secondary" onclick="alertManager.editRule('${rule.id}')">
                            <span class="icon">✏️</span> Edit
                        </button>
                        <button class="btn btn-sm ${rule.enabled ? 'btn-warning' : 'btn-success'}" 
                                onclick="alertManager.toggleRule('${rule.id}', ${!rule.enabled})">
                            <span class="icon">${rule.enabled ? '⏸️' : '▶️'}</span> 
                            ${rule.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="alertManager.deleteRule('${rule.id}')">
                            <span class="icon">🗑️</span> Delete
                        </button>
                    </div>
                </div>
                
                <div class="rule-stats">
                    <span>📊 Cooldown: ${rule.cooldown_minutes}min</span>
                    <span>📈 Max/hour: ${rule.max_alerts_per_hour}</span>
                    <span>📤 Channels: ${rule.channels.join(', ')}</span>
                    ${rule.updated_at ? `<span>⏰ Updated: ${this.formatDateTime(rule.updated_at)}</span>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    filterAlertRules() {
        const ruleType = document.getElementById('ruleTypeFilter')?.value;
        const metricType = document.getElementById('metricTypeFilter')?.value;
        const severity = document.getElementById('severityFilter')?.value;
        const enabledOnly = document.getElementById('enabledOnlyFilter')?.checked;
        
        let filteredRules = [...this.alertRules];
        
        if (ruleType) {
            filteredRules = filteredRules.filter(rule => rule.rule_type === ruleType);
        }
        
        if (metricType) {
            filteredRules = filteredRules.filter(rule => rule.metric_type === metricType);
        }
        
        if (severity) {
            filteredRules = filteredRules.filter(rule => rule.severity === severity);
        }
        
        if (enabledOnly) {
            filteredRules = filteredRules.filter(rule => rule.enabled);
        }
        
        const container = document.getElementById('alertRulesContainer');
        this.renderAlertRules(filteredRules, container);
    }
    
    async loadAlertHistory() {
        const container = document.getElementById('alertHistoryContainer');
        const loading = document.getElementById('alertHistoryLoading');
        
        this.showLoading(loading);
        
        try {
            const params = new URLSearchParams();
            
            const timeRange = document.getElementById('historyTimeRange')?.value || '24';
            params.append('hours', timeRange);
            
            const severity = document.getElementById('historySeverityFilter')?.value;
            if (severity) params.append('severity', severity);
            
            const status = document.getElementById('historyStatusFilter')?.value;
            if (status) params.append('status', status);
            
            const search = document.getElementById('historySearchInput')?.value;
            if (search) params.append('search', search);
            
            const response = await fetch(`/api/alerts/history?${params}`);
            if (!response.ok) throw new Error('Failed to load alert history');
            
            const history = await response.json();
            this.alertHistory = history;
            
            this.hideLoading(loading);
            this.renderAlertHistory(history, container);
            
        } catch (error) {
            console.error('Failed to load alert history:', error);
            this.hideLoading(loading);
            this.showError('Failed to load alert history');
        }
    }
    
    renderAlertHistory(history, container) {
        if (history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <h3>No Alert History</h3>
                    <p>No alerts found for the selected time period and filters.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="history-table">
                <table>
                    <thead>
                        <tr>
                            <th>Triggered</th>
                            <th>Message</th>
                            <th>Severity</th>
                            <th>Status</th>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(alert => `
                            <tr data-alert-id="${alert.id}">
                                <td>${this.formatDateTime(alert.triggered_at)}</td>
                                <td class="alert-message">${this.escapeHtml(alert.message)}</td>
                                <td>
                                    <span class="severity-badge ${alert.severity}">${alert.severity.toUpperCase()}</span>
                                </td>
                                <td>
                                    <span class="status-badge ${alert.status}">${alert.status.toUpperCase()}</span>
                                </td>
                                <td>${alert.metric_type.replace('_', ' ')}</td>
                                <td>${alert.trigger_value !== null ? alert.trigger_value : '--'}</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary" onclick="alertManager.showAlertDetails('${alert.id}', true)">
                                        <span class="icon">👁️</span> Details
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    async loadNotificationStatus() {
        try {
            const response = await fetch('/api/alerts/notifications/status');
            if (!response.ok) throw new Error('Chyba při načítání stavu notifikací');
            
            const status = await response.json();
            this.notificationStatus = status;
            
            this.renderNotificationChannels(status);
            this.updateNotificationStatusCard(status);
            
        } catch (error) {
            console.error('Failed to load notification status:', error);
            this.showError('Chyba při načítání stavu notifikací');
        }
    }
    
    renderNotificationChannels(status) {
        const container = document.getElementById('notificationChannelsContainer');
        
        const channels = Object.entries(status).map(([name, info]) => ({
            name,
            ...info
        }));
        
        if (channels.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <h3>No Notification Channels</h3>
                    <p>Configure notification channels to receive alerts.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = channels.map(channel => `
            <div class="channel-card">
                <div class="channel-icon ${channel.healthy ? 'online' : 'offline'}">
                    ${this.getChannelIcon(channel.name)}
                </div>
                <div class="channel-info">
                    <div class="channel-name">${this.formatChannelName(channel.name)}</div>
                    <div class="channel-status">
                        ${channel.healthy ? '✅ Online' : '❌ Offline'} • 
                        ${channel.enabled ? 'Enabled' : 'Disabled'}
                    </div>
                </div>
                <div class="channel-stats">
                    <div>Deliveries (24h): ${channel.deliveries_24h || 0}</div>
                    <div>Success Rate: ${Math.round((channel.success_rate_24h || 0) * 100)}%</div>
                    ${channel.last_delivery ? 
                        `<div>Last: ${this.formatDateTime(channel.last_delivery)}</div>` : 
                        '<div>Last: Never</div>'
                    }
                </div>
            </div>
        `).join('');
    }
    
    updateNotificationStatusCard(status) {
        const onlineCount = Object.values(status).filter(ch => ch.healthy).length;
        const totalCount = Object.keys(status).length;
        
        document.getElementById('channelsOnlineCount').textContent = `${onlineCount}/${totalCount}`;
        
        const statusCard = document.getElementById('notificationStatus');
        const statusIcon = document.getElementById('notificationStatusIcon');
        
        if (statusCard && statusIcon) {
            if (onlineCount === totalCount && totalCount > 0) {
                statusCard.classList.remove('offline');
                statusCard.classList.add('online');
                statusIcon.textContent = '🟢';
            } else {
                statusCard.classList.remove('online');
                statusCard.classList.add('offline');
                statusIcon.textContent = '🔴';
            }
        }
    }
    
    async sendTestNotification() {
        const checkboxes = document.querySelectorAll('input[type="checkbox"][value]');
        const selectedChannels = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        if (selectedChannels.length === 0) {
            this.showError('Vyberte alespoň jeden kanál pro test notifikací');
            return;
        }
        
        const button = document.getElementById('sendTestNotification');
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="spinner"></div> Odesílám...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/alerts/notifications/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    channels: selectedChannels
                })
            });
            
            if (!response.ok) throw new Error('Chyba při odesílání test notifikací');
            
            const result = await response.json();
            
            // Show results
            const successCount = result.results.filter(r => r.success).length;
            const totalCount = result.results.length;
            
            if (successCount === totalCount) {
                this.showSuccess(`Test notifikace úspěšně odeslány do všech ${totalCount} kanálů!`);
            } else {
                this.showWarning(`Test notifikace: ${successCount}/${totalCount} úspěšných`);
            }
            
            // Update notification history
            this.displayTestResults(result.results);
            
        } catch (error) {
            console.error('Failed to send test notifications:', error);
            this.showError('Chyba při odesílání test notifikací: ' + error.message);
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    async enableDesktopNotifications() {
        if (window.BrowserNotificationService) {
            try {
                // Check current permission status
                if (Notification.permission === 'denied') {
                    this.showWarning('⚠️ Desktop notifikace jsou zakázány v prohlížeči. Podívejte se do záložky "Notifikace" pro instrukce jak je povolit.');
                    // Switch to notifications tab to show instructions
                    this.switchTab('notifications');
                    return;
                }
                
                const granted = await window.BrowserNotificationService.requestNotificationPermission(true);
                if (granted) {
                    this.showSuccess('✅ Desktop notifikace byly úspěšně povoleny!');
                } else {
                    this.showWarning('Desktop notifikace nebyly povoleny. Zkontrolujte záložku "Notifikace" pro další instrukce.');
                    this.switchTab('notifications');
                }
            } catch (error) {
                this.showError('Chyba při povolování desktop notifikací: ' + error.message);
            }
        } else {
            this.showError('Browser Notification Service není dostupný');
        }
    }
    
    async testBrowserNotification() {
        const button = document.getElementById('testBrowserNotification');
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="spinner"></div> Generuji test...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/alerts/test-browser-notification', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Chyba při generování test notifikace');
            
            const result = await response.json();
            this.showSuccess('Test browser notifikace byla vygenerována! Měla by se zobrazit během několika sekund.');
            console.log('Test browser notification generated:', result);
            
        } catch (error) {
            console.error('Failed to generate test browser notification:', error);
            this.showError('Chyba při generování test browser notifikace: ' + error.message);
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    displayTestResults(results) {
        const container = document.getElementById('notificationHistoryContainer');
        
        const resultsHtml = results.map(result => `
            <div class="channel-card">
                <div class="channel-icon ${result.success ? 'online' : 'offline'}">
                    ${this.getChannelIcon(result.channel)}
                </div>
                <div class="channel-info">
                    <div class="channel-name">${this.formatChannelName(result.channel)}</div>
                    <div class="channel-status">
                        ${result.success ? '✅ Success' : '❌ Failed'} • 
                        To: ${result.recipient}
                    </div>
                    ${result.error ? `<div style="color: var(--error-color); font-size: 0.8rem;">${result.error}</div>` : ''}
                </div>
                <div class="channel-stats">
                    ${result.sent_at ? 
                        `<div>Sent: ${this.formatDateTime(result.sent_at)}</div>` : 
                        '<div>Not sent</div>'
                    }
                </div>
            </div>
        `).join('');
        
        container.innerHTML = `
            <h4>Test Notification Results</h4>
            ${resultsHtml}
        `;
    }
    
    // Alert action methods
    async showAlertDetails(alertId, isHistoryTab = false) {
        try {
            // First, try to find the alert in our local data
            let alert = null;
            
            if (isHistoryTab && this.alertHistory) {
                alert = this.alertHistory.find(a => a.id === alertId);
            } else if (this.activeAlerts) {
                alert = this.activeAlerts.find(a => a.id === alertId);
            }
            
            // If not found locally, fetch from API
            if (!alert) {
                const response = await fetch(`/api/alerts/${alertId}`);
                if (!response.ok) throw new Error('Failed to load alert details');
                alert = await response.json();
            }
            
            if (!alert) {
                throw new Error('Alert not found');
            }
            
            // Show the modal with alert details
            this.displayAlertModal(alert);
            
        } catch (error) {
            console.error('Failed to show alert details:', error);
            this.showError('Failed to load alert details: ' + error.message);
        }
    }
    
    displayAlertModal(alert) {
        const modal = document.getElementById('alertModal');
        const modalTitle = document.getElementById('alertModalTitle');
        const modalContent = document.getElementById('alertModalContent');
        
        // Set modal title
        modalTitle.textContent = `Alert Details - ${alert.severity.toUpperCase()}`;
        
        // Create status badge HTML
        const statusBadge = `<span class="status-badge ${alert.status}">${alert.status.charAt(0).toUpperCase() + alert.status.slice(1)}</span>`;
        const severityBadge = `<span class="severity-badge ${alert.severity}">${alert.severity.toUpperCase()}</span>`;
        
        // Format timestamps
        const formatDate = (dateStr) => {
            if (!dateStr) return 'N/A';
            return new Date(dateStr).toLocaleString();
        };
        
        // Build modal content
        modalContent.innerHTML = `
            <div class="alert-detail-section">
                <div class="alert-detail-header">
                    <div class="alert-badges">
                        ${statusBadge}
                        ${severityBadge}
                    </div>
                </div>
                
                <div class="alert-detail-grid">
                    <div class="alert-detail-item">
                        <label>Alert ID:</label>
                        <span class="monospace">${alert.id}</span>
                    </div>
                    
                    <div class="alert-detail-item">
                        <label>Rule ID:</label>
                        <span class="monospace">${alert.rule_id}</span>
                    </div>
                    
                    <div class="alert-detail-item">
                        <label>Metric Type:</label>
                        <span>${alert.metric_type}</span>
                    </div>
                    
                    <div class="alert-detail-item">
                        <label>Station ID:</label>
                        <span>${alert.station_id || 'All stations'}</span>
                    </div>
                    
                    <div class="alert-detail-item">
                        <label>Triggered At:</label>
                        <span>${formatDate(alert.triggered_at)}</span>
                    </div>
                    
                    ${alert.trigger_value !== null ? `
                    <div class="alert-detail-item">
                        <label>Current Value:</label>
                        <span class="value">${alert.trigger_value}</span>
                    </div>
                    ` : ''}
                    
                    ${alert.threshold_value !== null ? `
                    <div class="alert-detail-item">
                        <label>Threshold Value:</label>
                        <span class="value">${alert.threshold_value}</span>
                    </div>
                    ` : ''}
                    
                    ${alert.acknowledged_at ? `
                    <div class="alert-detail-item">
                        <label>Acknowledged At:</label>
                        <span>${formatDate(alert.acknowledged_at)}</span>
                    </div>
                    ` : ''}
                    
                    ${alert.acknowledged_by ? `
                    <div class="alert-detail-item">
                        <label>Acknowledged By:</label>
                        <span>${alert.acknowledged_by}</span>
                    </div>
                    ` : ''}
                    
                    ${alert.resolved_at ? `
                    <div class="alert-detail-item">
                        <label>Resolved At:</label>
                        <span>${formatDate(alert.resolved_at)}</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="alert-message">
                    <label>Message:</label>
                    <div class="message-content">${alert.message}</div>
                </div>
                
                ${alert.notifications_sent && alert.notifications_sent.length > 0 ? `
                <div class="alert-notifications">
                    <label>Notifications Sent:</label>
                    <div class="notifications-list">
                        ${alert.notifications_sent.map(notification => `
                            <div class="notification-item ${notification.success ? 'success' : 'failed'}">
                                <span class="channel">${notification.channel}</span>
                                <span class="recipient">${notification.recipient || 'N/A'}</span>
                                <span class="status">${notification.success ? '✅ Sent' : '❌ Failed'}</span>
                                ${notification.sent_at ? `<span class="time">${formatDate(notification.sent_at)}</span>` : ''}
                                ${notification.error ? `<span class="error">${notification.error}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        
        // Add event listeners to close buttons
        modal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.hideModal(modal);
            });
        });
        
        // Add click outside to close
        const clickOutsideHandler = (e) => {
            if (e.target === modal) {
                this.hideModal(modal);
                modal.removeEventListener('click', clickOutsideHandler);
            }
        };
        modal.addEventListener('click', clickOutsideHandler);
        
        // Show the modal
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    acknowledged_by: 'user'
                })
            });
            
            if (!response.ok) throw new Error('Failed to acknowledge alert');
            
            this.showSuccess('Alert acknowledged successfully');
            this.loadActiveAlerts(); // Refresh active alerts
            
        } catch (error) {
            console.error('Failed to acknowledge alert:', error);
            this.showError('Failed to acknowledge alert: ' + error.message);
        }
    }
    
    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    resolved_by: 'user'
                })
            });
            
            if (!response.ok) throw new Error('Failed to resolve alert');
            
            this.showSuccess('Alert resolved successfully');
            this.loadActiveAlerts(); // Refresh active alerts
            
        } catch (error) {
            console.error('Failed to resolve alert:', error);
            this.showError('Failed to resolve alert: ' + error.message);
        }
    }
    
    async acknowledgeAllAlerts() {
        if (this.activeAlerts.length === 0) {
            this.showInfo('No active alerts to acknowledge');
            return;
        }
        
        if (!confirm(`Are you sure you want to acknowledge all ${this.activeAlerts.length} active alerts?`)) {
            return;
        }
        
        let successCount = 0;
        let failCount = 0;
        
        for (const alert of this.activeAlerts) {
            try {
                await this.acknowledgeAlert(alert.id);
                successCount++;
            } catch (error) {
                failCount++;
            }
        }
        
        if (failCount === 0) {
            this.showSuccess(`Successfully acknowledged all ${successCount} alerts`);
        } else {
            this.showWarning(`Acknowledged ${successCount} alerts, ${failCount} failed`);
        }
    }
    
    // Rule management methods
    showRuleModal(ruleData = null) {
        const modal = document.getElementById('ruleModal');
        const title = document.getElementById('ruleModalTitle');
        const form = document.getElementById('ruleForm');
        
        if (ruleData) {
            title.textContent = 'Edit Alert Rule';
            this.populateRuleForm(ruleData);
            form.dataset.ruleId = ruleData.id;
        } else {
            title.textContent = 'Create Alert Rule';
            form.reset();
            delete form.dataset.ruleId;
        }
        
        this.showModal(modal);
        this.updateConditionFields();
    }
    
    populateRuleForm(rule) {
        document.getElementById('ruleName').value = rule.name || '';
        document.getElementById('ruleDescription').value = rule.description || '';
        document.getElementById('ruleMetricType').value = rule.metric_type || '';
        document.getElementById('ruleType').value = rule.rule_type || '';
        document.getElementById('ruleSeverity').value = rule.severity || '';
        document.getElementById('stationId').value = rule.station_id || '';
        document.getElementById('cooldownMinutes').value = rule.cooldown_minutes || 60;
        document.getElementById('maxAlertsPerHour').value = rule.max_alerts_per_hour || 5;
        document.getElementById('ruleEnabled').checked = rule.enabled !== false;
        
        // Set channels
        document.querySelectorAll('input[name="channels"]').forEach(checkbox => {
            checkbox.checked = rule.channels && rule.channels.includes(checkbox.value);
        });
        
        // Set conditions (will be handled by updateConditionFields)
        this.currentRuleConditions = rule.conditions || {};
    }
    
    updateConditionFields() {
        const ruleType = document.getElementById('ruleType').value;
        const metricType = document.getElementById('ruleMetricType').value;
        const container = document.getElementById('conditionFields');
        
        if (!ruleType) {
            container.innerHTML = '<p class="text-muted">Select a rule type to configure conditions</p>';
            return;
        }
        
        let fieldsHtml = '';
        const conditions = this.currentRuleConditions || {};
        
        switch (ruleType) {
            case 'threshold':
                fieldsHtml = `
                    <div class="form-row">
                        <div class="form-group">
                            <label for="thresholdOperator">Operator</label>
                            <select id="thresholdOperator" name="operator" required>
                                <option value="">Select Operator</option>
                                <option value="gt" ${conditions.operator === 'gt' ? 'selected' : ''}>Greater than (>)</option>
                                <option value="gte" ${conditions.operator === 'gte' ? 'selected' : ''}>Greater than or equal (>=)</option>
                                <option value="lt" ${conditions.operator === 'lt' ? 'selected' : ''}>Less than (<)</option>
                                <option value="lte" ${conditions.operator === 'lte' ? 'selected' : ''}>Less than or equal (<=)</option>
                                <option value="eq" ${conditions.operator === 'eq' ? 'selected' : ''}>Equal to (=)</option>
                                <option value="ne" ${conditions.operator === 'ne' ? 'selected' : ''}>Not equal to (!=)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="thresholdValue">Threshold Value</label>
                            <input type="number" id="thresholdValue" name="value" step="0.01" required
                                   value="${conditions.value || ''}"
                                   placeholder="Enter threshold value">
                        </div>
                    </div>
                `;
                break;
                
            case 'range':
                fieldsHtml = `
                    <div class="form-row">
                        <div class="form-group">
                            <label for="rangeMin">Minimum Value</label>
                            <input type="number" id="rangeMin" name="min" step="0.01"
                                   value="${conditions.min || ''}"
                                   placeholder="Minimum value (optional)">
                        </div>
                        <div class="form-group">
                            <label for="rangeMax">Maximum Value</label>
                            <input type="number" id="rangeMax" name="max" step="0.01"
                                   value="${conditions.max || ''}"
                                   placeholder="Maximum value (optional)">
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="rangeOutside" name="outside" 
                                   ${conditions.outside !== false ? 'checked' : ''}>
                            <span>Alert when value is outside range (uncheck for inside range)</span>
                        </label>
                    </div>
                `;
                break;
                
            case 'rate_of_change':
                fieldsHtml = `
                    <div class="form-row">
                        <div class="form-group">
                            <label for="changeThreshold">Change Threshold</label>
                            <input type="number" id="changeThreshold" name="change_threshold" 
                                   step="0.01" required
                                   value="${conditions.change_threshold || ''}"
                                   placeholder="Rate of change per minute">
                            <small>Maximum rate of change per minute before alerting</small>
                        </div>
                        <div class="form-group">
                            <label for="timeWindow">Time Window (minutes)</label>
                            <input type="number" id="timeWindow" name="time_window_minutes" 
                                   min="1" max="1440" required
                                   value="${conditions.time_window_minutes || 30}"
                                   placeholder="Time window in minutes">
                            <small>Time period to calculate rate of change</small>
                        </div>
                    </div>
                `;
                break;
                
            case 'missing_data':
                fieldsHtml = `
                    <div class="form-group">
                        <label for="maxAge">Maximum Data Age (minutes)</label>
                        <input type="number" id="maxAge" name="max_age_minutes" 
                               min="1" max="10080" required
                               value="${conditions.max_age_minutes || 60}"
                               placeholder="Maximum minutes without data">
                        <small>Alert if no data received for this many minutes</small>
                    </div>
                `;
                break;
        }
        
        container.innerHTML = fieldsHtml;
    }
    
    async saveAlertRule() {
        const form = document.getElementById('ruleForm');
        const formData = new FormData(form);
        
        const ruleData = {
            name: formData.get('name'),
            description: formData.get('description'),
            rule_type: formData.get('rule_type'),
            metric_type: formData.get('metric_type'),
            station_id: formData.get('station_id') || null,
            severity: formData.get('severity'),
            enabled: formData.has('enabled'),
            cooldown_minutes: parseInt(formData.get('cooldown_minutes')),
            max_alerts_per_hour: parseInt(formData.get('max_alerts_per_hour')),
            channels: Array.from(formData.getAll('channels')),
            conditions: this.buildConditions(formData)
        };
        
        // Validation
        if (!ruleData.conditions || Object.keys(ruleData.conditions).length === 0) {
            this.showError('Please configure rule conditions');
            return;
        }
        
        if (ruleData.channels.length === 0) {
            this.showError('Please select at least one notification channel');
            return;
        }
        
        const button = form.querySelector('button[type="submit"]');
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="spinner"></div> Saving...';
        button.disabled = true;
        
        try {
            const isEdit = form.dataset.ruleId;
            const url = isEdit ? `/api/alerts/rules/${form.dataset.ruleId}` : '/api/alerts/rules';
            const method = isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(ruleData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save rule');
            }
            
            this.showSuccess(isEdit ? 'Rule updated successfully!' : 'Rule created successfully!');
            this.hideModal(document.getElementById('ruleModal'));
            
            if (this.currentTab === 'alert-rules') {
                this.loadAlertRules();
            }
            
        } catch (error) {
            console.error('Failed to save rule:', error);
            this.showError('Failed to save rule: ' + error.message);
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    buildConditions(formData) {
        const ruleType = formData.get('rule_type');
        const conditions = {};
        
        switch (ruleType) {
            case 'threshold':
                conditions.operator = formData.get('operator');
                conditions.value = parseFloat(formData.get('value'));
                break;
                
            case 'range':
                if (formData.get('min')) conditions.min = parseFloat(formData.get('min'));
                if (formData.get('max')) conditions.max = parseFloat(formData.get('max'));
                conditions.outside = formData.has('outside');
                break;
                
            case 'rate_of_change':
                conditions.change_threshold = parseFloat(formData.get('change_threshold'));
                conditions.time_window_minutes = parseInt(formData.get('time_window_minutes'));
                break;
                
            case 'missing_data':
                conditions.max_age_minutes = parseInt(formData.get('max_age_minutes'));
                break;
        }
        
        return conditions;
    }
    
    async editRule(ruleId) {
        const rule = this.alertRules.find(r => r.id === ruleId);
        if (rule) {
            this.showRuleModal(rule);
        } else {
            this.showError('Rule not found');
        }
    }
    
    async toggleRule(ruleId, enabled) {
        try {
            const response = await fetch(`/api/alerts/rules/${ruleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled })
            });
            
            if (!response.ok) throw new Error('Failed to toggle rule');
            
            this.showSuccess(`Rule ${enabled ? 'enabled' : 'disabled'} successfully`);
            this.loadAlertRules();
            
        } catch (error) {
            console.error('Failed to toggle rule:', error);
            this.showError('Failed to toggle rule: ' + error.message);
        }
    }
    
    async deleteRule(ruleId) {
        const rule = this.alertRules.find(r => r.id === ruleId);
        if (!rule) {
            this.showError('Rule not found');
            return;
        }
        
        if (!confirm(`Are you sure you want to delete the rule "${rule.name}"? This action cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/alerts/rules/${ruleId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete rule');
            
            this.showSuccess('Rule deleted successfully');
            this.loadAlertRules();
            
        } catch (error) {
            console.error('Failed to delete rule:', error);
            this.showError('Failed to delete rule: ' + error.message);
        }
    }
    
    // Modal management
    showModal(modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    
    hideModal(modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    // Utility methods
    switchTab(tabName) {
        const tabs = document.querySelectorAll('.tab-button');
        const panels = document.querySelectorAll('.tab-panel');
        
        // Update active tab button
        tabs.forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabName) {
                tab.classList.add('active');
            }
        });
        
        // Show corresponding panel
        panels.forEach(panel => {
            panel.classList.remove('active');
            if (panel.id === tabName) {
                panel.classList.add('active');
            }
        });
        
        this.currentTab = tabName;
        this.loadTabData(tabName);
    }
    
    showLoading(element) {
        if (element) element.style.display = 'flex';
    }
    
    hideLoading(element) {
        if (element) element.style.display = 'none';
    }
    
    formatDateTime(dateString) {
        if (!dateString) return '--';
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    formatChannelName(channel) {
        const names = {
            email: '📧 Email',
            telegram: '💬 Telegram',
            discord: '🎮 Discord',
            browser: '🌐 Browser'
        };
        return names[channel] || channel;
    }
    
    getChannelIcon(channel) {
        const icons = {
            email: '📧',
            telegram: '💬',
            discord: '🎮',
            browser: '🌐'
        };
        return icons[channel] || '🔔';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Notification methods
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showWarning(message) {
        this.showNotification(message, 'warning');
    }
    
    showInfo(message) {
        this.showNotification(message, 'info');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        // Add to DOM
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Channel Management Methods
    async loadNotificationChannels() {
        try {
            const response = await fetch('/api/notification-channels');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const channels = await response.json();
            this.displayNotificationChannels(channels);
        } catch (error) {
            console.error('Error loading notification channels:', error);
            this.showNotification('Failed to load notification channels', 'error');
        }
    }
    
    displayNotificationChannels(channels) {
        const container = document.getElementById('channelsList');
        if (!container) return;
        
        if (channels.length === 0) {
            container.innerHTML = '<p class="text-muted">No notification channels configured</p>';
            return;
        }
        
        const channelsHtml = channels.map(channel => `
            <div class="channel-item" data-channel-id="${channel.id}">
                <div class="channel-info">
                    <div class="channel-header">
                        <span class="channel-type">${this.getChannelTypeIcon(channel.type)} ${channel.type.toUpperCase()}</span>
                        <span class="channel-status ${channel.enabled ? 'enabled' : 'disabled'}">
                            ${channel.enabled ? '✅ Enabled' : '⏸️ Disabled'}
                        </span>
                    </div>
                    <div class="channel-name">${channel.name}</div>
                    ${channel.description ? `<div class="channel-description">${channel.description}</div>` : ''}
                </div>
                <div class="channel-actions">
                    <button class="btn btn-sm btn-secondary" onclick="alertManager.testNotificationChannel('${channel.id}')">
                        Test
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="alertManager.editNotificationChannel('${channel.id}')">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="alertManager.deleteNotificationChannel('${channel.id}')">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = channelsHtml;
    }
    
    getChannelTypeIcon(type) {
        switch (type) {
            case 'discord': return '💬';
            case 'email': return '📧';
            case 'webhook': return '🔗';
            case 'telegram': return '📱';
            default: return '📢';
        }
    }
    
    showChannelModal(channelId = null) {
        const modal = document.getElementById('channelModal');
        const form = document.getElementById('channelForm');
        const title = document.getElementById('channelModalTitle');
        
        if (channelId) {
            title.textContent = 'Edit Notification Channel';
            this.loadChannelForEditing(channelId);
        } else {
            title.textContent = 'Add Notification Channel';
            form.reset();
            this.updateChannelConfigFields();
        }
        
        modal.style.display = 'flex';
    }
    
    async loadChannelForEditing(channelId) {
        try {
            const response = await fetch(`/api/notification-channels/${channelId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const channel = await response.json();
            this.populateChannelForm(channel);
        } catch (error) {
            console.error('Error loading channel for editing:', error);
            this.showNotification('Failed to load channel details', 'error');
        }
    }
    
    populateChannelForm(channel) {
        document.getElementById('channelId').value = channel.id || '';
        document.getElementById('channelName').value = channel.name || '';
        document.getElementById('channelType').value = channel.type || '';
        document.getElementById('channelDescription').value = channel.description || '';
        document.getElementById('channelEnabled').checked = channel.enabled !== false;
        
        // Store config for updateChannelConfigFields to use
        this.currentChannelConfig = channel.config || {};
        this.updateChannelConfigFields();
    }
    
    updateChannelConfigFields() {
        const channelType = document.getElementById('channelType').value;
        const container = document.getElementById('channelConfigFields');
        
        if (!channelType) {
            container.innerHTML = '<p class="text-muted">Select a channel type to configure</p>';
            return;
        }
        
        let fieldsHtml = '';
        const config = this.currentChannelConfig || {};
        
        switch (channelType) {
            case 'discord':
                fieldsHtml = `
                    <div class="form-group">
                        <label for="discordWebhookUrl">Discord Webhook URL *</label>
                        <input type="url" id="discordWebhookUrl" name="webhook_url" 
                               value="${config.webhook_url || ''}" required
                               placeholder="https://discord.com/api/webhooks/...">
                        <small class="form-text text-muted">
                            Get webhook URL from Discord server settings → Integrations → Webhooks
                        </small>
                    </div>
                    <div class="form-group">
                        <label for="discordUsername">Bot Username</label>
                        <input type="text" id="discordUsername" name="username" 
                               value="${config.username || 'PondMonitor'}"
                               placeholder="PondMonitor">
                    </div>
                    <div class="form-group">
                        <label for="discordAvatarUrl">Avatar URL</label>
                        <input type="url" id="discordAvatarUrl" name="avatar_url" 
                               value="${config.avatar_url || ''}"
                               placeholder="https://example.com/avatar.png">
                    </div>
                `;
                break;
                
            case 'email':
                fieldsHtml = `
                    <div class="form-group">
                        <label for="emailRecipients">Recipients *</label>
                        <input type="text" id="emailRecipients" name="recipients" 
                               value="${config.recipients || ''}" required
                               placeholder="user@example.com, admin@example.com">
                        <small class="form-text text-muted">
                            Comma-separated list of email addresses
                        </small>
                    </div>
                    <div class="form-group">
                        <label for="emailSubjectPrefix">Subject Prefix</label>
                        <input type="text" id="emailSubjectPrefix" name="subject_prefix" 
                               value="${config.subject_prefix || '[PondMonitor Alert]'}"
                               placeholder="[PondMonitor Alert]">
                    </div>
                `;
                break;
                
            case 'webhook':
                fieldsHtml = `
                    <div class="form-group">
                        <label for="webhookUrl">Webhook URL *</label>
                        <input type="url" id="webhookUrl" name="url" 
                               value="${config.url || ''}" required
                               placeholder="https://api.example.com/webhook">
                    </div>
                    <div class="form-group">
                        <label for="webhookMethod">HTTP Method</label>
                        <select id="webhookMethod" name="method">
                            <option value="POST" ${config.method === 'POST' ? 'selected' : ''}>POST</option>
                            <option value="PUT" ${config.method === 'PUT' ? 'selected' : ''}>PUT</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="webhookHeaders">Custom Headers</label>
                        <textarea id="webhookHeaders" name="headers" rows="3"
                                  placeholder="Authorization: Bearer token123&#10;Content-Type: application/json">${config.headers || ''}</textarea>
                        <small class="form-text text-muted">
                            One header per line in format: Header-Name: value
                        </small>
                    </div>
                `;
                break;
                
            case 'telegram':
                fieldsHtml = `
                    <div class="form-group">
                        <label for="telegramBotToken">Bot Token *</label>
                        <input type="text" id="telegramBotToken" name="bot_token" 
                               value="${config.bot_token || ''}" required
                               placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ">
                    </div>
                    <div class="form-group">
                        <label for="telegramChatId">Chat ID *</label>
                        <input type="text" id="telegramChatId" name="chat_id" 
                               value="${config.chat_id || ''}" required
                               placeholder="-1001234567890">
                        <small class="form-text text-muted">
                            Use @userinfobot to get chat ID
                        </small>
                    </div>
                `;
                break;
        }
        
        container.innerHTML = fieldsHtml;
    }
    
    async saveChannel() {
        const form = document.getElementById('channelForm');
        const formData = new FormData(form);
        const channelId = formData.get('id');
        
        // Build config object from form fields
        const config = {};
        const channelType = formData.get('type');
        
        switch (channelType) {
            case 'discord':
                config.webhook_url = formData.get('webhook_url');
                config.username = formData.get('username') || 'PondMonitor';
                if (formData.get('avatar_url')) config.avatar_url = formData.get('avatar_url');
                break;
            case 'email':
                config.recipients = formData.get('recipients');
                config.subject_prefix = formData.get('subject_prefix') || '[PondMonitor Alert]';
                break;
            case 'webhook':
                config.url = formData.get('url');
                config.method = formData.get('method') || 'POST';
                if (formData.get('headers')) {
                    config.headers = formData.get('headers');
                }
                break;
            case 'telegram':
                config.bot_token = formData.get('bot_token');
                config.chat_id = formData.get('chat_id');
                break;
        }
        
        const channelData = {
            name: formData.get('name'),
            type: channelType,
            description: formData.get('description') || '',
            enabled: formData.get('enabled') === 'on',
            config: config
        };
        
        try {
            const url = channelId ? `/api/notification-channels/${channelId}` : '/api/notification-channels';
            const method = channelId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(channelData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }
            
            this.showNotification(
                channelId ? 'Channel updated successfully' : 'Channel created successfully',
                'success'
            );
            
            this.closeChannelModal();
            await this.loadNotificationChannels();
            
        } catch (error) {
            console.error('Error saving channel:', error);
            this.showNotification(`Failed to save channel: ${error.message}`, 'error');
        }
    }
    
    closeChannelModal() {
        const modal = document.getElementById('channelModal');
        modal.style.display = 'none';
        this.currentChannelConfig = null;
    }
    
    editNotificationChannel(channelId) {
        this.showChannelModal(channelId);
    }
    
    async deleteNotificationChannel(channelId) {
        if (!confirm('Are you sure you want to delete this notification channel?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/notification-channels/${channelId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }
            
            this.showNotification('Channel deleted successfully', 'success');
            await this.loadNotificationChannels();
            
        } catch (error) {
            console.error('Error deleting channel:', error);
            this.showNotification(`Failed to delete channel: ${error.message}`, 'error');
        }
    }
    
    async testNotificationChannel(channelId) {
        try {
            const response = await fetch(`/api/notification-channels/${channelId}/test`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.showNotification('Test notification sent successfully', 'success');
            
        } catch (error) {
            console.error('Error testing channel:', error);
            this.showNotification(`Test failed: ${error.message}`, 'error');
        }
    }
    
    testCurrentChannel() {
        const form = document.getElementById('channelForm');
        const formData = new FormData(form);
        
        // Build temporary channel object for testing
        const config = {};
        const channelType = formData.get('type');
        
        switch (channelType) {
            case 'discord':
                config.webhook_url = formData.get('webhook_url');
                config.username = formData.get('username') || 'PondMonitor';
                if (formData.get('avatar_url')) config.avatar_url = formData.get('avatar_url');
                break;
            case 'email':
                config.recipients = formData.get('recipients');
                config.subject_prefix = formData.get('subject_prefix') || '[PondMonitor Alert]';
                break;
            case 'webhook':
                config.url = formData.get('url');
                config.method = formData.get('method') || 'POST';
                if (formData.get('headers')) {
                    config.headers = formData.get('headers');
                }
                break;
            case 'telegram':
                config.bot_token = formData.get('bot_token');
                config.chat_id = formData.get('chat_id');
                break;
        }
        
        const testData = {
            type: channelType,
            config: config
        };
        
        fetch('/api/notification-channels/test-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(result => {
            this.showNotification('Test notification sent successfully', 'success');
        })
        .catch(error => {
            console.error('Error testing channel config:', error);
            this.showNotification(`Test failed: ${error.message || 'Unknown error'}`, 'error');
        });
    }
    
    async loadAlertSettings() {
        try {
            const response = await fetch('/api/alert-settings');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const settings = await response.json();
            this.displayAlertSettings(settings);
        } catch (error) {
            console.error('Error loading alert settings:', error);
            this.showNotification('Failed to load alert settings', 'error');
        }
    }
    
    displayAlertSettings(settings) {
        const form = document.getElementById('alertSettingsForm');
        if (!form) return;
        
        // Populate form fields
        Object.keys(settings).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = settings[key];
                } else {
                    field.value = settings[key];
                }
            }
        });
    }
    
    async saveAlertSettings() {
        const form = document.getElementById('alertSettingsForm');
        const formData = new FormData(form);
        
        const settings = {};
        for (let [key, value] of formData.entries()) {
            // Convert checkbox values
            if (form.querySelector(`[name="${key}"]`).type === 'checkbox') {
                settings[key] = value === 'on';
            } else {
                settings[key] = value;
            }
        }
        
        try {
            const response = await fetch('/api/alert-settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }
            
            this.showNotification('Alert settings saved successfully', 'success');
            
        } catch (error) {
            console.error('Error saving alert settings:', error);
            this.showNotification(`Failed to save settings: ${error.message}`, 'error');
        }
    }
    
    // Cleanup
    destroy() {
        // Clear intervals
        Object.values(this.refreshIntervals).forEach(interval => {
            if (interval) clearInterval(interval);
        });
    }
}

// Initialize alert manager when DOM is loaded
let alertManager;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚨 AlertManager: DOM loaded, initializing...');
    try {
        alertManager = new AlertManager();
        console.log('✅ AlertManager: Successfully initialized');
    } catch (error) {
        console.error('❌ AlertManager: Failed to initialize:', error);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (alertManager) {
        alertManager.destroy();
    }
});

// Add notification styles to head
const notificationStyles = `
<style>
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.notification {
    padding: 12px 16px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-width: 300px;
    max-width: 500px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideIn 0.3s ease-out;
}

.notification.success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.notification.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.notification.warning {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeeba;
}

.notification.info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

.notification button {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: inherit;
    opacity: 0.7;
}

.notification button:hover {
    opacity: 1;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

[data-theme="dark"] .notification.success {
    background: #1e3a2e;
    color: #4caf50;
    border-color: #2e5233;
}

[data-theme="dark"] .notification.error {
    background: #3a1e1e;
    color: #f44336;
    border-color: #522e2e;
}

[data-theme="dark"] .notification.warning {
    background: #3a2e1e;
    color: #ff9800;
    border-color: #523e2e;
}

[data-theme="dark"] .notification.info {
    background: #1e2e3a;
    color: #2196f3;
    border-color: #2e3e52;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', notificationStyles);