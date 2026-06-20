"""
Process Scheduler Simulator with Cybersecurity
Core implementation of scheduling algorithms with integrated security monitoring
"""

import time
import heapq
import random
import threading
from collections import deque, defaultdict
from datetime import datetime
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Process:
    """Represents a system process with scheduling and security attributes"""
    pid: int
    name: str
    arrival_time: int
    burst_time: int
    priority: int
    remaining_time: int = 0
    start_time: int = -1
    finish_time: int = 0
    waiting_time: int = 0
    turnaround_time: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    is_rogue: bool = False
    
    def __post_init__(self):
        if self.remaining_time == 0:
            self.remaining_time = self.burst_time

class SecurityMonitor:
    """Cybersecurity monitoring component for process anomaly detection"""
    
    def __init__(self):
        self.cpu_threshold = 80.0
        self.memory_threshold = 70.0
        self.dos_detection_window = 10
        self.process_history: Dict[int, List[float]] = defaultdict(list)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        
    def monitor_process(self, process: Process) -> Dict[str, any]:
        """Monitor a process for suspicious activity"""
        try:
            # Simulate process metrics for demonstration
            if process.name == "rogue_proc" or "rogue" in process.name.lower():
                process.cpu_usage = random.uniform(85, 98)
                process.memory_usage = random.uniform(60, 80)
            else:
                process.cpu_usage = random.uniform(5, 25)
                process.memory_usage = random.uniform(10, 40)
            
            # Store metrics history
            self.process_history[process.pid].append(process.cpu_usage)
            
            # Keep only recent history
            if len(self.process_history[process.pid]) > 100:
                self.process_history[process.pid] = self.process_history[process.pid][-100:]
            
            # Detect anomalies
            anomaly_score = self._detect_anomaly(process)
            
            security_status = {
                'pid': process.pid,
                'name': process.name,
                'cpu_usage': process.cpu_usage,
                'memory_usage': process.memory_usage,
                'is_suspicious': self._is_suspicious(process),
                'anomaly_score': anomaly_score,
                'timestamp': datetime.now()
            }
            
            return security_status
            
        except Exception as e:
            logger.error(f"Error monitoring process {process.pid}: {e}")
            return {}
    
    def _detect_anomaly(self, process: Process) -> float:
        """Use ML-based anomaly detection"""
        if len(self.process_history[process.pid]) < 10:
            return 0.0
        
        try:
            recent_data = self.process_history[process.pid][-10:]
            features = np.array([
                [cpu, process.memory_usage, process.burst_time, process.priority]
                for cpu in recent_data
            ])
            
            if not self.is_trained and len(features) >= 10:
                self.anomaly_detector.fit(features[:5])
                self.is_trained = True
            
            if self.is_trained:
                score = self.anomaly_detector.decision_function(features[-1:])
                return float(score[0])
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Anomaly detection error for PID {process.pid}: {e}")
            return 0.0
    
    def _is_suspicious(self, process: Process) -> bool:
        """Rule-based suspicious activity detection"""
        suspicious_indicators = []
        
        if process.cpu_usage > self.cpu_threshold:
            suspicious_indicators.append(f"High CPU: {process.cpu_usage:.1f}%")
        
        if process.memory_usage > self.memory_threshold:
            suspicious_indicators.append(f"High Memory: {process.memory_usage:.1f}%")
        
        suspicious_names = ['rogue', 'malware', 'virus', 'trojan', 'backdoor']
        if any(name in process.name.lower() for name in suspicious_names):
            suspicious_indicators.append(f"Suspicious name: {process.name}")
        
        if suspicious_indicators:
            logger.warning(f"Suspicious activity detected in PID {process.pid}: {'; '.join(suspicious_indicators)}")
            process.is_rogue = True
            return True
        
        return False
    
    def generate_security_alert(self, security_status: Dict) -> None:
        """Generate security alerts for suspicious processes"""
        if security_status.get('is_suspicious', False):
            alert_msg = f"""
SECURITY ALERT - Rogue Process Detected!
========================================
PID: {security_status['pid']}
Process Name: {security_status['name']}
CPU Usage: {security_status['cpu_usage']:.1f}%
Memory Usage: {security_status['memory_usage']:.1f}%
Anomaly Score: {security_status['anomaly_score']:.3f}
Timestamp: {security_status['timestamp']}
Action: Process flagged for termination
"""
            logger.critical(alert_msg)

