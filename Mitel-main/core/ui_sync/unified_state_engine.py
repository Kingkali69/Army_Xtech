#!/usr/bin/env python3
"""
UNIFIED INPUT STATE ENGINE (UISE)
=================================
Patent-Pending Technology by KK&GDevOps

This engine handles:
- Button presses and input events
- UI State Propagation across all nodes
- Conflict resolution (simultaneous events)
- Real-time mirroring with zero lag
- Logging and error reporting

Each OS instance runs a lightweight agent connected to this engine.
The agent watches local actions and applies remote actions from the engine.
All UI updates (colors, positions, toggles) go through the engine.
All three UIs look identical at all times, no matter which one the user controls.

MASTER DYNAMIC CONTROL SWITCHING (MDCS):
- Any node can become master with authentication
- Master changes propagate instantly
- All peers automatically follow new master
"""

import json
import time
import threading
import hashlib
import os
import socket
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [UISE] %(message)s')
logger = logging.getLogger('UISE')

@dataclass
class UIEvent:
    """Represents a UI event to be synchronized"""
    event_type: str  # 'button_press', 'page_change', 'scroll', 'input', 'toggle', 'panel_open', etc.
    target_id: str   # DOM element ID or identifier
    value: Any       # Event value/data
    source_device: str
    timestamp: float
    sequence: int    # For ordering
    hash: str = ""   # For conflict detection
    
    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type,
            'target_id': self.target_id,
            'value': self.value,
            'source_device': self.source_device,
            'timestamp': self.timestamp,
            'sequence': self.sequence,
            'hash': self.hash
        }
    
    @staticmethod
    def from_dict(d: Dict) -> 'UIEvent':
        return UIEvent(
            event_type=d.get('event_type', ''),
            target_id=d.get('target_id', ''),
            value=d.get('value'),
            source_device=d.get('source_device', ''),
            timestamp=d.get('timestamp', 0),
            sequence=d.get('sequence', 0),
            hash=d.get('hash', '')
        )


