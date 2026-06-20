"""
Flask API Backend for Process Scheduler Simulator with Cybersecurity
Provides REST endpoints and WebSocket support for real-time monitoring
"""

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List, Any

# Import our scheduler components
from process_scheduler_security import Process, ProcessScheduler, SecurityMonitor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'scheduler_security_key_2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state management
class SchedulerState:
    def __init__(self):
        self.scheduler = ProcessScheduler()
        self.is_running = False
        self.current_algorithm = "round_robin"
        self.process_counter = 1000
        self.simulation_thread = None
        self.real_time_updates = queue.Queue()
        
    def reset(self):
        """Reset scheduler state"""
        self.scheduler = ProcessScheduler()
        self.is_running = False
        self.real_time_updates = queue.Queue()

scheduler_state = SchedulerState()

@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current scheduler status"""
    return jsonify({
        'is_running': scheduler_state.is_running,
        'algorithm': scheduler_state.current_algorithm,
        'total_processes': len(scheduler_state.scheduler.processes),
        'completed_processes': len(scheduler_state.scheduler.completed_processes),
        'current_time': scheduler_state.scheduler.current_time
    })

@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get all processes with their current status"""
    processes_data = []
    
    for proc in scheduler_state.scheduler.processes:
        processes_data.append({
            'pid': proc.pid,
            'name': proc.name,
            'arrival_time': proc.arrival_time,
            'burst_time': proc.burst_time,
            'remaining_time': proc.remaining_time,
            'priority': proc.priority,
            'start_time': proc.start_time,
            'finish_time': proc.finish_time,
            'waiting_time': proc.waiting_time,
            'turnaround_time': proc.turnaround_time,
            'cpu_usage': proc.cpu_usage,
            'memory_usage': proc.memory_usage,
            'is_rogue': proc.is_rogue,
            'status': 'completed' if proc.finish_time > 0 else 'running' if proc.start_time > -1 else 'waiting'
        })
    
    return jsonify({'processes': processes_data})

@app.route('/api/processes', methods=['POST'])
def add_process():
    """Add a new process to the scheduler"""
    try:
        data = request.get_json()
        
        scheduler_state.process_counter += 1
        pid = scheduler_state.process_counter
        
        new_process = Process(
            pid=pid,
            name=data.get('name', f'proc_{pid}'),
            arrival_time=data.get('arrival_time', 0),
            burst_time=data.get('burst_time', 5),
            priority=data.get('priority', 3)
        )
        
        scheduler_state.scheduler.add_process(new_process)
        
        socketio.emit('process_added', {
            'pid': pid,
            'name': new_process.name,
            'arrival_time': new_process.arrival_time,
            'burst_time': new_process.burst_time,
            'priority': new_process.priority
        })
        
        return jsonify({
            'success': True,
            'message': f'Process {new_process.name} added successfully',
            'pid': pid
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error adding process: {str(e)}'
        }), 400

@app.route('/api/processes/<int:pid>', methods=['DELETE'])
def delete_process(pid):
    """Delete a process from the scheduler"""
    try:
        scheduler_state.scheduler.processes = [
            p for p in scheduler_state.scheduler.processes if p.pid != pid
        ]
        
        socketio.emit('process_deleted', {'pid': pid})
        
        return jsonify({
            'success': True,
            'message': f'Process {pid} deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting process: {str(e)}'
        }), 400

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start the scheduling simulation"""
    try:
        data = request.get_json()
        algorithm = data.get('algorithm', 'round_robin')
        
        if scheduler_state.is_running:
            return jsonify({
                'success': False,
                'message': 'Simulation is already running'
            }), 400
        
        if not scheduler_state.scheduler.processes:
            return jsonify({
                'success': False,
                'message': 'No processes to schedule'
            }), 400
        
        scheduler_state.current_algorithm = algorithm
        scheduler_state.is_running = True
        
        scheduler_state.simulation_thread = threading.Thread(
            target=run_simulation_background,
            args=(algorithm,)
        )
        scheduler_state.simulation_thread.daemon = True
        scheduler_state.simulation_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Simulation started with {algorithm} algorithm'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting simulation: {str(e)}'
        }), 500

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop the current simulation"""
    try:
        scheduler_state.is_running = False
        
        socketio.emit('simulation_stopped', {
            'message': 'Simulation stopped by user'
        })
        
        return jsonify({
            'success': True,
            'message': 'Simulation stopped'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping simulation: {str(e)}'
        }), 500

