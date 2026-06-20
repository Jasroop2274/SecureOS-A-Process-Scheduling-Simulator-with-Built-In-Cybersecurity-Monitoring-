/**
 * Process Scheduler Simulator Frontend JavaScript
 * Handles WebSocket communication, UI updates, and user interactions
 */

class SchedulerApp {
    constructor() {
        this.socket = null;
        this.processes = [];
        this.ganttData = [];
        this.isConnected = false;
        this.isRunning = false;
        this.securityAlerts = [];
        
        this.initializeSocket();
        this.initializeEventHandlers();
        this.loadInitialData();
    }

    /**
     * Initialize WebSocket connection
     */
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.updateConnectionStatus();
            this.showNotification('Connected to server', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus();
            this.showNotification('Disconnected from server', 'error');
        });

        // Real-time event handlers
        this.socket.on('process_added', (data) => {
            this.showNotification(`Process ${data.name} added`, 'success');
            this.refreshProcesses();
        });

        this.socket.on('simulation_started', (data) => {
            this.isRunning = true;
            this.updateSimulationControls();
            this.showNotification(`Simulation started with ${data.algorithm}`, 'success');
            this.clearGanttChart();
        });

        this.socket.on('simulation_completed', (data) => {
            this.isRunning = false;
            this.updateSimulationControls();
            this.showNotification(`Simulation completed with ${data.algorithm}`, 'success');
            this.updateMetrics(data.metrics);
            this.updateGanttChart(data.gantt_chart);
        });

        this.socket.on('process_update', (data) => {
            this.handleProcessUpdate(data);
        });

        this.socket.on('security_alert', (data) => {
            this.handleSecurityAlert(data);
        });
    }

    /**
     * Initialize event handlers for UI elements
     */
    initializeEventHandlers() {
        // Process form submission
        document.getElementById('processForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addProcess();
        });

        // Auto-refresh process table every 5 seconds when simulation is running
        setInterval(() => {
            if (this.isRunning) {
                this.refreshProcesses();
            }
        }, 5000);

        // Auto-refresh status every 2 seconds
        setInterval(() => {
            this.refreshStatus();
        }, 2000);
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        await this.refreshStatus();
        await this.refreshProcesses();
        await this.refreshMetrics();
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus() {
        const statusEl = document.getElementById('connectionStatus');
        if (this.isConnected) {
            statusEl.className = 'connection-status connected';
            statusEl.innerHTML = '<i class="fas fa-wifi"></i> Connected';
        } else {
            statusEl.className = 'connection-status disconnected';
            statusEl.innerHTML = '<i class="fas fa-wifi"></i> Disconnected';
        }
    }

    /**
     * Update simulation control buttons
     */
    updateSimulationControls() {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');

        if (this.isRunning) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusDot.className = 'status-dot running';
            statusText.textContent = 'Running';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusDot.className = 'status-dot stopped';
            statusText.textContent = 'Stopped';
        }
    }

    /**
     * Add a new process
     */
    async addProcess() {
        const name = document.getElementById('processName').value.trim();
        const arrivalTime = parseInt(document.getElementById('arrivalTime').value);
        const burstTime = parseInt(document.getElementById('burstTime').value);
        const priority = parseInt(document.getElementById('priority').value);

        if (!name) {
            this.showNotification('Please enter a process name', 'error');
            return;
        }

        if (burstTime <= 0) {
            this.showNotification('Burst time must be greater than 0', 'error');
            return;
        }

        try {
            const response = await fetch('/api/processes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    arrival_time: arrivalTime,
                    burst_time: burstTime,
                    priority: priority
                })
            });

            const result = await response.json();

            if (result.success) {
                // Clear form
                document.getElementById('processForm').reset();
                document.getElementById('arrivalTime').value = '0';
                document.getElementById('burstTime').value = '5';
                document.getElementById('priority').value = '3';
                
                // Refresh processes
                await this.refreshProcesses();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error adding process: ' + error.message, 'error');
        }
    }

    /**
     * Start simulation
     */
    async startSimulation() {
        const algorithm = document.getElementById('algorithmSelect').value;

        try {
            const response = await fetch('/api/simulation/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ algorithm: algorithm })
            });

            const result = await response.json();

            if (!result.success) {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error starting simulation: ' + error.message, 'error');
        }
    }

    /**
     * Stop simulation
     */
    async stopSimulation() {
        try {
            const response = await fetch('/api/simulation/stop', {
                method: 'POST'
            });

            const result = await response.json();

            if (!result.success) {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error stopping simulation: ' + error.message, 'error');
        }
    }

    /**
     * Reset simulation
     */
    async resetSimulation() {
        try {
            const response = await fetch('/api/simulation/reset', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.clearGanttChart();
                this.clearMetrics();
                await this.refreshProcesses();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error resetting simulation: ' + error.message, 'error');
        }
    }

    /**
     * Refresh processes from server
     */
    async refreshProcesses() {
        try {
            const response = await fetch('/api/processes');
            const data = await response.json();
            this.processes = data.processes;
            this.updateProcessTable();
        } catch (error) {
            console.error('Error refreshing processes:', error);
        }
    }

    /**
     * Refresh status from server
     */
    async refreshStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.isRunning = status.is_running;
            this.updateSimulationControls();
            
            document.getElementById('currentAlgorithm').textContent = status.algorithm || 'None';
            document.getElementById('processCount').textContent = status.total_processes;
            document.getElementById('currentTime').textContent = status.current_time;
        } catch (error) {
            console.error('Error refreshing status:', error);
        }
    }

    /**
     * Refresh metrics from server
     */
    async refreshMetrics() {
        try {
            const response = await fetch('/api/metrics');
            const data = await response.json();
            this.updateMetrics(data.metrics);
        } catch (error) {
            console.error('Error refreshing metrics:', error);
        }
    }

    /**
     * Update process table
     */
    updateProcessTable() {
        const tbody = document.getElementById('processTableBody');
        
        if (this.processes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No processes added</td></tr>';
            return;
        }

        tbody.innerHTML = this.processes.map(process => {
            const statusClass = process.status === 'waiting' ? 'badge bg-warning' : 
                              process.status === 'running' ? 'badge bg-success' : 'badge bg-primary';
            
            const rowClass = process.is_rogue ? 'rogue-process' : '';
            const rogueIcon = process.is_rogue ? '<i class="fas fa-virus text-danger"></i>' : '';
            
            return `
                <tr class="${rowClass}">
                    <td>${process.pid}</td>
                    <td>${process.name} ${rogueIcon}</td>
                    <td>${process.arrival_time}</td>
                    <td>${process.burst_time}</td>
                    <td>${process.remaining_time}</td>
                    <td>${process.priority}</td>
                    <td>${process.cpu_usage.toFixed(1)}%</td>
                    <td><span class="${statusClass}">${process.status}</span></td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="app.deleteProcess(${process.pid})" 
                                ${this.isRunning ? 'disabled' : ''}>
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    /**
     * Delete a process
     */
    async deleteProcess(pid) {
        if (!confirm('Are you sure you want to delete this process?')) {
            return;
        }

        try {
            const response = await fetch(`/api/processes/${pid}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                await this.refreshProcesses();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error deleting process: ' + error.message, 'error');
        }
    }

    /**
     * Update metrics display
     */
    updateMetrics(metrics) {
        if (!metrics) return;
        
        document.getElementById('avgWaitingTime').textContent = metrics.avg_waiting_time?.toFixed(2) || '0.00';
        document.getElementById('avgTurnaroundTime').textContent = metrics.avg_turnaround_time?.toFixed(2) || '0.00';
        document.getElementById('rogueProcesses').textContent = metrics.rogue_processes_detected || 0;
        document.getElementById('detectionRate').textContent = ((metrics.security_detection_rate || 0) * 100).toFixed(1) + '%';
        document.getElementById('avgCpuUsage').textContent = (metrics.avg_cpu_usage || 0).toFixed(1) + '%';
        document.getElementById('totalExecutionTime').textContent = metrics.total_execution_time || 0;
    }

    /**
     * Clear metrics display
     */
    clearMetrics() {
        document.getElementById('avgWaitingTime').textContent = '0.00';
        document.getElementById('avgTurnaroundTime').textContent = '0.00';
        document.getElementById('rogueProcesses').textContent = '0';
        document.getElementById('detectionRate').textContent = '0%';
        document.getElementById('avgCpuUsage').textContent = '0.0%';
        document.getElementById('totalExecutionTime').textContent = '0';
    }

    /**
     * Update Gantt chart
     */
    updateGanttChart(ganttData) {
        const container = document.getElementById('ganttChart');
        
        if (!ganttData || ganttData.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No execution data available</p>';
            return;
        }

        // Calculate total time for scaling
        const totalTime = Math.max(...ganttData.map(item => item.end));
        
        container.innerHTML = ganttData.map(item => {
            const width = ((item.end - item.start) / totalTime) * 100;
            const isRogue = item.cpu_usage > 80;
            const barClass = isRogue ? 'rogue' : 'normal';
            
            return `
                <div class="gantt-bar ${barClass}" style="width: ${width}%; margin-bottom: 5px;">
                    ${item.process} (${item.start}-${item.end}) 
                    <small>${item.cpu_usage.toFixed(1)}% CPU</small>
                    ${isRogue ? '<i class="fas fa-exclamation-triangle ms-1"></i>' : ''}
                </div>
            `;
        }).join('');
    }

    /**
     * Clear Gantt chart
     */
    clearGanttChart() {
        document.getElementById('ganttChart').innerHTML = '<p class="text-muted text-center">Start simulation to see Gantt chart</p>';
    }

    /**
     * Handle real-time process updates
     */
    handleProcessUpdate(data) {
        // Update process in local array
        const processIndex = this.processes.findIndex(p => p.pid === data.pid);
        if (processIndex !== -1) {
            this.processes[processIndex].remaining_time = data.remaining_time;
            this.processes[processIndex].cpu_usage = data.cpu_usage;
            this.processes[processIndex].is_rogue = data.is_rogue;
            this.processes[processIndex].status = data.remaining_time > 0 ? 'running' : 'completed';
        }
        
        // Update current time
        document.getElementById('currentTime').textContent = data.current_time;
        
        // Update table
        this.updateProcessTable();
        
        // Add to Gantt chart if gantt_entry is provided
        if (data.gantt_entry) {
            this.addGanttEntry(data.gantt_entry);
        }
    }

    /**
     * Add single Gantt entry (for real-time updates)
     */
    addGanttEntry(entry) {
        const container = document.getElementById('ganttChart');
        
        if (container.innerHTML.includes('Start simulation')) {
            container.innerHTML = '';
        }
        
        const isRogue = entry.cpu_usage > 80;
        const barClass = isRogue ? 'rogue' : 'normal';
        
        const ganttBar = document.createElement('div');
        ganttBar.className = `gantt-bar ${barClass}`;
        ganttBar.style.marginBottom = '5px';
        ganttBar.innerHTML = `
            ${entry.process} (${entry.start}-${entry.end}) 
            <small>${entry.cpu_usage.toFixed(1)}% CPU</small>
            ${isRogue ? '<i class="fas fa-exclamation-triangle ms-1"></i>' : ''}
        `;
        
        container.appendChild(ganttBar);
        
        // Scroll to bottom to show latest entry
        container.scrollTop = container.scrollHeight;
    }

    /**
     * Handle security alerts
     */
    handleSecurityAlert(data) {
        this.securityAlerts.unshift(data);
        
        // Keep only last 10 alerts
        if (this.securityAlerts.length > 10) {
            this.securityAlerts = this.securityAlerts.slice(0, 10);
        }
        
        this.updateSecurityAlerts();
        this.showNotification(`SECURITY ALERT: Rogue process ${data.name} detected!`, 'error');
    }

    /**
     * Update security alerts panel
     */
    updateSecurityAlerts() {
        const container = document.getElementById('securityAlerts');
        const alertCount = document.getElementById('alertCount');
        
        alertCount.textContent = this.securityAlerts.length;
        
        if (this.securityAlerts.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No security alerts</p>';
            return;
        }

        container.innerHTML = this.securityAlerts.map(alert => `
            <div class="security-alert">
                <strong>PID ${alert.pid}: ${alert.name}</strong><br>
                <small>CPU Usage: ${alert.cpu_usage.toFixed(1)}% | Action: ${alert.action}</small><br>
                <small class="text-muted">${new Date(alert.timestamp).toLocaleTimeString()}</small>
            </div>
        `).join('');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 1050;
            min-width: 300px;
            animation: slideInRight 0.3s ease;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

/**
 * Utility Functions
 */

// Add sample processes
function addSampleProcesses() {
    const sampleProcesses = [
        { name: 'system_service', arrival: 0, burst: 8, priority: 1 },
        { name: 'web_browser', arrival: 1, burst: 12, priority: 3 },
        { name: 'text_editor', arrival: 2, burst: 6, priority: 4 },
        { name: 'media_player', arrival: 3, burst: 15, priority: 3 },
        { name: 'background_task', arrival: 4, burst: 10, priority: 5 }
    ];
    
    sampleProcesses.forEach(async (proc, index) => {
        setTimeout(async () => {
            document.getElementById('processName').value = proc.name;
            document.getElementById('arrivalTime').value = proc.arrival;
            document.getElementById('burstTime').value = proc.burst;
            document.getElementById('priority').value = proc.priority;
            await app.addProcess();
        }, index * 200);
    });
}

// Add rogue process
function addRogueProcess() {
    document.getElementById('processName').value = 'rogue_malware';
    document.getElementById('arrivalTime').value = '5';
    document.getElementById('burstTime').value = '20';
    document.getElementById('priority').value = '2';
    
    app.showNotification('Rogue process template loaded - click Add Process', 'warning');
}

// Refresh processes
function refreshProcesses() {
    app.refreshProcesses();
}

// Start simulation
function startSimulation() {
    app.startSimulation();
}

// Stop simulation  
function stopSimulation() {
    app.stopSimulation();
}

// Reset simulation
function resetSimulation() {
    app.resetSimulation();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SchedulerApp();
    
    console.log('Process Scheduler Simulator Frontend Initialized');
    console.log('Features: Real-time updates, WebSocket communication, Interactive UI');
});