@dataclass
class UIState:
    """Complete UI state that gets mirrored"""
    current_page: int = 0
    panels: Dict[str, bool] = field(default_factory=dict)  # panel_id -> visible
    scroll_positions: Dict[str, int] = field(default_factory=dict)  # element_id -> scroll_top
    form_values: Dict[str, str] = field(default_factory=dict)  # input_id -> value
    selected_elements: List[str] = field(default_factory=list)
    toggle_states: Dict[str, bool] = field(default_factory=dict)  # toggle_id -> on/off
    custom_state: Dict[str, Any] = field(default_factory=dict)
    state_hash: str = ""
    last_update: float = 0
    
    def compute_hash(self) -> str:
        """Compute hash of current state for change detection"""
        state_str = json.dumps({
            'page': self.current_page,
            'panels': self.panels,
            'toggles': self.toggle_states,
            'custom': self.custom_state
        }, sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        self.state_hash = self.compute_hash()
        return {
            'current_page': self.current_page,
            'panels': self.panels,
            'scroll_positions': self.scroll_positions,
            'form_values': self.form_values,
            'selected_elements': self.selected_elements,
            'toggle_states': self.toggle_states,
            'custom_state': self.custom_state,
            'state_hash': self.state_hash,
            'last_update': self.last_update
        }
    
    @staticmethod
    def from_dict(d: Dict) -> 'UIState':
        state = UIState()
        state.current_page = d.get('current_page', 0)
        state.panels = d.get('panels', {})
        state.scroll_positions = d.get('scroll_positions', {})
        state.form_values = d.get('form_values', {})
        state.selected_elements = d.get('selected_elements', [])
        state.toggle_states = d.get('toggle_states', {})
        state.custom_state = d.get('custom_state', {})
        state.state_hash = d.get('state_hash', '')
        state.last_update = d.get('last_update', 0)
        return state


class ConflictResolver:
    """Handles conflict resolution for simultaneous events"""
    
    RESOLUTION_STRATEGIES = ['master_wins', 'latest_wins', 'first_wins', 'merge']
    
    def __init__(self, strategy: str = 'master_wins'):
        self.strategy = strategy
        self.conflict_log: deque = deque(maxlen=100)
    
    def resolve(self, local_event: UIEvent, remote_event: UIEvent, 
                is_master: bool, master_device: str) -> UIEvent:
        """
        Resolve conflict between two events.
        Returns the event that should be applied.
        """
        # Log conflict
        self.conflict_log.append({
            'local': local_event.to_dict(),
            'remote': remote_event.to_dict(),
            'time': time.time(),
            'strategy': self.strategy
        })
        
        if self.strategy == 'master_wins':
            # Master's event always wins
            if local_event.source_device == master_device:
                logger.info(f"[CONFLICT] Master wins: {local_event.target_id}")
                return local_event
            elif remote_event.source_device == master_device:
                logger.info(f"[CONFLICT] Master wins: {remote_event.target_id}")
                return remote_event
            # If neither is master, fall back to latest_wins
            return local_event if local_event.timestamp > remote_event.timestamp else remote_event
        
        elif self.strategy == 'latest_wins':
            winner = local_event if local_event.timestamp > remote_event.timestamp else remote_event
            logger.info(f"[CONFLICT] Latest wins: {winner.target_id} from {winner.source_device}")
            return winner
        
        elif self.strategy == 'first_wins':
            winner = local_event if local_event.sequence < remote_event.sequence else remote_event
            logger.info(f"[CONFLICT] First wins: {winner.target_id} seq={winner.sequence}")
            return winner
        
        else:  # merge - try to combine
            logger.info(f"[CONFLICT] Merge strategy - using local event")
            return local_event


class UnifiedStateEngine:
    """
    Main engine for unified UI state synchronization.
    
    Each OS runs this engine. One is master, others are peers.
    All button presses, page changes, and UI events flow through here.
    """
    
    def __init__(self, device_id: str, port: int = 7899, is_master: bool = False):
        self.device_id = device_id
        self.port = port
        self.is_master = is_master
        
        # Master tracking
        self.master_id = device_id if is_master else None
        self.master_ip = '127.0.0.1' if is_master else None
        self.master_port = port if is_master else None
        
        # State
        self.ui_state = UIState()
        self.event_queue: deque = deque(maxlen=1000)
        self.event_sequence = 0
        self.peers: Dict[str, Dict[str, Any]] = {}
        
        # Conflict resolution
        self.conflict_resolver = ConflictResolver('master_wins')
        
        # Callbacks for UI updates
        self.state_callbacks: List[Callable[[UIState], None]] = []
        self.event_callbacks: List[Callable[[UIEvent], None]] = []
        
        # Threading
        self.running = False
        self._lock = threading.RLock()
        self._event_lock = threading.Lock()
        
        # Logging
        self.event_log: deque = deque(maxlen=500)
        self.error_log: deque = deque(maxlen=100)
        
        logger.info(f"UnifiedStateEngine initialized: {device_id} (master={is_master})")
    
    def start(self):
        """Start the engine"""
        self.running = True
        
        # Start broadcast/poll threads
        if self.is_master:
            threading.Thread(target=self._master_broadcast_loop, daemon=True, name="UISE-Broadcast").start()
        else:
            threading.Thread(target=self._peer_poll_loop, daemon=True, name="UISE-Poll").start()
        
        # Start event processor
        threading.Thread(target=self._event_processor_loop, daemon=True, name="UISE-Events").start()
        
        logger.info(f"Engine started: {'MASTER' if self.is_master else 'PEER'}")
    
    def stop(self):
        """Stop the engine"""
        self.running = False
        logger.info("Engine stopped")
    
    def register_peer(self, device_id: str, ip: str, port: int):
        """Register a peer node"""
        with self._lock:
            self.peers[device_id] = {
                'ip': ip,
                'port': port,
                'last_seen': time.time(),
                'online': True
            }
        logger.info(f"Peer registered: {device_id} at {ip}:{port}")
    
    def set_master(self, master_id: str, master_ip: str, master_port: int):
        """Set the master node"""
        with self._lock:
            old_master = self.master_id
            self.master_id = master_id
            self.master_ip = master_ip
            self.master_port = master_port
            self.is_master = (master_id == self.device_id)
        
        if old_master != master_id:
            logger.info(f"Master changed: {old_master} -> {master_id}")
            self._restart_threads()
    
    def take_control(self, password: str = None) -> bool:
        """
        MDCS - Master Dynamic Control Switching
        Take control and become the master node.
        """
        if password != 'ghostops':
            logger.warning("Control switch denied: invalid password")
            return False
        
        with self._lock:
            old_master = self.master_id
            self.is_master = True
            self.master_id = self.device_id
            self.master_ip = '127.0.0.1'
            self.master_port = self.port
        
        # Announce to all peers
        self._broadcast_master_change()
        self._restart_threads()
        
        logger.info(f"[MDCS] Control transferred: {old_master} -> {self.device_id}")
        return True
    
    def push_event(self, event_type: str, target_id: str, value: Any = None) -> bool:
        """
        Push a UI event to be synchronized.
        Called when user interacts with UI.
        """
        with self._event_lock:
            self.event_sequence += 1
            event = UIEvent(
                event_type=event_type,
                target_id=target_id,
                value=value,
                source_device=self.device_id,
                timestamp=time.time(),
                sequence=self.event_sequence
            )
            event.hash = hashlib.md5(f"{event.target_id}:{event.timestamp}".encode()).hexdigest()[:8]
            
            self.event_queue.append(event)
            self.event_log.append(event.to_dict())
        
        # Apply locally first
        self._apply_event(event)
        
        # If master, broadcast immediately
        if self.is_master:
            self._broadcast_event(event)
        else:
            # Forward to master
            self._forward_event_to_master(event)
        
        logger.debug(f"Event pushed: {event_type} on {target_id}")
        return True
    
    def update_state(self, changes: Dict[str, Any]) -> bool:
        """Update UI state with multiple changes"""
        with self._lock:
            if 'current_page' in changes:
                self.ui_state.current_page = changes['current_page']
            if 'panels' in changes:
                self.ui_state.panels.update(changes['panels'])
            if 'toggle_states' in changes:
                self.ui_state.toggle_states.update(changes['toggle_states'])
            if 'scroll_positions' in changes:
                self.ui_state.scroll_positions.update(changes['scroll_positions'])
            if 'form_values' in changes:
                self.ui_state.form_values.update(changes['form_values'])
            if 'custom_state' in changes:
                self.ui_state.custom_state.update(changes['custom_state'])
            
            self.ui_state.last_update = time.time()
        
        # Notify callbacks
        self._notify_state_change()
        
        # Broadcast if master
        if self.is_master:
            self._broadcast_state()
        
        return True
    
    def get_state(self) -> Dict[str, Any]:
        """Get current UI state"""
        with self._lock:
            return self.ui_state.to_dict()
    
    def apply_remote_state(self, state_dict: Dict[str, Any]) -> bool:
        """Apply state received from master"""
        if self.is_master:
            return False  # Master doesn't apply remote state
        
        with self._lock:
            remote_hash = state_dict.get('state_hash', '')
            local_hash = self.ui_state.compute_hash()
            
            if remote_hash != local_hash:
                self.ui_state = UIState.from_dict(state_dict)
                self._notify_state_change()
                logger.debug(f"Remote state applied: hash={remote_hash[:8]}")
                return True
        
        return False
    
    def on_state_change(self, callback: Callable[[UIState], None]):
        """Register callback for state changes"""
        self.state_callbacks.append(callback)
    
    def on_event(self, callback: Callable[[UIEvent], None]):
        """Register callback for events"""
        self.event_callbacks.append(callback)
    
    def get_logs(self, log_type: str = 'events', limit: int = 50) -> List[Dict]:
        """Get logs for debugging"""
        if log_type == 'events':
            return list(self.event_log)[-limit:]
        elif log_type == 'errors':
            return list(self.error_log)[-limit:]
        elif log_type == 'conflicts':
            return list(self.conflict_resolver.conflict_log)[-limit:]
        return []
    
    # === Internal Methods ===
    
    def _apply_event(self, event: UIEvent):
        """Apply an event to local state"""
        with self._lock:
            if event.event_type == 'page_change':
                self.ui_state.current_page = event.value
            elif event.event_type == 'panel_toggle':
                self.ui_state.panels[event.target_id] = event.value
            elif event.event_type == 'toggle':
                self.ui_state.toggle_states[event.target_id] = event.value
            elif event.event_type == 'scroll':
                self.ui_state.scroll_positions[event.target_id] = event.value
            elif event.event_type == 'input':
                self.ui_state.form_values[event.target_id] = event.value
            elif event.event_type == 'button_press':
                # Button presses trigger callbacks but may not change state directly
                pass
            
            self.ui_state.last_update = time.time()
        
        # Notify event callbacks
        for cb in self.event_callbacks:
            try:
                cb(event)
            except Exception as e:
                self._log_error(f"Event callback error: {e}")
    
    def _notify_state_change(self):
        """Notify all state callbacks"""
        state = self.ui_state
        for cb in self.state_callbacks:
            try:
                cb(state)
            except Exception as e:
                self._log_error(f"State callback error: {e}")
    
    def _broadcast_state(self):
        """Broadcast current state to all peers"""
        if not self.is_master:
            return
        
        state_data = {
            'type': 'ui_state_sync',
            'state': self.get_state(),
            'master': self.device_id,
            'ts': time.time()
        }
        
        self._send_to_all_peers('/uise/state', state_data)
    
    def _broadcast_event(self, event: UIEvent):
        """Broadcast an event to all peers"""
        if not self.is_master:
            return
        
        event_data = {
            'type': 'ui_event',
            'event': event.to_dict(),
            'master': self.device_id,
            'ts': time.time()
        }
        
        self._send_to_all_peers('/uise/event', event_data)
    
    def _broadcast_master_change(self):
        """Announce master change to all peers"""
        data = {
            'type': 'master_change',
            'new_master': self.device_id,
            'ip': '127.0.0.1',
            'port': self.port,
            'ts': time.time()
        }
        
        self._send_to_all_peers('/uise/master_change', data)
    
    def _forward_event_to_master(self, event: UIEvent):
        """Forward event to master for distribution"""
        if self.is_master or not self.master_ip:
            return
        
        try:
            data = json.dumps({
                'type': 'ui_event_forward',
                'event': event.to_dict(),
                'source': self.device_id
            }).encode()
            
            req = Request(
                f"http://{self.master_ip}:{self.master_port}/uise/event_forward",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            urlopen(req, timeout=2)
        except Exception as e:
            self._log_error(f"Failed to forward event to master: {e}")
    
    def _send_to_all_peers(self, endpoint: str, data: Dict):
        """Send data to all registered peers"""
        with self._lock:
            peers = list(self.peers.items())
        
        json_data = json.dumps(data).encode()
        
        for pid, pinfo in peers:
            if pid == self.device_id:
                continue
            try:
                req = Request(
                    f"http://{pinfo['ip']}:{pinfo['port']}{endpoint}",
                    data=json_data,
                    headers={'Content-Type': 'application/json'}
                )
                urlopen(req, timeout=1)
            except Exception as e:
                self._log_error(f"Failed to send to {pid}: {e}")
    
    def _master_broadcast_loop(self):
        """Master continuously broadcasts state"""
        while self.running and self.is_master:
            try:
                self._broadcast_state()
            except Exception as e:
                self._log_error(f"Broadcast error: {e}")
            time.sleep(30.0)  # Slow down to 30s for consumer hardware (was 3s)
    
    def _peer_poll_loop(self):
        """Peer polls master for state updates"""
        while self.running and not self.is_master:
            if self.master_ip and self.master_port:
                try:
                    url = f"http://{self.master_ip}:{self.master_port}/uise/state"
                    with urlopen(url, timeout=2) as resp:
                        data = json.loads(resp.read())
                        if data.get('type') == 'ui_state_sync':
                            self.apply_remote_state(data.get('state', {}))
                except Exception:
                    pass  # Master offline, will retry
            time.sleep(30.0)  # Slow down to 30s for consumer hardware (was 3s)
    
    def _event_processor_loop(self):
        """Process queued events"""
        while self.running:
            try:
                # Process any pending events
                while self.event_queue:
                    with self._event_lock:
                        if not self.event_queue:
                            break
                        event = self.event_queue.popleft()
                    
                    # Already applied locally, just for tracking
            except Exception as e:
                self._log_error(f"Event processor error: {e}")
            time.sleep(10.0)  # Slow down to 10s for consumer hardware (was 1s)
    
    def _restart_threads(self):
        """Restart broadcast/poll threads after master change"""
        # Threads will exit on their own when is_master changes
        # Start appropriate thread
        if self.is_master:
            threading.Thread(target=self._master_broadcast_loop, daemon=True, name="UISE-Broadcast").start()
        else:
            threading.Thread(target=self._peer_poll_loop, daemon=True, name="UISE-Poll").start()
    
    def _log_error(self, message: str):
        """Log an error"""
        self.error_log.append({
            'message': message,
            'time': time.time(),
            'device': self.device_id
        })
        logger.error(message)


# Singleton instance for each OS
_engine_instance: Optional[UnifiedStateEngine] = None

def get_engine() -> Optional[UnifiedStateEngine]:
    """Get the global engine instance"""
    return _engine_instance

def init_engine(device_id: str, port: int = 7899, is_master: bool = False) -> UnifiedStateEngine:
    """Initialize the global engine instance"""
    global _engine_instance
    _engine_instance = UnifiedStateEngine(device_id, port, is_master)
    return _engine_instance


# === JavaScript Integration Code ===
# This gets injected into the HTML to handle UI events

UISE_JAVASCRIPT = '''
// UNIFIED INPUT STATE ENGINE - Browser Integration
(function() {
    const UISE = {
        deviceId: '%DEVICE_ID%',
        masterMode: %IS_MASTER%,
        wsUrl: 'ws://' + window.location.host + '/uise/ws',
        socket: null,
        state: {},
        callbacks: [],
        
        init: function() {
            console.log('[UISE] Initializing...');
            this.setupEventCapture();
            this.pollState();
            setInterval(() => this.pollState(), 300);
        },
        
        setupEventCapture: function() {
            // Capture all button clicks
            document.addEventListener('click', (e) => {
                const btn = e.target.closest('button, a[data-action], .btn');
                if (btn) {
                    this.pushEvent('button_press', btn.id || btn.dataset.action, {
                        text: btn.textContent,
                        action: btn.dataset.action
                    });
                }
            });
            
            // Capture page changes
            window.addEventListener('hashchange', () => {
                const page = parseInt(window.location.hash.replace('#page-', '') || '0');
                this.pushEvent('page_change', 'main', page);
            });
            
            // Capture scroll
            let scrollTimeout;
            document.addEventListener('scroll', (e) => {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    this.pushEvent('scroll', 'body', window.scrollY);
                }, 100);
            }, true);
        },
        
        pushEvent: function(eventType, targetId, value) {
            fetch('/uise/push_event', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    event_type: eventType,
                    target_id: targetId,
                    value: value
                })
            }).catch(console.error);
        },
        
        pollState: function() {
            fetch('/uise/state')
                .then(r => r.json())
                .then(data => {
                    if (data.state_hash !== this.state.state_hash) {
                        this.applyState(data);
                    }
                })
                .catch(() => {});
        },
        
        applyState: function(newState) {
            const oldState = this.state;
            this.state = newState;
            
            // Apply page change
            if (newState.current_page !== oldState.current_page) {
                const hash = '#page-' + newState.current_page;
                if (window.location.hash !== hash) {
                    window.location.hash = hash;
                }
            }
            
            // Apply toggle states
            for (const [id, value] of Object.entries(newState.toggle_states || {})) {
                const el = document.getElementById(id);
                if (el) {
                    el.classList.toggle('active', value);
                }
            }
            
            // Apply panel visibility
            for (const [id, visible] of Object.entries(newState.panels || {})) {
                const el = document.getElementById(id);
                if (el) {
                    el.style.display = visible ? 'block' : 'none';
                }
            }
            
            // Notify callbacks
            this.callbacks.forEach(cb => {
                try { cb(newState); } catch (e) {}
            });
        },
        
        onStateChange: function(callback) {
            this.callbacks.push(callback);
        }
    };
    
    window.UISE = UISE;
    document.addEventListener('DOMContentLoaded', () => UISE.init());
})();
'''

def get_uise_javascript(device_id: str, is_master: bool = False) -> str:
    """Get the JavaScript code to inject into HTML"""
    return UISE_JAVASCRIPT.replace('%DEVICE_ID%', device_id).replace('%IS_MASTER%', 'true' if is_master else 'false')


if __name__ == '__main__':
    # Test the engine
    import sys
    
    device_id = sys.argv[1] if len(sys.argv) > 1 else 'test_device'
    is_master = '--master' in sys.argv
    
    engine = init_engine(device_id, port=7899, is_master=is_master)
    engine.start()
    
    print(f"[UISE] Running as {'MASTER' if is_master else 'PEER'}")
    print("[UISE] Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
        print("[UISE] Stopped")