@app.route('/api/simulation/reset', methods=['POST'])
def reset_simulation():
    """Reset the scheduler state"""
    try:
        scheduler_state.reset()
        
        socketio.emit('simulation_reset', {
            'message': 'Simulation reset'
        })
        
        return jsonify({
            'success': True,
            'message': 'Simulation reset successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resetting simulation: {str(e)}'
        }), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current performance and security metrics"""
    try:
        if scheduler_state.scheduler.completed_processes:
            metrics = scheduler_state.scheduler.calculate_metrics(
                scheduler_state.scheduler.completed_processes
            )
        else:
            metrics = {
                'avg_waiting_time': 0,
                'avg_turnaround_time': 0,
                'total_processes': 0,
                'rogue_processes_detected': 0,
                'security_detection_rate': 0,
                'avg_cpu_usage': 0,
                'total_execution_time': 0
            }
        
        return jsonify({'metrics': metrics})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error calculating metrics: {str(e)}'
        }), 500

@app.route('/api/gantt', methods=['GET'])
def get_gantt_chart():
    """Get Gantt chart data"""
    try:
        gantt_data = []
        
        for entry in scheduler_state.scheduler.gantt_chart:
            gantt_data.append({
                'process': entry['process'],
                'start': entry['start'],
                'end': entry['end'],
                'cpu_usage': entry['cpu_usage'],
                'is_rogue': entry.get('cpu_usage', 0) > 80
            })
        
        return jsonify({'gantt_chart': gantt_data})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting Gantt chart: {str(e)}'
        }), 500

def run_simulation_background(algorithm: str):
    """Run the simulation in background thread with real-time updates"""
    try:
        socketio.emit('simulation_started', {
            'algorithm': algorithm,
            'total_processes': len(scheduler_state.scheduler.processes)
        })
        
        # Reset scheduler state
        scheduler_state.scheduler.completed_processes = []
        scheduler_state.scheduler.current_time = 0
        scheduler_state.scheduler.gantt_chart = []
        
        for process in scheduler_state.scheduler.processes:
            process.remaining_time = process.burst_time
            process.start_time = -1
            process.finish_time = 0
            process.waiting_time = 0
            process.turnaround_time = 0
            process.is_rogue = False
        
        rogue_pids = [p.pid for p in scheduler_state.scheduler.processes if 'rogue' in p.name.lower()]
        if rogue_pids:
            scheduler_state.scheduler.simulate_dos_attack(rogue_pids[0])
        
        if algorithm.lower() == "round_robin":
            run_round_robin_with_updates()
        elif algorithm.lower() == "priority":
            run_priority_with_updates()
        
        if scheduler_state.scheduler.completed_processes:
            metrics = scheduler_state.scheduler.calculate_metrics(
                scheduler_state.scheduler.completed_processes
            )
        else:
            metrics = {}
        
        socketio.emit('simulation_completed', {
            'algorithm': algorithm,
            'metrics': metrics,
            'gantt_chart': scheduler_state.scheduler.gantt_chart
        })
        
        scheduler_state.is_running = False
        
    except Exception as e:
        socketio.emit('simulation_error', {
            'message': f'Simulation error: {str(e)}'
        })
        scheduler_state.is_running = False

def run_round_robin_with_updates():
    """Round Robin with real-time WebSocket updates"""
    from collections import deque
    
    ready_queue = deque()
    completed = []
    current_time = 0
    time_quantum = scheduler_state.scheduler.time_quantum
    
    processes = sorted(scheduler_state.scheduler.processes.copy(), key=lambda p: p.arrival_time)
    process_index = 0
    
    while (process_index < len(processes) or ready_queue) and scheduler_state.is_running:
        while (process_index < len(processes) and 
               processes[process_index].arrival_time <= current_time):
            ready_queue.append(processes[process_index])
            process_index += 1
        
        if not ready_queue:
            current_time += 1
            continue
        
        current_process = ready_queue.popleft()
        
        security_status = scheduler_state.scheduler.security_monitor.monitor_process(current_process)
        if security_status:
            scheduler_state.scheduler.security_monitor.generate_security_alert(security_status)
            
            if current_process.is_rogue:
                socketio.emit('security_alert', {
                    'pid': current_process.pid,
                    'name': current_process.name,
                    'cpu_usage': current_process.cpu_usage,
                    'action': 'terminated',
                    'timestamp': datetime.now().isoformat()
                })
                
                current_process.finish_time = current_time
                current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed.append(current_process)
                continue
        
        if current_process.start_time == -1:
            current_process.start_time = current_time
        
        execution_time = min(time_quantum, current_process.remaining_time)
        current_time += execution_time
        current_process.remaining_time -= execution_time
        
        gantt_entry = {
            'process': current_process.name,
            'start': current_time - execution_time,
            'end': current_time,
            'cpu_usage': current_process.cpu_usage
        }
        scheduler_state.scheduler.gantt_chart.append(gantt_entry)
        
        socketio.emit('process_update', {
            'pid': current_process.pid,
            'name': current_process.name,
            'current_time': current_time,
            'remaining_time': current_process.remaining_time,
            'cpu_usage': current_process.cpu_usage,
            'is_rogue': current_process.is_rogue,
            'gantt_entry': gantt_entry
        })
        
        if current_process.remaining_time == 0:
            current_process.finish_time = current_time
            current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
            current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
            completed.append(current_process)
            
            socketio.emit('process_completed', {
                'pid': current_process.pid,
                'name': current_process.name,
                'finish_time': current_time,
                'waiting_time': current_process.waiting_time,
                'turnaround_time': current_process.turnaround_time
            })
        else:
            ready_queue.append(current_process)
        
        time.sleep(0.5)
    
    scheduler_state.scheduler.completed_processes = completed

def run_priority_with_updates():
    """Priority scheduling with real-time updates"""
    import heapq
    
    completed = []
    current_time = 0
    processes = sorted(scheduler_state.scheduler.processes.copy(), key=lambda p: p.arrival_time)
    ready_queue = []
    process_index = 0
    
    while (process_index < len(processes) or ready_queue) and scheduler_state.is_running:
        while (process_index < len(processes) and 
               processes[process_index].arrival_time <= current_time):
            heapq.heappush(ready_queue, 
                         (processes[process_index].priority, 
                          processes[process_index].arrival_time,
                          processes[process_index]))
            process_index += 1
        
        if not ready_queue:
            current_time += 1
            continue
        
        priority, arrival, current_process = heapq.heappop(ready_queue)
        
        security_status = scheduler_state.scheduler.security_monitor.monitor_process(current_process)
        if security_status:
            scheduler_state.scheduler.security_monitor.generate_security_alert(security_status)
            
            if current_process.is_rogue:
                socketio.emit('security_alert', {
                    'pid': current_process.pid,
                    'name': current_process.name,
                    'cpu_usage': current_process.cpu_usage,
                    'action': 'terminated',
                    'timestamp': datetime.now().isoformat()
                })
                
                current_process.finish_time = current_time
                current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed.append(current_process)
                continue
        
        if current_process.start_time == -1:
            current_process.start_time = current_time
        
        execution_time = current_process.remaining_time
        current_time += execution_time
        
        gantt_entry = {
            'process': current_process.name,
            'start': current_time - execution_time,
            'end': current_time,
            'cpu_usage': current_process.cpu_usage
        }
        scheduler_state.scheduler.gantt_chart.append(gantt_entry)
        
        socketio.emit('process_update', {
            'pid': current_process.pid,
            'name': current_process.name,
            'current_time': current_time,
            'remaining_time': 0,
            'cpu_usage': current_process.cpu_usage,
            'is_rogue': current_process.is_rogue,
            'gantt_entry': gantt_entry
        })
        
        current_process.finish_time = current_time
        current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
        current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
        current_process.remaining_time = 0
        completed.append(current_process)
        
        socketio.emit('process_completed', {
            'pid': current_process.pid,
            'name': current_process.name,
            'finish_time': current_time,
            'waiting_time': current_process.waiting_time,
            'turnaround_time': current_process.turnaround_time
        })
        
        time.sleep(0.8)
    
    scheduler_state.scheduler.completed_processes = completed

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to Process Scheduler Simulator'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    print("🚀 Starting Process Scheduler Simulator API Server")
    print("=" * 50)
    print("Features:")
    print("- REST API endpoints for process management")
    print("- WebSocket support for real-time updates")
    print("- Integrated security monitoring")
    print("- Multi-algorithm scheduling simulation")
    print("\nServer starting on http://localhost:5000")
    print("=" * 50)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
