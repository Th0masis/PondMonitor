/**
 * PondMonitor - Advanced Export Interface
 * Handles the advanced export functionality with filtering and progress tracking
 */

class AdvancedExportManager {
    constructor() {
        this.config = {
            dataTypes: [],
            format: 'excel',
            aggregation: 'raw',
            includeCharts: true,
            excelFormatting: true,
            filters: {}
        };
        
        this.exportOptions = null;
        this.currentEstimate = null;
        this.init();
    }

    async init() {
        try {
            // Load export configuration options
            await this.loadExportOptions();
            
            // Initialize form elements
            this.initializeForm();
            this.setupEventListeners();
            
            // Set default date range (last 7 days)
            this.setDateRange('7d');
            
            // Initial preview update
            await this.updatePreview();
            
        } catch (error) {
            console.error('Failed to initialize export manager:', error);
            PondUtils.showError('Chyba při načítání exportu');
        }
    }

    async loadExportOptions() {
        try {
            const response = await PondUtils.apiRequest('/api/advanced-export/config');
            this.exportOptions = response;
            
            this.renderDataTypeOptions();
            this.renderFormatOptions();
            this.renderAggregationOptions();
            this.setupFilterControls();
            
        } catch (error) {
            console.error('Failed to load export options:', error);
            throw error;
        }
    }

    renderDataTypeOptions() {
        const container = document.getElementById('dataTypeSelection');
        container.innerHTML = '';
        
        this.exportOptions.data_types.forEach(dataType => {
            const card = document.createElement('div');
            card.className = 'selection-card';
            card.dataset.value = dataType.id;
            card.innerHTML = `
                <div class="selection-card-title">${dataType.name}</div>
                <div class="selection-card-description">${dataType.description}</div>
            `;
            
            card.addEventListener('click', () => {
                this.toggleDataType(dataType.id, card);
            });
            
            container.appendChild(card);
        });
        
        // Select pond_data by default
        this.toggleDataType('pond_data', container.querySelector('[data-value="pond_data"]'));
    }

    renderFormatOptions() {
        const container = document.getElementById('formatSelection');
        container.innerHTML = '';
        
        this.exportOptions.export_formats.forEach(format => {
            const card = document.createElement('div');
            card.className = 'selection-card';
            card.dataset.value = format.id;
            card.innerHTML = `
                <div class="selection-card-title">${format.name}</div>
                <div class="selection-card-description">${format.description}</div>
            `;
            
            card.addEventListener('click', () => {
                this.selectFormat(format.id, card);
            });
            
            container.appendChild(card);
        });
        
        // Select Excel by default
        this.selectFormat('excel', container.querySelector('[data-value="excel"]'));
    }

    renderAggregationOptions() {
        const container = document.getElementById('aggregationSelection');
        container.innerHTML = '';
        
        this.exportOptions.aggregation_options.forEach(option => {
            const card = document.createElement('div');
            card.className = 'selection-card';
            card.dataset.value = option.id;
            card.innerHTML = `
                <div class="selection-card-title">${option.name}</div>
                <div class="selection-card-description">${option.description}</div>
            `;
            
            card.addEventListener('click', () => {
                this.selectAggregation(option.id, card);
            });
            
            container.appendChild(card);
        });
        
        // Select raw by default
        this.selectAggregation('raw', container.querySelector('[data-value="raw"]'));
    }

    setupFilterControls() {
        const filters = ['temp', 'battery', 'signal'];
        
        filters.forEach(filterType => {
            const checkbox = document.getElementById(`enable${filterType.charAt(0).toUpperCase() + filterType.slice(1)}Filter`);
            const controls = document.getElementById(`${filterType}RangeControls`);
            const minInput = document.getElementById(`${filterType}Min`);
            const maxInput = document.getElementById(`${filterType}Max`);
            
            checkbox.addEventListener('change', () => {
                controls.style.display = checkbox.checked ? 'block' : 'none';
                controls.parentElement.classList.toggle('enabled', checkbox.checked);
                
                if (checkbox.checked) {
                    this.initializeFilterRange(filterType);
                } else {
                    delete this.config.filters[`${filterType}_range`];
                }
                this.updatePreview();
            });
            
            [minInput, maxInput].forEach(input => {
                input.addEventListener('input', () => {
                    if (checkbox.checked) {
                        this.updateFilterRange(filterType);
                    }
                });
            });
        });
    }

    initializeFilterRange(filterType) {
        const ranges = this.exportOptions.filter_ranges;
        const range = ranges[`${filterType}_range`];
        
        if (range) {
            const minInput = document.getElementById(`${filterType}Min`);
            const maxInput = document.getElementById(`${filterType}Max`);
            
            minInput.value = range.min;
            maxInput.value = range.max;
            minInput.min = range.absolute_min;
            minInput.max = range.absolute_max;
            maxInput.min = range.absolute_min;
            maxInput.max = range.absolute_max;
            
            this.config.filters[`${filterType}_range`] = [range.min, range.max];
        }
    }