class ProcessScheduler:
    """Multi-algorithm process scheduler with security monitoring"""
    
    def __init__(self):
        self.processes: List[Process] = []
        self.ready_queue = []
        self.completed_processes: List[Process] = []
        self.current_time = 0
        self.time_quantum = 3
        self.security_monitor = SecurityMonitor()
        self.gantt_chart = []
        
    def add_process(self, process: Process) -> None:
        """Add a process to the scheduler"""
        self.processes.append(process)
        logger.info(f"Added process PID:{process.pid} Name:{process.name}")
    
    def simulate_dos_attack(self, target_pid: int, duration: int = 10) -> None:
        """Simulate a DoS attack by creating high CPU usage"""
        logger.warning(f"Simulating DoS attack on PID {target_pid} for {duration} seconds")
        
        def dos_simulation():
            start_time = time.time()
            while time.time() - start_time < duration:
                for process in self.processes:
                    if process.pid == target_pid:
                        process.cpu_usage = random.uniform(90, 99)
                time.sleep(0.1)
        
        dos_thread = threading.Thread(target=dos_simulation)
        dos_thread.daemon = True
        dos_thread.start()
    
    def round_robin_scheduling(self) -> List[Process]:
        """Round Robin scheduling with security monitoring"""
        logger.info("Starting Round Robin scheduling with security monitoring")
        
        ready_queue = deque()
        completed = []
        current_time = 0
        
        processes = sorted(self.processes.copy(), key=lambda p: p.arrival_time)
        process_index = 0
        
        while process_index < len(processes) or ready_queue:
            # Add arrived processes to ready queue
            while (process_index < len(processes) and 
                   processes[process_index].arrival_time <= current_time):
                ready_queue.append(processes[process_index])
                process_index += 1
            
            if not ready_queue:
                current_time += 1
                continue
            
            current_process = ready_queue.popleft()
            
            # Security monitoring
            security_status = self.security_monitor.monitor_process(current_process)
            if security_status:
                self.security_monitor.generate_security_alert(security_status)
                
                if current_process.is_rogue:
                    logger.critical(f"TERMINATING ROGUE PROCESS PID:{current_process.pid}")
                    current_process.finish_time = current_time
                    current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
                    current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                    completed.append(current_process)
                    continue
            
            if current_process.start_time == -1:
                current_process.start_time = current_time
            
            execution_time = min(self.time_quantum, current_process.remaining_time)
            current_time += execution_time
            current_process.remaining_time -= execution_time
            
            self.gantt_chart.append({
                'process': current_process.name,
                'start': current_time - execution_time,
                'end': current_time,
                'cpu_usage': current_process.cpu_usage
            })
            
            logger.info(f"Executed {current_process.name} for {execution_time} units "
                       f"(CPU: {current_process.cpu_usage:.1f}%)")
            
            if current_process.remaining_time == 0:
                current_process.finish_time = current_time
                current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed.append(current_process)
                logger.info(f"Process {current_process.name} completed at time {current_time}")
            else:
                ready_queue.append(current_process)
        
        return completed
    
    def priority_scheduling(self) -> List[Process]:
        """Priority-based scheduling with preemption and security monitoring"""
        logger.info("Starting Priority scheduling with security monitoring")
        
        completed = []
        current_time = 0
        processes = sorted(self.processes.copy(), key=lambda p: p.arrival_time)
        ready_queue = []
        
        process_index = 0
        
        while process_index < len(processes) or ready_queue:
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
            
            # Security monitoring
            security_status = self.security_monitor.monitor_process(current_process)
            if security_status:
                self.security_monitor.generate_security_alert(security_status)
                
                if current_process.is_rogue:
                    logger.critical(f"TERMINATING ROGUE PROCESS PID:{current_process.pid}")
                    current_process.finish_time = current_time
                    current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
                    current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                    completed.append(current_process)
                    continue
            
            if current_process.start_time == -1:
                current_process.start_time = current_time
            
            current_time += current_process.remaining_time
            
            self.gantt_chart.append({
                'process': current_process.name,
                'start': current_time - current_process.remaining_time,
                'end': current_time,
                'cpu_usage': current_process.cpu_usage
            })
            
            current_process.finish_time = current_time
            current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
            current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
            current_process.remaining_time = 0
            completed.append(current_process)
        
        return completed
    
    def calculate_metrics(self, completed_processes: List[Process]) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not completed_processes:
            return {}
        
        total_waiting = sum(p.waiting_time for p in completed_processes)
        total_turnaround = sum(p.turnaround_time for p in completed_processes)
        total_processes = len(completed_processes)
        
        rogue_processes = sum(1 for p in completed_processes if p.is_rogue)
        avg_cpu_usage = sum(p.cpu_usage for p in completed_processes) / total_processes
        
        metrics = {
            'avg_waiting_time': total_waiting / total_processes,
            'avg_turnaround_time': total_turnaround / total_processes,
            'total_processes': total_processes,
            'rogue_processes_detected': rogue_processes,
            'security_detection_rate': rogue_processes / total_processes if total_processes > 0 else 0,
            'avg_cpu_usage': avg_cpu_usage,
            'total_execution_time': max(p.finish_time for p in completed_processes) if completed_processes else 0
        }
        
        return metrics
    
    def print_results(self, completed_processes: List[Process], algorithm_name: str) -> None:
        """Print scheduling results with security analysis"""
        print(f"\n{algorithm_name} Scheduling Results with Security Analysis")
        print("=" * 70)
        
        print(f"{'PID':<5} {'Name':<12} {'AT':<4} {'BT':<4} {'Pri':<4} {'ST':<4} {'FT':<4} {'WT':<4} {'TAT':<4} {'CPU%':<6} {'Rogue'}")
        print("-" * 70)
        
        for p in completed_processes:
            rogue_status = "YES" if p.is_rogue else "NO"
            print(f"{p.pid:<5} {p.name:<12} {p.arrival_time:<4} {p.burst_time:<4} {p.priority:<4} "
                  f"{p.start_time:<4} {p.finish_time:<4} {p.waiting_time:<4} {p.turnaround_time:<4} "
                  f"{p.cpu_usage:<6.1f} {rogue_status}")
        
        metrics = self.calculate_metrics(completed_processes)
        print(f"\nPerformance Metrics:")
        print(f"Average Waiting Time: {metrics['avg_waiting_time']:.2f}")
        print(f"Average Turnaround Time: {metrics['avg_turnaround_time']:.2f}")
        print(f"Total Execution Time: {metrics['total_execution_time']}")
        
        print(f"\nSecurity Analysis:")
        print(f"Total Processes: {metrics['total_processes']}")
        print(f"Rogue Processes Detected: {metrics['rogue_processes_detected']}")
        print(f"Security Detection Rate: {metrics['security_detection_rate']:.1%}")
        print(f"Average CPU Usage: {metrics['avg_cpu_usage']:.1f}%")
        
        print(f"\nGantt Chart:")
        print("-" * 50)
        for entry in self.gantt_chart:
            status = "[ROGUE]" if entry['cpu_usage'] > 80 else "[NORMAL]"
            print(f"Time {entry['start']}-{entry['end']}: {entry['process']} {status} (CPU: {entry['cpu_usage']:.1f}%)")
    
    def run_simulation(self, algorithm: str = "round_robin") -> None:
        """Run the complete simulation with security monitoring"""
        logger.info(f"Starting {algorithm} simulation with cybersecurity monitoring")
        
        rogue_pids = [p.pid for p in self.processes if 'rogue' in p.name.lower()]
        if rogue_pids:
            self.simulate_dos_attack(rogue_pids[0])
        
        self.completed_processes = []
        self.current_time = 0
        self.gantt_chart = []
        
        for process in self.processes:
            process.remaining_time = process.burst_time
            process.start_time = -1
            process.finish_time = 0
            process.waiting_time = 0
            process.turnaround_time = 0
            process.is_rogue = False
        
        if algorithm.lower() == "round_robin":
            completed = self.round_robin_scheduling()
        elif algorithm.lower() == "priority":
            completed = self.priority_scheduling()
        else:
            logger.error(f"Unknown algorithm: {algorithm}")
            return
        
        self.print_results(completed, algorithm.title())
        logger.info(f"Simulation completed. Check scheduler_security.log for detailed security analysis.")

