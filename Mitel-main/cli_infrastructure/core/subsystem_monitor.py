#!/usr/bin/env python3
"""
Subsystem Monitoring System
Tracks SC-SUB, EB-SUB, SEC-SUB health with heartbeat monitoring
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

class SubsystemStatus(Enum):
    """Subsystem health status"""
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"

@dataclass
class SubsystemEvent:
    """Subsystem event with timestamp"""
    event_id: str
    event_type: str  # SESSION, ALERT, UPDATE, THREAT
    timestamp: float
    severity: str  # HIGH, MEDIUM, LOW
    affected_subsystems: List[str]
    message: str

@dataclass
class RecoveryEvent:
    """Recovery action event"""
    subsystem: str
    action: str
    timestamp: float
    success: bool
    message: str

@dataclass
class SubsystemHealth:
    """Health status of a subsystem"""
    name: str
    status: SubsystemStatus
    last_heartbeat: float
    heartbeat_interval: float = 0.1  # 100ms
    consecutive_failures: int = 0
    recovery_count: int = 0

class SubsystemMonitor:
    """Monitor subsystem health (SC-SUB, EB-SUB, SEC-SUB)"""
    
    def __init__(self):
        # Start all subsystems as HEALTHY - they're active and sending heartbeats
        current_time = time.time()
        self.subsystems = {
            'SC-SUB': SubsystemHealth('SC-SUB', SubsystemStatus.HEALTHY, current_time),
            'EB-SUB': SubsystemHealth('EB-SUB', SubsystemStatus.HEALTHY, current_time),
            'SEC-SUB': SubsystemHealth('SEC-SUB', SubsystemStatus.HEALTHY, current_time)
        }
        
        self.events = deque(maxlen=100)  # Recent events
        self.recovery_events = deque(maxlen=50)  # Recovery actions
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Event counter
        self.event_counter = 0
        
    def start_monitoring(self):
        """Start monitoring subsystems"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Monitor loop - checks heartbeat every 100ms and simulates subsystem activity"""
        while self.monitoring:
            try:
                current_time = time.time()
                
                with self.lock:
                    for name, subsystem in self.subsystems.items():
                        time_since_heartbeat = current_time - subsystem.last_heartbeat
                        
                        # Simulate periodic heartbeats (every 0.5 seconds)
                        # This makes subsystems appear active
                        if time_since_heartbeat > 0.5:
                            # Send heartbeat
                            subsystem.last_heartbeat = current_time
                            # Always mark as healthy when heartbeat received
                            subsystem.status = SubsystemStatus.HEALTHY
                            subsystem.consecutive_failures = 0
                            # HEARTBEAT SPAM REMOVED - Heartbeats only shown in sidebar status, not main terminal feed
                            # This reduces log noise and makes important events (failover, recovery) more visible
                        
                        # Recalculate after potential heartbeat update
                        time_since_heartbeat = current_time - subsystem.last_heartbeat
                        
                        # Check if heartbeat is stale (more than 1.5 seconds = 3x the 0.5s interval)
                        # This gives a buffer so subsystems don't flip-flop
                        if time_since_heartbeat > 1.5:
                            if subsystem.status != SubsystemStatus.UNHEALTHY:
                                subsystem.status = SubsystemStatus.UNHEALTHY
                                subsystem.consecutive_failures += 1
                                self._add_event('ALERT', 'MEDIUM', [name], 
                                              f"{name} heartbeat timeout ({time_since_heartbeat:.1f}s)")
                        else:
                            # Heartbeat is fresh - ensure healthy status
                            if subsystem.status == SubsystemStatus.UNHEALTHY:
                                # Recovered!
                                subsystem.status = SubsystemStatus.HEALTHY
                                subsystem.consecutive_failures = 0
                                subsystem.recovery_count += 1
                                self._add_recovery_event(name, "restart", True, 
                                                       f"{name} restart [success]")
                                
                                # Log recovery to unified monitoring
                                try:
                                    from ghostops_adapter import GhostOpsServer
                                    from datetime import datetime
                                    ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                    GhostOpsServer.add_log(f"[RECOVERY] {name} restart [success]", name)
                                except:
                                    pass
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                print(f"[SUBSYSTEM MONITOR] Error: {e}")
                time.sleep(0.1)
    
    def heartbeat(self, subsystem_name: str):
        """Receive heartbeat from subsystem"""
        with self.lock:
            if subsystem_name in self.subsystems:
                self.subsystems[subsystem_name].last_heartbeat = time.time()
                if self.subsystems[subsystem_name].status == SubsystemStatus.UNHEALTHY:
                    # Mark as healthy on first heartbeat after failure
                    self.subsystems[subsystem_name].status = SubsystemStatus.HEALTHY
                    self.subsystems[subsystem_name].consecutive_failures = 0
    
    def _add_event(self, event_type: str, severity: str, affected: List[str], message: str):
        """Add event to log"""
        self.event_counter += 1
        event = SubsystemEvent(
            event_id=f"evt-{self.event_counter}",
            event_type=event_type,
            timestamp=time.time(),
            severity=severity,
            affected_subsystems=affected,
            message=message
        )
        self.events.append(event)
    
    def _add_recovery_event(self, subsystem: str, action: str, success: bool, message: str):
        """Add recovery event"""
        recovery = RecoveryEvent(
            subsystem=subsystem,
            action=action,
            timestamp=time.time(),
            success=success,
            message=message
        )
        self.recovery_events.append(recovery)
        
        # Log to unified monitoring
        try:
            from ghostops_adapter import GhostOpsServer
            from datetime import datetime
            ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            GhostOpsServer.add_log(f"[RECOVERY] {message}", subsystem)
        except:
            pass
    
    def get_status(self) -> Dict:
        """Get subsystem status report"""
        with self.lock:
            current_time = time.time()
            subsystem_status = {}
            
            for name, subsystem in self.subsystems.items():
                time_since = current_time - subsystem.last_heartbeat
                # Round to 0.1s to reduce jumping numbers
                rounded_time = round(time_since, 1)
                subsystem_status[name] = {
                    'status': subsystem.status.value,
                    'last_heartbeat': rounded_time,
                    'last_heartbeat_str': f"{rounded_time:.1f}s ago",
                    'recovery_count': subsystem.recovery_count,
                    'consecutive_failures': subsystem.consecutive_failures
                }
            
            # Get recent events
            recent_events = []
            for event in list(self.events)[-10:]:  # Last 10 events
                dt = datetime.fromtimestamp(event.timestamp)
                recent_events.append({
                    'id': event.event_id,
                    'type': event.event_type,
                    'timestamp': dt.strftime('%H:%M:%S.%f')[:-3],
                    'severity': event.severity,
                    'affected': event.affected_subsystems,
                    'message': event.message
                })
            
            # Get recovery events
            recovery_list = []
            for recovery in list(self.recovery_events)[-5:]:  # Last 5 recoveries
                dt = datetime.fromtimestamp(recovery.timestamp)
                recovery_list.append({
                    'subsystem': recovery.subsystem,
                    'action': recovery.action,
                    'timestamp': dt.strftime('%H:%M:%S'),
                    'success': recovery.success,
                    'message': recovery.message
                })
            
            # Statistics
            healthy_count = sum(1 for s in self.subsystems.values() if s.status == SubsystemStatus.HEALTHY)
            total_events = len(self.events)
            total_recoveries = sum(s.recovery_count for s in self.subsystems.values())
            uptime = current_time - self.start_time
            
            return {
                'subsystems': subsystem_status,
                'recent_events': recent_events,
                'recovery_events': recovery_list,
                'statistics': {
                    'total_events': total_events,
                    'recovery_actions': total_recoveries,
                    'healthy_subs': f"{healthy_count}/{len(self.subsystems)}",
                    'uptime': f"{uptime:.1f}s"
                }
            }
    
    def plan_recovery(self, subsystem: str) -> Dict:
        """Plan recovery for subsystem"""
        with self.lock:
            if subsystem not in self.subsystems:
                return {'status': 'error', 'message': f'Unknown subsystem: {subsystem}'}
            
            sub = self.subsystems[subsystem]
            plan = {
                'subsystem': subsystem,
                'current_status': sub.status.value,
                'failures': sub.consecutive_failures,
                'action': 'restart',
                'estimated_time': '5s'
            }
            
            return {'status': 'ok', 'plan': plan}
    
    def execute_recovery(self, subsystem: str) -> Dict:
        """Execute recovery plan"""
        with self.lock:
            if subsystem not in self.subsystems:
                return {'status': 'error', 'message': f'Unknown subsystem: {subsystem}'}
            
            sub = self.subsystems[subsystem]
            
            # Simulate recovery
            sub.status = SubsystemStatus.HEALTHY
            sub.last_heartbeat = time.time()
            sub.consecutive_failures = 0
            sub.recovery_count += 1
            
            self._add_recovery_event(subsystem, "restart", True, 
                                   f"{subsystem} restart [success]")
            
            return {'status': 'ok', 'message': f'{subsystem} recovery executed successfully'}

# Global instance
_monitor_instance = None

def get_subsystem_monitor() -> SubsystemMonitor:
    """Get global subsystem monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SubsystemMonitor()
        _monitor_instance.start_monitoring()
    return _monitor_instance