    updateFilterRange(filterType) {
        const minInput = document.getElementById(`${filterType}Min`);
        const maxInput = document.getElementById(`${filterType}Max`);
        
        const min = parseFloat(minInput.value);
        const max = parseFloat(maxInput.value);
        
        if (!isNaN(min) && !isNaN(max) && min <= max) {
            this.config.filters[`${filterType}_range`] = [min, max];
            this.updatePreview();
        }
    }

    initializeForm() {
        // Set default dates
        const endDate = new Date();
        const startDate = new Date(endDate.getTime() - (7 * 24 * 60 * 60 * 1000));
        
        document.getElementById('startDate').value = this.formatDateForInput(startDate);
        document.getElementById('endDate').value = this.formatDateForInput(endDate);
    }

    setupEventListeners() {
        // Date range changes
        ['startDate', 'endDate'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.updatePreview();
            });
        });

        // Excel options
        document.getElementById('includeCharts').addEventListener('change', (e) => {
            this.config.includeCharts = e.target.checked;
            this.updatePreview();
        });

        document.getElementById('excelFormatting').addEventListener('change', (e) => {
            this.config.excelFormatting = e.target.checked;
        });

        // Action buttons
        document.getElementById('refreshPreview').addEventListener('click', () => {
            this.updatePreview();
        });

        document.getElementById('estimateExport').addEventListener('click', () => {
            this.estimateExport();
        });

        document.getElementById('startExport').addEventListener('click', () => {
            this.startExport();
        });

        // Format change to show/hide Excel options
        this.updateExcelOptionsVisibility();
    }

    setDateRange(range) {
        const endDate = new Date();
        let startDate;
        
        switch (range) {
            case '1d':
                startDate = new Date(endDate.getTime() - (24 * 60 * 60 * 1000));
                break;
            case '3d':
                startDate = new Date(endDate.getTime() - (3 * 24 * 60 * 60 * 1000));
                break;
            case '7d':
                startDate = new Date(endDate.getTime() - (7 * 24 * 60 * 60 * 1000));
                break;
            case '30d':
                startDate = new Date(endDate.getTime() - (30 * 24 * 60 * 60 * 1000));
                break;
        }
        
        document.getElementById('startDate').value = this.formatDateForInput(startDate);
        document.getElementById('endDate').value = this.formatDateForInput(endDate);
        
        // Update active button
        document.querySelectorAll('.quick-range-buttons .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event?.target.classList.add('active');
        
        this.updatePreview();
    }

    toggleDataType(dataType, element) {
        const isSelected = element.classList.contains('selected');
        
        if (isSelected) {
            element.classList.remove('selected');
            const index = this.config.dataTypes.indexOf(dataType);
            if (index > -1) {
                this.config.dataTypes.splice(index, 1);
            }
        } else {
            element.classList.add('selected');
            this.config.dataTypes.push(dataType);
        }
        
        this.updatePreview();
        this.updateExportButton();
    }

    selectFormat(format, element) {
        // Remove selection from all format cards
        document.querySelectorAll('#formatSelection .selection-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select the clicked format
        element.classList.add('selected');
        this.config.format = format;
        
        this.updateExcelOptionsVisibility();
        this.updatePreview();
    }

    selectAggregation(aggregation, element) {
        // Remove selection from all aggregation cards
        document.querySelectorAll('#aggregationSelection .selection-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select the clicked aggregation
        element.classList.add('selected');
        this.config.aggregation = aggregation;
        
        this.updatePreview();
    }

    updateExcelOptionsVisibility() {
        const excelOptions = document.getElementById('excelOptions');
        const isExcel = this.config.format === 'excel';
        excelOptions.style.display = isExcel ? 'block' : 'none';
    }

    async updatePreview() {
        const previewContainer = document.getElementById('exportPreview');
        previewContainer.innerHTML = `
            <div class="preview-loading" style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-secondary);">
                <svg style="width: 2rem; height: 2rem; margin-bottom: 1rem; animation: spin 1s linear infinite;" fill="none" viewBox="0 0 24 24">
                    <circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p>Aktualizuje se náhled...</p>
            </div>
        `;
        
        try {
            // Simulate preview data - in real implementation, this would call an API
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const mockStats = [
                { label: 'Záznamy', value: '2,847', change: '+12%' },
                { label: 'Datové body', value: '15,234', change: '+8%' },
                { label: 'Časové období', value: '7 dní', change: null },
                { label: 'Velikost (~)', value: '850 KB', change: null }
            ];
            
            previewContainer.innerHTML = mockStats.map(stat => `
                <div class="preview-stat">
                    <div class="preview-stat-value">${stat.value}</div>
                    <div class="preview-stat-label">${stat.label}</div>
                    ${stat.change ? `<div class="preview-stat-change ${stat.change.startsWith('+') ? 'positive' : 'negative'}">${stat.change}</div>` : ''}
                </div>
            `).join('');
            
        } catch (error) {
            console.error('Failed to update preview:', error);
            previewContainer.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--color-red);">
                    <p>Chyba při načítání náhledu</p>
                </div>
            `;
        }
    }

    async estimateExport() {
        const estimateButton = document.getElementById('estimateExport');
        estimateButton.disabled = true;
        estimateButton.innerHTML = `
            <svg style="width: 1rem; height: 1rem; margin-right: 0.5rem; animation: spin 1s linear infinite;" fill="none" viewBox="0 0 24 24">
                <circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Odhaduje se...
        `;
        
        try {
            const exportConfig = this.buildExportConfig();
            const response = await PondUtils.apiRequest('/api/advanced-export/estimate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(exportConfig)
            });
            
            this.currentEstimate = response;
            this.displayEstimate(response);
            
            // Enable export button
            document.getElementById('startExport').disabled = false;
            
        } catch (error) {
            console.error('Failed to estimate export:', error);
            PondUtils.showError('Chyba při odhadu exportu');
        } finally {
            estimateButton.disabled = false;
            estimateButton.innerHTML = `
                <svg style="width: 1rem; height: 1rem; margin-right: 0.5rem;" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2h2zm-1 0h4V5a1 1 0 011-1h2a1 1 0 011 1v1h4a1 1 0 011 1v1H3V7a1 1 0 011-1zM3 12v3a1 1 0 001 1h12a1 1 0 001-1v-3H3z" clip-rule="evenodd"></path>
                </svg>
                Odhadnout velikost
            `;
        }
    }

    displayEstimate(estimate) {
        const container = document.getElementById('exportEstimate');
        container.style.display = 'grid';
        
        const items = [
            { label: 'Počet záznamů', value: estimate.records_count?.toLocaleString() || '0' },
            { label: 'Velikost souboru', value: this.formatFileSize(estimate.file_size || 0) },
            { label: 'Odhadovaný čas', value: this.formatDuration(estimate.estimated_time || 0) },
            { label: 'Datové typy', value: estimate.data_types_count || '0' }
        ];
        
        container.innerHTML = items.map(item => `
            <div class="estimate-item">
                <div class="estimate-value">${item.value}</div>
                <div class="estimate-label">${item.label}</div>
            </div>
        `).join('');
    }

    async startExport() {
        const exportButton = document.getElementById('startExport');
        const progressContainer = document.getElementById('exportProgress');
        
        // Show progress UI
        exportButton.style.display = 'none';
        progressContainer.style.display = 'flex';
        
        try {
            const exportConfig = this.buildExportConfig();
            
            // Start the export
            const response = await fetch('/api/advanced-export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(exportConfig)
            });
            
            if (!response.ok) {
                throw new Error(`Export failed: ${response.statusText}`);
            }
            
            // Update progress to 100%
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('progressText').textContent = '100%';
            document.getElementById('progressStatus').textContent = 'Export dokončen!';
            
            // Create download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // Get filename from response header or generate one
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition 
                ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
                : `export_${new Date().toISOString().slice(0, 10)}.${this.config.format}`;
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Show success message
            PondUtils.showSuccess('Export byl úspěšně dokončen a stahuje se');
            
        } catch (error) {
            console.error('Export failed:', error);
            PondUtils.showError('Chyba při exportu dat');
            
            document.getElementById('progressStatus').textContent = 'Export se nezdařil';
            document.getElementById('progressFill').style.backgroundColor = 'var(--color-red)';
        } finally {
            // Reset UI after a delay
            setTimeout(() => {
                exportButton.style.display = 'flex';
                progressContainer.style.display = 'none';
                document.getElementById('progressFill').style.width = '0%';
                document.getElementById('progressText').textContent = '0%';
                document.getElementById('progressStatus').textContent = 'Připravuje se...';
                document.getElementById('progressFill').style.backgroundColor = '';
            }, 3000);
        }
    }

    buildExportConfig() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        return {
            start_time: new Date(startDate).toISOString(),
            end_time: new Date(endDate).toISOString(),
            data_types: this.config.dataTypes,
            format: this.config.format,
            aggregation: this.config.aggregation,
            include_charts: this.config.includeCharts,
            excel_formatting: this.config.excelFormatting,
            temperature_range: this.config.filters.temp_range,
            battery_range: this.config.filters.battery_range,
            signal_range: this.config.filters.signal_range
        };
    }

    updateExportButton() {
        const button = document.getElementById('startExport');
        const hasDataTypes = this.config.dataTypes.length > 0;
        const hasValidDates = this.validateDateRange();
        
        button.disabled = !(hasDataTypes && hasValidDates);
    }

    validateDateRange() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        return startDate && endDate && new Date(startDate) <= new Date(endDate);
    }

    formatDateForInput(date) {
        return date.toISOString().slice(0, 16);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.ceil(seconds / 60)}m`;
        return `${Math.ceil(seconds / 3600)}h`;
    }
}

// Global functions for date range buttons
window.setDateRange = function(range) {
    if (window.exportManager) {
        window.exportManager.setDateRange(range);
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.exportManager = new AdvancedExportManager();
});