def main():
    """Main function to demonstrate the scheduler with security features"""
    
    scheduler = ProcessScheduler()
    
    sample_processes = [
        Process(pid=1, name="system_proc", arrival_time=0, burst_time=8, priority=1),
        Process(pid=2, name="user_app", arrival_time=1, burst_time=6, priority=3),
        Process(pid=3, name="background", arrival_time=2, burst_time=12, priority=5),
        Process(pid=4, name="rogue_proc", arrival_time=3, burst_time=20, priority=2),
        Process(pid=5, name="web_server", arrival_time=4, burst_time=9, priority=2),
        Process(pid=6, name="database", arrival_time=5, burst_time=15, priority=1)
    ]
    
    for process in sample_processes:
        scheduler.add_process(process)
    
    print("Process Scheduler Simulator with Cybersecurity")
    print("=" * 50)
    print("Features:")
    print("- Multi-algorithm scheduling (Round Robin, Priority)")
    print("- Real-time process monitoring")
    print("- Rogue process detection")
    print("- DoS attack simulation and detection")
    print("- Security alerting system")
    print("- Anomaly detection using Machine Learning")
    print()
    
    print("Running Round Robin Scheduling with Security Monitoring...")
    scheduler.run_simulation("round_robin")
    
    time.sleep(2)
    
    print("\n" + "="*70)
    print("Running Priority Scheduling with Security Monitoring...")
    scheduler.run_simulation("priority")

if __name__ == "__main__":
    main()
